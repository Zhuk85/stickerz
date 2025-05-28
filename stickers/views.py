import mimetypes
import logging
import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import City, Sticker, Category, Like, Comment, Notification, Chat, Message, User
from django.db.models import Count, Q
from PIL import Image
from .forms import CustomUserCreationForm
from moviepy.editor import VideoFileClip
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files.base import ContentFile
from transliterate import translit
import re
from background_task import background

# Настройка логирования
logger = logging.getLogger(__name__)

def get_notification_count(user):
    if user.is_authenticated:
        notification_count = Notification.objects.filter(user=user, is_read=False).count()
        chats = user.chats.all()
        unread_messages = sum(chat.messages.filter(is_read=False).exclude(sender=user).count() for chat in chats)
        return notification_count + unread_messages
    return 0

def clean_filename(filename):
    """Очищаем имя файла: транслитерируем кириллицу и убираем недопустимые символы."""
    # Транслитерируем кириллицу в латиницу
    filename = translit(filename, 'ru', reversed=True)
    # Убираем недопустимые символы, оставляем только буквы, цифры, подчеркивания и точки
    filename = re.sub(r'[^a-zA-Z0-9_.]', '_', filename)
    # Убираем множественные подчеркивания
    filename = re.sub(r'_+', '_', filename)
    # Убираем подчеркивания в начале и конце
    filename = filename.strip('_')
    return filename

def home(request):
    logger.info(f"User {request.user.username if request.user.is_authenticated else 'Anonymous'} accessed home page. Language: {request.LANGUAGE_CODE}")
    cities = City.objects.all()
    city_stickers = []
    for city in cities:
        sticker = Sticker.objects.filter(city=city).first()
        logger.debug(f"City: {city.name}, city image: {city.image}, sticker: {sticker}, sticker image: {sticker.image if sticker else 'No sticker'}")
        city_stickers.append({
            'city': city.slug,
            'original_name': city.name,
            'sticker': sticker,
            'image': city.image
        })
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/home.html', {
        'city_stickers': city_stickers,
        'notification_count': notification_count
    })

def city_stickers(request, city_slug):
    city = get_object_or_404(City, slug=city_slug)
    categories = Category.objects.all()
    category_filter = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '-created_at')
    categories_with_stickers = []
    for category in categories:
        stickers = Sticker.objects.filter(city=city, category=category)
        if category_filter and category.id != int(category_filter):
            continue
        sort_options = {
            '-created_at': '-created_at',
            'created_at': 'created_at',
        }
        stickers = stickers.order_by(sort_options.get(sort_by, '-created_at'))
        sticker = stickers.first() if stickers.exists() else None
        categories_with_stickers.append({
            'category': category,
            'sticker': sticker,
        })
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/city_stickers.html', {
        'city': city,
        'categories_with_stickers': categories_with_stickers,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'categories': categories,
        'notification_count': notification_count
    })

def category_stickers(request, city_slug, category_id):
    city = get_object_or_404(City, slug=city_slug)
    category = get_object_or_404(Category, id=category_id)
    stickers = Sticker.objects.filter(city=city, category=category).annotate(
        like_count=Count('like')
    ).order_by('-created_at')
    paginator = Paginator(stickers, 10)
    page = request.GET.get('page')
    try:
        stickers_page = paginator.page(page)
    except PageNotAnInteger:
        stickers_page = paginator.page(1)
    except EmptyPage:
        stickers_page = paginator.page(paginator.num_pages)
    for sticker in stickers_page:
        sticker.is_liked = request.user.is_authenticated and sticker.like_set.filter(user=request.user).exists()
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/category_stickers.html', {
        'city': city.name,
        'category': category.name,
        'stickers': stickers_page,
        'notification_count': notification_count
    })

def sticker_detail(request, sticker_id):
    sticker = get_object_or_404(Sticker.objects.annotate(like_count=Count('like')), id=sticker_id)
    comments = sticker.comment_set.all().order_by('-created_at')
    is_liked = request.user.is_authenticated and sticker.like_set.filter(user=request.user).exists()
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/sticker_detail.html', {
        'sticker': sticker,
        'comments': comments,
        'is_liked': is_liked,
        'like_count': sticker.like_count,
        'notification_count': notification_count
    })

