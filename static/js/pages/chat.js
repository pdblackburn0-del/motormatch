(function () {
    'use strict';

    var lastId         = 0;
    var reactV         = -1;
    var typingTimer    = null;
    var POLL_MS        = 2500;
    var pendingGif     = null;
    var gifSearchTimer = null;

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

    if (!box || !input) return;

    document.querySelectorAll('.bubble-wrap[data-id]').forEach(function (el) {
        var id = parseInt(el.getAttribute('data-id'), 10);
        if (id > lastId) lastId = id;
    });

    function scrollBottom(smooth) {
        box.scrollTo({ top: box.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
    }
    scrollBottom(false);

    input.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 160) + 'px';

        clearTimeout(typingTimer);
        typingTimer = setTimeout(function () {
            fetch(TYPING_URL, { method: 'POST', headers: { 'X-CSRFToken': CSRF } });
        }, 300);
    });

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); doSend(); }
    });
    sendBtn.addEventListener('click', doSend);

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

    var removeAttachBtn = document.querySelector('.remove-attach');
    if (removeAttachBtn) {
        removeAttachBtn.addEventListener('click', function () { window.clearAttachment(); });
    }

    document.addEventListener('click', function (e) {
        var img = e.target.closest('img.attach');
        if (img) window.open(img.src);
    });

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

    var EMOJI_CATS = [
        { icon: '\uD83D\uDE42', label: 'smileys', emojis: ['\uD83D\uDE00','\uD83D\uDE03','\uD83D\uDE04','\uD83D\uDE01','\uD83D\uDE06','\uD83E\uDD29','\uD83D\uDE05','\uD83D\uDE02','\uD83E\uDD23','\uD83E\uDD72','\uD83D\uDE0A','\uD83D\uDE07','\uD83D\uDE42','\uD83D\uDE43','\uD83D\uDE09','\uD83D\uDE0C','\uD83D\uDE0D','\uD83E\uDD70','\uD83D\uDE18','\uD83D\uDE17','\uD83D\uDE1A','\uD83D\uDE0B','\uD83D\uDE1B','\uD83D\uDE1D','\uD83D\uDE1C','\uD83E\uDD2A','\uD83E\uDD28','\uD83E\uDDD0','\uD83E\uDD13','\uD83D\uDE0E','\uD83E\uDD73','\uD83E\uDD29','\uD83D\uDE0F','\uD83D\uDE12','\uD83D\uDE1E','\uD83D\uDE14','\uD83D\uDE1F','\uD83D\uDE15','\uD83D\uDE41','\u2639\uFE0F','\uD83D\uDE23','\uD83D\uDE16','\uD83D\uDE2B','\uD83D\uDE29','\uD83E\uDD7A','\uD83D\uDE22','\uD83D\uDE2D','\uD83D\uDE24','\uD83D\uDE20','\uD83D\uDE21','\uD83E\uDD2C','\uD83E\uDD2F','\uD83D\uDE33','\uD83E\uDD75','\uD83E\uDD76','\uD83D\uDE31','\uD83D\uDE28','\uD83D\uDE30','\uD83D\uDE25','\uD83D\uDE13','\uD83E\uDD17','\uD83E\uDD14','\uD83E\uDD2D','\uD83E\uDD2B','\uD83E\uDD25','\uD83D\uDE36','\uD83E\uDEE0','\uD83D\uDE10','\uD83D\uDE11','\uD83D\uDE2C','\uD83E\uDD10','\uD83E\uDD74','\uD83D\uDE35','\uD83E\uDD24','\uD83D\uDE2A','\uD83D\uDE34','\uD83E\uDD71','\uD83E\uDD22','\uD83E\uDD2E','\uD83E\uDD27','\uD83D\uDE37','\uD83E\uDD12','\uD83E\uDD15','\uD83E\uDD11','\uD83E\uDD20'] },
        { icon: '\uD83D\uDC4B', label: 'people', emojis: ['\uD83D\uDC4B','\uD83E\uDD1A','\uD83D\uDD90\uFE0F','\u270B','\uD83E\uDD96','\uD83D\uDC4C','\u270C\uFE0F','\uD83E\uDD1E','\uD83E\uDD1F','\uD83E\uDD18','\uD83E\uDD19','\uD83D\uDC48','\uD83D\uDC49','\uD83D\uDC46','\uD83D\uDD95','\uD83D\uDC47','\u261D\uFE0F','\u270A','\uD83D\uDC4A','\uD83E\uDD1B','\uD83E\uDD1C','\uD83D\uDC4F','\uD83D\uDE4C','\uD83E\uDEB6','\uD83E\uDD32','\uD83E\uDD1D','\uD83D\uDE4F','\u270D\uFE0F','\uD83D\uDCAA','\uD83D\uDC4D','\uD83D\uDC4E','\u270B','\uD83D\uDC40','\uD83D\uDC44','\uD83D\uDC43','\uD83D\uDC42','\uD83D\uDC83','\uD83D\uDD7A','\uD83E\uDDD1','\uD83D\uDC68','\uD83D\uDC69','\uD83D\uDC76','\uD83D\uDC74','\uD83D\uDC75','\uD83D\uDC71','\uD83D\uDC7C','\uD83E\uDD35','\uD83D\uDC78','\uD83E\uDD34'] },
        { icon: '\u2764\uFE0F', label: 'hearts', emojis: ['\u2764\uFE0F','\uD83E\uDDE1','\uD83D\uDC9B','\uD83D\uDC9A','\uD83D\uDC99','\uD83D\uDC9C','\uD83E\uDD0D','\uD83E\uDD0E','\uD83D\uDDA4','\u2764\uFE0F\u200D\uD83D\uDD25','\uD83D\uDC95','\uD83D\uDC9E','\uD83D\uDC93','\uD83D\uDC97','\uD83D\uDC96','\uD83D\uDC98','\uD83D\uDC9D','\uD83D\uDC9F','\uD83D\uDC94','\uD83D\uDC8B','\uD83D\uDC8C','\uD83D\uDCAF','\u2728','\u2B50','\uD83C\uDF1F','\uD83D\uDCAB','\u26A1','\uD83D\uDD25','\uD83C\uDF08','\uD83C\uDF89','\uD83C\uDF8A','\uD83C\uDF88','\uD83C\uDF81','\uD83E\uDD73','\uD83C\uDFC6','\uD83C\uDFAF','\uD83C\uDF40','\uD83C\uDF38','\uD83C\uDF3A','\uD83C\uDF3B','\uD83C\uDF39','\uD83C\uDF37','\uD83C\uDF3C','\uD83D\uDC90','\uD83C\uDF1D','\uD83C\uDF1E','\uD83C\uDF19'] },
        { icon: '\uD83D\uDC36', label: 'animals', emojis: ['\uD83D\uDC36','\uD83D\uDC31','\uD83D\uDC2D','\uD83D\uDC39','\uD83D\uDC30','\uD83E\uDD8A','\uD83D\uDC3B','\uD83D\uDC3C','\uD83D\uDC28','\uD83D\uDC2F','\uD83E\uDD81','\uD83D\uDC2E','\uD83D\uDC37','\uD83D\uDC38','\uD83D\uDC35','\uD83D\uDE48','\uD83D\uDE49','\uD83D\uDE4A','\uD83D\uDC14','\uD83D\uDC27','\uD83D\uDC26','\uD83E\uDD86','\uD83E\uDD85','\uD83E\uDD89','\uD83E\uDD87','\uD83D\uDC3A','\uD83D\uDC34','\uD83E\uDD84','\uD83D\uDC1D','\uD83E\uDD8B','\uD83D\uDC0C','\uD83D\uDC1E','\uD83D\uDC1C','\uD83D\uDC22','\uD83E\uDD8E','\uD83D\uDC0D','\uD83E\uDD95','\uD83D\uDC0A','\uD83E\uDD92','\uD83D\uDC18','\uD83E\uDD9C','\uD83E\uDD8D','\uD83D\uDC2C','\uD83D\uDC33','\uD83D\uDC1F','\uD83D\uDC20','\uD83D\uDC19','\uD83D\uDC99'] },
        { icon: '\uD83C\uDF55', label: 'food', emojis: ['\uD83C\uDF4E','\uD83C\uDF4A','\uD83C\uDF4B','\uD83C\uDF47','\uD83C\uDF53','\uD83C\uDF52','\uD83C\uDF51','\uD83E\uDED0','\uD83C\uDF4D','\uD83E\uDD6D','\uD83C\uDF4C','\uD83E\uDD5D','\uD83C\uDF45','\uD83E\uDD65','\uD83E\uDD51','\uD83C\uDF46','\uD83E\uDD66','\uD83E\uDD6C','\uD83C\uDF3D','\uD83E\uDD55','\uD83E\uDDC4','\uD83E\uDD54','\uD83C\uDF5E','\uD83E\uDD50','\uD83C\uDF55','\uD83D\uDC2D','\uD83C\uDF73','\uD83E\uDDC7','\uD83E\uDD53','\uD83E\uDD69','\uD83C\uDF57','\uD83C\uDF56','\uD83C\uDF2D','\uD83C\uDF54','\uD83C\uDF5F','\uD83E\uDD6A','\uD83E\uDD57','\uD83C\uDF5C','\uD83C\uDF63','\uD83C\uDF71','\uD83E\uDD9E','\uD83E\uDD90','\uD83C\uDF70','\uD83C\uDF61','\uD83E\uDD9F','\uD83C\uDF7F','\u2615','\uD83C\uDF75','\uD83E\uDDB8','\uD83C\uDF7A','\uD83E\uDD42','\uD83C\uDF77','\uD83C\uDF89','\uD83C\uDF82','\uD83E\uDDC1','\uD83C\uDF69','\uD83C\uDF6A','\uD83C\uDF6B','\uD83C\uDF6C','\uD83C\uDF6D'] },
        { icon: '\uD83C\uDFAE', label: 'misc', emojis: ['\uD83C\uDFAE','\uD83C\uDFB2','\uD83E\uDD84','\uD83C\uDFB3','\uD83C\uDFA8','\uD83C\uDFAC','\uD83C\uDFA4','\uD83C\uDFA7','\uD83C\uDFB5','\uD83C\uDFB6','\uD83C\uDFB8','\uD83E\uDD41','\uD83C\uDFBA','\uD83C\uDFBB','\uD83C\uDFB7','\u26BD','\uD83C\uDFC0','\uD83C\uDFC8','\u26BE','\uD83C\uDFBE','\uD83C\uDFD0','\uD83C\uDFC9','\uD83C\uDFB1','\uD83C\uDFD3','\uD83C\uDFF8','\uD83E\uDD4A','\uD83C\uDFBF','\uD83C\uDFC6','\uD83E\uDD47','\uD83E\uDD48','\uD83E\uDD49','\uD83D\uDE97','\u2708\uFE0F','\uD83D\uDE80','\uD83D\uDEF8','\uD83C\uDF0D','\uD83C\uDF0A','\uD83C\uDFDD\uFE0F','\uD83C\uDFD6\uFE0F','\uD83C\uDFD4\uFE0F','\uD83C\uDF0B','\uD83C\uDFDB\uFE0F','\uD83C\uDFF0','\u26EA','\uD83D\uDDFA\uFE0F','\uD83C\uDDEC\uD83C\uDDE7','\uD83D\uDCF1','\uD83D\uDCBB','\u231A','\uD83D\uDCE6','\uD83D\uDCA1','\uD83D\uDCB0','\uD83C\uDF81'] },
    ];

    var RECENT_KEY = 'mm_recent_emoji';
    var MAX_RECENT = 32;

    function getRecent() {
        try { return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]'); }
        catch (e) { return []; }
    }

    function addRecent(emoji) {
        var recent = getRecent().filter(function (e) { return e !== emoji; });
        recent.unshift(emoji);
        if (recent.length > MAX_RECENT) recent = recent.slice(0, MAX_RECENT);
        try { localStorage.setItem(RECENT_KEY, JSON.stringify(recent)); } catch (e) {}
    }

    var emojiPanel = null;
    var emojiPendingMsgId = null;
    var emojiActiveCat = 0;

    function buildEmojiPanel() {
        var panel = document.createElement('div');
        panel.id = 'emoji-picker-panel';
        panel.className = 'emoji-picker-panel';
        var catHtml = EMOJI_CATS.map(function (c, i) {
            return '<button class="epk-cat-btn' + (i === 0 ? ' active' : '') + '" data-cat="' + i + '" title="' + c.label + '">' + c.icon + '</button>';
        }).join('');
        panel.innerHTML =
            '<div class="epk-search-wrap"><input class="epk-search" type="text" placeholder="Search\u2026" autocomplete="off" spellcheck="false"></div>'
            + '<div class="epk-cats">' + catHtml + '<button class="epk-cat-btn" data-cat="recent" title="recent">\uD83D\uDD50</button></div>'
            + '<div class="epk-grid" id="epk-grid"></div>';
        document.body.appendChild(panel);
        panel.querySelector('.epk-search').addEventListener('input', function () {
            renderEmojiGrid(this.value.trim());
        });
        panel.addEventListener('click', function (e) {
            e.stopPropagation();
            var catBtn = e.target.closest('.epk-cat-btn');
            if (catBtn) {
                panel.querySelectorAll('.epk-cat-btn').forEach(function (b) { b.classList.remove('active'); });
                catBtn.classList.add('active');
                var cat = catBtn.dataset.cat;
                emojiActiveCat = cat === 'recent' ? 'recent' : parseInt(cat, 10);
                panel.querySelector('.epk-search').value = '';
                renderEmojiGrid('');
                return;
            }
            var emojiBtn = e.target.closest('.epk-emoji');
            if (emojiBtn) {
                var emoji = emojiBtn.dataset.emoji;
                if (emojiPendingMsgId !== null) {
                    addRecent(emoji);
                    sendReaction(emojiPendingMsgId, emoji);
                }
                closeEmojiPanel();
            }
        });
        document.addEventListener('click', function (e) {
            if (emojiPanel && emojiPanel.classList.contains('open') && !emojiPanel.contains(e.target) && !e.target.closest('.bact-react')) {
                closeEmojiPanel();
            }
        });
        return panel;
    }

    function renderEmojiGrid(query) {
        var grid = document.getElementById('epk-grid');
        if (!grid) return;
        var emojis;
        if (query) {
            var all = [];
            EMOJI_CATS.forEach(function (c) { c.emojis.forEach(function (e) { if (all.indexOf(e) === -1) all.push(e); }); });
            var q = query.toLowerCase();
            emojis = all.filter(function (e) { return e.toLowerCase().indexOf(q) !== -1; });
            if (!emojis.length) emojis = all;
        } else if (emojiActiveCat === 'recent') {
            emojis = getRecent();
        } else {
            emojis = EMOJI_CATS[emojiActiveCat].emojis;
        }
        grid.innerHTML = emojis.length
            ? emojis.map(function (e) { return '<button class="epk-emoji" data-emoji="' + e + '">' + e + '</button>'; }).join('')
            : '<span class="epk-empty">No emoji found</span>';
    }

    function openEmojiPanel(triggerEl, msgId) {
        if (!emojiPanel) emojiPanel = buildEmojiPanel();
        emojiPendingMsgId = msgId;
        emojiActiveCat = 0;
        emojiPanel.querySelector('.epk-search').value = '';
        emojiPanel.querySelectorAll('.epk-cat-btn').forEach(function (b) {
            b.classList.toggle('active', b.dataset.cat === '0');
        });
        renderEmojiGrid('');
        emojiPanel.classList.add('open');
        var rect = triggerEl.getBoundingClientRect();
        var pw = 260;
        var ph = 280;
        var left = rect.left + window.scrollX;
        var top  = rect.top + window.scrollY - ph - 8;
        if (left + pw > window.innerWidth - 8) left = window.innerWidth - pw - 8;
        if (top < window.scrollY + 8) top = rect.bottom + window.scrollY + 8;
        emojiPanel.style.left = left + 'px';
        emojiPanel.style.top  = top + 'px';
    }

    function closeEmojiPanel() {
        if (emojiPanel) {
            emojiPanel.classList.remove('open');
            emojiPendingMsgId = null;
        }
    }

    function buildActionsHtml(msgId, isMine) {
        var del = isMine
            ? '<button class="bact-btn bact-delete" data-msgid="' + msgId + '" title="Delete"><i class="bi bi-trash3"></i></button>'
            : '';
        return '<div class="bubble-actions">'
            + '<button class="bact-btn bact-react" title="React"><i class="bi bi-emoji-smile"></i></button>'
            + del
            + '</div>';
    }

    box.addEventListener('click', function (e) {
        var reactBtn = e.target.closest('.bact-react');
        if (reactBtn) {
            e.stopPropagation();
            var wrap = reactBtn.closest('.bubble-wrap');
            var msgId = parseInt(wrap.getAttribute('data-id'), 10);
            if (emojiPanel && emojiPanel.classList.contains('open') && emojiPendingMsgId === msgId) {
                closeEmojiPanel();
            } else {
                openEmojiPanel(reactBtn, msgId);
            }
            return;
        }

        var delBtn = e.target.closest('.bact-delete');
        if (delBtn) {
            openDeleteMsgModal(parseInt(delBtn.dataset.msgid, 10));
            return;
        }

        var chip = e.target.closest('.reaction-chip');
        if (chip) {
            sendReaction(parseInt(chip.dataset.msgid, 10), chip.dataset.emoji);
            return;
        }
    });

    function sendReaction(msgId, emoji) {
        var url = REACT_URL + msgId + '/react/';
        fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': CSRF, 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'emoji=' + encodeURIComponent(emoji),
        })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.ok) updateReactionChips(msgId, d.reactions);
            })
            .catch(function () {});
    }

    function updateReactionChips(msgId, reactions) {
        var reactionDiv = document.querySelector('.bubble-reactions[data-msgid="' + msgId + '"]');
        if (!reactionDiv) return;
        reactionDiv.innerHTML = '';
        (reactions || []).forEach(function (r) {
            var btn = document.createElement('button');
            btn.className = 'reaction-chip' + (r.mine ? ' mine' : '');
            btn.dataset.msgid = msgId;
            btn.dataset.emoji = r.emoji;
            btn.innerHTML = '<span class="r-emoji">' + r.emoji + '</span><span class="r-count">' + r.count + '</span>';
            reactionDiv.appendChild(btn);
        });
    }

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
                    var reactionDiv = tmpEl.querySelector('.bubble-reactions');
                    if (reactionDiv) reactionDiv.dataset.msgid = d.id;
                    var bubbleRow = tmpEl.querySelector('.bubble-row');
                    if (bubbleRow && !tmpEl.querySelector('.bubble-actions')) {
                        var tmp = document.createElement('div');
                        tmp.innerHTML = buildActionsHtml(d.id, true);
                        bubbleRow.appendChild(tmp.firstChild);
                    } else {
                        var existDel = tmpEl.querySelector('.bact-delete');
                        if (existDel) existDel.dataset.msgid = d.id;
                    }
                }
            })
            .catch(function () {});
    }

    function esc(s) {
        return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function appendBubble(m) {
        var es = document.getElementById('emptyState');
        if (es) es.remove();

        var wrap = document.createElement('div');
        wrap.className = 'bubble-wrap ' + (m.is_mine ? 'mine' : 'theirs');
        wrap.setAttribute('data-id', m.id);

        var avatar = m.is_mine ? '' : (OTHER_AVATAR_URL
            ? '<img src="' + OTHER_AVATAR_URL + '" class="avatar-sm flex-shrink-0" style="object-fit:cover;" alt="">'
            : '<div class="avatar-sm flex-shrink-0">' + esc(m.initials) + '</div>');

        var bubbleContent;
        var bubbleClass = 'bubble ' + (m.is_mine ? 'mine' : 'theirs');
        if (m.is_deleted) {
            bubbleClass += ' bubble--deleted';
            var notice = m.deleted_by_staff ? 'Message deleted by staff' : 'Message deleted';
            bubbleContent = '<span class="bubble__deleted-notice"><i class="bi bi-slash-circle"></i> ' + notice + '</span>';
        } else {
            var gifHtml  = m.gif_url ? '<img src="' + m.gif_url + '" class="attach gif-attach" alt="GIF">' : '';
            var bodyHtml = (!m.gif_url && m.body) ? esc(m.body) : '';
            var imgHtml  = (!m.gif_url && m.attachment_url) ? '<img src="' + m.attachment_url + '" class="attach" alt="attachment">' : '';
            bubbleContent = gifHtml + bodyHtml + imgHtml;
        }
        var tick = m.is_mine
            ? '<i class="bi bi-check2 tick-icon" style="color:#adb5bd;"></i>'
            : '';

        var isTmp = typeof m.id === 'string' && m.id.indexOf('tmp_') === 0;
        var actionsHtml = (!m.is_deleted && !isTmp) ? buildActionsHtml(m.id, m.is_mine) : '';
        var reactionsId = isTmp ? 'tmp' : m.id;

        wrap.innerHTML = avatar +
            '<div class="bubble-col">' +
                '<div class="bubble-row">' +
                    '<div class="' + bubbleClass + '">' + bubbleContent + '</div>' +
                    actionsHtml +
                '</div>' +
                '<div class="bubble-reactions" data-msgid="' + reactionsId + '"></div>' +
                '<div class="bubble-time">' + m.time + tick + '</div>' +
            '</div>';

        box.insertBefore(wrap, typingBubble);

        if (typeof m.id === 'number' && m.id > lastId) lastId = m.id;
    }

    function applyDeleted(id, byStaff) {
        var el = document.querySelector('.bubble-wrap[data-id="' + id + '"]');
        if (!el) return;
        var bubble = el.querySelector('.bubble');
        if (!bubble || bubble.classList.contains('bubble--deleted')) return;
        bubble.classList.add('bubble--deleted');
        var notice = byStaff ? 'Message deleted by staff' : 'Message deleted';
        bubble.innerHTML = '<span class="bubble__deleted-notice"><i class="bi bi-slash-circle"></i> ' + notice + '</span>';
        var actions = el.querySelector('.bubble-actions');
        if (actions) actions.remove();
        var reactionDiv = el.querySelector('.bubble-reactions');
        if (reactionDiv) reactionDiv.innerHTML = '';
    }

    function poll() {
        fetch(POLL_URL + '?after=' + lastId + '&react_v=' + reactV, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
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

                if (d.deleted_ids && d.deleted_ids.length) {
                    d.deleted_ids.forEach(function (id) {
                        applyDeleted(id, true);
                    });
                }

                if (d.reaction_updates && d.reaction_updates.length) {
                    d.reaction_updates.forEach(function (ru) {
                        updateReactionChips(ru.id, ru.reactions);
                    });
                }

                if (typeof d.react_v === 'number') reactV = d.react_v;

                if (d.typing) {
                    typingBubble.classList.remove('d-none');
                    if (typingStatus) typingStatus.textContent = 'typing\u2026';
                    var os = document.getElementById('onlineStatus');
                    if (os) os.style.display = 'none';
                    scrollBottom(false);
                } else {
                    typingBubble.classList.add('d-none');
                    if (typingStatus) typingStatus.textContent = '';
                    var os2 = document.getElementById('onlineStatus');
                    if (os2) os2.style.display = '';
                }

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

    if ('ontouchstart' in window) {
        var tapStartY = 0;
        box.addEventListener('touchstart', function (e) {
            tapStartY = e.touches[0].clientY;
        }, { passive: true });

        box.addEventListener('touchend', function (e) {
            if (Math.abs(e.changedTouches[0].clientY - tapStartY) > 10) return;
            if (e.target.closest('.bact-btn, .bubble-actions, .emoji-picker-panel')) return;
            var wrap = e.target.closest('.bubble-wrap');
            document.querySelectorAll('.bubble-wrap.active-actions').forEach(function (el) {
                el.classList.remove('active-actions');
            });
            if (!wrap) return;
            var bubble = wrap.querySelector('.bubble');
            if (!bubble) return;
            var touch = e.changedTouches[0];
            var rect = bubble.getBoundingClientRect();
            if (touch.clientX < rect.left || touch.clientX > rect.right ||
                touch.clientY < rect.top  || touch.clientY > rect.bottom) return;
            wrap.classList.add('active-actions');
        }, { passive: true });
    }

    var pendingDeleteId = null;

    function openDeleteMsgModal(msgId) {
        pendingDeleteId = msgId;
        var modal = document.getElementById('deleteMsgModal');
        if (!modal) return;
        new bootstrap.Modal(modal).show();
    }
    window.openDeleteMsgModal = openDeleteMsgModal;

    var confirmBtn = document.getElementById('deleteMsgConfirm');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function () {
            if (!pendingDeleteId) return;
            var modalEl = document.getElementById('deleteMsgModal');
            var bsModal = bootstrap.Modal.getInstance(modalEl);
            if (bsModal) bsModal.hide();
            var msgId = pendingDeleteId;
            pendingDeleteId = null;

            var url = '/inbox/' + OTHER_PK + '/message/' + msgId + '/delete/';
            fetch(url, { method: 'POST', headers: { 'X-CSRFToken': CSRF } })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (d.ok) applyDeleted(msgId, false);
                })
                .catch(function () {});
        });
    }

    if (typeof INITIAL_REACTIONS !== 'undefined') {
        Object.keys(INITIAL_REACTIONS).forEach(function (msgId) {
            updateReactionChips(parseInt(msgId, 10), INITIAL_REACTIONS[msgId]);
        });
    }

    var outer = document.querySelector('.chat-outer');
    var swatches = document.querySelectorAll('.theme-swatch');
    var THEME_KEY = 'mm_chat_theme';

    function applyTheme(theme) {
        if (!outer) return;
        outer.classList.remove('theme-ocean', 'theme-rose', 'theme-dark');
        if (theme) outer.classList.add(theme);
        swatches.forEach(function (s) {
            s.classList.toggle('active', s.dataset.theme === theme);
        });
    }

    applyTheme(localStorage.getItem(THEME_KEY) || '');

    swatches.forEach(function (s) {
        s.addEventListener('click', function () {
            var t = s.dataset.theme;
            applyTheme(t);
            localStorage.setItem(THEME_KEY, t);
        });
    });

    var ptrEl = document.getElementById('ptrIndicator');
    var chatCard = document.querySelector('.chat-card');
    var ptrStartY = 0;
    var ptrDy = 0;
    var ptrActive = false;
    var PTR_THRESHOLD = 70;

    if (ptrEl && chatCard) {
        chatCard.addEventListener('touchstart', function (e) {
            ptrStartY = e.touches[0].clientY;
            ptrDy = 0;
            ptrActive = box.scrollTop < 2;
        }, { passive: true });

        chatCard.addEventListener('touchmove', function (e) {
            if (!ptrActive) return;
            ptrDy = e.touches[0].clientY - ptrStartY;
            if (ptrDy <= 0) return;
            var h = Math.min(ptrDy * 0.45, 56);
            ptrEl.style.transition = 'none';
            ptrEl.style.height = h + 'px';
            if (ptrDy >= PTR_THRESHOLD) {
                ptrEl.classList.add('ptr-ready');
                ptrEl.innerHTML = '<i class="bi bi-arrow-up-circle"></i> Release to refresh';
            } else {
                ptrEl.classList.remove('ptr-ready');
                ptrEl.innerHTML = '<i class="bi bi-arrow-down-circle"></i> Pull to refresh';
            }
        }, { passive: true });

        chatCard.addEventListener('touchend', function () {
            if (!ptrActive) return;
            ptrActive = false;
            ptrEl.style.transition = '';
            if (ptrDy >= PTR_THRESHOLD) {
                ptrEl.classList.remove('ptr-ready');
                ptrEl.style.height = '48px';
                ptrEl.innerHTML = '<span class="ptr-spin"><i class="bi bi-arrow-repeat"></i></span> Refreshing…';
                setTimeout(function () { window.location.reload(); }, 500);
            } else {
                ptrEl.style.height = '0';
                ptrEl.classList.remove('ptr-ready');
                setTimeout(function () { ptrEl.innerHTML = ''; }, 220);
            }
            ptrDy = 0;
        }, { passive: true });

        chatCard.addEventListener('touchcancel', function () {
            ptrActive = false;
            ptrDy = 0;
            ptrEl.style.transition = '';
            ptrEl.style.height = '0';
            ptrEl.classList.remove('ptr-ready');
            setTimeout(function () { ptrEl.innerHTML = ''; }, 220);
        }, { passive: true });
    }

})();