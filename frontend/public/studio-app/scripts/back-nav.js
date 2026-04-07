(() => {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "ca-back-btn";
  button.setAttribute("aria-label", "Go back to previous page");
  button.title = "Back";
  button.innerHTML = `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M14.5 5.5 8 12l6.5 6.5M8.2 12h9.8"
        fill="none"
        stroke="currentColor"
        stroke-width="1.9"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
    <span>Back</span>
  `;

  button.addEventListener("click", () => {
    const inIframe = window.top && window.top !== window;

    if (inIframe) {
      try {
        const referrerUrl = document.referrer ? new URL(document.referrer) : null;
        const sameStudioFrame =
          referrerUrl &&
          referrerUrl.origin === window.location.origin &&
          referrerUrl.pathname.startsWith("/studio-app/");

        if (sameStudioFrame && window.history.length > 1) {
          window.history.back();
          return;
        }

        if (window.top.history.length > 1) {
          window.top.history.back();
          return;
        }
      } catch (_error) {
        // ignore cross-frame history issues and fallback to home
      }

      window.top.location.href = "/";
      return;
    }

    if (window.history.length > 1) {
      window.history.back();
      return;
    }

    if (document.referrer) {
      try {
        const referrerUrl = new URL(document.referrer);
        if (referrerUrl.origin === window.location.origin) {
          window.location.href = document.referrer;
          return;
        }
      } catch (_error) {
        // invalid referrer, fallback to home
      }
    }

    window.location.href = "/";
  });

  document.addEventListener("DOMContentLoaded", () => {
    document.body.appendChild(button);
  });
})();
