/* Subtle interactions: scroll progress + reveal-on-scroll + project filtering */
(function () {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  // Scroll progress bar
  const progressEl = $(".progress");
  const updateProgress = () => {
    if (!progressEl) return;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const height = document.documentElement.scrollHeight - window.innerHeight;
    const pct = height > 0 ? Math.max(0, Math.min(1, scrollTop / height)) : 0;
    progressEl.style.width = `${pct * 100}%`;
  };
  updateProgress();
  window.addEventListener("scroll", updateProgress, { passive: true });

  // Reduced motion handling (also respects CSS prefers-reduced-motion)
  const media = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  if (media && media.matches) {
    document.documentElement.classList.add("reduced-motion");
  }

  // Reveal on scroll (IntersectionObserver)
  const revealEls = $$(".reveal");
  // Stagger reveal timing for a more premium "data dashboard" feel.
  revealEls.forEach((el, i) => el.style.setProperty("--reveal-delay", `${i * 65}ms`));
  if ("IntersectionObserver" in window && revealEls.length) {
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.12 }
    );

    revealEls.forEach((el) => io.observe(el));
  } else {
    // Fallback: make visible
    revealEls.forEach((el) => el.classList.add("is-visible"));
  }

  // Footer year
  const yearEl = $("#year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  // Project filtering
  const selectEl = $("#projectFilter");
  const cards = $$("#projectGrid .project-card");
  const animateHide = (card) => {
    card.style.display = "";
    card.style.transition = "opacity 180ms ease, transform 180ms ease, filter 180ms ease";
    card.style.opacity = "0";
    card.style.transform = "translateY(10px)";
    card.style.filter = "blur(3px)";
    card.style.pointerEvents = "none";

    window.setTimeout(() => {
      card.style.display = "none";
      card.style.opacity = "";
      card.style.transform = "";
      card.style.filter = "";
      card.style.pointerEvents = "";
      card.style.transition = "";
    }, 200);
  };

  const animateShow = (card) => {
    card.style.display = "";
    card.style.transition = "opacity 180ms ease, transform 180ms ease, filter 180ms ease";
    card.style.opacity = "0";
    card.style.transform = "translateY(10px)";
    card.style.filter = "blur(3px)";
    card.style.pointerEvents = "";

    requestAnimationFrame(() => {
      card.style.opacity = "1";
      card.style.transform = "translateY(0px)";
      card.style.filter = "blur(0px)";
    });

    window.setTimeout(() => {
      card.style.opacity = "";
      card.style.transform = "";
      card.style.filter = "";
      card.style.transition = "";
    }, 210);
  };

  const applyFilter = () => {
    const val = selectEl ? selectEl.value : "all";
    for (const card of cards) {
      const tags = (card.getAttribute("data-tags") || "").split(",").map((t) => t.trim());
      const show = val === "all" || tags.includes(val) || tags.includes("data") && val === "data";
      const showNormalized =
        val === "all" ||
        tags.includes(val) ||
        (val === "data" && tags.includes("data")) ||
        (val === "backend" && tags.includes("backend")) ||
        (val === "llm" && tags.includes("llm"));

      if (showNormalized) animateShow(card);
      else animateHide(card);
    }
  };

  if (selectEl && cards.length) {
    selectEl.addEventListener("change", applyFilter);
    applyFilter();
  }

  // Animated counters (Data Snapshot)
  const counters = $$(".counter[data-target]");
  const animateCounter = (el) => {
    const target = Number(el.getAttribute("data-target") || "0");
    const start = 0;
    const durationMs = 900;
    const startTs = performance.now();

    const tick = (ts) => {
      const t = Math.min(1, (ts - startTs) / durationMs);
      // Ease-out for a smoother “sexy” feel
      const eased = 1 - Math.pow(1 - t, 3);
      const value = Math.round(start + (target - start) * eased);
      el.textContent = String(value);
      if (t < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
  };

  if (counters.length && "IntersectionObserver" in window) {
    const counterIO = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            counterIO.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.28 }
    );
    counters.forEach((c) => counterIO.observe(c));
  } else {
    // Fallback: just fill
    counters.forEach((c) => animateCounter(c));
  }
})();

