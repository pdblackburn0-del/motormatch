(function () {
    'use strict';

    var DVLA_URL = JSON.parse(document.getElementById('data-dvla-url').textContent);

    var ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
    var MAX_FILE_BYTES = 5 * 1024 * 1024; // 5 MB

    function validateImageFile(file) {
        if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
            showNotice('Only JPEG, PNG, and WebP images are allowed.');
            return false;
        }
        if (file.size > MAX_FILE_BYTES) {
            showNotice('Image must be under 5 MB.');
            return false;
        }
        return true;
    }

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

    var lookupBtn = document.getElementById('dvlaLookupBtn');
    var regInput  = document.getElementById('dvlaReg');
    var msgEl     = document.getElementById('dvlaMsg');

    function runLookup() {
        var reg = regInput.value.replace(/\s/g, '').toUpperCase();
        if (!reg) return;
        msgEl.className = 'small mt-2 text-muted';
        msgEl.textContent = 'Looking up\u2026';
        msgEl.classList.remove('d-none');
        fetch(DVLA_URL + '?reg=' + encodeURIComponent(reg))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) {
                    msgEl.className = 'small mt-2 text-danger';
                    msgEl.textContent = data.error;
                    return;
                }
                var set = function (id, val) { var el = document.getElementById(id); if (el) el.value = val; };
                set('id_make', data.make);
                set('id_model', data.model);
                set('id_year', data.year);
                set('id_mileage', data.mileage.replace(/[^0-9]/g, ''));
                ['id_fuel', 'id_transmission'].forEach(function (id) {
                    var sel = document.getElementById(id);
                    if (!sel) return;
                    var key = id === 'id_fuel' ? data.fuel : data.transmission;
                    for (var i = 0; i < sel.options.length; i++) {
                        var opt = sel.options[i];
                        if (opt.text.toLowerCase() === key.toLowerCase() || opt.value.toLowerCase() === key.toLowerCase()) {
                            sel.value = opt.value;
                            break;
                        }
                    }
                });
                msgEl.className = 'small mt-2 text-success';
                msgEl.textContent = '\u2713 Found: ' + data.year + ' ' + data.make + ' ' + data.model + ' \u2014 ' + data.colour + ', ' + data.fuel;
            })
            .catch(function () {
                msgEl.className = 'small mt-2 text-danger';
                msgEl.textContent = 'Lookup failed. Please fill in details manually.';
            });
    }

    if (lookupBtn) lookupBtn.addEventListener('click', runLookup);
    if (regInput) regInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); runLookup(); }
    });

    var fileInput   = document.querySelector('#photoDropzone input[type="file"]');
    var dropzone    = document.getElementById('photoDropzone');
    var previewBox  = document.getElementById('photoPreviewBox');
    var previewImg  = document.getElementById('photoPreviewImg');
    var clearBtn    = document.getElementById('photoClearBtn');
    var urlToggle   = document.getElementById('urlToggleBtn');
    var urlWrap     = document.getElementById('urlInputWrap');

    function showPreview(src) {
        previewImg.src = src;
        previewBox.style.display = 'block';
        dropzone.style.display = 'none';
    }

    function clearPreview() {
        previewImg.src = '';
        previewBox.style.display = 'none';
        dropzone.style.display = 'block';
        if (fileInput) fileInput.value = '';
    }

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            var file = this.files[0];
            if (!file) return;
            if (!validateImageFile(file)) { this.value = ''; return; }
            var reader = new FileReader();
            reader.onload = function (e) { showPreview(e.target.result); };
            reader.readAsDataURL(this.files[0]);
        });
    }

    if (clearBtn) clearBtn.addEventListener('click', clearPreview);

    if (dropzone) {
        dropzone.addEventListener('dragover', function (e) {
            e.preventDefault();
            dropzone.classList.add('drag-over');
        });
        dropzone.addEventListener('dragleave', function () {
            dropzone.classList.remove('drag-over');
        });
        dropzone.addEventListener('drop', function (e) {
            e.preventDefault();
            dropzone.classList.remove('drag-over');
            var file = e.dataTransfer.files[0];
            if (!file || !file.type.startsWith('image/')) return;
            if (fileInput) {
                try {
                    var dt = new DataTransfer();
                    dt.items.add(file);
                    fileInput.files = dt.files;
                } catch (ex) {}
            }
            var reader = new FileReader();
            reader.onload = function (ev) { showPreview(ev.target.result); };
            reader.readAsDataURL(file);
        });
    }

    if (urlToggle && urlWrap) {
        urlToggle.addEventListener('click', function () {
            var open = urlWrap.style.display === 'none';
            urlWrap.style.display = open ? 'block' : 'none';
            urlToggle.innerHTML = open
                ? '<i class="bi bi-x"></i> Hide image URL'
                : '<i class="bi bi-link-45deg"></i> Use image URL instead';
        });
    }

    var urlInput      = document.getElementById('id_image_url');
    var urlPreviewWrap = document.getElementById('urlPreviewWrap');
    var urlPreviewImg  = document.getElementById('urlPreviewImg');

    if (urlInput) {
        urlInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') e.preventDefault();
        });
        urlInput.addEventListener('input', function () {
            var url = this.value.trim();
            if (!url || !/^https?:\/\//i.test(url)) {
                if (urlPreviewWrap) urlPreviewWrap.style.display = 'none';
                return;
            }
            if (urlPreviewImg && urlPreviewWrap) {
                urlPreviewImg.src = url;
                urlPreviewImg.onload = function () {
                    urlPreviewWrap.style.display = 'block';
                    showPreview(url);
                };
                urlPreviewImg.onerror = function () {
                    urlPreviewWrap.style.display = 'none';
                };
            }
        });
    }

    var extraInput   = document.getElementById('extraPhotosInput');
    var extraPreview = document.getElementById('extraPhotosPreview');
    var extraStore   = (typeof DataTransfer !== 'undefined') ? new DataTransfer() : null;

    function renderExtraPreview() {
        if (!extraPreview || !extraStore) return;
        extraPreview.innerHTML = '';
        Array.from(extraStore.files).forEach(function (file, idx) {
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
                        Array.from(extraStore.files).forEach(function (f, j) { if (j !== i) dt.items.add(f); });
                        extraStore = dt;
                        if (extraInput) extraInput.files = extraStore.files;
                        renderExtraPreview();
                    });
                }(idx));
                wrap.appendChild(img);
                wrap.appendChild(rb);
                extraPreview.appendChild(wrap);
            };
            reader.readAsDataURL(file);
        });
    }

    if (extraInput && extraPreview && extraStore) {
        extraInput.addEventListener('change', function () {
            var skipped = 0;
            Array.from(this.files).forEach(function (f) {
                if (extraStore.files.length >= 9) { skipped++; return; }
                if (!ALLOWED_IMAGE_TYPES.includes(f.type) || f.size > MAX_FILE_BYTES) { skipped++; return; }
                extraStore.items.add(f);
            });
            extraInput.files = extraStore.files;
            renderExtraPreview();
            if (skipped > 0) {
                showNotice(skipped + ' file(s) skipped — only JPEG/PNG/WebP under 5 MB, max 9 extra photos.');
            }
        });
    }

})();

(function () {
    'use strict';
    var textarea = document.querySelector('[data-maxlength]');
    if (!textarea) return;
    var max     = parseInt(textarea.getAttribute('data-maxlength'), 10);
    var counter = document.getElementById('descCounter') || textarea.nextElementSibling;
    function update() {
        if (!counter) return;
        var n = textarea.value.length;
        counter.textContent = n + ' / ' + max;
        counter.style.color = n >= max ? '#dc2626' : '';
    }
    textarea.addEventListener('input', update);
    update();
}());
