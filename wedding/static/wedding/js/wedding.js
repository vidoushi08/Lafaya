(function () {
  const form = document.querySelector("[data-wedding-booking-form]");
  if (!form) return;

  const packageSelect = form.querySelector("[data-wedding-package]");
  const venueSelect = form.querySelector('[name="venue"]');
  const guestsInput = form.querySelector('[name="expected_guests"]');
  const budgetInput = form.querySelector('[name="budget"]');
  const serviceInputs = form.querySelectorAll('input[name="optional_services"]');
  const totalOutput = form.querySelector("[data-wedding-estimate]");
  const noteOutput = form.querySelector("[data-wedding-estimate-note]");
  const submitButton = form.querySelector("[data-wedding-submit]");
  const formatter = new Intl.NumberFormat("en-MU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  function updateBookingDetails() {
    const guests = Number(guestsInput.value || 0);
    const selectedPackage = packageSelect.options[packageSelect.selectedIndex];
    const selectedVenue = venueSelect.options[venueSelect.selectedIndex];
    let total = selectedPackage && selectedPackage.value
      ? Number(selectedPackage.dataset.price || 0)
      : 0;

    serviceInputs.forEach((input) => {
      if (!input.checked) return;
      total += Number(input.dataset.price || 0) *
        (input.dataset.basis === "per_guest" ? guests : 1);
    });
    totalOutput.textContent = `Rs ${formatter.format(total)}`;

    const capacity = Number(selectedVenue && selectedVenue.dataset.capacity || 0);
    const minGuests = Number(selectedPackage && selectedPackage.dataset.minGuests || 0);
    const maxGuests = Number(selectedPackage && selectedPackage.dataset.maxGuests || 0);
    const tooManyForVenue = guests > 0 && capacity > 0 && guests > capacity;
    const outsidePackageRange = guests > 0 && selectedPackage && selectedPackage.value &&
      ((minGuests > 0 && guests < minGuests) || (maxGuests > 0 && guests > maxGuests));
    const budget = Number(budgetInput.value || 0);
    const overBudget = budget > 0 && total > budget;

    if (!selectedPackage || !selectedPackage.value) {
      noteOutput.textContent = "Choose a package to see your estimate. Venue costs and final pricing are confirmed by our team.";
    } else if (tooManyForVenue) {
      noteOutput.textContent = `This venue accommodates up to ${capacity} guests. Choose another venue or reduce your guest count.`;
    } else if (outsidePackageRange) {
      noteOutput.textContent = `This package is for ${minGuests}${maxGuests ? ` to ${maxGuests}` : "+"} guests. Adjust your guest count or choose another package.`;
    } else if (overBudget) {
      noteOutput.textContent = `Your package and services are Rs ${formatter.format(total - budget)} over budget. Adjust your choices or raise your budget. Venue costs are confirmed separately.`;
    } else if (budget > 0) {
      noteOutput.textContent = `Within budget, with Rs ${formatter.format(budget - total)} remaining before venue costs. Our team will confirm venue and final pricing.`;
    } else {
      noteOutput.textContent = "Venue costs and final pricing are confirmed by our team.";
    }

    submitButton.disabled = tooManyForVenue || outsidePackageRange || overBudget;
  }

  form.addEventListener("change", updateBookingDetails);
  form.addEventListener("input", updateBookingDetails);
  updateBookingDetails();
})();