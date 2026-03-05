/* ============================================================
   Motor Match – global real-time notification polling
   Loaded in base.html for authenticated users only.
   Polls /notifications/poll/ every 15s and updates navbar
   bell and message badge counts without a page refresh.
   ============================================================ */

(function () {
    'use strict';

    var POLL_INTERVAL = 15000; // 15 seconds

    function updateBadge(el, count) {
        if (!el) return;
        if (count > 0) {
            el.textContent = count > 9 ? '9+' : count;
            el.classList.remove('d-none');
        } else {
            el.classList.add('d-none');
        }
    }

    function pollNotifications() {
        fetch('/notifications/poll/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (d) {
                if (!d) return;
                updateBadge(document.getElementById('navBellBadge'), d.unread_notifs);
                updateBadge(document.getElementById('navMsgBadge'),  d.unread_msgs);
                // Also update dashboard topbar badge if present (dashboard.html)
                updateBadge(document.getElementById('topBellBadge'), d.unread_notifs);
            })
            .catch(function () {/* silent – offline or server error */});
    }

    // Kick off immediately then repeat
    pollNotifications();
    setInterval(pollNotifications, POLL_INTERVAL);
})();

/* ============================================================
   Shared AJAX save / unsave helper – used on home, saved, etc.
   ============================================================ */
function getCsrf() {
    var match = document.cookie.split(';').map(function(c){ return c.trim(); })
        .find(function(c){ return c.startsWith('csrftoken='); });
    return match ? match.split('=')[1] : '';
}

function toggleSaveCard(btn) {
    var icon = btn.querySelector('i');
    fetch(btn.dataset.url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCsrf() }
    })
    .then(function(r){ return r.json(); })
    .then(function(d){
        if (d.saved) {
            if (icon) icon.className = icon.className.replace('bi-heart text-muted', 'bi-heart-fill text-danger');
            btn.title = 'Unsave';
            btn.dataset.saved = '1';
        } else {
            if (icon) icon.className = icon.className.replace('bi-heart-fill text-danger', 'bi-heart text-muted');
            btn.title = 'Save';
            btn.dataset.saved = '0';
            // Remove card from saved page if we're on it
            var card = btn.closest('.col');
            if (card && document.querySelector('.saved-grid')) card.remove();
        }
    })
    .catch(function(){});
}
