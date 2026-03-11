'use strict';

var avatarInput = document.getElementById('id_avatar');
if (avatarInput) {
    avatarInput.addEventListener('change', function (e) {
        var file = e.target.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function (ev) {
            var preview  = document.getElementById('avatarPreview');
            var initials = document.getElementById('avatarInitials');
            preview.src = ev.target.result;
            preview.style.display = 'block';
            if (initials) initials.style.display = 'none';
        };
        reader.readAsDataURL(file);
    });
}

var avatarEditBtn = document.getElementById('avatarEditBtn');
if (avatarEditBtn) {
    avatarEditBtn.addEventListener('click', function () {
        document.getElementById('id_avatar').click();
    });
}
