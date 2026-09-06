document.addEventListener('DOMContentLoaded', function () {
    var header = document.getElementById('header');
    if (header) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 40) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        }, { passive: true });
    }

    var menuBtn = document.getElementById('menuToggle');
    var sidebarMenu = document.getElementById('sidebarMenu');
    var menuOverlay = document.getElementById('menuOverlay');

    if (menuBtn && sidebarMenu) {
        var currentPage = window.location.pathname.split('/').pop() || 'index.html';
        sidebarMenu.querySelectorAll('a').forEach(function (link) {
            var href = link.getAttribute('href');
            if (href === currentPage || (currentPage === '' && href === 'index.html')) {
                link.classList.add('active');
            }
        });

        function closeMenu() {
            sidebarMenu.classList.add('closing');
            menuBtn.classList.remove('open');
            document.body.style.overflow = '';
            if (menuOverlay) menuOverlay.classList.remove('visible');
            setTimeout(function () {
                sidebarMenu.classList.remove('visible');
                sidebarMenu.classList.remove('closing');
            }, 320);
        }

        menuBtn.addEventListener('click', function (e) {
            e.preventDefault();
            if (sidebarMenu.classList.contains('visible')) {
                closeMenu();
            } else {
                sidebarMenu.classList.remove('closing');
                sidebarMenu.classList.add('visible');
                menuBtn.classList.add('open');
                document.body.style.overflow = 'hidden';
                if (menuOverlay) menuOverlay.classList.add('visible');
            }
        });

        sidebarMenu.addEventListener('click', function () {
            closeMenu();
        });

        if (menuOverlay) {
            menuOverlay.addEventListener('click', function () {
                closeMenu();
            });
        }
    }

    document.body.classList.remove('is-preload');

    // Scroll reveal
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        const revealSelectors = [
            '.project',
            '.cs-card',
            '.case-section',
            '.platform-card',
            '.about-section',
            '.timeline-card',
            '.belief-card',
            '.resume-section > li',
            '.appstore-app',
            '.contrib-item'
        ].join(', ');

        const revealEls = document.querySelectorAll(revealSelectors);

        revealEls.forEach(function (el, i) {
            const rect = el.getBoundingClientRect();
            if (rect.top < window.innerHeight && rect.bottom > 0) return;
            el.classList.add('sr-hidden');
            // Stagger siblings in the same parent
            const siblings = el.parentElement.querySelectorAll(':scope > .sr-hidden');
            const idx = Array.from(siblings).indexOf(el);
            el.style.transitionDelay = (idx * 0.07) + 's';
        });

        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('sr-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -20px 0px' });

        revealEls.forEach(function (el) { observer.observe(el); });
    }

    // Drag-to-scroll for horizontal galleries (fixes Windows mouse-only users)
    document.querySelectorAll('.screenshot-scroll-track, .sb-scroll-track').forEach(function (track) {
        var isDown = false;
        var startX, startLeft;

        track.addEventListener('mousedown', function (e) {
            isDown = true;
            startX = e.pageX;
            startLeft = track.scrollLeft;
            track.style.cursor = 'grabbing';
            track.style.userSelect = 'none';
        });

        document.addEventListener('mouseup', function () {
            if (!isDown) return;
            isDown = false;
            track.style.cursor = '';
            track.style.userSelect = '';
        });

        document.addEventListener('mousemove', function (e) {
            if (!isDown) return;
            e.preventDefault();
            track.scrollLeft = startLeft - (e.pageX - startX);
        });

        // Restore default cursor if mouse leaves window while dragging
        document.addEventListener('mouseleave', function () {
            if (!isDown) return;
            isDown = false;
            track.style.cursor = '';
            track.style.userSelect = '';
        });
    });
});

// Restore page visibility when navigating back (bfcache restores page-leaving/is-preload state)
window.addEventListener('pageshow', function (e) {
    if (e.persisted) {
        document.body.classList.remove('is-preload', 'page-leaving');
    }
});

