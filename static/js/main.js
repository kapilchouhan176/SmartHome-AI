// SmartHome AI - small page helpers (no frameworks needed)

// Hides flash messages automatically after 5 seconds.
function autoDismissAlerts() {
  document.querySelectorAll(".auto-dismiss").forEach((alert) => {
    setTimeout(() => bootstrap.Alert.getOrCreateInstance(alert).close(), 5000);
  });
}

// Register page: shows provider-only fields when "Provider" is chosen.
function setupRoleToggle() {
  const radios = document.querySelectorAll("input[name='role']");
  const providerFields = document.getElementById("provider-fields");
  if (!radios.length || !providerFields) return;
  const update = () => {
    const isProvider = document.querySelector("input[name='role']:checked")?.value === "provider";
    providerFields.classList.toggle("d-none", !isProvider);
  };
  radios.forEach((radio) => radio.addEventListener("change", update));
  update();
}

// Service page: allows 2-3 providers to be ticked for comparison.
function setupCompare() {
  const boxes = document.querySelectorAll(".compare-box");
  const button = document.getElementById("compare-btn");
  if (!boxes.length || !button) return;
  const update = () => {
    const count = [...boxes].filter((box) => box.checked).length;
    button.disabled = count < 2 || count > 3;
    button.textContent = `Compare (${count})`;
    boxes.forEach((box) => { box.disabled = !box.checked && count >= 3; });
  };
  boxes.forEach((box) => box.addEventListener("change", update));
  update();
}

// Booking page: updates the total when "urgent" is ticked.
function setupUrgentToggle() {
  const urgent = document.getElementById("is_urgent");
  if (!urgent) return;
  const base = parseFloat(urgent.dataset.base);
  const fee = parseFloat(urgent.dataset.fee);
  const update = () => {
    const extra = urgent.checked ? fee : 0;
    document.getElementById("urgent-amount").textContent = formatInr(extra);
    document.getElementById("total-amount").textContent = formatInr(base + extra);
  };
  urgent.addEventListener("change", update);
  update();
}

// Booking page: reloads free/booked slots when the date changes.
function setupSlotPicker() {
  const dateInput = document.getElementById("booking_date");
  const grid = document.getElementById("slot-grid");
  if (!dateInput || !grid) return;
  dateInput.addEventListener("change", async () => {
    const url = `/bookings/slots?provider_id=${grid.dataset.provider}&date=${dateInput.value}`;
    const response = await fetch(url);
    const data = await response.json();
    renderSlots(grid, data.slots || []);
  });
}

// Draws the slot buttons; booked or past slots are disabled.
function renderSlots(grid, slots) {
  grid.innerHTML = "";
  if (!slots.length) {
    grid.innerHTML = '<span class="text-danger small">Please choose a valid date.</span>';
    return;
  }
  slots.forEach((slot, index) => {
    const id = `slot-${index}`;
    grid.insertAdjacentHTML("beforeend", `
      <input type="radio" class="btn-check" name="time_slot" id="${id}" value="${slot.time}"
             ${slot.available ? "" : "disabled"} required>
      <label class="btn btn-outline-accent" for="${id}">${slot.time}</label>`);
  });
}

// Formats a number as rupees, e.g. 1499 -> ₹1,499.
function formatInr(amount) {
  return "₹" + Math.round(amount).toLocaleString("en-IN");
}

document.addEventListener("DOMContentLoaded", () => {
  autoDismissAlerts();
  setupRoleToggle();
  setupCompare();
  setupUrgentToggle();
  setupSlotPicker();
});
