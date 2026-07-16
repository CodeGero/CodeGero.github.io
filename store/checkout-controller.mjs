import {pickAvailableSlot, fulfilledClaims} from "./checkout.mjs";

function readClaims(storage) {
  try {
    const parsed = JSON.parse(storage.getItem("claimed") || "[]");
    return Array.isArray(parsed) ? parsed.map(Number).filter(Number.isInteger) : [];
  } catch {
    return [];
  }
}

export function createCheckoutController({
  fetchCatalog,
  storage,
  ui,
  randomSource = Math.random,
  schedule = (fn, ms) => setTimeout(fn, ms),
  pollMs = 20_000,
}) {
  const schedulePoll = () => schedule(() => controller.poll(), pollMs);

  const controller = {
    async buy(productId) {
      try {
        const catalog = await fetchCatalog();
        const claimed = readClaims(storage);
        const slot = pickAvailableSlot(catalog, productId, claimed, randomSource);
        if (!slot) {
          ui.showError("No checkout slots are available right now. Please try again shortly.");
          return null;
        }
        claimed.push(Number(slot.slot));
        storage.setItem("claimed", JSON.stringify([...new Set(claimed)]));
        ui.showPayment(slot);
        schedulePoll();
        return slot;
      } catch {
        ui.showError("Could not start checkout. Please try again in a moment.");
        return null;
      }
    },

    async poll() {
      const claimed = readClaims(storage);
      if (claimed.length === 0) return [];
      try {
        const catalog = await fetchCatalog();
        const fulfilled = fulfilledClaims(catalog, claimed);
        if (fulfilled.length > 0) ui.showFulfillments(fulfilled);
        else schedulePoll();
        return fulfilled;
      } catch {
        ui.showError("Could not refresh payment status. Your order is saved in this browser; retrying automatically.");
        schedulePoll();
        return [];
      }
    },

    start() {
      if (readClaims(storage).length > 0) return controller.poll();
      return Promise.resolve([]);
    },
  };

  return controller;
}
