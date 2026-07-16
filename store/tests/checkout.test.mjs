import test from "node:test";
import assert from "node:assert/strict";

import {
  pickAvailableSlot,
  fulfilledClaims,
  renderFulfillment,
} from "../checkout.mjs";

const catalog = [
  {slot: 1, product_id: "devflow-premium", fulfilled: false, address: "bc1-a", amount: 0.0001},
  {slot: 2, product_id: "devflow-premium", fulfilled: false, address: "bc1-b", amount: 0.0001},
  {slot: 3, product_id: "devflow-premium", fulfilled: true, address: "bc1-c", amount: 0.0001, key: "KRYP-PAID"},
  {slot: 4, product_id: "other", fulfilled: false, address: "bc1-d", amount: 0.0002},
];

test("pickAvailableSlot excludes fulfilled, wrong-product, and browser-claimed slots", () => {
  const chosen = pickAvailableSlot(catalog, "devflow-premium", [1], () => 0);
  assert.equal(chosen.slot, 2);
});

test("pickAvailableSlot uses the supplied random source instead of always selecting the first slot", () => {
  const chosen = pickAvailableSlot(catalog, "devflow-premium", [], () => 0.99);
  assert.equal(chosen.slot, 2);
});

test("pickAvailableSlot returns null when no usable slot remains", () => {
  assert.equal(pickAvailableSlot(catalog, "devflow-premium", [1, 2], () => 0.5), null);
});

test("fulfilledClaims returns only fulfilled records claimed by this browser", () => {
  const result = fulfilledClaims(catalog, [2, 3, 999]);
  assert.deepEqual(result.map((item) => item.slot), [3]);
});

test("renderFulfillment renders a license key without interpreting catalog HTML", () => {
  const view = renderFulfillment({slot: 3, product: "DevFlow <b>Premium</b>", key: "KRYP-<script>"});
  assert.match(view.text, /DevFlow <b>Premium<\/b>/);
  assert.equal(view.code, "KRYP-<script>");
  assert.equal(view.href, null);
});

test("renderFulfillment accepts only HTTPS download links", () => {
  assert.equal(renderFulfillment({slot: 4, product: "File", download: "javascript:alert(1)"}).href, null);
  assert.equal(renderFulfillment({slot: 5, product: "File", download: "https://example.com/file.zip"}).href, "https://example.com/file.zip");
});
