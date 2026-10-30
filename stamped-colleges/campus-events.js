// Campus events on a Stamped! school page: the next few weeks from the school's own Localist
// calendar, read live like the app does (CampusEventsService.swift). Localist allows any site to
// read its public events. The section stays hidden if the calendar can't be reached or is empty.
(function () {
    const section = document.querySelector("[data-localist]");
    if (!section) return;
    const host = section.dataset.localist;
    const list = section.querySelector(".event-list");

    // The 12 most popular events of the next 30 days, one entry per recurring event
    const url = `https://${host}/api/2/events?pp=12&days=30&sort=ranking&distinct=true`;

    function text(tag, className, value) {
        const element = document.createElement(tag);
        if (className) element.className = className;
        element.textContent = value;   // textContent, never innerHTML: the calendar's text is untrusted
        return element;
    }

    // Plain text from the calendar's HTML-ish fields. DOMParser builds an inert document: nothing
    // in it runs or loads (unlike innerHTML on an element, where <img onerror> would fire).
    function clean(value) {
        const doc = new DOMParser().parseFromString(value || "", "text/html");
        return (doc.body.textContent || "").replace(/\s+/g, " ").trim();
    }

    fetch(url)
        .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
        .then((data) => {
            const now = Date.now();
            const events = (data.events || [])
                .map((item) => item.event)
                // Like the app: in-person only, nothing cancelled, an https link to the school's page
                .filter((event) => event.experience !== "virtual" && !/cancel/i.test(event.status || "") &&
                    /^https:\/\//.test(event.localist_url || ""))
                .map((event) => {
                    const upcoming = (event.event_instances || [])
                        .map((i) => i.event_instance)
                        .find((i) => new Date(i.start).getTime() >= now - (i.all_day ? 86400000 : 0));
                    return upcoming ? { event, start: new Date(upcoming.start), allDay: upcoming.all_day } : null;
                })
                .filter(Boolean)
                .sort((a, b) => a.start - b.start);

            if (!events.length) return;
            const day = new Intl.DateTimeFormat(undefined, { weekday: "short", month: "short", day: "numeric" });
            const time = new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" });

            for (const { event, start, allDay } of events) {
                const item = document.createElement("li");
                const link = document.createElement("a");
                link.href = event.localist_url;
                link.rel = "noopener";
                link.appendChild(text("strong", "", clean(event.title)));
                link.appendChild(text("span", "event-when", `${day.format(start)} · ${allDay ? "All day" : time.format(start)}`));
                const venue = clean(event.location_name || event.location || "");
                if (venue && !/^(online|virtual|zoom)$/i.test(venue)) link.appendChild(text("span", "event-where", venue));
                item.appendChild(link);
                list.appendChild(item);
            }
            section.hidden = false;
        })
        .catch(() => { /* leave the section hidden */ });
})();
