(function () {
  var form = document.querySelector("[data-booking-form]");
  if (!form) {
    return;
  }

  var guestsInput = form.querySelector("#conference-guests");
  var budgetInput = form.querySelector("#conference-budget");
  var venueSelect = form.querySelector("#conference-venue");
  var packageSelect = form.querySelector("#conference-package");
  var services = Array.prototype.slice.call(
    form.querySelectorAll('input[name="optional_services"]')
  );
  var totalOutput = form.querySelector("[data-estimate-total]");
  var noteOutput = form.querySelector("[data-estimate-note]");
  var submitButton = form.querySelector('button[type="submit"]');

  function setSubmitBlocked(blocked) {
    submitButton.disabled = blocked;
    submitButton.title = blocked
      ? "Your selection is over your budget. Change a choice or raise your budget."
      : "";
  }

  function money(value) {
    return "Rs " + value.toLocaleString("en-US", { maximumFractionDigits: 2 });
  }

  function cost(element, guests) {
    var price = parseFloat(element.dataset.price);
    return element.dataset.basis === "per_guest" ? price * guests : price;
  }

  function chosen(select) {
    var option = select.options[select.selectedIndex];
    return option && option.value ? option : null;
  }

  function fitsGuests(option, guests) {
    var capacity = parseInt(option.dataset.capacity, 10);
    var minGuests = parseInt(option.dataset.minGuests, 10);
    var maxGuests = parseInt(option.dataset.maxGuests, 10);
    if (capacity && guests > capacity) {
      return false;
    }
    if (minGuests && guests < minGuests) {
      return false;
    }
    if (maxGuests && guests > maxGuests) {
      return false;
    }
    return true;
  }

  function cheapest(select, guests) {
    var best = null;
    Array.prototype.forEach.call(select.options, function (option) {
      if (!option.value || !fitsGuests(option, guests)) {
        return;
      }
      var value = cost(option, guests);
      best = best === null ? value : Math.min(best, value);
    });
    return best;
  }

  function updateOptions(select, guests) {
    Array.prototype.forEach.call(select.options, function (option) {
      if (!option.value) {
        return;
      }
      var available = !guests || option.selected || fitsGuests(option, guests);
      option.disabled = !available;
      option.title = available ? "" : "Not available for this attendee count";
    });
  }

  function update() {
    var guests = parseInt(guestsInput.value, 10);
    var budget = parseFloat(budgetInput.value);
    var haveGuests = guests > 0;
    var haveBudget = budget > 0;
    var venue = chosen(venueSelect);
    var pack = chosen(packageSelect);
    var picked = services.filter(function (box) {
      return box.checked;
    });

    updateOptions(venueSelect, haveGuests ? guests : 0);
    updateOptions(packageSelect, haveGuests ? guests : 0);

    if (!haveGuests) {
      setSubmitBlocked(false);
      totalOutput.textContent = "Rs 0";
      noteOutput.textContent =
        "Enter your expected attendees to see your estimate.";
      return;
    }

    var total =
      (venue ? cost(venue, guests) : 0) +
      (pack ? cost(pack, guests) : 0) +
      picked.reduce(function (sum, box) {
        return sum + cost(box, guests);
      }, 0);
    totalOutput.textContent = money(total);
    setSubmitBlocked(haveBudget && total > budget);

    var venueFloor = cheapest(venueSelect, guests);
    var packageFloor = cheapest(packageSelect, guests);

    if (venueFloor === null || packageFloor === null) {
      noteOutput.textContent =
        "No venue or package is available for this number of attendees.";
    } else if (haveBudget && venueFloor + packageFloor > budget) {
      noteOutput.textContent =
        "For " + guests + " attendees the lowest possible total is " +
        money(venueFloor + packageFloor) + ", which is above your budget.";
    } else if (!venue || !pack) {
      noteOutput.textContent = "Choose a venue and package to see your estimate.";
    } else if (haveBudget && total > budget) {
      noteOutput.textContent =
        "This selection is " + money(total - budget) +
        " over your budget. Pick a cheaper venue, package or services, or raise your budget.";
    } else if (haveBudget) {
      noteOutput.textContent =
        "Within your budget. " + money(budget - total) + " remaining.";
    } else {
      noteOutput.textContent = "Enter your budget to check this estimate.";
    }
  }

  [guestsInput, budgetInput, venueSelect, packageSelect]
    .concat(services)
    .forEach(function (element) {
      element.addEventListener("input", update);
      element.addEventListener("change", update);
    });
  update();
})();
