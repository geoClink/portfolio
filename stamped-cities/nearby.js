// Restaurants and hotels near the landmark picked on a city guide's map, from Apple Maps
// (MapKit JS's points-of-interest search, the same data the app uses). map.js sends a
// "stamped:landmark" event with the map and the landmark; this lists the closest places with
// an estimated walking time and pins them on the map. Nothing shows if MapKit or the search fails.
(() => {
    const section = document.querySelector('[data-city-map]');
    const box = section && section.querySelector('[data-nearby]');
    if (!box) return;

    const RADIUS_METRES = 800;        // how far around the landmark to search
    const MAX_METRES = 1200;          // ignore anything farther than a ~15 minute walk
    const PER_LIST = 5;
    const WALK_METRES_PER_MINUTE = 80;   // about 4.8 km/h
    const KINDS = [
        { list: 'restaurants', category: 'Restaurant', color: '#8E6CEF', glyph: 'R' },
        { list: 'hotels', category: 'Hotel', color: '#2F7DD1', glyph: 'H' }
    ];

    const results = {};   // landmark id -> { restaurants: [...], hotels: [...] }, so a repeat pick is instant
    let pins = [];
    let current = null;   // the landmark id being shown, so a slow answer for an old pick is ignored

    // Straight-line distance in metres between two coordinates (haversine)
    const distance = (a, b) => {
        const toRadians = (degrees) => degrees * Math.PI / 180;
        const dLat = toRadians(b.latitude - a.latitude);
        const dLng = toRadians(b.longitude - a.longitude);
        const h = Math.sin(dLat / 2) ** 2
            + Math.cos(toRadians(a.latitude)) * Math.cos(toRadians(b.latitude)) * Math.sin(dLng / 2) ** 2;
        return 2 * 6371000 * Math.asin(Math.sqrt(h));
    };

    const walkLabel = (metres) => {
        const minutes = Math.max(1, Math.round(metres / WALK_METRES_PER_MINUTE));
        return `about ${minutes} min walk`;
    };

    const appleMapsLink = (place) => {
        const query = new URLSearchParams({
            q: place.name,
            ll: `${place.coordinate.latitude},${place.coordinate.longitude}`
        });
        return `https://maps.apple.com/?${query.toString()}`;
    };

    // One points-of-interest search; resolves to the closest places of that category, nearest first
    const search = (center, kind) => new Promise((resolve) => {
        try {
            const category = mapkit.PointOfInterestCategory[kind.category];
            const searcher = new mapkit.PointsOfInterestSearch({
                center: center,
                radius: RADIUS_METRES,
                pointOfInterestFilter: mapkit.PointOfInterestFilter.including([category])
            });
            searcher.search((error, data) => {
                if (error || !data || !Array.isArray(data.places)) {
                    resolve([]);
                    return;
                }
                const places = data.places
                    .filter((place) => place && place.name && place.coordinate)
                    .map((place) => ({ place: place, metres: distance(center, place.coordinate) }))
                    .filter((item) => item.metres <= MAX_METRES)
                    .sort((a, b) => a.metres - b.metres)
                    .slice(0, PER_LIST);
                resolve(places);
            });
        } catch (error) {
            resolve([]);   // an older MapKit without this search: just show nothing
        }
    });

    const clearPins = (map) => {
        if (pins.length) map.removeAnnotations(pins);
        pins = [];
    };

    const showPins = (map, found) => {
        clearPins(map);
        KINDS.forEach((kind) => {
            found[kind.list].forEach((item) => {
                const pin = new mapkit.MarkerAnnotation(item.place.coordinate, {
                    title: item.place.name,
                    subtitle: walkLabel(item.metres),
                    color: kind.color,
                    glyphText: kind.glyph,
                    displayPriority: mapkit.Annotation.DisplayPriority
                        ? mapkit.Annotation.DisplayPriority.Low : 250
                });
                pins.push(pin);
            });
        });
        if (pins.length) map.addAnnotations(pins);
    };

    // Fill one list with links to Apple Maps. Text goes in with textContent only.
    const fillList = (list, items) => {
        list.replaceChildren();
        items.forEach((item) => {
            const row = document.createElement('li');
            const link = document.createElement('a');
            link.href = appleMapsLink(item.place);
            link.rel = 'noopener';
            link.target = '_blank';
            link.textContent = item.place.name;
            const walk = document.createElement('span');
            walk.className = 'nearby-walk';
            walk.textContent = walkLabel(item.metres);
            row.append(link, walk);
            list.append(row);
        });
        list.closest('.nearby-group').hidden = items.length === 0;
    };

    const show = (map, landmark, found) => {
        const total = KINDS.reduce((sum, kind) => sum + found[kind.list].length, 0);
        if (total === 0) {
            box.hidden = true;
            clearPins(map);
            return;
        }
        box.querySelector('.nearby-landmark').textContent = landmark.name;
        KINDS.forEach((kind) => {
            fillList(box.querySelector(`[data-list="${kind.list}"]`), found[kind.list]);
        });
        box.hidden = false;
        showPins(map, found);
    };

    section.addEventListener('stamped:landmark', async (event) => {
        const { map, landmark, coordinate } = event.detail;
        if (!window.mapkit || !mapkit.PointsOfInterestSearch || !mapkit.PointOfInterestFilter
            || !mapkit.PointOfInterestCategory) {
            return;   // box stays hidden
        }
        current = landmark.id;
        if (!results[landmark.id]) {
            const lists = await Promise.all(KINDS.map((kind) => search(coordinate, kind)));
            results[landmark.id] = {};
            KINDS.forEach((kind, index) => { results[landmark.id][kind.list] = lists[index]; });
        }
        if (current !== landmark.id) return;   // another landmark was picked while this one loaded
        show(map, landmark, results[landmark.id]);
    });
})();
