// One search across the Stamped! city guides and school pages: cities, schools, architects and
// landmarks. It adds a Search button to the page header and fills in any box marked
// [data-site-search]. The index (search-index.json, from tools/stamped/build_search_index.py)
// loads the first time someone searches, and the search runs in the browser, so nothing typed
// leaves the page. Text goes in with textContent only.
(() => {
    const script = document.currentScript;
    if (!script) return;
    const indexUrl = new URL("search-index.json", script.src);
    const siteRoot = new URL("../", script.src);   // index URLs start at the site root
    const maxResults = 10;
    const typeNames = { continent: "Continent", city: "City", school: "School", architect: "Architect", landmark: "Landmark" };
    // Places and people first: their pages lead to the landmarks
    const typeWeight = { city: 120, school: 120, architect: 110, continent: 100, landmark: 0 };

    let indexPromise = null;
    let widgetCount = 0;

    // Lowercased words without accents or punctuation ("Gaudí" finds "gaudi", "St. Paul's" -> "st pauls")
    function words(text) {
        return String(text).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
            .replace(/['’]/g, "")
            .split(/[^\p{L}\p{N}]+/u)
            .filter((word) => word !== "");
    }

    function loadIndex() {
        if (!indexPromise) {
            // no-cache: the browser checks for a newer index, and reuses its copy if there isn't one
            indexPromise = fetch(indexUrl, { cache: "no-cache" })
                .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
                .then((data) => data.items.map(([type, name, detail, url, extra]) => {
                    const nameWords = words(name);
                    return {
                        type, name, detail, url,
                        nameText: nameWords.join(" "),
                        nameWords,
                        allWords: [...nameWords, ...words(detail), ...words(extra || "")],
                    };
                }))
                .catch((error) => {
                    indexPromise = null;   // try again next time
                    throw error;
                });
        }
        return indexPromise;
    }

    // Every word typed must start a word of the item. Name matches, then cities, schools and
    // architects, rank above landmarks; shorter names win a tie.
    function search(items, query) {
        const tokens = words(query);
        if (tokens.length === 0) return [];
        const phrase = tokens.join(" ");
        const startsAWord = (list) => tokens.every((token) => list.some((word) => word.startsWith(token)));
        const scored = [];
        for (const item of items) {
            if (!startsAWord(item.allWords)) continue;
            let score = typeWeight[item.type] || 0;
            if (item.nameText === phrase) score += 300;
            else if (item.nameText.startsWith(phrase)) score += 60;
            if (startsAWord(item.nameWords)) score += 80;
            scored.push({ item, score });
        }
        scored.sort((a, b) => b.score - a.score || a.item.name.length - b.item.name.length);
        return scored.slice(0, maxResults).map((entry) => entry.item);
    }

    function el(tag, className, text) {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (text !== undefined) element.textContent = text;   // never innerHTML
        return element;
    }

    function magnifier() {
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.setAttribute("width", "18");
        svg.setAttribute("height", "18");
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("focusable", "false");
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", "M10.5 3a7.5 7.5 0 0 1 5.9 12.1l4.8 4.8-1.4 1.4-4.8-4.8A7.5 7.5 0 1 1 10.5 3zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11z");
        path.setAttribute("fill", "currentColor");
        svg.append(path);
        return svg;
    }

    // A search box with a list of results (the ARIA combobox pattern), filled into `container`.
    // `onEscape` runs when Escape is pressed with nothing left to close (the header uses it to hide).
    function buildWidget(container, onEscape) {
        widgetCount += 1;
        const id = `site-search-${widgetCount}`;
        const label = el("label", "site-search-label", "Search cities, schools, landmarks and architects");
        label.htmlFor = `${id}-input`;
        const field = el("div", "site-search-field");
        const input = el("input");
        input.type = "search";
        input.id = `${id}-input`;
        input.placeholder = "Try Gaudí, Paris or Michigan";
        input.autocomplete = "off";
        input.spellcheck = false;
        input.setAttribute("enterkeyhint", "go");
        input.setAttribute("role", "combobox");
        input.setAttribute("aria-autocomplete", "list");
        input.setAttribute("aria-expanded", "false");
        input.setAttribute("aria-controls", `${id}-results`);
        field.append(magnifier(), input);
        const list = el("ul", "site-search-results");
        list.id = `${id}-results`;
        list.setAttribute("role", "listbox");
        list.setAttribute("aria-label", "Search results");
        list.hidden = true;
        const status = el("p", "site-search-status");
        status.setAttribute("aria-live", "polite");
        container.replaceChildren(label, field, list, status);
        container.hidden = false;

        let results = [];
        let active = -1;

        function go(item) {
            window.location.href = new URL(item.url, siteRoot).href;
        }

        function setActive(index) {
            active = index;
            list.querySelectorAll("[role=option]").forEach((option, i) => {
                option.setAttribute("aria-selected", i === index ? "true" : "false");
                if (i === index) option.scrollIntoView({ block: "nearest" });
            });
            if (index >= 0) input.setAttribute("aria-activedescendant", `${id}-option-${index}`);
            else input.removeAttribute("aria-activedescendant");
        }

        function close() {
            list.hidden = true;
            input.setAttribute("aria-expanded", "false");
            setActive(-1);
        }

        function render(query) {
            list.replaceChildren();
            results.forEach((item, i) => {
                const option = el("li", "site-search-option");
                option.id = `${id}-option-${i}`;
                option.setAttribute("role", "option");
                option.setAttribute("aria-selected", "false");
                option.append(el("span", `site-search-type type-${item.type}`, typeNames[item.type] || ""),
                    el("strong", "", item.name), el("span", "site-search-detail", item.detail));
                // mousedown would move focus off the box before the click lands
                option.addEventListener("mousedown", (event) => event.preventDefault());
                option.addEventListener("click", () => go(item));
                list.append(option);
            });
            active = -1;
            input.removeAttribute("aria-activedescendant");
            const open = results.length > 0;
            list.hidden = !open;
            input.setAttribute("aria-expanded", open ? "true" : "false");
            if (!query.trim()) status.textContent = "";
            else if (open) status.textContent = `${results.length}${results.length === maxResults ? "+" : ""} result${results.length === 1 ? "" : "s"}. Use the arrow keys to choose one.`;
            else status.textContent = `Nothing found for “${query.trim()}”.`;
        }

        function update() {
            const query = input.value;
            if (!query.trim()) {
                results = [];
                render(query);
                return;
            }
            loadIndex()
                .then((items) => {
                    if (input.value !== query) return;   // a newer search already ran
                    results = search(items, query);
                    render(query);
                })
                .catch(() => { status.textContent = "Search isn't available right now. Try again in a moment."; });
        }

        input.addEventListener("focus", () => { loadIndex().catch(() => {}); });
        input.addEventListener("input", update);
        input.addEventListener("keydown", (event) => {
            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                if (!results.length) return;
                event.preventDefault();
                if (list.hidden) { list.hidden = false; input.setAttribute("aria-expanded", "true"); }
                // Down from the last result goes back to the first, and up from the first to the last
                if (event.key === "ArrowDown") setActive(active + 1 >= results.length ? 0 : active + 1);
                else setActive(active <= 0 ? results.length - 1 : active - 1);
            } else if (event.key === "Enter") {
                if (!results.length) return;
                event.preventDefault();
                go(results[active >= 0 ? active : 0]);
            } else if (event.key === "Escape") {
                if (!list.hidden) {
                    event.preventDefault();
                    close();
                } else if (input.value) {
                    event.preventDefault();
                    input.value = "";
                    update();
                } else if (onEscape) {
                    event.preventDefault();
                    onEscape();
                }
            }
        });
        // Close the list when focus leaves the box
        container.addEventListener("focusout", (event) => {
            if (!container.contains(event.relatedTarget)) close();
        });
        input.addEventListener("click", () => { if (results.length) { list.hidden = false; input.setAttribute("aria-expanded", "true"); } });
        return input;
    }

    // Boxes already on the page (the city guides index, the schools page)
    document.querySelectorAll("[data-site-search]").forEach((container) => buildWidget(container, null));

    // A Search button in the header that opens a box under it
    const header = document.querySelector(".site-header");
    const nav = header && header.querySelector(".header-nav");
    if (!nav) return;
    const toggle = el("button", "search-toggle");
    toggle.type = "button";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", "site-search-panel");
    toggle.append(magnifier(), el("span", "search-toggle-label", "Search"));
    const panel = el("div", "search-panel");
    panel.id = "site-search-panel";
    panel.hidden = true;
    const inner = el("div", "container");
    const box = el("div", "site-search");
    inner.append(box);
    panel.append(inner);
    header.append(panel);

    function setOpen(open) {
        panel.hidden = !open;
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) input.focus();
        else toggle.focus();
    }
    const input = buildWidget(box, () => setOpen(false));
    toggle.addEventListener("click", () => setOpen(panel.hidden));
    nav.insertBefore(toggle, nav.querySelector(".header-button"));

    // "/" opens the search from anywhere on the page, as on many sites
    document.addEventListener("keydown", (event) => {
        const typing = event.target.closest && event.target.closest("input, textarea, select, [contenteditable]");
        if (event.key === "/" && !typing && !event.metaKey && !event.ctrlKey && !event.altKey) {
            event.preventDefault();
            setOpen(true);
        }
    });
})();
