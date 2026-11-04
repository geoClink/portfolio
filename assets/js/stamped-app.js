// Stamped! landing page (stamped-app.html and its es/de/ja copies): header, scroll effects,
// videos and the sample quiz. The text it shows comes from window.stampedCopy, set in a small
// inline script on each page, so this one file works for every language and stays cached.
(() => {
    const copy = window.stampedCopy;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduceMotion && 'IntersectionObserver' in window) {
        document.documentElement.classList.add('motion');
    }

    // Header gets a bottom line once the page scrolls
    const header = document.querySelector('.site-header');
    const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // Close the language menu on an outside click
    const langSwitch = document.querySelector('.lang-switch');
    document.addEventListener('click', (event) => {
        if (langSwitch.open && !langSwitch.contains(event.target)) langSwitch.open = false;
    });

    // Fade sections in and thud stamps down as they scroll into view
    if (document.documentElement.classList.contains('motion')) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-in');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });
        document.querySelectorAll('.reveal, .stamp:not([hidden])').forEach((el) => observer.observe(el));
    }

    // Hero video: only load it when motion is OK and the visitor isn't saving data, and only
    // download and play it while it's on screen (on phones it sits below the headline)
    const video = document.querySelector('.hero-video');
    const toggle = document.querySelector('.video-toggle');
    const saveData = navigator.connection && navigator.connection.saveData;
    let pausedByVisitor = false;
    const playHeroVideo = () => {
        if (!video.src) video.src = video.dataset.src;
        video.play().then(() => {
            toggle.classList.add('is-ready');
        }).catch(() => { /* autoplay blocked: the poster stays */ });
    };
    const watchHeroVideo = () => {
        if (!('IntersectionObserver' in window)) {
            playHeroVideo();
            return;
        }
        const heroObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting && !pausedByVisitor) playHeroVideo();
                else if (!entry.isIntersecting && !video.paused) video.pause();
            });
        }, { threshold: 0.25 });
        heroObserver.observe(video);
    };
    if (video && !reduceMotion && !saveData) {
        // Wait for the page itself to finish loading so the video never competes with it
        if (document.readyState === 'complete') watchHeroVideo();
        else window.addEventListener('load', watchHeroVideo);
        toggle.addEventListener('click', () => {
            const icon = toggle.querySelector('i');
            if (video.paused) {
                pausedByVisitor = false;
                video.play();
                icon.className = 'fas fa-pause';
                toggle.setAttribute('aria-label', copy.pause);
            } else {
                pausedByVisitor = true;
                video.pause();
                icon.className = 'fas fa-play';
                toggle.setAttribute('aria-label', copy.play);
            }
        });
    }

    // Tour clips load when they scroll near, play only while visible, and stay as posters for reduced motion
    const tourVideos = document.querySelectorAll('.tour-video');
    const showPoster = (clip) => {
        if (clip.dataset.poster) clip.poster = clip.dataset.poster;
    };
    // Posters (data-poster) wait until the section is within about 800px, so they don't compete
    // with the first screen
    if ('IntersectionObserver' in window) {
        const posterObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    showPoster(entry.target);
                    posterObserver.unobserve(entry.target);
                }
            });
        }, { rootMargin: '800px 0px' });
        tourVideos.forEach((clip) => posterObserver.observe(clip));
    } else {
        tourVideos.forEach(showPoster);
    }
    if (!reduceMotion && !saveData && 'IntersectionObserver' in window) {
        const tourObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                const clip = entry.target;
                if (entry.isIntersecting) {
                    if (!clip.src) clip.src = clip.dataset.src;
                    clip.play().catch(() => {});
                } else if (!clip.paused) {
                    clip.pause();
                }
            });
        }, { threshold: 0.35 });
        tourVideos.forEach((clip) => tourObserver.observe(clip));
    } else {
        tourVideos.forEach((clip) => {
            clip.src = clip.dataset.src;
            clip.setAttribute('controls', '');
        });
    }

    // Sample quiz
    const quiz = document.querySelector('[data-quiz]');
    if (!quiz) return;
    const questions = copy.questions;
    let index = 0;
    let score = 0;
    const countEl = quiz.querySelector('[data-quiz-count]');
    const questionEl = quiz.querySelector('[data-quiz-question]');
    const optionsEl = quiz.querySelector('[data-quiz-options]');
    const feedbackEl = quiz.querySelector('[data-quiz-feedback]');
    const nextEl = quiz.querySelector('[data-quiz-next]');
    const dots = quiz.querySelectorAll('.quiz-dots span');
    const stampEl = quiz.querySelector('[data-quiz-stamp]');

    const choose = (choice) => {
        const item = questions[index];
        const buttons = optionsEl.querySelectorAll('button');
        const right = choice === item.answer;
        if (right) score++;
        buttons.forEach((button, buttonIndex) => {
            button.disabled = true;
            if (buttonIndex === item.answer) {
                button.classList.add('is-right');
                button.insertAdjacentHTML('beforeend', '<i class="fas fa-check" aria-hidden="true"></i>');
            } else if (buttonIndex === choice) {
                button.classList.add('is-wrong');
                button.insertAdjacentHTML('beforeend', '<i class="fas fa-times" aria-hidden="true"></i>');
            }
        });
        dots[index].classList.add(right ? 'is-right' : 'is-wrong');
        feedbackEl.textContent = (right ? copy.correct : copy.wrong) + item.note;
        nextEl.textContent = index < questions.length - 1 ? copy.next : copy.seeStamp;
        nextEl.hidden = false;
        nextEl.focus();
    };

    const render = () => {
        const item = questions[index];
        countEl.textContent = copy.question.replace('{n}', index + 1).replace('{total}', questions.length);
        questionEl.textContent = item.q;
        optionsEl.innerHTML = '';
        item.options.forEach((label, optionIndex) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = label;
            button.addEventListener('click', () => choose(optionIndex));
            optionsEl.appendChild(button);
        });
        nextEl.hidden = true;
    };

    const finish = () => {
        quiz.querySelector('[data-quiz-score]').textContent = `${score} / ${questions.length}`;
        quiz.querySelector('[data-quiz-rank]').textContent = copy.ranks[score];
        stampEl.hidden = false;
        // Two frames, so the stamp is drawn once before it animates in
        requestAnimationFrame(() => {
            requestAnimationFrame(() => stampEl.classList.add('is-in'));
        });
        countEl.textContent = copy.done;
        questionEl.textContent = score === questions.length
            ? copy.perfect
            : copy.yourScore.replace('{score}', score).replace('{total}', questions.length);
        optionsEl.innerHTML = '';
        feedbackEl.textContent = copy.more;
        nextEl.textContent = copy.playAgain;
        nextEl.hidden = false;
        index = questions.length;
    };

    nextEl.addEventListener('click', () => {
        if (index >= questions.length) {
            index = 0;
            score = 0;
            stampEl.hidden = true;
            stampEl.classList.remove('is-in');
            dots.forEach((dot) => { dot.className = ''; });
            feedbackEl.textContent = copy.intro;
            render();
            optionsEl.querySelector('button').focus();
        } else if (index === questions.length - 1) {
            finish();
        } else {
            index++;
            render();
            optionsEl.querySelector('button').focus();
        }
    });

    // Swap the static first-question buttons for live ones
    render();

    // Email sign-up: the form still posts to Buttondown in a new tab, because Buttondown sometimes
    // needs to show a "prove you're human" check there (its docs say not to send the form with fetch).
    // Meanwhile this page swaps the form for a stamped "check your inbox" note.
    const signup = document.querySelector('.signup');
    const signupDone = document.querySelector('.signup-done');
    if (signup && signupDone) {
        // 'submit' only fires once the email passes the browser's own check
        signup.addEventListener('submit', () => {
            // Wait one moment so the browser sends the form before it's hidden
            setTimeout(() => {
                signup.hidden = true;
                signupDone.hidden = false;
                signupDone.focus();
                // Thud the stamp down one frame after it appears, so the animation runs
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => signupDone.querySelector('.stamp').classList.add('is-in'));
                });
            }, 0);
        });
    }
})();
