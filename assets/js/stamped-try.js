// "Try it" on the Stamped! landing pages: a live Apple Map of one city at a time, a Look Around
// preview of the landmark you pick, and a passport stamp when you stamp it. MapKit JS only loads
// when the section scrolls near; the token comes from stamped-cities/map-token.js. If MapKit can't
// load (another origin, an expired token, a blocker), the section stays hidden.
(function () {
    var section = document.querySelector('[data-stamped-try]');
    var dataEl = document.getElementById('try-data');
    var textEl = document.getElementById('try-strings');
    if (!section || !dataEl || !textEl || !window.STAMPED_MAPKIT_TOKEN) return;

    var cities = JSON.parse(dataEl.textContent);
    var t = JSON.parse(textEl.textContent);
    var mapEl = section.querySelector('.try-map');
    var chips = section.querySelector('.try-cities');
    var list = section.querySelector('.try-list');
    var panel = section.querySelector('.try-look');
    var status = section.querySelector('.try-status');
    var nameEl = section.querySelector('.try-name');
    var subEl = section.querySelector('.try-sub');
    var stampBtn = section.querySelector('.try-stamp-btn');
    var mapsLink = section.querySelector('.try-maps');
    var guideLink = section.querySelector('.try-guide');
    var progress = section.querySelector('.try-progress');
    var stampEl = section.querySelector('.try-stamp');
    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    var map = null;
    var preview = null;
    var city = null;
    var markers = [];
    var current = null;
    var stamped = load();

    function load() {
        try { return JSON.parse(localStorage.getItem('stamped-try') || '{}'); } catch (e) { return {}; }
    }
    function save() {
        try { localStorage.setItem('stamped-try', JSON.stringify(stamped)); } catch (e) { /* private mode */ }
    }
    function fill(template, values) {
        return template.replace(/\{(\w+)\}/g, function (_, key) { return values[key]; });
    }
    function fail() {
        section.hidden = true;   // No map is better than a broken one
    }

    function renderProgress() {
        var count = city.landmarks.filter(function (l) { return stamped[l.id]; }).length;
        progress.textContent = fill(t.progress, { n: count, total: city.landmarks.length, city: city.name });
    }

    function markerStyle(marker) {
        var done = !!stamped[marker.landmark.id];
        marker.color = done ? '#2F5D4A' : '#F2743F';
        marker.glyphText = done ? '✓' : String(marker.index + 1);
    }

    // fly: zoom in on the landmark, like tapping a pin in the app (only for the visitor's own taps)
    function select(index, fly) {
        current = markers[index];
        var landmark = current.landmark;
        list.querySelectorAll('button').forEach(function (b, i) {
            b.setAttribute('aria-current', i === index ? 'true' : 'false');
        });
        if (map.selectedAnnotation !== current) map.selectedAnnotation = current;
        if (fly) {
            map.setRegionAnimated(new mapkit.CoordinateRegion(current.coordinate, new mapkit.CoordinateSpan(0.012, 0.012)), !reduceMotion);
        }

        nameEl.textContent = landmark.name;
        subEl.textContent = landmark.subtitle;
        mapsLink.href = 'https://maps.apple.com/?ll=' + landmark.lat + ',' + landmark.lng + '&q=' + encodeURIComponent(landmark.name);
        updateStampButton();
        stampEl.classList.remove('is-down');

        if (preview) { preview.destroy(); preview = null; }
        panel.innerHTML = '';
        panel.classList.remove('is-empty');
        status.textContent = t.loading;
        preview = new mapkit.LookAroundPreview(panel, current.coordinate);
        preview.addEventListener('load', function () { status.textContent = t.hint; });
        preview.addEventListener('error', function () {
            panel.classList.add('is-empty');
            status.textContent = t.noImagery;
        });
    }

    function updateStampButton() {
        var done = !!stamped[current.landmark.id];
        stampBtn.textContent = done ? t.stamped : t.stamp;
        stampBtn.setAttribute('aria-pressed', done ? 'true' : 'false');
    }

    function stampIt() {
        var landmark = current.landmark;
        var done = !stamped[landmark.id];
        if (done) stamped[landmark.id] = true; else delete stamped[landmark.id];
        save();
        markerStyle(current);
        list.querySelectorAll('button')[current.index].classList.toggle('is-stamped', done);
        updateStampButton();
        renderProgress();
        stampEl.classList.remove('is-down');
        if (!done) return;
        stampEl.querySelector('.try-stamp-arc textPath').textContent = landmark.name.toUpperCase().slice(0, 26);
        stampEl.querySelector('.try-stamp-big').textContent = city.code;
        stampEl.querySelector('.try-stamp-small').textContent = String(new Date().getFullYear());
        void stampEl.offsetWidth;   // restart the animation
        stampEl.classList.add('is-down');
    }

    function showCity(slug, animate) {
        city = cities.filter(function (c) { return c.slug === slug; })[0];
        chips.querySelectorAll('button').forEach(function (b) {
            b.setAttribute('aria-pressed', b.dataset.city === slug ? 'true' : 'false');
        });
        guideLink.href = 'stamped-cities/' + city.slug + '.html';
        guideLink.textContent = fill(t.guide, { city: city.name });

        if (markers.length) map.removeAnnotations(markers);
        markers = city.landmarks.map(function (landmark, index) {
            var marker = new mapkit.MarkerAnnotation(new mapkit.Coordinate(landmark.lat, landmark.lng), {
                title: landmark.name,
                subtitle: landmark.subtitle
            });
            marker.landmark = landmark;
            marker.index = index;
            markerStyle(marker);
            return marker;
        });
        map.showItems(markers, { animate: animate && !reduceMotion, padding: new mapkit.Padding(48, 40, 48, 40) });

        list.innerHTML = '';
        city.landmarks.forEach(function (landmark, index) {
            var li = document.createElement('li');
            var button = document.createElement('button');
            button.type = 'button';
            button.innerHTML = '<span class="try-num"></span><span class="try-label"></span>';
            button.querySelector('.try-num').textContent = String(index + 1);
            button.querySelector('.try-label').textContent = landmark.name;
            button.classList.toggle('is-stamped', !!stamped[landmark.id]);
            button.addEventListener('click', function () { select(index, true); });
            li.appendChild(button);
            list.appendChild(li);
        });
        renderProgress();
        select(0);
    }

    window.initStampedTry = function () {
        if (!window.mapkit || !mapkit.Map) { fail(); return; }
        mapkit.addEventListener('error', fail);
        var mapTypes = mapkit.MapType || mapkit.Map.MapTypes;
        map = new mapkit.Map(mapEl, {
            mapType: mapTypes.Hybrid,
            showsPointsOfInterest: false,
            isRotationEnabled: true,
            showsCompass: mapkit.FeatureVisibility ? mapkit.FeatureVisibility.Adaptive : undefined
        });
        map.addEventListener('select', function (event) {
            var marker = event.annotation;
            if (marker && marker.landmark && marker !== current) select(marker.index, true);
        });
        chips.addEventListener('click', function (event) {
            var button = event.target.closest('button[data-city]');
            if (button && (!city || button.dataset.city !== city.slug)) showCity(button.dataset.city, true);
        });
        stampBtn.addEventListener('click', stampIt);
        showCity(cities[0].slug, false);
    };

    function loadMapKit() {
        var script = document.createElement('script');
        script.src = 'https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.core.js';
        script.crossOrigin = 'anonymous';
        script.async = true;
        script.dataset.callback = 'initStampedTry';
        script.dataset.libraries = 'map,annotations,look-around';
        script.dataset.token = window.STAMPED_MAPKIT_TOKEN;
        script.dataset.language = document.documentElement.lang || 'en';
        script.onerror = fail;
        document.head.appendChild(script);
    }

    section.hidden = false;
    if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries) {
            if (entries.some(function (entry) { return entry.isIntersecting; })) {
                observer.disconnect();
                loadMapKit();
            }
        }, { rootMargin: '600px 0px' });
        observer.observe(section);
    } else {
        loadMapKit();
    }
})();