@login_required
def profile(request):
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    if notifications:
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    user_stickers = Sticker.objects.filter(user=user).annotate(
        like_count=Count('like')
    ).order_by('-created_at')
    # Добавляем отладочный лог
    logger.info(f"Profile page for user {user.username}: {len(user_stickers)} stickers found")
    for sticker in user_stickers:
        logger.info(f"Sticker ID: {sticker.id}, User: {sticker.user.username}, City: {sticker.city.name if sticker.city else 'None'}, Category: {sticker.category.name if sticker.category else 'None'}")
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/profile.html', {
        'user': user,
        'user_stickers': user_stickers,
        'notifications': notifications,
        'notification_count': notification_count
    })

def top_stickers(request):
    top_stickers = Sticker.objects.annotate(
        like_count=Count('like')
    ).order_by('-like_count')[:10]
    for sticker in top_stickers:
        sticker.is_liked = request.user.is_authenticated and sticker.like_set.filter(user=request.user).exists()
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/top.html', {
        'top_stickers': top_stickers,
        'notification_count': notification_count
    })

@login_required
def add_comment(request, sticker_id):
    if request.method == 'POST':
        sticker = get_object_or_404(Sticker, id=sticker_id)
        text = request.POST.get('comment_text', '').strip()
        if text:
            comment = Comment.objects.create(user=request.user, sticker=sticker, text=text)
            if sticker.user != request.user:
                Notification.objects.create(
                    user=sticker.user,
                    sender=request.user,
                    sticker=sticker,
                    message=f"{request.user.username} прокомментировал ваш стикер: '{text[:50]}'..."
                )
        return redirect('sticker_detail', sticker_id=sticker_id)
    return redirect('home')

