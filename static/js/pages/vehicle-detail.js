(function () {
    'use strict';

    var starContainer = document.getElementById('starPicker');
    if (starContainer) {
        var labels = Array.from(starContainer.querySelectorAll('.star-label'));
        var icons  = labels.map(function (l) { return l.querySelector('i'); });

        function paint(upTo) {
            icons.forEach(function (ic, idx) {
                ic.style.color = idx <= upTo ? '#f59e0b' : '#d1d5db';
            });
        }

        labels.forEach(function (lbl, idx) {
            lbl.addEventListener('mouseenter', function () { paint(idx); });
            lbl.addEventListener('click', function () {
                paint(idx);
                lbl.querySelector('input').checked = true;
            });
        });

        starContainer.addEventListener('mouseleave', function () {
            var checkedIdx = labels.findIndex(function (l) { return l.querySelector('input').checked; });
            paint(checkedIdx >= 0 ? checkedIdx : 4);
        });

        var initIdx = labels.findIndex(function (l) { return l.querySelector('input').checked; });
        paint(initIdx >= 0 ? initIdx : 4);
    }

    var saveBtn = document.getElementById('saveBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function () {
            var btn  = this;
            var icon = document.getElementById('saveIcon');
            fetch(btn.dataset.url, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': btn.dataset.csrf }
            })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.saved) {
                    icon.className = 'bi bi-heart-fill text-danger';
                    btn.title = 'Unsave';
                    btn.dataset.saved = '1';
                } else {
                    icon.className = 'bi bi-heart text-muted';
                    btn.title = 'Save';
                    btn.dataset.saved = '0';
                }
            })
            .catch(function () {});
        });
    }

    var mainImg   = document.getElementById('gallery-main-img');
    var prevBtn   = document.getElementById('galleryPrev');
    var nextBtn   = document.getElementById('galleryNext');
    var openBtn   = document.getElementById('galleryOpenBtn');
    var lbMain    = document.getElementById('lightbox-main');
    var lbPrev    = document.getElementById('lbPrev');
    var lbNext    = document.getElementById('lbNext');
    var lbThumbs  = Array.from(document.querySelectorAll('.lb-thumb'));
    var stripThumbs = Array.from(document.querySelectorAll('.gallery-strip-thumb'));

    var dataEl = document.getElementById('gallery-data');
    if (!dataEl || !mainImg) return;

    var images     = JSON.parse(dataEl.textContent);
    var currentIdx = 0;

    function setActive(idx, animate) {
        currentIdx = ((idx % images.length) + images.length) % images.length;

        if (animate) {
            mainImg.style.opacity = '0';
            setTimeout(function () {
                mainImg.src = images[currentIdx];
                mainImg.style.opacity = '1';
            }, 140);
        } else {
            mainImg.src = images[currentIdx];
        }

        stripThumbs.forEach(function (t, i) {
            t.classList.toggle('active', i === currentIdx);
        });

        lbThumbs.forEach(function (t, i) {
            t.classList.toggle('active', i === currentIdx);
            if (i === currentIdx) {
                t.style.border = '2.5px solid #2563eb';
                t.style.outline = 'none';
                t.style.opacity = '1';
            } else {
                t.style.border = '2.5px solid transparent';
                t.style.outline = 'none';
                t.style.opacity = '0.55';
            }
        });

        if (lbMain) {
            var lbEl = document.getElementById('galleryLightbox');
            if (lbEl && lbEl.classList.contains('show')) {
                lbMain.style.opacity = '0';
                setTimeout(function () {
                    lbMain.src = images[currentIdx];
                    lbMain.style.opacity = '1';
                }, 100);
            } else {
                lbMain.src = images[currentIdx];
            }
        }

        var lbCounter = document.getElementById('lb-counter');
        if (lbCounter) lbCounter.textContent = (currentIdx + 1) + ' / ' + images.length;

        var activeThumb = lbThumbs[currentIdx];
        if (activeThumb) activeThumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });

        var counter = document.getElementById('gallery-counter');
        if (counter) counter.textContent = (currentIdx + 1) + ' / ' + images.length;
    }

    if (prevBtn) prevBtn.addEventListener('click', function () { setActive(currentIdx - 1, true); });
    if (nextBtn) nextBtn.addEventListener('click', function () { setActive(currentIdx + 1, true); });
    if (lbPrev)  lbPrev.addEventListener('click',  function () { setActive(currentIdx - 1, false); });
    if (lbNext)  lbNext.addEventListener('click',  function () { setActive(currentIdx + 1, false); });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft')  setActive(currentIdx - 1, true);
        if (e.key === 'ArrowRight') setActive(currentIdx + 1, true);
    });

    stripThumbs.forEach(function (t, i) {
        t.addEventListener('click', function () { setActive(i, true); });
    });

    lbThumbs.forEach(function (t, i) {
        t.addEventListener('click', function () { setActive(i, false); });
    });

    if (openBtn) {
        openBtn.addEventListener('click', function () {
            setActive(currentIdx, false);
            var lbEl = document.getElementById('galleryLightbox');
            if (lbEl && window.bootstrap) {
                new bootstrap.Modal(lbEl).show();
            }
        });
    }

    setActive(0, false);
})();
