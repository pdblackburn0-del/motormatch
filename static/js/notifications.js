/* ============================================================
   Motor Match – global real-time notification polling
   Loads in base.html for authenticated users only.
   Polls /notifications/poll/ every 15s, updates navbar
   bell badge and populates the dropdown in real-time.
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

    function escHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // ── Render notification list in the dropdown ────────────────
    function renderNotifs(latest) {
        var list  = document.getElementById('notifList');
        var empty = document.getElementById('notifEmpty');
        if (!list) return;

        // Remove old rendered items (keep the empty state element)
        list.querySelectorAll('.notif-item').forEach(function (el) { el.remove(); });

        if (!latest || latest.length === 0) {
            if (empty) empty.style.display = '';
            return;
        }

        if (empty) empty.style.display = 'none';

        var iconMap = { success: 'bi-check-lg bg-success text-white', warning: 'bi-exclamation bg-warning text-dark', info: 'bi-bell bg-primary text-white' };

        latest.forEach(function (n) {
            var div = document.createElement('div');
            div.className = 'notif-item d-flex align-items-start gap-2 px-3 py-2 border-bottom';
            div.dataset.id = n.id;
            var icon = iconMap[n.notif_type] || iconMap.info;
            div.innerHTML =
                '<span class="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0 mt-1 ' + icon + '" style="width:28px;height:28px;font-size:.7rem;">' +
                    '<i class="bi ' + icon.split(' ')[0] + ' small"></i>' +
                '</span>' +
                '<div class="flex-grow-1 min-w-0">' +
                    (n.url ? '<a href="' + escHtml(n.url) + '" class="text-decoration-none text-dark">' : '') +
                    '<p class="fw-semibold mb-0" style="font-size:.78rem;">' + escHtml(n.title) + '</p>' +
                    '<p class="text-muted mb-0" style="font-size:.73rem;">' + escHtml(n.message) + '</p>' +
                    '<span class="text-muted" style="font-size:.68rem;">' + escHtml(n.created_at) + '</span>' +
                    (n.url ? '</a>' : '') +
                '</div>' +
                '<button class="dismiss-notif btn p-0 border-0 text-muted flex-shrink-0 ms-1" data-id="' + n.id + '" title="Dismiss" style="font-size:1rem;line-height:1;">&times;</button>';
            list.insertBefore(div, list.querySelector('.notif-item') ? null : empty);
        });
    }

    // ── Dismiss single notification ─────────────────────────────
    function dismissOne(id, el) {
        fetch('/notifications/' + id + '/dismiss/', {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCsrf() }
        })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
            if (!d) return;
            // Animate out
            el.style.transition = 'opacity .2s, max-height .25s';
            el.style.overflow = 'hidden';
            el.style.opacity = '0';
            el.style.maxHeight = el.offsetHeight + 'px';
            setTimeout(function () { el.style.maxHeight = '0'; el.style.padding = '0'; }, 10);
            setTimeout(function () { el.remove(); checkEmpty(); }, 260);
            updateBadge(document.getElementById('navBellBadge'), d.unread);
            updateBadge(document.getElementById('topBellBadge'), d.unread);
        })
        .catch(function () {});
    }

    // ── Clear all notifications ─────────────────────────────────
    document.addEventListener('click', function (e) {
        // Dismiss one
        var btn = e.target.closest('.dismiss-notif');
        if (btn) {
            e.stopPropagation();
            var item = btn.closest('.notif-item');
            if (item) dismissOne(btn.dataset.id, item);
            return;
        }

        // Clear all
        if (e.target.id === 'clearAllNotifs') {
            fetch('/notifications/dismiss-all/', {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCsrf() }
            })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (d) {
                if (!d) return;
                document.querySelectorAll('.notif-item').forEach(function (el) { el.remove(); });
                checkEmpty();
                updateBadge(document.getElementById('navBellBadge'), 0);
                updateBadge(document.getElementById('topBellBadge'), 0);
            })
            .catch(function () {});
        }
    });

    function checkEmpty() {
        var empty = document.getElementById('notifEmpty');
        if (!empty) return;
        var hasItems = document.querySelectorAll('.notif-item').length > 0;
        empty.style.display = hasItems ? 'none' : '';
    }

    // ── Poll ────────────────────────────────────────────────────
    function pollNotifications() {
        fetch('/notifications/poll/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (d) {
                if (!d) return;
                updateBadge(document.getElementById('navBellBadge'), d.unread_notifs);
                updateBadge(document.getElementById('navMsgBadge'),  d.unread_msgs);
                updateBadge(document.getElementById('topBellBadge'), d.unread_notifs);
                renderNotifs(d.latest);
            })
            .catch(function () {/* silent */});
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
    var wasSaved = btn.dataset.saved === '1';

    // Optimistic immediate update
    if (icon) {
        if (wasSaved) {
            icon.classList.remove('bi-heart-fill', 'vc__heart-icon--saved', 'text-danger');
            icon.classList.add('bi-heart', 'vc__heart-icon', 'text-muted');
        } else {
            icon.classList.remove('bi-heart', 'vc__heart-icon', 'text-muted');
            icon.classList.add('bi-heart-fill', 'vc__heart-icon--saved', 'text-danger');
        }
    }
    btn.dataset.saved = wasSaved ? '0' : '1';
    btn.title = wasSaved ? 'Save' : 'Unsave';

    fetch(btn.dataset.url, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCsrf() }
    })
    .then(function(r){ return r.json(); })
    .then(function(d){
        // Sync with server truth in case of mismatch
        if (d.saved !== !wasSaved) {
            if (icon) {
                if (d.saved) {
                    icon.classList.remove('bi-heart', 'vc__heart-icon', 'text-muted');
                    icon.classList.add('bi-heart-fill', 'vc__heart-icon--saved', 'text-danger');
                } else {
                    icon.classList.remove('bi-heart-fill', 'vc__heart-icon--saved', 'text-danger');
                    icon.classList.add('bi-heart', 'vc__heart-icon', 'text-muted');
                }
                btn.dataset.saved = d.saved ? '1' : '0';
                btn.title = d.saved ? 'Unsave' : 'Save';
            }
        }
        // Remove card from saved page if unsaved
        if (!d.saved) {
            var card = btn.closest('.col');
            if (card && document.querySelector('.saved-grid')) card.remove();
        }
    })
    .catch(function(){
        // Revert optimistic update on failure
        if (icon) {
            if (wasSaved) {
                icon.classList.remove('bi-heart', 'vc__heart-icon', 'text-muted');
                icon.classList.add('bi-heart-fill', 'vc__heart-icon--saved', 'text-danger');
            } else {
                icon.classList.remove('bi-heart-fill', 'vc__heart-icon--saved', 'text-danger');
                icon.classList.add('bi-heart', 'vc__heart-icon', 'text-muted');
            }
            btn.dataset.saved = wasSaved ? '1' : '0';
            btn.title = wasSaved ? 'Unsave' : 'Save';
        }
    });
}