@login_required
def toggle_like(request, sticker_id):
    sticker = get_object_or_404(Sticker, id=sticker_id)
    user = request.user
    like, created = Like.objects.get_or_create(user=user, sticker=sticker)
    if not created:
        like.delete()
        message = "Лайк удалён"
    else:
        message = "Лайк добавлен"
        if sticker.user != user:
            Notification.objects.create(
                user=sticker.user,
                sender=user,
                sticker=sticker,
                message=f"{user.username} лайкнул ваш стикер!"
            )
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def create_sticker(request):
    categories = Category.objects.all()
    logger.info(f"User {request.user.username} accessed create_sticker. Available categories: {categories}")
    if not categories:
        return render(request, 'stickers/create_sticker.html', {
            'cities': City.objects.all(),
            'categories': categories,
            'notification_count': get_notification_count(request.user),
            'error': 'Нет доступных категорий. Пожалуйста, добавьте категории через админ-панель.'
        })
    if request.method == 'POST':
        logger.info("Received POST request for creating sticker")
        description = request.POST.get('description')
        city_id = request.POST.get('city')
        category_id = request.POST.get('category')
        navigation_link = request.POST.get('navigation_link', '').strip()
        proportion = request.POST.get('proportion', '1:1')
        media_file = request.FILES.get('media_file')
        video_start = float(request.POST.get('video_start', 0))
        video_end = float(request.POST.get('video_end', 30))
        # Добавляем запасное значение для thumbnail_time
        thumbnail_time = float(request.POST.get('thumbnail_time', 0))
        if thumbnail_time <= 0:
            thumbnail_time = (video_start + video_end) / 2
        
        logger.info(f"Form data: description={description}, city_id={city_id}, category_id={category_id}, navigation_link={navigation_link}, proportion={proportion}, video_start={video_start}, video_end={video_end}, thumbnail_time={thumbnail_time}, media_file={media_file.name if media_file else None}")
        
        try:
            city = City.objects.get(id=city_id)
            logger.debug(f"City found: {city.name}, image: {city.image}")
        except City.DoesNotExist:
            logger.error(f"City with ID {city_id} not found, sticker creation aborted")
            return redirect('home')
        original_city_image = city.image
        try:
            category = Category.objects.get(id=category_id)
            logger.debug(f"Category: {category.name}")
        except Category.DoesNotExist:
            logger.error(f"Category with ID {category_id} not found, sticker creation aborted")
            return redirect('home')
        
        mime_type, _ = mimetypes.guess_type(media_file.name) if media_file else (None, None)
        is_image = mime_type and mime_type.startswith('image')
        is_video = mime_type and mime_type.startswith('video')
        allowed_video_formats = ['video/mp4', 'video/webm']
        
        # Проверяем размер файла
        if media_file:
            max_size = 50 * 1024 * 1024  # 50 МБ
            if media_file.size > max_size:
                logger.warning(f"File size exceeds limit: {media_file.size} bytes")
                return render(request, 'stickers/create_sticker.html', {
                    'cities': City.objects.all(),
                    'categories': categories,
                    'notification_count': get_notification_count(request.user),
                    'error': 'Файл слишком большой. Максимальный размер — 50 МБ.',
                })
        
        if is_video and mime_type not in allowed_video_formats:
            logger.warning(f"Unsupported video format: {mime_type}")
            return render(request, 'stickers/create_sticker.html', {
                'cities': City.objects.all(),
                'categories': categories,
                'notification_count': get_notification_count(request.user),
                'error': 'Неподдерживаемый формат видео. Пожалуйста, загрузите видео в формате MP4 или WebM.',
            })

        sticker = Sticker(
            user=request.user,
            description=description,
            city=city,
            category=category,
            navigation_link=navigation_link if navigation_link else None,
            proportion=proportion,
        )

        if is_image and media_file:
            logger.info("Processing image upload")
            # Очищаем имя файла для изображений
            cleaned_filename = clean_filename(media_file.name)
            media_file.name = cleaned_filename
            sticker.image = media_file
            sticker.save()
            try:
                with Image.open(sticker.image.path) as img:
                    width, height = img.size
                    proportion = get_proportion(width, height)
                    sticker.proportion = proportion
                    sticker.save()
                logger.debug(f"Sticker image proportion: {proportion}")
            except Exception as e:
                logger.error(f"Error processing sticker image: {e}")
                sticker.image.delete()
                sticker.image = None
                sticker.save()
                return render(request, 'stickers/create_sticker.html', {
                    'cities': City.objects.all(),
                    'categories': categories,
                    'notification_count': get_notification_count(request.user),
                    'error': 'Не удалось обработать изображение.',
                })
        elif is_video and media_file:
            logger.info("Starting video processing")
            # Очищаем имя файла для видео
            cleaned_filename = clean_filename(media_file.name)
            media_file.name = cleaned_filename
            logger.debug(f"Cleaned video filename: {cleaned_filename}")
            
            # Сохраняем временный файл для видео
            temp_upload_path = os.path.join('media', 'sticker_videos', f'upload_{cleaned_filename}')
            with open(temp_upload_path, 'wb+') as destination:
                for chunk in media_file.chunks():
                    destination.write(chunk)
            logger.info(f"Temporary video file saved to: {temp_upload_path}")

            # Сохраняем стикер в базу данных перед фоновой задачей
            sticker.save()
            
            # Запускаем фоновую задачу для обработки видео
            process_video_sticker(sticker.id, temp_upload_path, cleaned_filename, video_start, video_end, thumbnail_time)
            
            # Уведомление об успешной загрузке
            logger.info("Video processing scheduled, redirecting to home page")
            messages.success(request, "Видео успешно загружено и обрабатывается. Вы будете уведомлены, когда оно будет готово.")
        elif not media_file:
            logger.warning("No media file uploaded")
            return render(request, 'stickers/create_sticker.html', {
                'cities': City.objects.all(),
                'categories': categories,
                'notification_count': get_notification_count(request.user),
                'error': 'Пожалуйста, загрузите изображение или видео.',
            })
        
        logger.debug(f"City image after saving sticker: {city.image}")
        if city.image != original_city_image:
            city.image = original_city_image
            city.save()
            logger.info(f"Restored city image for {city.name}: {city.image}")
        else:
            logger.debug(f"City image for {city.name} unchanged: {city.image}")
        logger.info("Redirecting to home page after successful sticker creation")
        return redirect('home')
    else:
        notification_count = get_notification_count(request.user)
        return render(request, 'stickers/create_sticker.html', {
            'cities': City.objects.all(),
            'categories': categories,
            'notification_count': notification_count
        })

