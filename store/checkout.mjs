function safeText(value) {
  return String(value ?? "");
}

export function pickAvailableSlot(catalog, productId, claimedSlots, randomSource = Math.random) {
  const claimed = new Set((claimedSlots ?? []).map(Number));
  const available = (catalog ?? []).filter((slot) =>
    slot &&
    slot.product_id === productId &&
    slot.fulfilled !== true &&
    Number.isInteger(Number(slot.slot)) &&
    !claimed.has(Number(slot.slot)) &&
    typeof slot.address === "string" &&
    Number(slot.amount) > 0
  );
  if (available.length === 0) return null;
  const raw = Number(randomSource());
  const bounded = Number.isFinite(raw) ? Math.min(Math.max(raw, 0), 0.999999999999) : 0;
  return available[Math.floor(bounded * available.length)];
}

export function fulfilledClaims(catalog, claimedSlots) {
  const claimed = new Set((claimedSlots ?? []).map(Number));
  return (catalog ?? []).filter((slot) =>
    slot && slot.fulfilled === true && claimed.has(Number(slot.slot)) && (slot.key || slot.download)
  );
}

export function renderFulfillment(slot) {
  const rawHref = typeof slot?.download === "string" ? slot.download : "";
  const href = rawHref.startsWith("https://") ? rawHref : null;
  return {
    text: safeText(slot?.product || slot?.product_id || `Order ${slot?.slot ?? ""}`),
    code: slot?.key ? safeText(slot.key) : null,
    href,
  };
}
