'use strict';

function openDeleteModal(userPk, name) {
    document.getElementById('inboxDeleteText').textContent =
        'All messages with ' + name + ' will be permanently removed. This cannot be undone.';
    document.getElementById('inboxDeleteForm').action = '/inbox/' + userPk + '/delete/';
    new bootstrap.Modal(document.getElementById('inboxDeleteModal')).show();
}

document.addEventListener('click', function (e) {
    var btn = e.target.closest('.inbox-delete-btn');
    if (btn) openDeleteModal(btn.dataset.userPk, btn.dataset.userName);
});