@login_required
def edit_sticker(request, sticker_id):
    sticker = get_object_or_404(Sticker, id=sticker_id, user=request.user)
    categories = Category.objects.all()
    if not categories:
        return render(request, 'stickers/edit_sticker.html', {
            'sticker': sticker,
            'cities': City.objects.all(),
            'categories': categories,
            'notification_count': get_notification_count(request.user),
            'error': 'Нет доступных категорий. Пожалуйста, добавьте категории через админ-панель.'
        })
    if request.method == 'POST':
        logger.info(f"Received POST request for editing sticker {sticker_id}")
        description = request.POST.get('description')
        city_id = request.POST.get('city')
        category_id = request.POST.get('category')
        navigation_link = request.POST.get('navigation_link', '').strip()
        proportion = request.POST.get('proportion', '1:1')
        media_file = request.FILES.get('media_file')
        video_start = float(request.POST.get('video_start', 0))
        video_end = float(request.POST.get('video_end', 30))
        thumbnail_time = float(request.POST.get('thumbnail_time', (video_start + video_end) / 2))
        
        logger.info(f"Form data: description={description}, city_id={city_id}, category_id={category_id}, navigation_link={navigation_link}, proportion={proportion}, video_start={video_start}, video_end={video_end}, thumbnail_time={thumbnail_time}, media_file={media_file.name if media_file else None}")
        
        try:
            city = City.objects.get(id=city_id)
            logger.debug(f"City found: {city.name}, image: {city.image}")
        except City.DoesNotExist:
            logger.error(f"City with ID {city_id} not found, sticker editing aborted")
            return redirect('sticker_detail', sticker_id=sticker.id)
        original_city_image = city.image
        category = Category.objects.get(id=category_id)
        logger.debug(f"Category: {category.name}")
        
        sticker.description = description
        sticker.city = city
        sticker.category = category
        sticker.navigation_link = navigation_link if navigation_link else None
        sticker.proportion = proportion
        
        if media_file:
            # Проверяем размер файла
            max_size = 50 * 1024 * 1024  # 50 МБ
            if media_file.size > max_size:
                logger.warning(f"File size exceeds limit: {media_file.size} bytes")
                return render(request, 'stickers/edit_sticker.html', {
                    'sticker': sticker,
                    'cities': City.objects.all(),
                    'categories': categories,
                    'notification_count': get_notification_count(request.user),
                    'error': 'Файл слишком большой. Максимальный размер — 50 МБ.',
                })

            if sticker.image:
                sticker.image.delete()
                sticker.image = None
            if sticker.video:
                sticker.video.delete()
                sticker.video = None
            mime_type, _ = mimetypes.guess_type(media_file.name)
            is_image = mime_type and mime_type.startswith('image')
            is_video = mime_type and mime_type.startswith('video')
            allowed_video_formats = ['video/mp4', 'video/webm']
            if is_video and mime_type not in allowed_video_formats:
                logger.warning(f"Unsupported video format: {mime_type}")
                return render(request, 'stickers/edit_sticker.html', {
                    'sticker': sticker,
                    'cities': City.objects.all(),
                    'categories': categories,
                    'notification_count': get_notification_count(request.user),
                    'error': 'Неподдерживаемый формат видео. Пожалуйста, загрузите видео в формате MP4 или WebM.',
                })
            
            if is_image:
                logger.info("Processing image upload for editing")
                # Очищаем имя файла для изображений
                cleaned_filename = clean_filename(media_file.name)
                media_file.name = cleaned_filename
                sticker.image = media_file
                sticker.save()
                try:
                    with Image.open(sticker.image.path) as img:
                        width, height = img.size
                        proportion = get_proportion(width, height)
                        sticker.proportion = proportion
                        sticker.save()
                    logger.debug(f"Sticker image proportion: {proportion}")
                except Exception as e:
                    logger.error(f"Error processing sticker image: {e}")
                    sticker.image.delete()
                    sticker.image = None
                    sticker.save()
                    return render(request, 'stickers/edit_sticker.html', {
                        'sticker': sticker,
                        'cities': City.objects.all(),
                        'categories': categories,
                        'notification_count': get_notification_count(request.user),
                        'error': 'Не удалось обработать изображение.',
                    })
            elif is_video:
                logger.info("Starting video processing for editing")
                # Очищаем имя файла для видео
                cleaned_filename = clean_filename(media_file.name)
                media_file.name = cleaned_filename
                logger.debug(f"Cleaned video filename: {cleaned_filename}")
                
                # Сохраняем временный файл для видео
                temp_upload_path = os.path.join('media', 'sticker_videos', f'upload_{cleaned_filename}')
                with open(temp_upload_path, 'wb+') as destination:
                    for chunk in media_file.chunks():
                        destination.write(chunk)
                logger.info(f"Temporary video file saved to: {temp_upload_path}")

                # Сохраняем стикер в базу данных перед фоновой задачей
                sticker.save()
                
                # Запускаем фоновую задачу для обработки видео
                process_video_sticker(sticker.id, temp_upload_path, cleaned_filename, video_start, video_end, thumbnail_time)
                
                # Уведомление об успешной загрузке
                logger.info("Video processing scheduled, redirecting to sticker detail page")
                messages.success(request, "Видео успешно загружено и обрабатывается. Вы будете уведомлены, когда оно будет готово.")
            else:
                logger.warning("No valid image or video uploaded during editing")
                return render(request, 'stickers/edit_sticker.html', {
                    'sticker': sticker,
                    'cities': City.objects.all(),
                    'categories': categories,
                    'notification_count': get_notification_count(request.user),
                    'error': 'Пожалуйста, загрузите изображение или видео.',
                })
        else:
            sticker.save()
        
        logger.debug(f"City image after editing sticker: {city.image}")
        if city.image != original_city_image:
            city.image = original_city_image
            city.save()
            logger.info(f"Restored city image for {city.name}: {city.image}")
        else:
            logger.debug(f"City image for {city.name} unchanged: {city.image}")
        logger.info("Redirecting to sticker detail page after successful edit")
        return redirect('sticker_detail', sticker_id=sticker.id)
    else:
        notification_count = get_notification_count(request.user)
        return render(request, 'stickers/edit_sticker.html', {
            'sticker': sticker,
            'cities': City.objects.all(),
            'categories': categories,
            'notification_count': notification_count
        })

