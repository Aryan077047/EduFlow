/* ==== extracted from template header.html ==== */

(function () {
    'use strict';

    var themeBtn = document.getElementById('themeToggle');
    var themeIcon = document.getElementById('themeIcon');
    var html = document.documentElement;

    function updateThemeIcon() {
        if (!themeIcon) return;
        themeIcon.className = html.getAttribute('data-theme') === 'dark'
            ? 'fa fa-sun'
            : 'fa fa-moon';
    }
    updateThemeIcon();

    if (themeBtn) {
        themeBtn.addEventListener('click', function () {
            var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            try { localStorage.setItem('theme', next); } catch (e) {}
            updateThemeIcon();
        });
    }

    var profileBtn = document.getElementById('profileBtn');
    var profileMenu = document.getElementById('profileMenu');
    if (profileBtn && profileMenu) {
        profileBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            profileMenu.classList.toggle('active');
        });
        document.addEventListener('click', function (e) {
            if (!profileBtn.contains(e.target) && !profileMenu.contains(e.target)) {
                profileMenu.classList.remove('active');
            }
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') profileMenu.classList.remove('active');
        });
    }

    initNotifications();

    var header = document.querySelector('.main-header');
    if (header) {
        var onScroll = function () {
            header.classList.toggle('scrolled', window.scrollY > 50);
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            var s = document.getElementById('globalSearch');
            if (s) s.focus();
        }
    });
})();

function initNotifications() {
    'use strict';

    var wrap = document.getElementById('notifDropdown');
    if (!wrap) return;

    var btn = document.getElementById('notifBtn');
    var panel = document.getElementById('notifPanel');
    var list = document.getElementById('notifList');
    var countEl = document.getElementById('notifCount');
    var readAllBtn = document.getElementById('notifReadAll');
    var profileMenu = document.getElementById('profileMenu');
    var text = list.dataset;

    function csrfToken() {
        var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    function request(url, method) {
        return fetch(url, {
            method: method || 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken()
            }
        }).then(function (response) {
            if (!response.ok) throw new Error(response.status);
            return response.json();
        });
    }

    function setCount(n) {
        n = Math.max(0, parseInt(n, 10) || 0);
        countEl.textContent = n > 99 ? '99+' : String(n);
        countEl.hidden = n === 0;
        readAllBtn.disabled = n === 0;
    }

    function timeAgo(iso) {
        var date = new Date(iso);
        var seconds = Math.round((date.getTime() - Date.now()) / 1000);
        var units = [['year', 31536000], ['month', 2592000], ['week', 604800],
                     ['day', 86400], ['hour', 3600], ['minute', 60]];
        try {
            var rtf = new Intl.RelativeTimeFormat(document.documentElement.lang || undefined, { numeric: 'auto' });
            for (var i = 0; i < units.length; i++) {
                if (Math.abs(seconds) >= units[i][1]) {
                    return rtf.format(Math.round(seconds / units[i][1]), units[i][0]);
                }
            }
            return rtf.format(0, 'second');
        } catch (e) {
            return date.toLocaleString();
        }
    }

    function message(icon, label) {
        list.innerHTML = '';
        var box = document.createElement('div');
        box.className = 'notif-empty';
        box.innerHTML = '<i class="fa ' + icon + '"></i>';
        var p = document.createElement('p');
        p.textContent = label;
        box.appendChild(p);
        list.appendChild(box);
    }

    function markItemRead(item) {
        item.classList.remove('unread');
        var mark = item.querySelector('.notif-mark');
        if (mark) mark.remove();
        var sr = item.querySelector('.notif-sr');
        if (sr) sr.remove();
    }

    function markRead(item) {
        if (!item.classList.contains('unread')) return Promise.resolve();
        return request(item.dataset.readUrl, 'POST').then(function (data) {
            markItemRead(item);
            setCount(data.unread_count);
        });
    }

    var ICONS = { info: 'fa-circle-info', success: 'fa-circle-check', warning: 'fa-triangle-exclamation', security: 'fa-shield-halved' };

    function render(items) {
        if (!items.length) {
            message('fa-bell-slash', text.emptyText);
            return;
        }
        list.innerHTML = '';
        items.forEach(function (n) {
            var item = document.createElement(n.link ? 'a' : 'div');
            item.className = 'notif-item kind-' + n.kind + (n.is_read ? '' : ' unread');
            item.dataset.readUrl = n.read_url;
            if (n.link) item.href = n.link;

            var icon = document.createElement('span');
            icon.className = 'notif-icon';
            icon.innerHTML = '<i class="fa ' + (ICONS[n.kind] || ICONS.info) + '"></i>';

            var body = document.createElement('div');
            body.className = 'notif-body';
            var msg = document.createElement('p');
            msg.className = 'notif-msg';
            msg.textContent = n.message;
            var time = document.createElement('time');
            time.dateTime = n.created_at;
            time.title = new Date(n.created_at).toLocaleString();
            time.textContent = timeAgo(n.created_at);
            body.appendChild(msg);
            body.appendChild(time);
            if (!n.is_read) {
                var sr = document.createElement('span');
                sr.className = 'notif-sr';
                sr.textContent = text.unreadText;
                body.appendChild(sr);
            }

            item.appendChild(icon);
            item.appendChild(body);

            if (!n.is_read) {
                var mark = document.createElement('button');
                mark.type = 'button';
                mark.className = 'notif-mark';
                mark.title = text.markReadText;
                mark.setAttribute('aria-label', text.markReadText);
                mark.innerHTML = '<i class="fa fa-check"></i>';
                mark.addEventListener('click', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    mark.disabled = true;
                    markRead(item).catch(function () { mark.disabled = false; });
                });
                item.appendChild(mark);
            }

            if (n.link) {
                item.addEventListener('click', function (e) {
                    if (!item.classList.contains('unread')) return;
                    e.preventDefault();
                    var go = function () { window.location.href = n.link; };
                    markRead(item).then(go, go);
                });
            }
            list.appendChild(item);
        });
    }

    function load() {
        message('fa-spinner fa-spin', text.loadingText);
        request(wrap.dataset.listUrl).then(function (data) {
            setCount(data.unread_count);
            render(data.notifications || []);
        }).catch(function () {
            message('fa-circle-exclamation', text.errorText);
        });
    }

    function setOpen(open) {
        panel.classList.toggle('active', open);
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (open) {
            if (profileMenu) profileMenu.classList.remove('active');
            load();
        }
    }

    btn.addEventListener('click', function (e) {
        e.stopPropagation();
        setOpen(!panel.classList.contains('active'));
    });
    document.addEventListener('click', function (e) {
        if (panel.classList.contains('active') && !wrap.contains(e.target)) setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && panel.classList.contains('active')) {
            setOpen(false);
            btn.focus();
        }
    });
    var profileBtn = document.getElementById('profileBtn');
    if (profileBtn) profileBtn.addEventListener('click', function () { setOpen(false); });

    readAllBtn.addEventListener('click', function () {
        readAllBtn.disabled = true;
        request(wrap.dataset.readAllUrl, 'POST').then(function () {
            list.querySelectorAll('.notif-item.unread').forEach(markItemRead);
            setCount(0);
        }).catch(function () {
            readAllBtn.disabled = false;
        });
    });
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}
