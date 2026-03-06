function userPrefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function enableNavScrollState(navSelector) {
  const nav = document.querySelector(navSelector);
  if (!nav) {
    return;
  }

  const sync = () => {
    nav.classList.toggle("is-scrolled", window.scrollY > 8);
  };

  sync();
  window.addEventListener("scroll", sync, { passive: true });
}

export function initPageMotion({
  navSelector,
  revealSelector = ".motion-reveal",
  revealThreshold = 0.18,
  revealRootMargin = "0px 0px -10% 0px",
  staggerStep = 55,
  maxStagger = 280,
} = {}) {
  if (navSelector) {
    enableNavScrollState(navSelector);
  }

  const revealNodes = Array.from(document.querySelectorAll(revealSelector));
  if (!revealNodes.length) {
    return;
  }

  const reducedMotion = userPrefersReducedMotion();
  if (reducedMotion || !("IntersectionObserver" in window)) {
    for (const node of revealNodes) {
      node.classList.add("in");
    }
    return;
  }

  for (const [index, node] of revealNodes.entries()) {
    node.style.setProperty("--reveal-delay", `${Math.min(index * staggerStep, maxStagger)}ms`);
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) {
          continue;
        }
        entry.target.classList.add("in");
        observer.unobserve(entry.target);
      }
    },
    {
      threshold: revealThreshold,
      rootMargin: revealRootMargin,
    },
  );

  for (const node of revealNodes) {
    observer.observe(node);
  }
}
