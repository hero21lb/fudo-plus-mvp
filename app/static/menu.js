const productsContainer = document.querySelector("#products");
const statusContainer = document.querySelector("#status");
const money = new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });

function showStatus(message) {
  statusContainer.textContent = message;
  statusContainer.hidden = false;
  productsContainer.hidden = true;
}

function makeCard(product) {
  const card = document.createElement("article");
  card.className = `card${product.is_available ? "" : " is-unavailable"}`;

  const image = document.createElement("div");
  image.className = "card-image";
  if (product.image_url) {
    const photo = document.createElement("img");
    photo.src = product.image_url;
    photo.alt = product.name;
    photo.loading = "lazy";
    image.append(photo);
  } else {
    const placeholder = document.createElement("span");
    placeholder.className = "image-placeholder";
    placeholder.setAttribute("aria-hidden", "true");
    placeholder.textContent = "✳";
    image.append(placeholder);
  }

  const body = document.createElement("div");
  body.className = "card-body";
  const top = document.createElement("div");
  top.className = "card-top";
  const name = document.createElement("h3");
  name.textContent = product.name;
  const price = document.createElement("span");
  price.className = "price";
  price.textContent = money.format(product.price_cents / 100);
  top.append(name, price);
  const description = document.createElement("p");
  description.textContent = product.description;
  const availability = document.createElement("span");
  availability.className = `availability${product.is_available ? "" : " unavailable"}`;
  availability.textContent = product.is_available ? "Disponible" : "Agotado";
  body.append(top, description, availability);
  const add = document.createElement("button");
  add.type = "button";
  add.textContent = "Agregar al pedido";
  add.disabled = !product.is_available;
  add.addEventListener("click", () => {
    const current = cart.get(product.id);
    if ((current?.quantity || 0) >= 100) return;
    cart.set(product.id, { product, quantity: (current?.quantity || 0) + 1 });
    renderCart();
  });
  body.append(add);
  card.append(image, body);
  return card;
}

async function loadMenu() {
  try {
    const response = await fetch("/api/products");
    if (!response.ok) throw new Error("No se pudo cargar el menú");
    const products = await response.json();
    if (products.length === 0) {
      showStatus("Todavía no hay productos publicados. Volvé a visitarnos pronto.");
      return;
    }
    productsContainer.replaceChildren(...products.map(makeCard));
    statusContainer.hidden = true;
    productsContainer.hidden = false;
  } catch {
    showStatus("No pudimos cargar el menú. Actualizá la página para volver a intentar.");
  }
}

const cart = new Map();
const checkout = document.querySelector("#checkout-form");
const submitOrder = document.querySelector("#submit-order");
let sending = false;

function renderCart() {
  const rows = [];
  let total = 0;
  for (const [id, { product, quantity }] of cart) {
    total += product.price_cents * quantity;
    const row = document.createElement("div");
    row.className = "cart-row";
    const name = document.createElement("span");
    name.textContent = `${product.name} · ${money.format(product.price_cents / 100)} c/u`;
    const amount = document.createElement("input");
    amount.type = "number";
    amount.min = "1";
    amount.max = "100";
    amount.value = quantity;
    amount.disabled = sending;
    amount.setAttribute("aria-label", `Cantidad de ${product.name}`);
    amount.addEventListener("change", () => {
      const next = Number(amount.value);
      if (Number.isInteger(next) && next >= 1 && next <= 100) cart.get(id).quantity = next;
      renderCart();
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Quitar";
    remove.disabled = sending;
    remove.setAttribute("aria-label", `Quitar ${product.name}`);
    remove.addEventListener("click", () => { cart.delete(id); renderCart(); });
    row.append(name, amount, remove);
    rows.push(row);
  }
  document.querySelector("#cart-items").replaceChildren(...(rows.length ? rows : [document.createTextNode("Todavía no agregaste productos.")]));
  document.querySelector("#cart-total").textContent = money.format(total / 100);
  submitOrder.disabled = sending || !cart.size;
}

checkout.elements.fulfillment_method.addEventListener("change", () => {
  const delivery = checkout.elements.fulfillment_method.value === "delivery";
  document.querySelector("#delivery-fields").hidden = !delivery;
  checkout.elements.delivery_address.disabled = !delivery;
  checkout.elements.delivery_address.required = delivery;
  checkout.elements.delivery_reference.disabled = !delivery;
});

checkout.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (sending || !cart.size) return;
  const result = document.querySelector("#order-result");
  const data = Object.fromEntries(new FormData(checkout));
  data.items = [...cart.values()].map(({ product, quantity }) => ({ product_id: product.id, quantity }));
  sending = true;
  renderCart();
  productsContainer.querySelectorAll("button").forEach((button) => { button.disabled = true; });
  result.textContent = "Enviando pedido…";
  try {
    const response = await fetch("/api/orders", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    const order = await response.json();
    if (!response.ok) throw new Error(typeof order.detail === "string" ? order.detail : "Revisá los datos del pedido.");
    cart.clear();
    result.textContent = `Pedido #${order.id} recibido. Total: ${money.format(order.total_cents / 100)}. ${order.payment_status === "simulated" ? "Pago simulado: no se realizó ningún cobro." : "Pago en efectivo pendiente al recibir."}`;
  } catch (error) {
    result.textContent = error instanceof TypeError ? "No pudimos confirmar la recepción. Consultá al negocio antes de volver a enviar." : error.message;
  } finally {
    sending = false;
    renderCart();
    await loadMenu();
  }
});

loadMenu();