@login_required
def delete_sticker(request, sticker_id):
    sticker = get_object_or_404(Sticker, id=sticker_id, user=request.user)
    if request.method == 'POST':
        if sticker.image:
            sticker.image.delete()
        if sticker.video:
            sticker.video.delete()
        Like.objects.filter(sticker=sticker).delete()
        Comment.objects.filter(sticker=sticker).delete()
        Notification.objects.filter(sticker=sticker).delete()
        sticker.delete()
        return redirect('profile')
    return render(request, 'stickers/delete_sticker.html', {
        'sticker': sticker,
        'notification_count': get_notification_count(request.user)
    })

def search(request):
    query = request.GET.get('q', '').strip()
    city_filter = request.GET.get('city', '')
    category_filter = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '-created_at')
    results = Sticker.objects.annotate(like_count=Count('like'))
    total_stickers = Sticker.objects.count()  # Добавляем общее количество стикеров
    logger.info(f"Search page: {results.count()} stickers found before filtering")
    if query:
        results = results.filter(
            Q(description__icontains=query) |
            Q(city__name__icontains=query) |
            Q(category__name__icontains=query)
        )
    if city_filter:
        results = results.filter(city__name__iexact=city_filter)
    if category_filter:
        results = results.filter(category__name__iexact=category_filter)
    logger.info(f"Search page: {results.count()} stickers found after filtering")
    sort_options = {
        '-created_at': '-created_at',
        'like_count': 'like_count',
        'description': 'description'
    }
    results = results.order_by(sort_options.get(sort_by, '-created_at'))
    for sticker in results:
        sticker.is_liked = request.user.is_authenticated and sticker.like_set.filter(user=request.user).exists()
    cities = City.objects.all()
    categories = Category.objects.all()
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/search.html', {
        'query': query,
        'results': results,
        'city_filter': city_filter,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'cities': cities,
        'categories': categories,
        'notification_count': notification_count,
        'total_stickers': total_stickers
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/register.html', {
        'form': form,
        'notification_count': notification_count
    })

def logout_view(request):
    logout(request)
    return redirect('home')

