/* ============================================================
   Motor Match – Chat page JS
   Handles: AJAX send, polling (messages + typing + read
   receipts), attachment preview, auto-grow textarea,
   GIF picker (Tenor API proxy).

   Depends on globals set inline in conversation.html:
     OTHER_PK, CSRF, MY_INITS, SEND_URL, POLL_URL, TYPING_URL
   ============================================================ */

(function () {
    'use strict';

    var lastId         = 0;
    var typingTimer    = null;
    var POLL_MS        = 2500;
    var pendingGif     = null;
    var gifSearchTimer = null;

    // ── DOM refs ───────────────────────────────────────────────
    var box          = document.getElementById('chatMessages');
    var input        = document.getElementById('msgInput');
    var sendBtn      = document.getElementById('sendBtn');
    var typingStatus = document.getElementById('typingStatus');
    var typingBubble = document.getElementById('typingBubble');
    var attachInput  = document.getElementById('attachInput');
    var gifBtn       = document.getElementById('gifBtn');
    var gifPicker    = document.getElementById('gifPicker');
    var gifSearch    = document.getElementById('gifSearch');
    var gifGrid      = document.getElementById('gifGrid');

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
        pendingGif = null;
    };

    // ── GIF picker ─────────────────────────────────────────────
    if (gifBtn && gifPicker) {
        gifBtn.addEventListener('click', function () {
            var isOpen = !gifPicker.classList.contains('d-none');
            gifPicker.classList.toggle('d-none');
            gifBtn.classList.toggle('active', !isOpen);
            if (!isOpen && gifGrid && gifGrid.children.length === 0) {
                fetchGifs('');
            }
        });
    }

    if (gifSearch) {
        gifSearch.addEventListener('input', function () {
            clearTimeout(gifSearchTimer);
            var q = this.value.trim();
            gifSearchTimer = setTimeout(function () { fetchGifs(q); }, 400);
        });
    }

    function fetchGifs(q) {
        if (!gifGrid) return;
        gifGrid.innerHTML = '<p class="text-muted small text-center py-2 mb-0">Loading\u2026</p>';
        fetch('/api/tenor/?q=' + encodeURIComponent(q))
            .then(function (r) { return r.json(); })
            .then(function (d) {
                gifGrid.innerHTML = '';
                var list = d.gifs || [];
                if (!list.length) {
                    gifGrid.innerHTML = '<p class="text-muted small text-center py-2 mb-0">No GIFs found</p>';
                    return;
                }
                list.forEach(function (g) {
                    var div = document.createElement('div');
                    div.className = 'gif-item';
                    var img = document.createElement('img');
                    img.src = g.preview;
                    img.loading = 'lazy';
                    img.alt = g.title || 'GIF';
                    div.appendChild(img);
                    div.addEventListener('click', function () {
                        pendingGif = g.url;
                        document.getElementById('attachThumb').src = g.url;
                        document.getElementById('attachPreview').style.display = 'block';
                        gifPicker.classList.add('d-none');
                        gifBtn.classList.remove('active');
                        doSend();
                    });
                    gifGrid.appendChild(div);
                });
            })
            .catch(function () {
                gifGrid.innerHTML = '<p class="text-muted small text-center py-2 mb-0">Failed to load GIFs</p>';
            });
    }

    // ── Send ───────────────────────────────────────────────────
    function doSend() {
        var body = input.value.trim();
        var file = attachInput ? attachInput.files[0] : null;
        if (!body && !file && !pendingGif) return;

        var fd = new FormData();
        if (body) fd.append('body', body);
        if (file) fd.append('attachment', file);
        if (pendingGif) fd.append('gif_url', pendingGif);

        var gifForBubble = pendingGif;
        pendingGif = null;

        // Optimistic bubble immediately
        var tmpId = 'tmp_' + Date.now();
        appendBubble({
            id: tmpId,
            body: body,
            gif_url: gifForBubble,
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

        var avatar  = m.is_mine ? '' : (OTHER_AVATAR_URL ? '<img src="' + OTHER_AVATAR_URL + '" class="avatar-sm flex-shrink-0" style="object-fit:cover;" alt="">' : '<div class="avatar-sm flex-shrink-0">' + esc(m.initials) + '</div>');

        var bubbleContent;
        var bubbleClass = 'bubble ' + (m.is_mine ? 'mine' : 'theirs');
        if (m.is_deleted) {
            bubbleClass += ' bubble--deleted';
            var notice = m.deleted_by_staff ? 'Message deleted by staff' : 'Message deleted';
            bubbleContent = '<span class="bubble__deleted-notice"><i class="bi bi-slash-circle"></i> ' + notice + '</span>';
        } else {
            var gifHtml  = m.gif_url ? '<img src="' + m.gif_url + '" class="attach gif-attach" onclick="window.open(this.src)" alt="GIF">' : '';
            var bodyHtml = (!m.gif_url && m.body) ? esc(m.body) : '';
            var imgHtml  = (!m.gif_url && m.attachment_url) ? '<img src="' + m.attachment_url + '" class="attach" onclick="window.open(this.src)" alt="attachment">' : '';
            bubbleContent = gifHtml + bodyHtml + imgHtml;
        }
        var tick = m.is_mine
            ? '<i class="bi bi-check2 tick-icon" style="color:#adb5bd;"></i>'
            : '';

        wrap.innerHTML = avatar +
            '<div class="bubble-col">' +
                '<div class="' + bubbleClass + '">' + bubbleContent + '</div>' +
                '<div class="bubble-time">' + m.time + tick + '</div>' +
            '</div>';

        box.insertBefore(wrap, typingBubble);

        if (typeof m.id === 'number' && m.id > lastId) lastId = m.id;
    }

    // ── Polling ────────────────────────────────────────────────
    function applyDeleted(id, byStaff) {
        var el = document.querySelector('.bubble-wrap[data-id="' + id + '"]');
        if (!el) return;
        var bubble = el.querySelector('.bubble');
        if (!bubble || bubble.classList.contains('bubble--deleted')) return;
        bubble.classList.add('bubble--deleted');
        var notice = byStaff ? 'Message deleted by staff' : 'Message deleted';
        bubble.innerHTML = '<span class="bubble__deleted-notice"><i class="bi bi-slash-circle"></i> ' + notice + '</span>';
    }

    function poll() {
        fetch(POLL_URL + '?after=' + lastId, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                d.messages.forEach(function (m) {
                    if (!document.querySelector('.bubble-wrap[data-id="' + m.id + '"]')) {
                        appendBubble(m);
                        scrollBottom(true);
                    } else if (m.is_deleted) {
                        applyDeleted(m.id, m.deleted_by_staff);
                    }
                });

                // Apply deletions to already-rendered bubbles
                if (d.deleted_ids && d.deleted_ids.length) {
                    d.deleted_ids.forEach(function (id) {
                        applyDeleted(id, true);
                    });
                }

                if (d.typing) {
                    typingBubble.classList.remove('d-none');
                    if (typingStatus) typingStatus.textContent = 'typing\u2026';
                    var os = document.getElementById('onlineStatus'); if (os) os.style.display = 'none';
                    scrollBottom(false);
                } else {
                    typingBubble.classList.add('d-none');
                    if (typingStatus) typingStatus.textContent = '';
                    var os2 = document.getElementById('onlineStatus'); if (os2) os2.style.display = '';
                }

                // Update online presence indicator live
                if (d.other_online) {
                    var onlineEl = document.getElementById('onlineStatus');
                    if (onlineEl) {
                        if (d.other_online.online) {
                            onlineEl.innerHTML = '<span class="text-success d-flex align-items-center gap-1"><i class="bi bi-circle-fill" style="font-size:.45rem;"></i>Online now</span>';
                        } else if (d.other_online.display) {
                            onlineEl.innerHTML = '<span class="text-muted">Last seen ' + d.other_online.display + '</span>';
                        } else {
                            onlineEl.innerHTML = '';
                        }
                    }
                }

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