// Page transitions
document.querySelectorAll('a[href]').forEach(function (link) {
    var href = link.getAttribute('href');
    if (!href || href.startsWith('http') || href.startsWith('#') || href.startsWith('mailto') || href.startsWith('tel:') || href.startsWith('javascript') || link.hasAttribute('download') || link.getAttribute('target') === '_blank') return;
    link.addEventListener('click', function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        var dest = href;
        document.body.classList.add('page-leaving');
        setTimeout(function () { window.location.href = dest; }, 210);
    });
});

// Screenshot lightbox
function openLightbox(el) {
    var img = el.querySelector('img');
    if (!img) return;

    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.88);display:flex;align-items:center;justify-content:center;padding:24px;cursor:zoom-out;';

    var image = document.createElement('img');
    image.src = img.src;
    image.alt = img.alt;
    image.style.cssText = 'max-width:100%;max-height:100%;border-radius:8px;box-shadow:0 8px 48px rgba(0,0,0,0.5);';

    overlay.appendChild(image);
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';

    function close() {
        document.body.removeChild(overlay);
        document.body.style.overflow = '';
        document.removeEventListener('keydown', onKey);
    }

    function onKey(e) { if (e.key === 'Escape') close(); }

    overlay.addEventListener('click', close);
    document.addEventListener('keydown', onKey);
}


// Ambient texture circles — fixed, subtle, breathing pulse
// Skip on case study pages and mobile
(function () {
    if (document.querySelector('.case-hero')) return;
    if (window.innerWidth < 768) return;

    // y values are % of full page height — bubbles spread as you scroll
    var bubbles = [
        // left side
        { x: -2, y:  3,  size: 140, dur: 8.0, delay: 0.0 },
        { x:  6, y: 11,  size:  38, dur: 9.5, delay: 1.4 },
        { x:  1, y: 20,  size: 110, dur: 7.2, delay: 3.1 },
        { x:  7, y: 30,  size:  28, dur: 8.8, delay: 0.7 },
        { x:  0, y: 40,  size: 160, dur: 6.8, delay: 2.3 },
        { x:  5, y: 51,  size:  52, dur: 9.2, delay: 4.0 },
        { x:  2, y: 62,  size:  90, dur: 7.5, delay: 1.8 },
        { x:  7, y: 73,  size:  35, dur: 8.3, delay: 0.5 },
        { x:  0, y: 83,  size: 120, dur: 6.9, delay: 3.2 },
        { x:  5, y: 93,  size:  48, dur: 9.0, delay: 2.0 },
        // right side
        { x: 95, y:  7,  size:  45, dur: 7.6, delay: 1.9 },
        { x: 91, y: 16,  size: 130, dur: 8.4, delay: 0.3 },
        { x: 97, y: 26,  size:  32, dur: 9.0, delay: 2.8 },
        { x: 90, y: 36,  size: 105, dur: 7.0, delay: 1.1 },
        { x: 96, y: 46,  size:  60, dur: 8.2, delay: 3.6 },
        { x: 92, y: 57,  size: 145, dur: 6.5, delay: 0.9 },
        { x: 95, y: 67,  size:  40, dur: 9.3, delay: 2.5 },
        { x: 91, y: 77,  size: 100, dur: 7.8, delay: 0.2 },
        { x: 97, y: 87,  size:  55, dur: 8.7, delay: 3.8 },
        { x: 93, y: 96,  size: 125, dur: 7.1, delay: 1.6 },
    ];

    var pageH = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, window.innerHeight);

    var container = document.createElement('div');
    container.className = 'bg-bubbles';
    container.style.height = pageH + 'px';

    bubbles.forEach(function (b) {
        var el = document.createElement('div');
        el.className = 'bg-bubble';
        el.style.left            = b.x + '%';
        el.style.top             = Math.round(b.y * pageH / 100) + 'px';
        el.style.width           = b.size + 'px';
        el.style.height          = b.size + 'px';
        el.style.animationDuration = b.dur + 's';
        el.style.animationDelay    = b.delay + 's';
        container.appendChild(el);
    });

    document.body.insertBefore(container, document.body.firstChild);
}());
