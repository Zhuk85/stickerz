document.addEventListener('DOMContentLoaded', function() {
    // Управление воспроизведением видео при наведении
    const stickers = document.querySelectorAll('.city-sticker, .sticker');
    stickers.forEach(sticker => {
        const video = sticker.querySelector('.sticker-video');
        if (video) {
            // Проверяем, что видео может быть воспроизведено
            video.addEventListener('canplay', () => {
                console.log('Видео готово к воспроизведению:', video.src);
            });
            video.addEventListener('error', (e) => {
                console.error('Ошибка загрузки видео:', e);
            });
            video.load();
            sticker.addEventListener('mouseenter', () => {
                video.play().catch(error => {
                    console.error('Ошибка воспроизведения видео:', error);
                });
            });
            sticker.addEventListener('mouseleave', () => {
                video.pause();
                video.currentTime = 0;
            });
        }
    });
});