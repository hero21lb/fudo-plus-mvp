const form = document.querySelector("#login-form");
const message = document.querySelector("#login-message");
const button = document.querySelector("#login-button");
const field = (name) => form.elements.namedItem(name);
const oauthMessage = document.querySelector("#oauth-message");

const loginErrors = {
  cancelled: "Se canceló el ingreso con Google.",
  unauthorized: "Ese correo de Google no está habilitado para administrar este negocio.",
};
const loginError = new URLSearchParams(window.location.search).get("error");
if (loginErrors[loginError]) {
  oauthMessage.textContent = loginErrors[loginError];
  oauthMessage.hidden = false;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  message.hidden = true;
  try {
    const response = await fetch("/api/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: field("username").value.trim(),
        password: field("password").value,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "No se pudo ingresar.");
    window.location.assign("/admin");
  } catch (error) {
    message.textContent = error.message || "No se pudo ingresar. Intentá de nuevo.";
    message.hidden = false;
    button.disabled = false;
  }
});
