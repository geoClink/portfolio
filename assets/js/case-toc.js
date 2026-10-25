// Case study "On this page" list: highlight the section being read (wide screens, where the list is fixed in the gutter)
(function () {
    const links = [...document.querySelectorAll('.case-toc a')];
    if (!links.length || !('IntersectionObserver' in window) || !window.matchMedia('(min-width: 1400px)').matches) return;
    const targets = links.map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
    const io = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (!e.isIntersecting) return;
            links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + e.target.id));
        });
    }, { rootMargin: '-30% 0px -60% 0px' });
    targets.forEach(t => io.observe(t));
})();
