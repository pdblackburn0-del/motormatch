(function () {
    'use strict';

    var loadMoreBtn = document.getElementById('load-more-btn');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function () {
            document.querySelectorAll('.extra-car').forEach(function (car) {
                car.classList.remove('d-none');
            });
            loadMoreBtn.style.display = 'none';
        });
    }

    var track = document.getElementById('featured-scroll');
    var btnL  = document.getElementById('scroll-left');
    var btnR  = document.getElementById('scroll-right');
    if (track && btnL && btnR) {
        var STEP = 292;
        btnL.addEventListener('click', function () { track.scrollBy({ left: -STEP, behavior: 'smooth' }); });
        btnR.addEventListener('click', function () { track.scrollBy({ left:  STEP, behavior: 'smooth' }); });
    }
})();
