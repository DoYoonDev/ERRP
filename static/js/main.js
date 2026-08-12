document.addEventListener("DOMContentLoaded", function () {
    const track = document.getElementById('slideTrack');
    if (!track) return;

    const slides = track.querySelectorAll('.slide-item');
    let currentIndex = 0;

    function moveSlide() {
        currentIndex = (currentIndex + 1) % slides.length;
        track.style.transform = `translateX(-${currentIndex * 100}%)`;
    }

    // 3초마다 자동으로 슬라이드 전환
    setInterval(moveSlide, 3000);
});