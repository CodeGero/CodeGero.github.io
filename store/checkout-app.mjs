import {createCheckoutController} from "./checkout-controller.mjs";
import {renderFulfillment} from "./checkout.mjs";

const box = document.getElementById("order-box");

function clearBox() {
  box.replaceChildren();
  box.style.display = "block";
}

function addLine(text, className = "") {
  const line = document.createElement("p");
  line.textContent = text;
  if (className) line.className = className;
  box.appendChild(line);
  return line;
}

const ui = {
  showPayment(slot) {
    clearBox();
    addLine(`Order slot ${slot.slot} is reserved in this browser.`, "order-title");
    addLine(`Send exactly ${Number(slot.amount).toFixed(8)} BTC to:`);
    const address = document.createElement("code");
    address.textContent = String(slot.address);
    address.className = "order-address";
    box.appendChild(address);
    addLine("Keep this browser open or return on the same device. Payment status refreshes every 20 seconds after blockchain confirmation.", "order-note");
  },

  showFulfillments(slots) {
    clearBox();
    addLine("Payment confirmed — delivery ready.", "order-title");
    for (const slot of slots) {
      const view = renderFulfillment(slot);
      addLine(view.text);
      if (view.code) {
        const key = document.createElement("code");
        key.textContent = view.code;
        key.className = "license-key";
        box.appendChild(key);
        addLine("Activate with: devflow activate YOUR-LICENSE-KEY", "order-note");
      }
      if (view.href) {
        const link = document.createElement("a");
        link.href = view.href;
        link.textContent = "Download your purchase";
        link.className = "buy";
        link.rel = "noopener";
        box.appendChild(link);
      }
    }
  },

  showError(message) {
    if (box.style.display !== "block") clearBox();
    addLine(message, "order-error");
  },
};

async function fetchCatalog() {
  const response = await fetch(`orders_catalog.json?ts=${Date.now()}`, {cache: "no-store"});
  if (!response.ok) throw new Error(`catalog HTTP ${response.status}`);
  const data = await response.json();
  if (!Array.isArray(data)) throw new Error("catalog is not an array");
  return data;
}

const controller = createCheckoutController({
  fetchCatalog,
  storage: window.localStorage,
  ui,
});

window.buy = (productId) => controller.buy(productId);
controller.start();
