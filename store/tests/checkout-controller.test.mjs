import test from "node:test";
import assert from "node:assert/strict";

import {createCheckoutController} from "../checkout-controller.mjs";

function memoryStorage(initial = {}) {
  const state = {...initial};
  return {
    getItem(key) { return Object.hasOwn(state, key) ? state[key] : null; },
    setItem(key, value) { state[key] = String(value); },
    snapshot() { return {...state}; },
  };
}

const pending = {slot: 8, product_id: "devflow-premium", fulfilled: false, address: "bc1-order", amount: 0.00014044, usd: 9};
const paid = {...pending, fulfilled: true, paid: true, key: "KRYP-REAL-KEY", product: "DevFlow Premium"};

test("buy reserves a browser-local slot, renders payment, and schedules fulfillment polling", async () => {
  const storage = memoryStorage();
  const shown = [];
  const timers = [];
  const controller = createCheckoutController({
    fetchCatalog: async () => [pending],
    storage,
    randomSource: () => 0,
    schedule: (fn, ms) => timers.push({fn, ms}),
    ui: {showPayment: (slot) => shown.push(slot), showError() {}, showFulfillments() {}},
  });

  const slot = await controller.buy("devflow-premium");

  assert.equal(slot.slot, 8);
  assert.deepEqual(JSON.parse(storage.snapshot().claimed), [8]);
  assert.deepEqual(shown.map((item) => item.slot), [8]);
  assert.equal(timers.length, 1);
  assert.equal(timers[0].ms, 20_000);
});

test("poll reveals fulfilled records claimed by this browser", async () => {
  const storage = memoryStorage({claimed: JSON.stringify([8])});
  const deliveries = [];
  const controller = createCheckoutController({
    fetchCatalog: async () => [paid],
    storage,
    schedule() {},
    ui: {showPayment() {}, showError() {}, showFulfillments: (items) => deliveries.push(items)},
  });

  const result = await controller.poll();

  assert.equal(result.length, 1);
  assert.equal(result[0].key, "KRYP-REAL-KEY");
  assert.equal(deliveries[0][0].slot, 8);
});

test("poll preserves the claimed order after transient fetch failures", async () => {
  const storage = memoryStorage({claimed: JSON.stringify([8])});
  const errors = [];
  const controller = createCheckoutController({
    fetchCatalog: async () => { throw new Error("offline"); },
    storage,
    schedule() {},
    ui: {showPayment() {}, showFulfillments() {}, showError: (message) => errors.push(message)},
  });

  const result = await controller.poll();

  assert.deepEqual(result, []);
  assert.deepEqual(JSON.parse(storage.snapshot().claimed), [8]);
  assert.match(errors[0], /payment status/i);
});

test("corrupt local storage cannot crash checkout", async () => {
  const storage = memoryStorage({claimed: "not-json"});
  const controller = createCheckoutController({
    fetchCatalog: async () => [pending],
    storage,
    randomSource: () => 0,
    schedule() {},
    ui: {showPayment() {}, showFulfillments() {}, showError() {}},
  });

  const slot = await controller.buy("devflow-premium");
  assert.equal(slot.slot, 8);
});
