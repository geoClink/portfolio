// "Know this place well?" form on each city guide and school page. Sends the suggestion to the same contact
// endpoint as contact.html, which emails it to George for checking before it goes into the app.
(function () {
    var form = document.querySelector('.suggest-form');
    if (!form) return;
    var fields = form.elements;
    var status = form.querySelector('.suggest-status');
    var button = form.querySelector('button');

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        if (fields['website'].value) return;   // filled in only by bots
        var kind = form.querySelector('input[name="kind"]:checked').value;
        var message = [
            '[Stamped! suggestion]',
            'Place: ' + form.dataset.place,
            'Type: ' + kind,
            'Page: ' + form.dataset.page,
            fields['source'].value ? 'Source: ' + fields['source'].value.trim() : '',
            '',
            fields['details'].value.trim()
        ].filter(function (line, i) { return line !== '' || i === 5; }).join('\n');

        button.disabled = true;
        status.textContent = 'Sending…';
        try {
            var res = await fetch('https://webplatform-api.vercel.app/api/platform/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({
                    name: fields['name'].value.trim().slice(0, 100),
                    email: fields['email'].value.trim().slice(0, 200),
                    subject: 'Stamped! ' + kind.toLowerCase() + ' for ' + form.dataset.place,
                    message: message.slice(0, 2400),
                    inquiry_type: 'stamped-suggestion'
                })
            });
            if (!res.ok) throw new Error('status ' + res.status);
            form.reset();
            status.textContent = 'Thanks! We’ll check it and add it to the app if it fits.';
            if (typeof gtag === 'function') gtag('event', 'generate_lead', { event_category: 'stamped-suggestion', event_label: kind });
        } catch (err) {
            status.textContent = 'That didn’t send. Please try again, or email GeorgeClinkscalesDev@proton.me.';
        } finally {
            button.disabled = false;
        }
    });
})();
