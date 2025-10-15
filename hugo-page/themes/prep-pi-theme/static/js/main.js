// themes/prep-pi-theme/static/js/main.js

document.addEventListener('DOMContentLoaded', function () {
    const themeToggle = document.getElementById('theme-toggle');
    const contrastToggle = document.getElementById('contrast-toggle');
    const simpleLangToggle = document.getElementById('simple-lang-toggle');
    const body = document.body;
    const root = document.documentElement;

    /**
     * Updates the theme toggle button icon based on the current theme.
     * Shows a sun ☀️ in dark mode and a moon 🌓 in light mode.
     */
    const updateThemeButton = () => {
        if (root.getAttribute('data-theme') === 'dark') {
            themeToggle.innerHTML = '☀️';
        } else {
            themeToggle.innerHTML = '🌓';
        }
    };

    /**
     * Adds or removes an 'active' class from the contrast button
     * to provide visual feedback.
     */
    const updateContrastButton = () => {
        if (root.hasAttribute('data-contrast')) {
            contrastToggle.classList.add('active');
        } else {
            contrastToggle.classList.remove('active');
        }
    };

    /**
     * Adds or removes an 'active' class from the simple language button
     * to provide visual feedback.
     */
    const updateSimpleLangButton = () => {
        if (body.classList.contains('simple-lang-active')) {
            simpleLangToggle.classList.add('active');
        } else {
            simpleLangToggle.classList.remove('active');
        }
    };

    /**
     * Applies user preferences from localStorage on page load and
     * updates the UI of the control buttons accordingly.
     */
    const applyStoredPreferences = () => {
        if (localStorage.getItem('theme')) {
            root.setAttribute('data-theme', localStorage.getItem('theme'));
        }
        if (localStorage.getItem('contrast')) {
            root.setAttribute('data-contrast', localStorage.getItem('contrast'));
        }
        if (localStorage.getItem('simple-lang')) {
            body.classList.add('simple-lang-active');
        }
        // Update all buttons to reflect the loaded state
        updateThemeButton();
        updateContrastButton();
        updateSimpleLangButton();
    };

    // --- INITIALIZATION ---
    applyStoredPreferences();

    // --- EVENT LISTENERS ---
    themeToggle.addEventListener('click', () => {
        if (root.getAttribute('data-theme') === 'dark') {
            root.removeAttribute('data-theme');
            localStorage.removeItem('theme');
        } else {
            root.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        }
        updateThemeButton();
    });

    contrastToggle.addEventListener('click', () => {
        if (root.hasAttribute('data-contrast')) {
            root.removeAttribute('data-contrast');
            localStorage.removeItem('contrast');
        } else {
            root.setAttribute('data-contrast', 'high');
            localStorage.setItem('contrast', 'high');
        }
        updateContrastButton();
    });

    simpleLangToggle.addEventListener('click', () => {
        body.classList.toggle('simple-lang-active');
        if (body.classList.contains('simple-lang-active')) {
            localStorage.setItem('simple-lang', 'true');
        } else {
            localStorage.removeItem('simple-lang');
        }
        updateSimpleLangButton();
    });
});