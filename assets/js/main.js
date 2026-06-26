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
            }
        });

        sidebarMenu.addEventListener('click', function () {
            closeMenu();
        });
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
