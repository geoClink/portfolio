// The architecture quiz on a Stamped! city guide or school page: ten questions made from the
// place's landmarks with the app's own rules (QuizView/QuizView-ViewModel.swift and
// QuizView/Components/QuizLogic.swift). The facts come from quiz/<slug>.json, written by
// tools/stamped/build_quiz_data.py. Text goes in with textContent only. The section stays
// hidden if the data can't be loaded.
(() => {
    const section = document.querySelector("[data-quiz]");
    if (!section) return;
    const card = section.querySelector(".quiz-card");
    const maxQuestions = 10;
    const storageKey = "stamped-quiz";   // best score per place, only in this browser
    const placeKey = section.dataset.quiz.replace(/^quiz\/|\.json$/g, "");

    // The app's prompts (QuestionType.swift)
    const prompts = {
        name: "Based on the data, which landmark is this?",
        photo: "Which building is this?",
        style: "What is the architectural style of this building?",
        year: "In what year was this structure completed?",
        architect: "Which architect or firm designed this building?",
        stories: "How many stories tall is this structure?",
    };

    let place = "";
    let landmarks = [];
    let queue = [];
    let questionCount = 0;
    let score = 0;
    let misses = [];
    let current = null;            // { building, type, options, correct }
    const noPhoto = new Set();     // ids whose photo failed to load: no photo questions for them

    // ----- Small helpers -----

    function el(tag, className, text) {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (text !== undefined) element.textContent = text;   // never innerHTML
        return element;
    }

    function shuffled(items) {
        const copy = items.slice();
        for (let i = copy.length - 1; i > 0; i -= 1) {
            const j = Math.floor(Math.random() * (i + 1));
            [copy[i], copy[j]] = [copy[j], copy[i]];
        }
        return copy;
    }

    // Lowercased words without accents or punctuation ("St. Paul's" -> ["st", "pauls"]), like QuizLogic.words
    function words(text) {
        return String(text).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
            .replace(/['’]/g, "")
            .split(/[^\p{L}\p{N}]+/u)
            .filter((word) => word !== "");
    }

    function sameText(first, second) {
        return words(first).join(" ") === words(second).join(" ");
    }

    // One style name contains the other ("Gothic" and "Gothic Revival")
    function overlaps(first, second) {
        const a = ` ${words(first).join(" ")} `;
        const b = ` ${words(second).join(" ")} `;
        return a.includes(b) || b.includes(a);
    }

    // The site writes years before 1 AD as "80 BC" (the app stores them as negative numbers)
    function yearLabel(year) {
        return year < 0 ? `${-year} BC` : String(year);
    }

    function floorsLabel(count) {
        return count === 1 ? "1 floor" : `${count} floors`;
    }

    // ----- Which question to ask (QuizLogic.choices and pick) -----

    function choices(building) {
        const list = [{ type: "name", weight: 1 }];
        if (building.photo && !noPhoto.has(building.id)) list.push({ type: "photo", weight: 1.5 });
        if (building.style) list.push({ type: "style", weight: 1 });
        if (building.year !== 0) list.push({ type: "year", weight: 1 });
        if (building.architect) list.push({ type: "architect", weight: 1 });
        // "1 floor" is too easy to guess, and "How many floors?" gets old fast
        if (building.stories >= 2) list.push({ type: "stories", weight: 0.35 });
        return list;
    }

    function pick(list) {
        const total = list.reduce((sum, choice) => sum + choice.weight, 0);
        let roll = Math.random() * total;
        for (const choice of list) {
            roll -= choice.weight;
            if (roll < 0) return choice.type;
        }
        return list[list.length - 1].type;
    }

    // ----- Wrong answers (QuizLogic distractors) -----

    // Up to three options that are not the answer, not blank and not repeated
    function uniqueDistractors(answer, candidates, keepOrder) {
        const ordered = keepOrder ? candidates : shuffled(candidates);
        const picked = [];
        for (const candidate of ordered) {
            if (picked.length === 3) break;
            const trimmed = String(candidate).trim();
            if (trimmed && !sameText(trimmed, answer) && !picked.some((other) => sameText(other, trimmed))) {
                picked.push(trimmed);
            }
        }
        return picked;
    }

    // Wrong years 5-40 years from the real one and at least 3 apart, never in the future.
    // A BC answer gets BC years, so the answer isn't the only one from its era.
    function yearDistractors(answer) {
        const thisYear = new Date().getFullYear();
        const candidates = [];
        for (let offset = 5; offset <= 40; offset += 1) candidates.push(answer - offset, answer + offset);
        const possible = candidates.filter((year) => year <= thisYear && (answer > 0 ? year >= 1 : year <= -1));
        const picked = [];
        for (const year of shuffled(possible)) {
            if (picked.length === 3) break;
            if (picked.every((other) => Math.abs(other - year) >= 3)) picked.push(year);
        }
        return picked.map(yearLabel);
    }

    // Close floor counts for short buildings, wider for towers (a 3-floor building gets 1-6)
    function floorDistractors(answer) {
        const spread = Math.max(3, Math.floor(answer / 3));
        const candidates = [];
        for (let count = Math.max(1, answer - spread); count <= answer + spread; count += 1) {
            if (count !== answer) candidates.push(count);
        }
        return shuffled(candidates).slice(0, 3).map(floorsLabel);
    }

    // Well-known styles with a rough peak year, for places with too few styles of their own
    const fallbackStyles = [
        ["Romanesque", 1100], ["Gothic", 1250], ["Renaissance", 1500], ["Baroque", 1680],
        ["Neoclassical", 1800], ["Gothic Revival", 1850], ["Victorian", 1870], ["Beaux-Arts", 1900],
        ["Art Nouveau", 1900], ["Art Deco", 1930], ["Modernist", 1950], ["Brutalist", 1965],
        ["Postmodern", 1985], ["Contemporary", 2010],
    ];

    // Styles from the place whose buildings are within 75 years of this one come first, then its
    // other styles, then well-known styles nearest in era, so "Brutalist" isn't an easy miss for a 1600s church
    function styleDistractors(answer, answerYear) {
        const eraDistance = new Map();
        for (const other of landmarks) {
            if (!other.style || sameText(other.style, answer)) continue;
            const distance = answerYear && other.year ? Math.abs(other.year - answerYear) : Infinity;
            eraDistance.set(other.style, Math.min(eraDistance.get(other.style) ?? Infinity, distance));
        }
        const styles = [...eraDistance.keys()];
        const sameEra = styles.filter((style) => eraDistance.get(style) <= 75);
        const otherEras = styles.filter((style) => eraDistance.get(style) > 75);
        const fallbacks = fallbackStyles
            .filter(([style]) => !overlaps(style, answer))
            .sort((a, b) => Math.abs(a[1] - (answerYear || a[1])) - Math.abs(b[1] - (answerYear || b[1])))
            .map(([style]) => style);
        return uniqueDistractors(answer, [...shuffled(sameEra), ...shuffled(otherEras), ...fallbacks], true);
    }

    // ----- One question -----

    function makeQuestion(building, type) {
        let correct;
        let wrong;
        if (type === "name" || type === "photo") {
            correct = building.name;
            wrong = uniqueDistractors(correct, landmarks.map((other) => other.name));
        } else if (type === "architect") {
            correct = building.architect;
            wrong = uniqueDistractors(correct, landmarks.map((other) => other.architect).filter(Boolean));
        } else if (type === "year") {
            correct = yearLabel(building.year);
            wrong = yearDistractors(building.year);
        } else if (type === "style") {
            correct = building.style;
            wrong = styleDistractors(correct, building.year || null);
        } else {
            correct = floorsLabel(building.stories);
            wrong = floorDistractors(building.stories);
        }
        // A small place may have fewer than three wrong answers, so the question shows fewer options
        return { building, type, correct, options: shuffled([...wrong, correct]) };
    }

    // "Notre-Dame Basilica · Gothic Revival · 1829 · James O'Donnell", shown after each answer
    function factLine(building) {
        return [building.name, building.style, building.year ? yearLabel(building.year) : "", building.architect]
            .filter(Boolean).join(" · ");
    }

    // ----- Screens -----

    function bestScore() {
        try { return JSON.parse(localStorage.getItem(storageKey) || "{}")[placeKey] || 0; } catch (error) { return 0; }
    }

    function saveBest(value) {
        try {
            const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
            saved[placeKey] = value;
            localStorage.setItem(storageKey, JSON.stringify(saved));
        } catch (error) { /* private mode: the score just isn't kept */ }
    }

    function button(className, text, onClick) {
        const element = el("button", className, text);
        element.type = "button";
        element.addEventListener("click", onClick);
        return element;
    }

    function showStart() {
        card.replaceChildren();
        const best = bestScore();
        card.append(el("p", "quiz-lead", `${maxQuestions} questions about the landmarks on this page.`));
        if (best) card.append(el("p", "quiz-best", `Your best here: ${best}/${maxQuestions}`));
        card.append(button("quiz-button", "Start the quiz", startRound));
    }

    function startRound() {
        queue = [];
        questionCount = 0;
        score = 0;
        misses = [];
        nextQuestion();
    }

    function nextQuestion() {
        if (questionCount >= maxQuestions) {
            showResults();
            return;
        }
        // Refill by shuffling, so a landmark doesn't come up twice in a row
        if (queue.length === 0) queue = shuffled(landmarks);
        const building = queue.shift();
        questionCount += 1;
        current = makeQuestion(building, pick(choices(building)));
        showQuestion(true);
    }

    // The photo failed to load: ask something else about the same building instead
    function photoUnavailable(building) {
        noPhoto.add(building.id);
        if (current && current.building === building && !current.answered) {
            current = makeQuestion(building, pick(choices(building)));
            showQuestion(card.contains(document.activeElement));
        }
    }

    function dataCard(question) {
        const { building, type } = question;
        const box = el("div", "quiz-data");
        if (type === "photo") {
            const figure = el("figure", "quiz-photo");
            const image = el("img");
            image.src = building.photo.src;
            image.width = building.photo.width;
            image.height = building.photo.height;
            image.alt = "Photo of the building in question";
            image.referrerPolicy = "no-referrer";
            image.addEventListener("error", () => photoUnavailable(building));
            const caption = el("figcaption", "", "Photo: ");
            const author = el("a", "", building.photo.author);
            author.href = building.photo.page;
            author.rel = "noopener";
            caption.append(author, `, ${building.photo.license}, via ${building.photo.site || "Wikimedia Commons"}`);
            figure.append(image, caption);
            box.append(figure);
            return box;
        }
        // The app's "field data" card: the fact being asked about is hidden as "Classified"
        box.append(el("p", type === "name" ? "quiz-data-name is-hidden" : "quiz-data-name",
            type === "name" ? "Identification required" : building.name));
        const list = el("dl");
        const rows = [
            ["Style", building.style, "style"],
            ["Year", building.year ? yearLabel(building.year) : "", "year"],
            ["Stories", building.stories > 0 ? String(building.stories) : "", "stories"],
            ["Architect", building.architect, "architect"],
        ];
        for (const [label, value, asks] of rows) {
            if (!value) continue;
            const row = el("div", asks === type ? "is-hidden" : "");
            row.append(el("dt", "", label), el("dd", "", asks === type ? "Classified" : value));
            list.append(row);
        }
        box.append(list);
        return box;
    }

    function showQuestion(moveFocus) {
        card.replaceChildren();
        const top = el("p", "quiz-progress");
        top.append(el("span", "", `Question ${questionCount} of ${maxQuestions}`), el("span", "", `Score ${score}`));
        const prompt = el("h3", "quiz-prompt", prompts[current.type]);
        prompt.tabIndex = -1;
        const options = el("ul", "quiz-options");
        options.setAttribute("aria-label", "Answers");
        for (const option of current.options) {
            const item = el("li");
            item.append(button("quiz-option", option, () => answer(option)));
            options.append(item);
        }
        const feedback = el("div", "quiz-feedback");
        feedback.setAttribute("aria-live", "polite");
        card.append(top, prompt, dataCard(current), options, feedback);
        if (moveFocus) prompt.focus();
    }

    function answer(selected) {
        if (current.answered) return;   // one answer per question
        current.answered = true;
        const isCorrect = selected === current.correct;
        if (isCorrect) {
            score += 1;
        } else {
            misses.push({ name: current.building.name, type: current.type, correct: current.correct, given: selected });
        }

        // Mark the right answer (and a wrong pick) with words as well as color
        for (const option of card.querySelectorAll(".quiz-option")) {
            option.setAttribute("aria-disabled", "true");
            if (option.textContent === current.correct) {
                option.classList.add("is-right");
                option.append(el("span", "quiz-mark", isCorrect ? " · Your answer, correct" : " · Correct answer"));
            } else if (option.textContent === selected) {
                option.classList.add("is-wrong");
                option.append(el("span", "quiz-mark", " · Your answer"));
            }
        }
        card.querySelector(".quiz-progress span:last-child").textContent = `Score ${score}`;

        // The app's verdict and fact line, plus a link to the landmark on this page
        const feedback = card.querySelector(".quiz-feedback");
        feedback.classList.add(isCorrect ? "is-right" : "is-wrong");
        feedback.append(el("strong", "", isCorrect ? "Correct!" : `Incorrect. The answer was ${current.correct}.`),
            el("span", "quiz-fact", factLine(current.building)));
        const more = el("a", "quiz-more", "Read about it on this page");
        more.href = `#${current.building.id}`;
        feedback.append(more);

        const next = button("quiz-button", questionCount >= maxQuestions ? "See results" : "Next question", nextQuestion);
        card.append(next);
        next.focus({ preventScroll: true });
    }

    function showResults() {
        card.replaceChildren();
        const stars = score >= 9 ? 3 : score >= 6 ? 2 : score >= 3 ? 1 : 0;
        const message = ["Try Again!", "Keep Practicing!", "Well Done!", score === maxQuestions ? "Perfect Score!" : "Outstanding!"][stars];
        const best = bestScore();
        if (score > best) saveBest(score);

        const heading = el("h3", "quiz-prompt", `${score}/${maxQuestions} · ${message}`);
        heading.tabIndex = -1;
        const starLine = el("p", "quiz-stars", "★".repeat(stars) + "☆".repeat(3 - stars));
        starLine.setAttribute("role", "img");
        starLine.setAttribute("aria-label", `${stars} of 3 stars`);
        card.append(heading, starLine,
            el("p", "quiz-best", score > best ? "New personal best!" : `Best: ${Math.max(best, score)}/${maxQuestions}`));

        if (misses.length) {
            card.append(el("h4", "quiz-subhead", "Review your misses"));
            const list = el("ul", "quiz-misses");
            for (const miss of misses) {
                const item = el("li");
                item.append(el("strong", "", miss.name));
                // For "which landmark?" questions the name is the answer
                if (miss.type !== "name" && miss.type !== "photo") item.append(el("span", "", `Correct answer: ${miss.correct}`));
                item.append(el("span", "quiz-given", `Your answer: ${miss.given}`));
                list.append(item);
            }
            card.append(list);
        }

        const actions = el("div", "quiz-actions");
        const app = el("a", "quiz-button quiz-app-link", "Get the app");
        app.href = section.dataset.appStore;
        actions.append(button("quiz-button quiz-again", "Play again", startRound), app);
        card.append(actions, el("p", "quiz-note",
            `In Stamped! you can answer out loud, take the quiz for every city and campus, and earn a passport stamp at each landmark in ${place}. Free on iPhone and iPad.`));
        heading.focus();
    }

    fetch(section.dataset.quiz, { cache: "no-cache" })
        .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
        .then((data) => {
            place = data.place;
            landmarks = data.landmarks || [];
            if (landmarks.length < 2) return;   // nothing to choose between
            showStart();
            section.hidden = false;
        })
        .catch(() => { /* leave the section hidden */ });
})();
