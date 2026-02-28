/**
 * SariKidung — Main JavaScript
 * Theme: Bali Heritage Minimalis
 */

document.addEventListener("DOMContentLoaded", function () {

    // ── 1. INTERSECTION OBSERVER ANIMATION ──────────────────
    const animEls = document.querySelectorAll('.animate');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity   = "1";
                entry.target.style.transform = "translateY(0)";
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08 });

    animEls.forEach(el => {
        el.style.opacity    = "0";
        el.style.transform  = "translateY(22px)";
        el.style.transition = "opacity .75s ease, transform .75s cubic-bezier(.165,.84,.44,1)";
        observer.observe(el);
    });

    // ── 2. NAVBAR SCROLL EFFECT ──────────────────────────────
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        const onScroll = () => {
            if (window.scrollY > 40) {
                navbar.style.boxShadow = "0 2px 18px rgba(0,0,0,.08)";
            } else {
                navbar.style.boxShadow = "none";
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
    }

    // ── 3. BOOTSTRAP TOOLTIPS ────────────────────────────────
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });

});

// ── 4. LIBRARY SEARCH (called via onkeyup) ───────────────────
function searchTable() {
    const input  = document.getElementById("searchInput");
    if (!input) return;
    const filter = input.value.toUpperCase().trim();
    const rows   = document.querySelectorAll("#kidungTable tbody tr");
    const noRes  = document.getElementById("noResult");
    let count    = 0;

    rows.forEach(row => {
        const text = (row.textContent || row.innerText).toUpperCase();
        const vis  = text.includes(filter);
        row.style.display = vis ? "" : "none";
        if (vis) count++;
    });

    if (noRes) noRes.classList.toggle("d-none", count > 0);
}