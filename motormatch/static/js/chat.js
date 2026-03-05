/* ============================================================
   Motor Match – Chat page JS
   Handles: AJAX send, polling (messages + typing + read
   receipts), attachment preview, auto-grow textarea.

   Depends on globals set inline in conversation.html:
     OTHER_PK, CSRF, MY_INITS, SEND_URL, POLL_URL, TYPING_URL
   ============================================================ */

(function () {
    'use strict';

    var lastId       = 0;
    var typingTimer  = null;
    var POLL_MS      = 2500;

    // ── DOM refs ───────────────────────────────────────────────
    var box          = document.getElementById('chatMessages');
    var input        = document.getElementById('msgInput');
    var sendBtn      = document.getElementById('sendBtn');
    var typingStatus = document.getElementById('typingStatus');
    var typingBubble = document.getElementById('typingBubble');
    var attachInput  = document.getElementById('attachInput');

    if (!box || !input) return; // Not on chat page

    // Seed lastId from server-rendered messages
    document.querySelectorAll('.bubble-wrap[data-id]').forEach(function (el) {
        var id = parseInt(el.getAttribute('data-id'), 10);
        if (id > lastId) lastId = id;
    });

    // ── Scroll ─────────────────────────────────────────────────
    function scrollBottom(smooth) {
        box.scrollTo({ top: box.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
    }
    scrollBottom(false);

    // ── Auto-grow textarea ─────────────────────────────────────
    input.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 160) + 'px';
        // Typing signal (debounced 300ms)
        clearTimeout(typingTimer);
        typingTimer = setTimeout(function () {
            fetch(TYPING_URL, { method: 'POST', headers: { 'X-CSRFToken': CSRF } });
        }, 300);
    });

    // ── Enter = send, Shift+Enter = newline ────────────────────
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); doSend(); }
    });
    sendBtn.addEventListener('click', doSend);

    // ── Attachment preview ─────────────────────────────────────
    if (attachInput) {
        attachInput.addEventListener('change', function () {
            if (!this.files[0]) return;
            var reader = new FileReader();
            reader.onload = function (e) {
                document.getElementById('attachThumb').src = e.target.result;
                document.getElementById('attachPreview').style.display = 'block';
            };
            reader.readAsDataURL(this.files[0]);
        });
    }

    window.clearAttachment = function () {
        if (attachInput) attachInput.value = '';
        document.getElementById('attachPreview').style.display = 'none';
        document.getElementById('attachThumb').src = '';
    };

    // ── Send ───────────────────────────────────────────────────
    function doSend() {
        var body = input.value.trim();
        var file = attachInput ? attachInput.files[0] : null;
        if (!body && !file) return;

        var fd = new FormData();
        if (body) fd.append('body', body);
        if (file) fd.append('attachment', file);

        // Optimistic bubble immediately
        var tmpId = 'tmp_' + Date.now();
        appendBubble({
            id: tmpId,
            body: body,
            attachment_url: file ? URL.createObjectURL(file) : null,
            time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
            is_mine: true,
            initials: MY_INITS,
            is_read: false,
        });
        input.value = '';
        input.style.height = 'auto';
        if (window.clearAttachment) window.clearAttachment();
        scrollBottom(true);

        fetch(SEND_URL, { method: 'POST', headers: { 'X-CSRFToken': CSRF }, body: fd })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                // Replace temp id with real server id
                var tmpEl = document.querySelector('.bubble-wrap[data-id="' + tmpId + '"]');
                if (tmpEl && d.id) {
                    tmpEl.setAttribute('data-id', d.id);
                    lastId = Math.max(lastId, d.id);
                }
            })
            .catch(function () {});
    }

    // ── HTML escaping ──────────────────────────────────────────
    function esc(s) {
        return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // ── Append bubble to DOM ───────────────────────────────────
    function appendBubble(m) {
        var es = document.getElementById('emptyState');
        if (es) es.remove();

        var wrap = document.createElement('div');
        wrap.className = 'bubble-wrap ' + (m.is_mine ? 'mine' : 'theirs');
        wrap.setAttribute('data-id', m.id);

        var avatar   = m.is_mine ? '' : '<div class="avatar-sm flex-shrink-0">' + esc(m.initials) + '</div>';
        var bodyHtml = m.body ? esc(m.body) : '';
        var imgHtml  = m.attachment_url
            ? '<img src="' + m.attachment_url + '" class="attach" onclick="window.open(this.src)" alt="attachment">'
            : '';
        var tick = m.is_mine
            ? '<i class="bi bi-check2 tick-icon" style="color:#adb5bd;"></i>'
            : '';

        wrap.innerHTML = avatar +
            '<div class="bubble-col">' +
                '<div class="bubble ' + (m.is_mine ? 'mine' : 'theirs') + '">' + bodyHtml + imgHtml + '</div>' +
                '<div class="bubble-time">' + m.time + tick + '</div>' +
            '</div>';

        box.insertBefore(wrap, typingBubble);

        if (typeof m.id === 'number' && m.id > lastId) lastId = m.id;
    }

    // ── Polling ────────────────────────────────────────────────
    function poll() {
        fetch(POLL_URL + '?after=' + lastId, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                // Append new messages from the other person
                d.messages.forEach(function (m) {
                    if (!document.querySelector('.bubble-wrap[data-id="' + m.id + '"]')) {
                        appendBubble(m);
                        scrollBottom(true);
                    }
                });

                // Typing indicator
                if (d.typing) {
                    typingBubble.classList.remove('d-none');
                    typingStatus.textContent = 'typing\u2026';
                    scrollBottom(false);
                } else {
                    typingBubble.classList.add('d-none');
                    typingStatus.textContent = '';
                }

                // Read receipts – upgrade grey tick to blue double-tick
                if (d.read_up_to) {
                    document.querySelectorAll('.bubble-wrap.mine').forEach(function (el) {
                        var id = parseInt(el.getAttribute('data-id'), 10);
                        if (!isNaN(id) && id <= d.read_up_to) {
                            var tick = el.querySelector('.tick-icon');
                            if (tick) {
                                tick.className = 'bi bi-check2-all tick-icon';
                                tick.style.color = '#a5b4fc';
                            }
                        }
                    });
                }
            })
            .catch(function () {});
    }

    setInterval(poll, POLL_MS);

})();
