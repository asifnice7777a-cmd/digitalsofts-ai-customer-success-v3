const API_BASE = "";
const sessionId = crypto.randomUUID();

const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const loadingIndicator = document.getElementById("loadingIndicator");
const resetBtn = document.getElementById("resetBtn");
const sendBtn = document.getElementById("sendBtn");

function appendMessage(role, text, agent) {
  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;
  const label = role === "user" ? "You" : `Assistant${agent ? " (" + agent + ")" : ""}`;
  bubble.innerHTML = `<span class="msg-label">${label}</span><p></p>`;
  bubble.querySelector("p").textContent = text;
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function setLoading(isLoading) {
  loadingIndicator.classList.toggle("hidden", !isLoading);
  sendBtn.disabled = isLoading;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  messageInput.value = "";
  setLoading(true);

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
    const data = await response.json();
    appendMessage("assistant", data.reply, data.agent);
  } catch (error) {
    appendMessage("assistant", "Sorry, something went wrong. Please try again.");
    console.error("Chat error:", error);
  } finally {
    setLoading(false);
  }
});

resetBtn.addEventListener("click", async () => {
  setLoading(true);
  try {
    await fetch(`${API_BASE}/reset-session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
    chatWindow.innerHTML = "";
    appendMessage("assistant", "Session has been reset. How can I help you today?");
  } catch (error) {
    console.error("Reset error:", error);
  } finally {
    setLoading(false);
  }
});

window.addEventListener("DOMContentLoaded", () => {
  appendMessage("assistant", "Hi! I'm the DigitalSofts AI assistant. Ask me about our services, pricing, technical capabilities, or book a meeting.");
});

/* ============================================================
   Floating chat widget — open/close behavior only.
   No chat API logic is touched above this point; this section
   only toggles visibility of the existing widget markup and,
   the first time it opens, focuses the existing message input.
   ============================================================ */
(function initChatWidget() {
  const launcher = document.getElementById("chatLauncher");
  const widget = document.getElementById("chatWidget");
  const closeBtn = document.getElementById("closeChatBtn");
  const heroCta = document.getElementById("heroChatCta");

  function openWidget() {
    widget.classList.remove("hidden");
    launcher.classList.add("is-open");
    launcher.setAttribute("aria-expanded", "true");
    setTimeout(() => messageInput.focus(), 150);
  }

  function closeWidget() {
    widget.classList.add("hidden");
    launcher.classList.remove("is-open");
    launcher.setAttribute("aria-expanded", "false");
  }

  function toggleWidget() {
    if (widget.classList.contains("hidden")) {
      openWidget();
    } else {
      closeWidget();
    }
  }

  launcher.addEventListener("click", toggleWidget);
  closeBtn.addEventListener("click", closeWidget);

  if (heroCta) {
    heroCta.addEventListener("click", () => {
      if (widget.classList.contains("hidden")) openWidget();
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !widget.classList.contains("hidden")) {
      closeWidget();
    }
  });
})();

/* ============================================================
   Contact form — front-end only, no backend endpoint exists for
   this form, so it simply shows a confirmation message locally
   rather than calling an API.
   ============================================================ */
(function initContactForm() {
  const contactForm = document.getElementById("contactForm");
  const contactConfirm = document.getElementById("contactConfirm");
  if (!contactForm) return;

  contactForm.addEventListener("submit", (event) => {
    event.preventDefault();
    contactConfirm.classList.remove("hidden");
    contactForm.reset();
  });
})();
