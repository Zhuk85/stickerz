document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.city-sticker, .sticker, .like-button');
    cards.forEach(card => {
        card.addEventListener('click', function(e) {
            this.classList.toggle('active');
            setTimeout(() => this.classList.remove('active'), 300);
        });
    });
});