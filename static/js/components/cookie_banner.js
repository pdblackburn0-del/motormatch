(function () {
    var key = 'mm_cookie_consent';
    if (!localStorage.getItem(key)) {
        var banner = document.getElementById('cookieBanner');
        if (banner) banner.style.display = 'block';
    }

    var acceptBtn = document.getElementById('cookieAccept');
    var declineBtn = document.getElementById('cookieDecline');

    if (acceptBtn) {
        acceptBtn.addEventListener('click', function () {
            localStorage.setItem(key, 'accepted');
            hideBanner();
        });
    }

    if (declineBtn) {
        declineBtn.addEventListener('click', function () {
            localStorage.setItem(key, 'declined');
            hideBanner();
        });
    }

    function hideBanner() {
        var b = document.getElementById('cookieBanner');
        if (!b) return;
        b.style.animation = 'cookieSlideDown .3s ease forwards';
        setTimeout(function () { b.remove(); }, 300);
    }
}());
