(function () {
  const form = document.querySelector("[data-wedding-booking-form]");
  if (!form) return;

  const packageSelect = form.querySelector("[data-wedding-package]");
  const totalOutput = form.querySelector("[data-wedding-estimate]");
  const serviceInputs = form.querySelectorAll('input[name="optional_services"]');

  function updateEstimate() {
    const selected = packageSelect.options[packageSelect.selectedIndex];
    if (!selected || !selected.value) {
      totalOutput.textContent = "Choose a package";
      return;
    }

    let total = Number(selected.dataset.price || 0);
    const guestsInput = form.querySelector('[name="expected_guests"]');
    const guests = Number(guestsInput.value || 0);
    serviceInputs.forEach((input) => {
      if (!input.checked) return;
      const quantity = input.dataset.basis === "per_guest" ? guests : 1;
      total += Number(input.dataset.price || 0) * quantity;
    });
    totalOutput.textContent = `Rs ${total.toLocaleString("en-MU", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  form.addEventListener("change", updateEstimate);
  form.addEventListener("input", updateEstimate);
  updateEstimate();
})();
