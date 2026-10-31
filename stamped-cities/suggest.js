// "Know this place well?" form on each city guide and school page. It opens the visitor's own
// email app with the suggestion filled in, so the site sends and stores nothing itself. The
// subject starts with the same tag as the app's report links, so one mail filter catches both.
(function () {
    var form = document.querySelector('.suggest-form');
    if (!form) return;
    var fields = form.elements;
    var status = form.querySelector('.suggest-status');
    var address = 'GeorgeClinkscalesDev@proton.me';
    var photoFields = form.querySelector('.photo-fields');
    var button = form.querySelector('button[type="submit"]');
    var buttonText = button.textContent;

    // "A photo" shows the credit name and the two permission boxes, and makes them required,
    // so a photo never arrives without the sender saying it's theirs to share.
    function isPhoto() {
        return form.querySelector('input[name="kind"]:checked').value === 'Photo';
    }
    function showPhotoFields() {
        if (!photoFields) return;
        var photo = isPhoto();
        photoFields.hidden = !photo;
        // A web page can't attach a file to an email, so the button says what comes next
        button.textContent = photo ? 'Write the email, then attach your photo' : buttonText;
        ['credit', 'own', 'license'].forEach(function (name) { fields[name].required = photo; });
    }
    form.querySelectorAll('input[name="kind"]').forEach(function (radio) {
        radio.addEventListener('change', showPhotoFields);
    });
    showPhotoFields();

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        var kind = form.querySelector('input[name="kind"]:checked').value;
        var source = fields['source'].value.trim();
        var photo = photoFields && isPhoto();
        var credit = photo ? fields['credit'].value.trim() : '';
        var body = [
            'Place: ' + form.dataset.place,
            'Type: ' + kind,
            'Page: ' + form.dataset.page,
            source ? 'Source: ' + source : null,
            photo ? 'Credit: ' + credit : null,
            photo ? 'Permission: I took this photo myself and share it under CC BY 4.0 ' +
                '(https://creativecommons.org/licenses/by/4.0/). Stamped! may use it free, ' +
                'in the app and on its website, credited to ' + credit + '.' : null,
            '',
            fields['details'].value.trim(),
            photo ? '\n(Photo attached.)' : null
        ].filter(function (line) { return line !== null; }).join('\n');
        var subject = '[Stamped! suggestion] ' + kind + ' for ' + form.dataset.place;

        window.location.href = 'mailto:' + address +
            '?subject=' + encodeURIComponent(subject) +
            '&body=' + encodeURIComponent(body.slice(0, 1800));
        status.textContent = photo
            ? 'Now attach your photo in the email and send it. If your email app didn\u2019t open, email ' + address + ' with the photo and the text above.'
            : 'If your email app didn\u2019t open, email ' + address + ' and paste your suggestion.';
        if (typeof gtag === 'function') gtag('event', 'stamped_suggestion', { event_category: 'stamped', event_label: kind });
    });
})();
