(function () {
    'use strict';

    var ALLOWED   = ['image/jpeg', 'image/png', 'image/webp'];
    var MAX_BYTES = 5 * 1024 * 1024;

    function showNotice(msg, type) {
        type = type || 'warning';
        var iconMap = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', danger: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
        var icon = iconMap[type] || iconMap.warning;
        var container = document.querySelector('.mm-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'mm-toast-container';
            document.body.appendChild(container);
        }
        var toast = document.createElement('div');
        toast.className = 'mm-toast mm-toast--' + type;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = '<div class="mm-toast__icon"><i class="bi ' + icon + '"></i></div>'
            + '<div class="mm-toast__body"><span class="mm-toast__msg">' + msg + '</span></div>'
            + '<button class="mm-toast__close" aria-label="Close"><i class="bi bi-x"></i></button>'
            + '<div class="mm-toast__progress"></div>';
        container.appendChild(toast);
        toast.querySelector('.mm-toast__close').addEventListener('click', function () {
            toast.style.animation = 'mmToastOut .3s ease forwards';
            setTimeout(function () { toast.remove(); }, 300);
        });
        setTimeout(function () {
            toast.style.animation = 'mmToastOut .3s ease forwards';
            setTimeout(function () { toast.remove(); }, 300);
        }, 4000);
    }

    document.querySelectorAll('.delete-photo-label').forEach(function (label) {
        label.addEventListener('click', function () {
            var cb = this.querySelector('.delete-photo-cb');
            if (!cb) return;
            setTimeout(function () {
                label.closest('.extra-img-thumb').style.opacity = cb.checked ? '0.35' : '1';
                recalcAfterDelete();
            }, 0);
        });
    });

    var newInput   = document.getElementById('newPhotosInput');
    var newPreview = document.getElementById('newPhotosPreview');
    var newStore   = (typeof DataTransfer !== 'undefined') ? new DataTransfer() : null;

    function renderNewPreview() {
        if (!newPreview || !newStore) return;
        newPreview.innerHTML = '';
        Array.from(newStore.files).forEach(function (file, idx) {
            var reader = new FileReader();
            reader.onload = function (e) {
                var wrap = document.createElement('div');
                wrap.className = 'position-relative';
                wrap.style.cssText = 'width:80px;height:60px;flex-shrink:0;';
                var img = document.createElement('img');
                img.src = e.target.result;
                img.style.cssText = 'width:100%;height:100%;object-fit:cover;border-radius:6px;border:1px solid #e5e7eb;';
                var rb = document.createElement('button');
                rb.type = 'button';
                rb.textContent = '\u00d7';
                rb.title = 'Remove';
                rb.style.cssText = 'position:absolute;top:2px;right:2px;background:rgba(220,38,38,0.85);color:#fff;border:none;border-radius:50%;width:18px;height:18px;font-size:13px;line-height:18px;cursor:pointer;padding:0;';
                (function (i) {
                    rb.addEventListener('click', function () {
                        var dt = new DataTransfer();
                        Array.from(newStore.files).forEach(function (f, j) { if (j !== i) dt.items.add(f); });
                        newStore = dt;
                        if (newInput) newInput.files = newStore.files;
                        renderNewPreview();
                    });
                }(idx));
                wrap.appendChild(img);
                wrap.appendChild(rb);
                newPreview.appendChild(wrap);
            };
            reader.readAsDataURL(file);
        });
    }

    var existingCount = newInput ? parseInt(newInput.dataset.existing || '0', 10) : 0;
    var pendingDeleteCount = 0;
    var maxNew = Math.max(0, 9 - existingCount);

    function recalcAfterDelete() {
        pendingDeleteCount = document.querySelectorAll('.delete-photo-cb:checked').length;
        var effective = existingCount - pendingDeleteCount;
        maxNew = Math.max(0, 9 - effective);
        if (newInput) {
            var total = effective + (newStore ? newStore.files.length : 0);
            newInput.disabled = total >= 9;
        }
        updateLimitBadge();
    }

    function updateLimitBadge() {
        var badge = document.getElementById('photoLimitBadge');
        if (!badge) return;
        var effective = existingCount - pendingDeleteCount;
        var total = effective + (newStore ? newStore.files.length : 0);
        badge.textContent = total + ' / 9';
        badge.className = 'badge ' + (total >= 9 ? 'bg-danger' : total >= 7 ? 'bg-warning text-dark' : 'bg-secondary');
        badge.style.fontSize = '.7rem';
    }

    if (newInput && newPreview && newStore) {
        newInput.addEventListener('change', function () {
            var skipped = 0;
            Array.from(this.files).forEach(function (f) {
                if (newStore.files.length >= maxNew) { skipped++; return; }
                if (!ALLOWED.includes(f.type) || f.size > MAX_BYTES) { skipped++; return; }
                newStore.items.add(f);
            });
            newInput.files = newStore.files;
            renderNewPreview();
            updateLimitBadge();
            if (skipped > 0) {
                showNotice(skipped + ' file(s) skipped \u2014 only JPEG/PNG/WebP under 5 MB, max 9 photos total.');
            }
        });
    }

    var delForm = document.getElementById('deleteListingForm');
    if (delForm) {
        delForm.addEventListener('submit', function (e) {
            if (!confirm('Permanently remove this listing? This cannot be undone.')) {
                e.preventDefault();
            }
        });
    }

})();

(function () {
    'use strict';
    document.querySelectorAll('[data-maxlength]').forEach(function (el) {
        var max = parseInt(el.getAttribute('data-maxlength'), 10);
        var ctr = document.createElement('small');
        ctr.className = 'form-text text-muted d-block text-end';
        ctr.style.fontSize = '.72rem';
        el.insertAdjacentElement('afterend', ctr);
        function update() {
            var n = el.value.length;
            ctr.textContent = n + ' / ' + max;
            ctr.style.color = n >= max ? '#dc2626' : '';
        }
        el.addEventListener('input', update);
        update();
    });
}());
