const list = document.querySelector("#product-list");
const form = document.querySelector("#product-form");
const status = document.querySelector("#status");
const saveButton = document.querySelector("#save-product");
const money = new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" });
let csrfToken = "";
let products = [];
let editingId = null;
const field = (name) => form.elements.namedItem(name);

function notify(message, isError = false) {
  status.textContent = message;
  status.classList.toggle("error", isError);
  status.hidden = false;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (response.status === 401) {
    window.location.assign("/admin/login");
    throw new Error("La sesión terminó. Volvé a ingresar.");
  }
  const body = await response.json();
  if (!response.ok) {
    throw new Error(typeof body.detail === "string" ? body.detail : "No se pudo completar la operación.");
  }
  return body;
}

function formData() {
  const price = Number(field("price").value);
  if (!Number.isFinite(price) || price < 0) throw new Error("Ingresá un precio válido.");
  const image = field("image_url").value.trim();
  if (image && !image.startsWith("https://")) throw new Error("La foto debe usar una URL HTTPS.");
  return {
    name: field("name").value.trim(),
    description: field("description").value.trim(),
    image_url: image || null,
    price_cents: Math.round(price * 100),
    is_published: field("is_published").checked,
    is_available: field("is_available").checked,
  };
}

function resetEditor() {
  editingId = null;
  form.reset();
  field("is_available").checked = true;
  document.querySelector("#editor-title").textContent = "Nuevo producto";
  document.querySelector("#cancel-edit").hidden = true;
  saveButton.textContent = "Guardar producto";
}

function editProduct(product) {
  editingId = product.id;
  field("name").value = product.name;
  field("description").value = product.description;
  field("image_url").value = product.image_url || "";
  field("price").value = (product.price_cents / 100).toFixed(2);
  field("is_published").checked = product.is_published;
  field("is_available").checked = product.is_available;
  document.querySelector("#editor-title").textContent = "Editar producto";
  document.querySelector("#cancel-edit").hidden = false;
  saveButton.textContent = "Guardar cambios";
  document.querySelector("#editor-title").scrollIntoView({ behavior: "smooth", block: "start" });
  field("name").focus();
}

function productCard(product) {
  const card = document.createElement("article");
  card.className = "admin-product";
  const image = document.createElement("div");
  image.className = "product-thumb";
  if (product.image_url) {
    const img = document.createElement("img");
    img.src = product.image_url;
    img.alt = "";
    image.append(img);
  } else {
    image.textContent = "✳";
  }
  const content = document.createElement("div");
  content.className = "product-copy";
  const name = document.createElement("h3");
  name.textContent = product.name;
  const detail = document.createElement("p");
  detail.textContent = `${money.format(product.price_cents / 100)} · ${product.is_published ? "Publicado" : "Borrador"}`;
  const badges = document.createElement("div");
  badges.className = "badges";
  const availability = document.createElement("span");
  availability.className = `badge ${product.is_available ? "positive" : "negative"}`;
  availability.textContent = product.is_available ? "Disponible" : "Agotado";
  badges.append(availability);
  content.append(name, detail, badges);
  const actions = document.createElement("div");
  actions.className = "product-actions";
  const edit = document.createElement("button");
  edit.type = "button";
  edit.textContent = "Editar";
  edit.addEventListener("click", () => editProduct(product));
  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.textContent = product.is_available ? "Marcar agotado" : "Marcar disponible";
  toggle.addEventListener("click", async () => {
    toggle.disabled = true;
    try {
      await api(`/api/admin/products/${product.id}`, {
        method: "PUT",
        headers: { "X-CSRF-Token": csrfToken },
        body: JSON.stringify({ ...product, is_available: !product.is_available }),
      });
      await loadProducts();
      notify("Disponibilidad actualizada en el menú público.");
    } catch (error) {
      notify(error.message, true);
      toggle.disabled = false;
    }
  });
  actions.append(edit, toggle);
  card.append(image, content, actions);
  return card;
}

function renderProducts() {
  document.querySelector("#total-count").textContent = products.length;
  document.querySelector("#published-count").textContent = products.filter((p) => p.is_published).length;
  document.querySelector("#available-count").textContent = products.filter((p) => p.is_available).length;
  document.querySelector("#list-count").textContent = `${products.length} en total`;
  if (products.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Todavía no hay productos. Cargá el primero con el formulario.";
    list.replaceChildren(empty);
  } else {
    list.replaceChildren(...products.map(productCard));
  }
}

async function loadProducts() {
  products = await api("/api/admin/products");
  renderProducts();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  saveButton.disabled = true;
  status.hidden = true;
  try {
    const data = formData();
    await api(editingId ? `/api/admin/products/${editingId}` : "/api/admin/products", {
      method: editingId ? "PUT" : "POST",
      headers: { "X-CSRF-Token": csrfToken },
      body: JSON.stringify(data),
    });
    await loadProducts();
    resetEditor();
    notify("Producto guardado. El menú público ya refleja los cambios.");
  } catch (error) {
    notify(error.message, true);
  } finally {
    saveButton.disabled = false;
  }
});

document.querySelector("#new-product").addEventListener("click", () => { resetEditor(); field("name").focus(); });
document.querySelector("#cancel-edit").addEventListener("click", resetEditor);
document.querySelector("#logout").addEventListener("click", async () => {
  try {
    await api("/api/admin/logout", { method: "POST", headers: { "X-CSRF-Token": csrfToken } });
    window.location.assign("/admin/login");
  } catch (error) { notify(error.message, true); }
});

(async () => {
  try {
    const session = await api("/api/admin/session");
    csrfToken = session.csrf_token;
    await loadProducts();
    await loadOrders();
  } catch (error) {
    notify(error.message, true);
  }
})();

const orderLabels = { pending: "Pendiente", confirmed: "Confirmado", preparing: "En preparación", ready: "Listo", completed: "Completado", cancelled: "Cancelado", approved: "Aprobado", rejected: "Rechazado", simulated: "Simulado (sin cobro)", cash: "Efectivo", online: "Online" };
async function loadOrders() {
  const container = document.querySelector("#order-list");
  const refresh = document.querySelector("#refresh-orders");
  refresh.disabled = true;
  try {
    const orders = await api("/api/admin/orders");
    const cards = orders.map((order) => {
      const card = document.createElement("article");
      card.className = "order-ticket";
      const title = document.createElement("h3");
      title.textContent = `Pedido #${order.id} · ${orderLabels[order.status] || order.status}`;
      card.append(title);
      const lines = [
        new Date(order.created_at).toLocaleString("es-AR"),
        `${order.customer_name} · ${order.customer_phone}`,
        order.fulfillment_method === "delivery" ? `Delivery: ${order.delivery_address}` : "Retiro en el local",
        ...(order.delivery_reference ? [`Referencia: ${order.delivery_reference}`] : []),
        ...order.items.map((item) => `${item.quantity} × ${item.product_name} · ${money.format(item.line_total_cents / 100)}`),
        `Total: ${money.format(order.total_cents / 100)}`,
        `Pago: ${orderLabels[order.payment_method]} · ${orderLabels[order.payment_status]}`,
      ];
      for (const text of lines) {
        const line = document.createElement("p");
        line.textContent = text;
        card.append(line);
      }
      return card;
    });
    container.replaceChildren(...(cards.length ? cards : [document.createTextNode("Todavía no hay pedidos.")]));
  } catch (error) {
    container.textContent = error.message;
  } finally {
    refresh.disabled = false;
  }
}
document.querySelector("#refresh-orders").addEventListener("click", loadOrders);
