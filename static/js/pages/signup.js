(function () {
    'use strict';

    function bindToggle(btnId, inputId) {
        var btn = document.getElementById(btnId);
        var inp = document.getElementById(inputId);
        if (!btn || !inp) return;
        btn.addEventListener('click', function () {
            var showing = inp.type === 'text';
            inp.type = showing ? 'password' : 'text';
            btn.querySelector('i').className = showing ? 'bi bi-eye-slash' : 'bi bi-eye';
        });
    }
    bindToggle('togglePw1', 'pw1');
    bindToggle('togglePw2', 'pw2');

    var signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', function (e) {
            var tc  = document.getElementById('termsCheck');
            var err = document.getElementById('terms-error');
            if (!tc.checked) {
                e.preventDefault();
                err.style.display = 'block';
                tc.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                err.style.display = 'none';
            }
        });
    }
    function bindNameValidation(fieldId, errId, label) {
        var field = document.getElementById(fieldId);
        var err   = document.getElementById(errId);
        if (!field || !err) return;
        field.addEventListener('blur', function () {
            var v = this.value.trim();
            if (!v) { err.style.display = 'none'; field.classList.remove('is-valid','is-invalid'); return; }
            if (v.length < 2) {
                err.textContent = label + ' must be at least 2 characters.';
                err.style.display = 'block';
                field.classList.add('is-invalid'); field.classList.remove('is-valid');
            } else if (v.length > 50) {
                err.textContent = label + ' must be 50 characters or fewer.';
                err.style.display = 'block';
                field.classList.add('is-invalid'); field.classList.remove('is-valid');
            } else if (!/^[A-Za-z\u00C0-\u024F'\- ]+$/.test(v)) {
                err.textContent = label + ' can only contain letters, hyphens, and apostrophes.';
                err.style.display = 'block';
                field.classList.add('is-invalid'); field.classList.remove('is-valid');
            } else {
                err.style.display = 'none';
                field.classList.remove('is-invalid'); field.classList.add('is-valid');
            }
        });
        field.addEventListener('input', function () {
            err.style.display = 'none';
            field.classList.remove('is-valid','is-invalid');
        });
    }
    bindNameValidation('id_first_name', 'err_first_name', 'First name');
    bindNameValidation('id_last_name',  'err_last_name',  'Last name');

    // ── Email validation tick ───────────────────────────────────────────────
    var emailInput = document.getElementById('id_email');
    if (emailInput) {
        emailInput.addEventListener('blur', function () {
            var v = this.value.trim();
            if (!v) { this.classList.remove('is-valid','is-invalid'); return; }
            if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
                this.classList.remove('is-invalid'); this.classList.add('is-valid');
            } else {
                this.classList.remove('is-valid'); this.classList.add('is-invalid');
            }
        });
        emailInput.addEventListener('input', function () {
            this.classList.remove('is-valid','is-invalid');
        });
    }

    var phoneInput = document.getElementById('id_phone_signup');
    var phoneErr   = document.getElementById('err_phone_signup');
    if (phoneInput && phoneErr) {
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
        phoneInput.addEventListener('blur', function () {
            var val = this.value.trim();
            if (val) {
                var formatted = formatUKPhone(val);
                this.value = formatted;
                val = formatted;
            }
            if (!isValidUKPhone(val)) {
                phoneErr.textContent = 'Enter a valid UK number (e.g. 07700 900000 or +44 7700 900000).';
                phoneErr.style.display = 'block';
                phoneInput.classList.add('is-invalid'); phoneInput.classList.remove('is-valid');
            } else {
                phoneErr.style.display = 'none';
                if (val) { phoneInput.classList.remove('is-invalid'); phoneInput.classList.add('is-valid'); }
                else { phoneInput.classList.remove('is-invalid','is-valid'); }
            }
        });
        phoneInput.addEventListener('input', function () {
            phoneErr.style.display = 'none';
            phoneInput.classList.remove('is-valid','is-invalid');
        });
    }

    var pw1      = document.getElementById('pw1');
    var pw2      = document.getElementById('pw2');
    var matchMsg  = document.getElementById('pwMatchMsg');

    function checkMatch() {
        var v1 = pw1 ? pw1.value : '';
        var v2 = pw2 ? pw2.value : '';
        if (!v2) {
            if (pw1) pw1.classList.remove('is-valid');
            if (pw2) pw2.classList.remove('is-valid', 'is-invalid');
            if (matchMsg)  matchMsg.style.display  = 'none';
            return;
        }
        if (v1 === v2 && v1 !== '') {
            if (pw1) { pw1.classList.remove('is-invalid'); pw1.classList.add('is-valid'); }
            if (pw2) { pw2.classList.remove('is-invalid'); pw2.classList.add('is-valid'); }
            if (matchMsg) {
                matchMsg.style.color   = 'var(--mm-success)';
                matchMsg.innerHTML     = '<i class="bi bi-check-circle-fill me-1"></i>Passwords match';
                matchMsg.style.display = 'block';
            }
        } else {
            if (pw1) pw1.classList.remove('is-valid');
            if (pw2) { pw2.classList.remove('is-valid'); pw2.classList.add('is-invalid'); }
            if (matchMsg) {
                matchMsg.style.color   = 'var(--mm-danger)';
                matchMsg.innerHTML     = '<i class="bi bi-x-circle-fill me-1"></i>Passwords don\'t match';
                matchMsg.style.display = 'block';
            }
        }
    }

    if (pw2) {
        pw2.addEventListener('input', checkMatch);
    }

    if (pw1) {
        var pwStrength = document.getElementById('pwStrength');
        var pwLabel    = document.getElementById('pwStrengthLabel');
        var segments   = pwStrength ? pwStrength.querySelectorAll('.pw-seg') : [];
        var checks     = pwStrength ? pwStrength.querySelectorAll('.pw-check') : [];

        var rules = {
            length: function (v) { return v.length >= 8; },
            upper:  function (v) { return /[A-Z]/.test(v); },
            number: function (v) { return /[0-9]/.test(v); },
            symbol: function (v) { return /[^A-Za-z0-9]/.test(v); }
        };

        var levelConfig = [
            { label: 'Weak',   color: '#ef4444' },
            { label: 'Fair',   color: 'var(--mm-accent)' },
            { label: 'Good',   color: '#eab308' },
            { label: 'Strong', color: 'var(--mm-success)' }
        ];

        pw1.addEventListener('input', function () {
            var v = this.value;
            if (!v) {
                if (pwStrength) pwStrength.style.display = 'none';
                checkMatch();
                return;
            }
            if (pwStrength) pwStrength.style.display = 'block';

            var score = 0;
            checks.forEach(function (el) {
                var rule = rules[el.dataset.rule];
                var ok   = rule && rule(v);
                if (ok) { score++; }
                el.style.color = ok ? 'var(--mm-success)' : '#9ca3af';
                var icon = el.querySelector('i');
                icon.className   = ok ? 'bi bi-check-circle-fill me-1' : 'bi bi-circle me-1';
                icon.style.fontSize = '.6rem';
            });

            var cfg = levelConfig[score - 1] || levelConfig[0];
            if (pwLabel) {
                pwLabel.textContent = cfg.label;
                pwLabel.style.color = cfg.color;
            }
            segments.forEach(function (seg, i) {
                seg.style.background = i < score ? cfg.color : '#e5e7eb';
            });

            checkMatch();
        });
    }
})();
