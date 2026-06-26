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
            sidebarMenu.classList.remove('visible');
            menuBtn.classList.remove('open');
            document.body.style.overflow = '';
        }

        menuBtn.addEventListener('click', function (e) {
            e.preventDefault();
            var isOpen = sidebarMenu.classList.toggle('visible');
            menuBtn.classList.toggle('open');
            document.body.style.overflow = isOpen ? 'hidden' : '';
        });

        sidebarMenu.addEventListener('click', function () {
            closeMenu();
        });
    }

    document.body.classList.remove('is-preload');
});