def get_proportion(width, height):
    try:
        if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
            logger.error(f"Invalid width ({width}) or height ({height}) type")
            return "1:1"
        width = float(width)
        height = float(height)
        if height == 0:
            raise ZeroDivisionError("Height is zero")
        aspect_ratio = width / height
        if 1.7 <= aspect_ratio <= 1.85:
            return "16:9"
        elif 0.95 <= aspect_ratio <= 1.05:
            return "1:1"
        elif 0.55 <= aspect_ratio <= 1.58:
            return "9:16"
        else:
            return "1:1"
    except ZeroDivisionError:
        logger.error("Height is zero, cannot calculate aspect ratio")
        return "1:1"
    except Exception as e:
        logger.error(f"Error calculating proportion: {e}")
        return "1:1"

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Неверный логин или пароль.")
    else:
        form = AuthenticationForm()
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/login.html', {
        'form': form,
        'notification_count': notification_count
    })

@login_required
def chat_list(request):
    chats = request.user.chats.all()
    for chat in chats:
        chat.last_message = chat.get_last_message()
        chat.unread_count = chat.messages.filter(is_read=False).exclude(sender=request.user).count()
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/chat_list.html', {
        'chats': chats,
        'notification_count': notification_count
    })

@login_required
def start_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user:
        return redirect('chat_list')
    chat = Chat.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not chat:
        chat = Chat.objects.create()
        chat.participants.add(request.user, other_user)
        chat.save()
    return redirect('chat_detail', chat_id=chat.id)

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user not in chat.participants.all():
        return redirect('chat_list')
    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    messages = chat.messages.all()
    other_user = chat.get_other_participant(request.user)
    notification_count = get_notification_count(request.user)
    return render(request, 'stickers/chat_detail.html', {
        'chat': chat,
        'messages': messages,
        'other_user': other_user,
        'notification_count': notification_count
    })

@login_required
def send_message(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user not in chat.participants.all():
        return redirect('chat_list')
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                chat=chat,
                sender=request.user,
                content=content,
            )
    return redirect('chat_detail', chat_id=chat.id)

