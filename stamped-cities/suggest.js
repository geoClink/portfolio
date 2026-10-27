// "Know this place well?" form on each city guide and school page. It opens the visitor's own
// email app with the suggestion filled in, so the site sends and stores nothing itself. The
// subject starts with the same tag as the app's report links, so one mail filter catches both.
(function () {
    var form = document.querySelector('.suggest-form');
    if (!form) return;
    var fields = form.elements;
    var status = form.querySelector('.suggest-status');
    var address = 'GeorgeClinkscalesDev@proton.me';

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        var kind = form.querySelector('input[name="kind"]:checked').value;
        var source = fields['source'].value.trim();
        var body = [
            'Place: ' + form.dataset.place,
            'Type: ' + kind,
            'Page: ' + form.dataset.page,
            source ? 'Source: ' + source : null,
            '',
            fields['details'].value.trim()
        ].filter(function (line) { return line !== null; }).join('\n');
        var subject = '[Stamped! suggestion] ' + kind + ' for ' + form.dataset.place;

        window.location.href = 'mailto:' + address +
            '?subject=' + encodeURIComponent(subject) +
            '&body=' + encodeURIComponent(body.slice(0, 1800));
        status.textContent = 'If your email app didn\u2019t open, email ' + address + ' and paste your suggestion.';
        if (typeof gtag === 'function') gtag('event', 'stamped_suggestion', { event_category: 'stamped', event_label: kind });
    });
})();
