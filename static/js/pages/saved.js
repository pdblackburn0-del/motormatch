(function () {
    'use strict';

    var selected = [];
    var selectedTitles = {};

    function toggleSelect(card) {
        var pk = card.dataset.pk;
        var title = card.dataset.title;

        if (card.classList.contains('is-selected')) {
            card.classList.remove('is-selected');
            selected = selected.filter(function (id) { return id !== pk; });
            delete selectedTitles[pk];
        } else {
            if (selected.length >= 2) {
                card.style.transition = 'none';
                card.style.border = '2px solid #ef4444 !important';
                setTimeout(function () { card.style.border = ''; card.style.transition = ''; }, 600);
                return;
            }
            card.classList.add('is-selected');
            selected.push(pk);
            selectedTitles[pk] = title;
        }
        updateCompareBar();
    }
    window.toggleSelect = toggleSelect;

    function updateCompareBar() {
        var n       = selected.length;
        var bar     = document.getElementById('compareBar');
        var titleEl = document.getElementById('compareTitle');
        var subEl   = document.getElementById('compareSubtitle');
        var btn     = document.getElementById('compareBtn');
        var slot0   = document.getElementById('slot0');
        var slot1   = document.getElementById('slot1');

        [slot0, slot1].forEach(function (slot, i) {
            var pk = selected[i];
            if (pk) {
                slot.className = 'compare-slot filled';
                slot.innerHTML = '<i class="bi bi-car-front me-1"></i>' + selectedTitles[pk];
            } else {
                slot.className = 'compare-slot';
                slot.innerHTML = '<i class="bi bi-plus me-1"></i>Car ' + (i + 1);
            }
        });

        if (n === 0) {
            titleEl.textContent = 'Select 2 vehicles to compare';
            subEl.textContent   = 'Click any saved car above to add it to your comparison.';
            btn.classList.add('disabled');
            btn.setAttribute('aria-disabled', 'true');
            btn.href = '#';
            bar.classList.remove('ready');
        } else if (n === 1) {
            titleEl.textContent = '1 vehicle selected — pick one more';
            subEl.textContent   = 'Select a second car to unlock the comparison.';
            btn.classList.add('disabled');
            btn.setAttribute('aria-disabled', 'true');
            btn.href = '#';
            bar.classList.remove('ready');
        } else {
            titleEl.textContent = 'Ready to compare!';
            subEl.textContent   = 'You\'ve selected 2 vehicles. Analyse their specs side-by-side.';
            btn.classList.remove('disabled');
            btn.removeAttribute('aria-disabled');
            btn.href = (window.COMPARE_BASE_URL || '/comparison/') + '?car1=' + selected[0] + '&car2=' + selected[1];
            bar.classList.add('ready');
        }
    }

    var clearSelBtn = document.getElementById('clearSelectionBtn');
    if (clearSelBtn) {
        clearSelBtn.addEventListener('click', function () {
            document.querySelectorAll('.saved-card.is-selected').forEach(function (c) {
                c.classList.remove('is-selected');
            });
            selected = [];
            selectedTitles = {};
            updateCompareBar();
        });
    }

    var clearAllBtn = document.getElementById('clearAllBtn');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function () {
            showConfirm(
                'Remove all saved vehicles?',
                'This will clear your entire saved list and cannot be undone.',
                function () {
                    fetch(window.CLEAR_SAVED_URL || '/saved/clear/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': getCsrf(), 'X-Requested-With': 'XMLHttpRequest' }
                    }).then(function (r) { return r.json(); }).then(function (data) {
                        if (data.ok) {
                            var grid = document.getElementById('savedGrid');
                            if (grid) {
                                grid.outerHTML =
                                    '<div class="text-center py-5 text-muted" id="emptyState">' +
                                    '<i class="bi bi-heart fs-1 d-block mb-3 text-secondary"></i>' +
                                    '<h5 class="fw-semibold">No saved vehicles yet</h5>' +
                                    '<p class="small mb-3">Browse cars and click the heart icon to save them here.</p>' +
                                    '<a href="' + (window.BROWSE_URL || '/browse/') + '" class="btn btn-primary">Browse Cars</a></div>';
                            }
                            clearAllBtn.remove();
                            selected = [];
                            selectedTitles = {};
                            updateCompareBar();
                            showToast('success', 'All saved vehicles removed.');
                        }
                    });
                }
            );
        });
    }

    function getCsrf() {
        var m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : '';
    }

    function showToast(type, msg) {
        var duration = 3500;
        var iconMap = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
        var icon = iconMap[type] || iconMap.info;
        var container = document.querySelector('.mm-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'mm-toast-container';
            container.setAttribute('aria-live', 'polite');
            document.body.appendChild(container);
        }
        var toast = document.createElement('div');
        toast.className = 'mm-toast mm-toast--' + type;
        toast.setAttribute('role', 'alert');
        toast.style.setProperty('--toast-duration', duration + 'ms');
        toast.innerHTML =
            '<div class="mm-toast__icon"><i class="bi ' + icon + '"></i></div>' +
            '<div class="mm-toast__body"><span class="mm-toast__msg">' + msg + '</span></div>' +
            '<button class="mm-toast__close" onclick="this.closest(\'.mm-toast\').remove()" aria-label="Close"><i class="bi bi-x"></i></button>' +
            '<div class="mm-toast__progress"></div>';
        container.appendChild(toast);
        setTimeout(function () {
            toast.style.animation = 'mmToastOut .28s ease forwards';
            setTimeout(function () { toast.remove(); }, 280);
        }, duration);
    }

    function showConfirm(title, subtitle, onConfirm) {
        var modal      = document.getElementById('mmConfirmModal');
        var confirmBtn = document.getElementById('mmConfirmOk');
        document.getElementById('mmConfirmTitle').textContent    = title;
        document.getElementById('mmConfirmSubtitle').textContent = subtitle;
        var newBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
        newBtn.addEventListener('click', function () {
            closeConfirmModal();
            onConfirm();
        });
        modal.style.display = 'flex';
        setTimeout(function () { modal.classList.add('mm-modal--in'); }, 10);
    }

    function closeConfirmModal() {
        var modal = document.getElementById('mmConfirmModal');
        modal.classList.remove('mm-modal--in');
        setTimeout(function () { modal.style.display = 'none'; }, 200);
    }

    var cancelBtn  = document.getElementById('mmConfirmCancel');
    var confirmModal = document.getElementById('mmConfirmModal');
    if (cancelBtn)      cancelBtn.addEventListener('click', closeConfirmModal);
    if (confirmModal) {
        confirmModal.addEventListener('click', function (e) {
            if (e.target === this) closeConfirmModal();
        });
    }

    updateCompareBar();
})();