@background(schedule=10)
def process_video_sticker(sticker_id, temp_upload_path, cleaned_filename, video_start, video_end, thumbnail_time=None):
    """Фоновая задача для обработки видео."""
    logger.info(f"Starting background video processing for sticker {sticker_id}")
    try:
        # Проверяем, доступен ли ffmpeg
        import subprocess
        try:
            result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"ffmpeg version: {result.stdout}")
            if result.returncode != 0:
                logger.error(f"ffmpeg error: {result.stderr}")
                raise RuntimeError(f"ffmpeg failed: {result.stderr}")
        except FileNotFoundError:
            logger.error("ffmpeg is not installed or not found in PATH")
            raise RuntimeError("ffmpeg is required for video processing but is not installed")

        sticker = Sticker.objects.get(id=sticker_id)
        logger.info(f"Processing video for sticker {sticker_id}, temp path: {temp_upload_path}")
        if not os.path.exists(temp_upload_path):
            logger.error(f"Temporary upload file {temp_upload_path} does not exist")
            raise FileNotFoundError(f"Temporary upload file {temp_upload_path} does not exist")

        with VideoFileClip(temp_upload_path) as video_clip:
            duration = video_clip.duration
            logger.debug(f"Original video duration: {duration} seconds")
            if video_end - video_start > 30:
                logger.error(f"Selected video duration {video_end - video_start} exceeds 30 seconds limit")
                raise ValueError("Video duration exceeds 30 seconds")
            if video_start < 0 or video_end > duration or video_start >= video_end:
                logger.error(f"Invalid video trim range: start={video_start}, end={video_end}, duration={duration}")
                raise ValueError("Invalid video trim range")
            
            # Обрезаем видео
            logger.info("Starting video trimming")
            trimmed_clip = video_clip.subclip(video_start, video_end)
            media_root = os.path.join(settings.MEDIA_ROOT, 'sticker_videos')
            if not os.path.exists(media_root):
                os.makedirs(media_root)
                logger.info(f"Created directory: {media_root}")
            temp_path = os.path.join(media_root, f'trimmed_{cleaned_filename}')
            logger.info(f"Writing trimmed video to: {temp_path}")
            trimmed_clip.write_videofile(
                temp_path,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                preset='ultrafast',
                logger=None
            )
            logger.info("Trimmed video written successfully")
            
            # Генерируем превью-изображение (используем указанное время или середину)
            if thumbnail_time is None:
                thumbnail_time = (video_start + video_end) / 2
            thumbnail_time = max(video_start, min(video_end, thumbnail_time))
            thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'sticker_thumbnails')
            if not os.path.exists(thumbnail_dir):
                os.makedirs(thumbnail_dir)
                logger.info(f"Created directory: {thumbnail_dir}")
            thumbnail_path = os.path.join(thumbnail_dir, f'thumbnail_{cleaned_filename}.jpg')
            logger.info(f"Attempting to generate thumbnail at: {thumbnail_path}, thumbnail time: {thumbnail_time}")
            trimmed_clip.save_frame(thumbnail_path, t=thumbnail_time)
            logger.info(f"Thumbnail generated successfully at: {thumbnail_path}")

            trimmed_clip.close()
            logger.info("Trimmed clip closed")

            # Сохраняем обрезанное видео
            if os.path.exists(temp_path):
                with open(temp_path, 'rb') as f:
                    trimmed_file = ContentFile(f.read(), name=cleaned_filename)
                    sticker.video.save(cleaned_filename, trimmed_file, save=False)
                    logger.info("Trimmed video saved to sticker")
            else:
                logger.error(f"Trimmed video file not found at: {temp_path}")
                raise FileNotFoundError(f"Trimmed video file not found at: {temp_path}")

            # Сохраняем превью
            if os.path.exists(thumbnail_path):
                with open(thumbnail_path, 'rb') as f:
                    thumbnail_file = ContentFile(f.read(), name=f'thumbnail_{cleaned_filename}.jpg')
                    logger.info(f"Saving thumbnail to sticker.video_thumbnail")
                    sticker.video_thumbnail.save(f'thumbnail_{cleaned_filename}.jpg', thumbnail_file, save=False)
                    logger.info("Thumbnail saved to sticker")
            else:
                logger.error(f"Thumbnail file not found at: {thumbnail_path}")
                raise FileNotFoundError(f"Thumbnail file not found at: {thumbnail_path}")

            # Удаляем временные файлы с обработкой исключений
            try:
                os.remove(temp_path)
                logger.info("Temporary trimmed file removed")
            except FileNotFoundError:
                logger.warning(f"Temporary trimmed file {temp_path} not found for removal")
            except Exception as e:
                logger.error(f"Error removing temporary trimmed file {temp_path}: {str(e)}")
            try:
                os.remove(thumbnail_path)
                logger.info("Temporary thumbnail file removed")
            except FileNotFoundError:
                logger.warning(f"Temporary thumbnail file {thumbnail_path} not found for removal")
            except Exception as e:
                logger.error(f"Error removing temporary thumbnail file {thumbnail_path}: {str(e)}")

        # Обновляем пропорции видео
        with VideoFileClip(sticker.video.path) as video:
            width = video.w if video.w else 1
            height = video.h if video.h else 1
            logger.debug(f"Processed video dimensions: width={width}, height={height}")
            if width <= 0 or height <= 0:
                logger.error("Invalid video dimensions: width or height is zero or negative")
                raise ValueError("Invalid video dimensions")
            proportion = get_proportion(width, height)
            sticker.proportion = proportion
            sticker.save()
            logger.debug(f"Sticker video proportion: {proportion}")

        # Создаём уведомление для пользователя
        Notification.objects.create(
            user=sticker.user,
            message=f"Ваше видео '{sticker.description}' успешно обработано!",
            sticker=sticker,
            sender=None
        )
        logger.info(f"Video processing completed for sticker {sticker_id}")
    except Exception as e:
        logger.error(f"Background video processing error for sticker {sticker_id}: {str(e)}")
        try:
            sticker = Sticker.objects.get(id=sticker_id)
            Notification.objects.create(
                user=sticker.user,
                message=f"Ошибка обработки видео '{sticker.description}': {str(e)}. Видео сохранено, но превью отсутствует.",
                sticker=sticker,
                sender=None
            )
        except Sticker.DoesNotExist:
            logger.error(f"Sticker {sticker_id} not found during error handling")
    finally:
        # Не удаляем временный файл, если задача может быть пересоздана
        pass