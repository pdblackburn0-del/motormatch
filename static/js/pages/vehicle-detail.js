(function () {
    'use strict';

    var container = document.getElementById('starPicker');
    if (container) {
        var labels = Array.from(container.querySelectorAll('.star-label'));
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

        container.addEventListener('mouseleave', function () {
            var checkedIdx = labels.findIndex(function (l) { return l.querySelector('input').checked; });
            paint(checkedIdx >= 0 ? checkedIdx : 4);
        });

        var initIdx = labels.findIndex(function (l) { return l.querySelector('input').checked; });
        paint(initIdx >= 0 ? initIdx : 4);
    }
})();

function toggleSave(btn) {
    var icon   = document.getElementById('saveIcon');
    var isSaved = btn.dataset.saved === '1';
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
}
