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
