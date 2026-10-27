// Live Apple Map for a city guide: every landmark pinned, and a Look Around preview of the
// one you tap. MapKit JS only loads when the map scrolls near. The token comes from map-token.js.
(function () {
    var section = document.querySelector('[data-city-map]');
    var dataEl = document.getElementById('map-data');
    if (!section || !dataEl || !window.STAMPED_MAPKIT_TOKEN) return;

    var data = JSON.parse(dataEl.textContent);
    var mapEl = section.querySelector('.city-map');
    var panel = section.querySelector('.look-around');
    var status = section.querySelector('.look-around-status');
    var preview = null;
    section.hidden = false;

    function fail() {
        section.hidden = true;   // No map is better than a broken one
    }

    function showLookAround(marker) {
        var landmark = marker.landmark;
        if (preview) {
            preview.destroy();
            preview = null;
        }
        panel.innerHTML = '';
        panel.classList.remove('is-empty');
        status.innerHTML = 'Loading Look Around at <strong></strong>…';
        status.querySelector('strong').textContent = landmark.name;

        preview = new mapkit.LookAroundPreview(panel, marker.coordinate);
        preview.addEventListener('load', function () {
            // Apple picks the nearest street photo and the web API can't aim it at the building,
            // so the caption says "nearest" rather than promising a view of it
            status.innerHTML = 'Street view nearest <strong></strong> · Tap it to look around. <a>Read more</a>';
            status.querySelector('strong').textContent = landmark.name;
            status.querySelector('a').href = '#' + landmark.id;
        });
        preview.addEventListener('error', function () {
            panel.classList.add('is-empty');
            status.innerHTML = 'Apple has no street-level imagery at <strong></strong> yet. <a>Read more</a>';
            status.querySelector('strong').textContent = landmark.name;
            status.querySelector('a').href = '#' + landmark.id;
        });
    }

    window.initStampedCityMap = function () {
        if (!window.mapkit || !mapkit.Map) {
            fail();
            return;
        }
        var markers = data.landmarks.map(function (landmark, index) {
            // Names show only on the selected pin; on a compact campus all of them at once overlap
            var hidden = mapkit.FeatureVisibility ? mapkit.FeatureVisibility.Hidden : 'hidden';
            var marker = new mapkit.MarkerAnnotation(new mapkit.Coordinate(landmark.lat, landmark.lng), {
                title: landmark.name,
                subtitle: landmark.subtitle,
                color: '#F2743F',
                glyphText: String(index + 1),
                titleVisibility: hidden,
                subtitleVisibility: hidden
            });
            marker.landmark = landmark;
            return marker;
        });
        var mapTypes = mapkit.MapType || mapkit.Map.MapTypes;
        var map = new mapkit.Map(mapEl, {
            mapType: mapTypes.Hybrid,
            showsPointsOfInterest: false,
            isRotationEnabled: true
        });
        map.showItems(markers, { animate: false, padding: new mapkit.Padding(56, 40, 56, 40) });
        map.addEventListener('select', function (event) {
            if (event.annotation && event.annotation.landmark) showLookAround(event.annotation);
        });
        if (markers.length) {
            markers[0].selected = true;   // shows its name, matching the Look Around preview
            showLookAround(markers[0]);
        }
    };

    function loadMapKit() {
        var script = document.createElement('script');
        script.src = 'https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.core.js';
        script.crossOrigin = 'anonymous';
        script.async = true;
        script.dataset.callback = 'initStampedCityMap';
        script.dataset.libraries = 'map,annotations,look-around';
        script.dataset.token = window.STAMPED_MAPKIT_TOKEN;
        script.onerror = fail;
        document.head.appendChild(script);
    }

    if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries) {
            if (entries.some(function (entry) { return entry.isIntersecting; })) {
                observer.disconnect();
                loadMapKit();
            }
        }, { rootMargin: '400px 0px' });
        observer.observe(section);
    } else {
        loadMapKit();
    }
})();
