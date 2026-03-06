import { initPageMotion } from "./page-motion.js";

const form = document.getElementById("contact-form");
const statusNode = document.getElementById("contact-form-status");
const submitBtn = document.getElementById("contact-submit");

initPageMotion({
  navSelector: ".contact-nav",
  revealSelector: ".motion-reveal",
});

function setStatus(message, isError = false) {
  if (!statusNode) {
    return;
  }
  statusNode.textContent = message;
  statusNode.classList.toggle("is-error", isError);
}

async function submitContactForm(event) {
  event.preventDefault();

  if (!(form instanceof HTMLFormElement)) {
    return;
  }

  const formData = new FormData(form);
  const payload = {
    name: String(formData.get("name") || "").trim(),
    email: String(formData.get("email") || "").trim(),
    subject: String(formData.get("subject") || "").trim(),
    message: String(formData.get("message") || "").trim(),
  };

  if (!payload.name || !payload.email || !payload.subject || !payload.message) {
    setStatus("Please fill all required fields.", true);
    return;
  }

  submitBtn?.setAttribute("disabled", "true");
  setStatus("Sending your message...");

  try {
    const response = await fetch("/api/v1/contact/send-email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const detail = typeof body?.detail === "string" ? body.detail : "Unable to send message now.";
      throw new Error(detail);
    }

    form.reset();
    setStatus("Message sent successfully. We'll get back to you soon.");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Something went wrong while sending.";
    setStatus(message, true);
  } finally {
    submitBtn?.removeAttribute("disabled");
  }
}

form?.addEventListener("submit", submitContactForm);
