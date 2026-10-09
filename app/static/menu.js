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

loadMenu();
