// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    const masonry = document.querySelector('.masonry');
    function updateLayout() {
        const windowWidth = window.innerWidth;
        if (windowWidth <= 600) {
            masonry.style.columnCount = '1';
        } else if (windowWidth <= 900) {
            masonry.style.columnCount = '2';
        } else if (windowWidth <= 1200) {
            masonry.style.columnCount = '4';
        } else {
            masonry.style.columnCount = '6';
        }
    }
    updateLayout();
    window.addEventListener('resize', updateLayout);
});