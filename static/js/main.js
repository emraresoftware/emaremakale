/**
 * Makale Üretici — Emare Finance DS
 * Scroll Reveal + Utilities
 */

document.addEventListener('DOMContentLoaded', function () {
    initScrollReveal();
});

/** Scroll Reveal — IntersectionObserver */
function initScrollReveal() {
    const els = document.querySelectorAll('.scroll-reveal');
    if (!els.length) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.15 }
    );

    els.forEach((el) => observer.observe(el));
}
