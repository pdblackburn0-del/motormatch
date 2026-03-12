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

(function () {
    var bioField   = document.getElementById('id_bio');
    var bioCounter = document.querySelector('.bio-counter');
    if (!bioField || !bioCounter) return;
    var max = parseInt(bioField.getAttribute('data-maxlength') || bioField.getAttribute('maxlength') || '500', 10);
    function updateBioCounter() {
        var n = bioField.value.length;
        bioCounter.textContent = n + ' / ' + max;
        bioCounter.style.color = n >= max ? '#dc2626' : '';
    }
    bioField.addEventListener('input', updateBioCounter);
    updateBioCounter();
}());

(function () {
    var phoneInput = document.getElementById('id_phone');
    if (!phoneInput) return;

    function formatUKPhone(val) {
        var raw = val.replace(/[^\d+]/g, '');
        if (/^0044/.test(raw)) raw = '+44' + raw.slice(4);
        if (/^0[1-9]/.test(raw)) raw = '+44' + raw.slice(1);
        if (raw.slice(0, 3) !== '+44') return val;
        var nat = raw.slice(3); 
        if (nat.length < 1) return '+44';
        if (nat.length <= 4) return '+44 ' + nat;
        return '+44 ' + nat.slice(0, 4) + ' ' + nat.slice(4, 10);
    }

    function isValidUKPhone(val) {
        if (!val) return true; 
        var cleaned = val.replace(/[\s\-\(\)\.]/g, '');
        return /^(\+44|0044|0)[1-9][0-9]{8,9}$/.test(cleaned);
    }

    var phoneErr = phoneInput.parentNode.querySelector('.phone-rt-error');
    if (!phoneErr) {
        phoneErr = document.createElement('div');
        phoneErr.className = 'text-danger small phone-rt-error';
        phoneInput.insertAdjacentElement('afterend', phoneErr);
    }

    phoneInput.addEventListener('blur', function () {
        var val = this.value.trim();
        if (val) {
            var formatted = formatUKPhone(val);
            this.value = formatted;
            val = formatted;
        }
        if (isValidUKPhone(val)) {
            phoneErr.textContent = '';
        } else {
            phoneErr.textContent = 'Enter a valid UK phone number (e.g. 07700 900000 or +44 7700 900000).';
        }
    });

    phoneInput.addEventListener('input', function () {
        phoneErr.textContent = '';
    });
}());

(function () {
    function addBlurValidation(fieldId, minLen, msg) {
        var field = document.getElementById(fieldId);
        if (!field) return;
        var err = field.parentNode.querySelector('.rt-error');
        if (!err) {
            err = document.createElement('div');
            err.className = 'text-danger small rt-error';
            field.insertAdjacentElement('afterend', err);
        }
        field.addEventListener('blur', function () {
            var val = this.value.trim();
            err.textContent = (val && val.length < minLen) ? msg : '';
        });
        field.addEventListener('input', function () {
            err.textContent = '';
        });
    }
    addBlurValidation('id_first_name', 2, 'First name must be at least 2 characters.');
    addBlurValidation('id_last_name',  2, 'Last name must be at least 2 characters.');
}());
