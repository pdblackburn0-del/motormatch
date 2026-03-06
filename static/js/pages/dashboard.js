(function () {
    'use strict';

    function initToasts() {
        var duration = 3500;
        document.querySelectorAll('.mm-toast').forEach(function (toast) {
            toast.style.setProperty('--toast-duration', duration + 'ms');
            setTimeout(function () {
                toast.style.animation = 'mmToastOut .28s ease forwards';
                setTimeout(function () { toast.remove(); }, 280);
            }, duration);
        });
    }

    function initRemoveModal() {
        var modal = document.getElementById('removeModal');
        if (!modal) return;
        modal.addEventListener('show.bs.modal', function (e) {
            var btn    = e.relatedTarget;
            var carId  = btn.getAttribute('data-car-id');
            var carName = btn.getAttribute('data-car-name');
            document.getElementById('removeModalBody').textContent =
                '"' + carName + '" will be hidden from buyers. Your conversations and bids are preserved.';
            document.getElementById('removeModalForm').action = '/vehicle/' + carId + '/delete/';
        });
    }

    function initDestroyModal() {
        var modal = document.getElementById('destroyModal');
        if (!modal) return;
        modal.addEventListener('show.bs.modal', function (e) {
            var btn    = e.relatedTarget;
            var carId  = btn.getAttribute('data-car-id');
            var carName = btn.getAttribute('data-car-name');
            document.getElementById('destroyModalBody').textContent =
                '"' + carName + '" will be permanently deleted. This cannot be undone.';
            document.getElementById('destroyModalForm').action = '/vehicle/' + carId + '/destroy/';
        });
    }

    function initSearch() {
        var input = document.getElementById('dbSearch');
        if (!input) return;
        input.addEventListener('input', function () {
            var q = this.value.toLowerCase().trim();
            document.querySelectorAll('.db-listing').forEach(function (row) {
                var text = row.querySelector('.db-listing__title');
                if (!text) return;
                row.style.display = (!q || text.textContent.toLowerCase().includes(q)) ? '' : 'none';
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initToasts();
        initRemoveModal();
        initDestroyModal();
        initSearch();
    });

})();
