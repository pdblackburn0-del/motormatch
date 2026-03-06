(function () {
    'use strict';

    var DVLA_URL = JSON.parse(document.getElementById('data-dvla-url').textContent);

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
            if (!this.files[0]) return;
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

})();
