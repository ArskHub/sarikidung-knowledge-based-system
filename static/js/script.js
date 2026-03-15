/**
 * SariKidung — Main JavaScript
 * Theme: Bali Heritage Luxury · Elegant & Professional
 */

(function () {
  'use strict';

  // ── 1. SCROLL REVEAL (support .animate & .reveal) ──────────
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const delay = parseInt(entry.target.dataset.delay) || 0;
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, delay);
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  function initReveal() {
    // Support both .animate (existing) dan .reveal (baru)
    document.querySelectorAll('.animate, .reveal').forEach(el => {
      if (!el.classList.contains('from-up')    &&
          !el.classList.contains('from-down')  &&
          !el.classList.contains('from-left')  &&
          !el.classList.contains('from-right') &&
          !el.classList.contains('from-scale')) {
        el.classList.add('from-up');
      }
      revealObserver.observe(el);
    });
  }


  // ── 2. STAGGER CHILDREN ─────────────────────────────────────
  // Usage: <div class="stagger-children"> anak-anak auto delay
  function initStagger() {
    document.querySelectorAll('.stagger-children').forEach(parent => {
      Array.from(parent.children).forEach((child, i) => {
        child.style.transitionDelay = (i * 0.09) + 's';
        if (!child.classList.contains('reveal')) {
          child.classList.add('reveal', 'from-up');
        }
        revealObserver.observe(child);
      });
    });
  }


  // ── 3. ANIMATED COUNTER ─────────────────────────────────────
  function animateCounter(el, target, duration = 1800) {
    const isFloat = target % 1 !== 0;
    const suffix  = el.dataset.suffix || '';
    const prefix  = el.dataset.prefix || '';
    let start = null;

    function step(ts) {
      if (!start) start = ts;
      const prog  = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - prog, 3);
      const cur   = target * eased;
      el.textContent = prefix + (isFloat ? cur.toFixed(1) : Math.floor(cur)) + suffix;
      if (prog < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target, parseFloat(entry.target.dataset.count) || 0);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  function initCounters() {
    document.querySelectorAll('[data-count]').forEach(el => counterObserver.observe(el));
  }


  // ── 4. PARALLAX HERO ────────────────────────────────────────
  function initParallax() {
    const hero = document.querySelector('.hero-visual');
    if (!hero) return;
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          hero.style.transform = `translateY(${window.scrollY * 0.18}px)`;
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }


  // ── 5. MAGNETIC BUTTONS ─────────────────────────────────────
  function initMagnetic() {
    // Magnetic hanya pada .btn-gold dan .btn-dark, tidak pada .btn-bronze (Konsultasi)
    document.querySelectorAll('.btn-gold, .btn-dark').forEach(btn => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top  - rect.height / 2;
        btn.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
      });
      btn.addEventListener('mouseenter', () => {
        btn.style.transition = 'transform .1s ease';
      });
      btn.addEventListener('mouseleave', () => {
        btn.style.transform  = '';
        btn.style.transition = 'transform .4s cubic-bezier(.22,1,.36,1)';
      });
    });
  }


  // ── 6. CURSOR TRAIL — 6 gold dots ───────────────────────────
  function initCursorTrail() {
    if (window.innerWidth < 768) return;
    const count = 6;
    const dots  = [];
    let mouseX = 0, mouseY = 0;

    for (let i = 0; i < count; i++) {
      const dot = document.createElement('div');
      dot.style.cssText = `
        position:fixed; pointer-events:none; z-index:9999;
        width:${4 - i * 0.45}px; height:${4 - i * 0.45}px;
        border-radius:50%;
        background:rgba(200,168,75,${0.38 - i * 0.05});
        transform:translate(-50%,-50%);
        top:0; left:0; will-change:top,left;
      `;
      document.body.appendChild(dot);
      dots.push({ el: dot, x: 0, y: 0 });
    }

    window.addEventListener('mousemove', e => {
      mouseX = e.clientX; mouseY = e.clientY;
      dots[0].x = mouseX; dots[0].y = mouseY;
      dots[0].el.style.top  = mouseY + 'px';
      dots[0].el.style.left = mouseX + 'px';
    }, { passive: true });

    (function animDots() {
      for (let i = 1; i < count; i++) {
        dots[i].x += (dots[i-1].x - dots[i].x) * 0.28;
        dots[i].y += (dots[i-1].y - dots[i].y) * 0.28;
        dots[i].el.style.top  = dots[i].y + 'px';
        dots[i].el.style.left = dots[i].x + 'px';
      }
      requestAnimationFrame(animDots);
    })();

    // Sembunyikan di atas elemen interaktif
    document.querySelectorAll('a, button, input, select, textarea').forEach(el => {
      el.addEventListener('mouseenter', () => dots.forEach(d => d.el.style.opacity = '0'));
      el.addEventListener('mouseleave', () => dots.forEach(d => d.el.style.opacity = '1'));
    });
  }


  // ── 7. CARD HOVER TILT ──────────────────────────────────────
  function initTilt() {
    document.querySelectorAll('.sk-card, .feature-card, .ref-card').forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width  - 0.5;
        const y = (e.clientY - rect.top)  / rect.height - 0.5;
        card.style.transform  = `perspective(700px) rotateY(${x * 5}deg) rotateX(${-y * 5}deg) scale(1.02)`;
        card.style.boxShadow  = '0 16px 48px rgba(146,98,55,.14)';
      });
      card.addEventListener('mouseenter', () => {
        card.style.transition = 'transform .12s ease, box-shadow .2s ease';
      });
      card.addEventListener('mouseleave', () => {
        card.style.transform  = '';
        card.style.boxShadow  = '';
        card.style.transition = 'transform .5s cubic-bezier(.22,1,.36,1), box-shadow .4s ease';
      });
    });
  }


  // ── 8. SPARKLE ON CTA / HERO ────────────────────────────────
  function initSparkles() {
    // Selector universal — semua section gelap, hero, CTA, chat btn, footer
    const targets = document.querySelectorAll([
      '.cta-band',
      '.page-header',
      '.hero-cta',
      '#nav-chat-btn',
      '#nav-chat-btn-mobile',
      'header.position-relative',          // hero home
      'section[style*="background:var(--dark)"]', // quote penutup
      'footer',                             // footer
      '.container .rounded-3[style*="linear-gradient(135deg"]', // CTA banner dark
    ].join(','));

    targets.forEach(cta => {
      cta.addEventListener('mousemove', (e) => {
        if (Math.random() > 0.80) {
          const rect  = cta.getBoundingClientRect();
          const size  = 3 + Math.random() * 6;
          const spark = document.createElement('div');
          spark.style.cssText = `
            position:absolute;
            left:${e.clientX - rect.left}px;
            top:${e.clientY - rect.top}px;
            width:${size}px; height:${size}px;
            border-radius:50%;
            background:rgba(146,98,55,${(0.45 + Math.random() * 0.35).toFixed(2)});
            pointer-events:none; z-index:10;
            animation:sk-sparkle .65s ease forwards;
            transform:translate(-50%,-50%);
          `;
          // Pastikan parent bisa jadi anchor position
          const pos = window.getComputedStyle(cta).position;
          if (pos === 'static') cta.style.position = 'relative';
          cta.style.overflow = 'hidden';
          cta.appendChild(spark);
          setTimeout(() => spark.remove(), 700);
        }
      });
    });
  }


  // ── 9. NAVBAR — scroll shadow + hide/show ───────────────────
  function initNavbar() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    let lastY = 0;
    navbar.style.transition = 'box-shadow .3s ease, transform .35s cubic-bezier(.22,1,.36,1)';

    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      navbar.style.boxShadow = y > 40
        ? '0 2px 24px rgba(146,98,55,.10)'
        : 'none';
      if (y > 120) {
        if (y > lastY + 4)      navbar.style.transform = 'translateY(-100%)';
        else if (y < lastY - 4) navbar.style.transform = 'translateY(0)';
      } else {
        navbar.style.transform = 'translateY(0)';
      }
      lastY = y;
    }, { passive: true });
  }


  // ── 10. SCROLL PROGRESS BAR ─────────────────────────────────
  function initProgressBar() {
    const bar = document.createElement('div');
    bar.id = 'sk-progress';
    bar.style.cssText = `
      position:fixed; top:0; left:0; height:2px; z-index:9998;
      background:linear-gradient(90deg,#7a5028,#c9a96e,#926237,#c9a96e,#7a5028);
      background-size:300% 100%;
      width:0%; transition:width .08s linear;
      animation:sk-shimmer 3s infinite linear;
    `;
    document.body.prepend(bar);
    window.addEventListener('scroll', () => {
      const total = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (total > 0 ? (window.scrollY / total) * 100 : 0) + '%';
    }, { passive: true });
  }


  // ── 11. IMAGE LAZY FADE ─────────────────────────────────────
  function initImages() {
    const imgObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.style.transition = 'opacity .6s ease, transform .6s cubic-bezier(.22,1,.36,1)';
          img.style.opacity    = '1';
          img.style.transform  = 'scale(1)';
          imgObs.unobserve(img);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('img').forEach(img => {
      if (!img.complete) {
        img.style.opacity   = '0';
        img.style.transform = 'scale(.97)';
        imgObs.observe(img);
        img.addEventListener('load', () => {
          img.style.opacity   = '1';
          img.style.transform = 'scale(1)';
        });
      }
    });
  }


  // ── 12. BUTTON RIPPLE ───────────────────────────────────────
  function initRipple() {
    document.querySelectorAll('.btn-bronze, .btn').forEach(btn => {
      btn.addEventListener('click', function(e) {
        const rect   = this.getBoundingClientRect();
        const size   = Math.max(rect.width, rect.height);
        const ripple = document.createElement('span');
        ripple.style.cssText = `
          position:absolute; border-radius:50%; pointer-events:none;
          width:${size}px; height:${size}px;
          left:${e.clientX - rect.left - size/2}px;
          top:${e.clientY - rect.top  - size/2}px;
          background:rgba(255,255,255,.22);
          transform:scale(0);
          animation:sk-ripple .55s ease-out forwards;
        `;
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
      });
    });
  }


  // ── 13. SMOOTH ANCHOR SCROLL ────────────────────────────────
  function initSmoothLinks() {
    document.querySelectorAll('a[href^="#"]').forEach(link => {
      link.addEventListener('click', (e) => {
        const el = document.getElementById(link.getAttribute('href').slice(1));
        if (!el) return;
        e.preventDefault();
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }


  // ── 14. TABLE ROW HOVER ─────────────────────────────────────
  function initTableHover() {
    document.querySelectorAll('#kidungTable tbody tr').forEach(row => {
      row.style.transition = 'background .15s ease';
      row.addEventListener('mouseenter', () => { row.style.background = 'rgba(146,98,55,.04)'; });
      row.addEventListener('mouseleave', () => { row.style.background = ''; });
    });
  }


  // ── 15. BOOTSTRAP TOOLTIPS ──────────────────────────────────
  function initTooltips() {
    if (typeof bootstrap === 'undefined') return;
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
      new bootstrap.Tooltip(el);
    });
  }


  // ── INJECT CSS ──────────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById('sk-anim-styles')) return;
    const s = document.createElement('style');
    s.id = 'sk-anim-styles';
    s.textContent = `
      html { scroll-behavior: smooth; }

      /* Page entrance */
      body { animation: sk-pagein .45s ease forwards; }
      @keyframes sk-pagein { from { opacity:0; } to { opacity:1; } }

      /* ── REVEAL BASE ── */
      .animate, .reveal {
        transition: opacity .7s ease, transform .7s cubic-bezier(.165,.84,.44,1);
      }

      /* Directions */
      .from-up    { opacity:0; transform: translateY(28px); }
      .from-down  { opacity:0; transform: translateY(-28px); }
      .from-left  { opacity:0; transform: translateX(-32px); }
      .from-right { opacity:0; transform: translateX(32px); }
      .from-scale { opacity:0; transform: scale(.93); }

      /* Visible state */
      .animate.visible,
      .reveal.visible {
        opacity:1 !important;
        transform: none !important;
      }

      /* Gold heading shimmer: disabled */

      /* Scroll progress shimmer */
      @keyframes sk-shimmer {
        0%   { background-position: 300% 0; }
        100% { background-position: -300% 0; }
      }

      /* Ripple */
      @keyframes sk-ripple {
        to { transform: scale(2.8); opacity:0; }
      }

      /* Sparkle */
      @keyframes sk-sparkle {
        0%   { transform:translate(-50%,-50%) scale(0); opacity:1; }
        60%  { transform:translate(-50%,-60%) scale(1.4); opacity:.7; }
        100% { transform:translate(-50%,-80%) scale(0); opacity:0; }
      }

      /* Table row fade on search */
      @keyframes sk-rowfade {
        from { opacity:0; transform:translateX(-5px); }
        to   { opacity:1; transform:translateX(0); }
      }

      /* Focus ring */
      *:focus-visible {
        outline: 2px solid rgba(146,98,55,.45);
        outline-offset: 3px;
        border-radius: 4px;
      }

      /* Text selection */
      ::selection {
        background: rgba(146,98,55,.18);
        color: inherit;
      }

      /* Nav link transition */
      .nav-link { transition: color .18s ease !important; }

      /* Gold dot pulse */
      .sk-pulse {
        animation: sk-dot-pulse 2.2s ease infinite;
      }
      @keyframes sk-dot-pulse {
        0%, 100% { opacity:1; transform:scale(1); }
        50%       { opacity:.6; transform:scale(1.2); }
      }
    `;
    document.head.appendChild(s);
  }


  // ── RE-INIT untuk dynamic content ───────────────────────────
  window.initAnimations = function () {
    initReveal();
    initStagger();
    initCounters();
    initTilt();
    initImages();
    initTableHover();
  };

  // MutationObserver untuk konten dinamis (CRUD admin, filter)
  const mutObs = new MutationObserver(() => {
    initReveal();
    initTilt();
    initMagnetic();
    initTableHover();
  });


  // ── INIT ────────────────────────────────────────────────────
  function init() {
    injectStyles();
    initReveal();
    initStagger();
    initCounters();
    initParallax();
    initMagnetic();
    initCursorTrail();
    initTilt();
    initSparkles();
    initNavbar();
    initProgressBar();
    initImages();
    initRipple();
    initSmoothLinks();
    initTableHover();
    initTooltips();

    mutObs.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();


// ── LIBRARY SEARCH (dipanggil via onkeyup) ───────────────────
function searchTable() {
  const input = document.getElementById("searchInput");
  if (!input) return;
  const filter = input.value.toUpperCase().trim();
  const rows   = document.querySelectorAll("#kidungTable tbody tr");
  const noRes  = document.getElementById("noResult");
  let   count  = 0;

  rows.forEach(row => {
    const vis = (row.textContent || row.innerText).toUpperCase().includes(filter);
    if (vis) {
      row.style.display   = '';
      row.style.animation = 'sk-rowfade .22s ease forwards';
      count++;
    } else {
      row.style.display = 'none';
    }
  });

  if (noRes) noRes.classList.toggle("d-none", count > 0);
}