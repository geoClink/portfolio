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
