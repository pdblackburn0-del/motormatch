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
})();
