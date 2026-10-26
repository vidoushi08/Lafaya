(function () {
  var VISIBLE_COUNT = 3;

  document.querySelectorAll("[data-explore-toggle]").forEach(function (button) {
    var list = document.getElementById(button.dataset.exploreToggle);
    if (!list) {
      return;
    }

    var items = Array.prototype.filter.call(list.children, function (child) {
      return child.tagName === "ARTICLE";
    });
    if (items.length <= VISIBLE_COUNT) {
      button.hidden = false;
      button.addEventListener("click", function () {
        var form = document.getElementById("car-events-enquiry");
        if (form) {
          form.scrollIntoView({ behavior: "smooth" });
        }
      });
      return;
    }

    var label = button.querySelector("span");
    var expanded = false;

    function render() {
      items.forEach(function (item, index) {
        item.hidden = !expanded && index >= VISIBLE_COUNT;
      });
      label.textContent = expanded
        ? button.dataset.labelLess
        : button.dataset.labelMore;
      button.setAttribute("aria-expanded", String(expanded));
      button.classList.toggle("is-expanded", expanded);
    }

    button.hidden = false;
    button.addEventListener("click", function () {
      expanded = !expanded;
      render();
    });
    render();
  });
})();

// Decorative racing pairs are independent of booking and pricing logic.
(function carEventsRacingEffect() {
  var carEventsLayer = document.querySelector('.car-events-racing-layer');
  if (!carEventsLayer || !document.querySelector('.car-events-page') ||
      typeof carEventsLayer.animate !== 'function') return;

  var carEventsMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var carEventsMobile = window.matchMedia('(max-width: 600px)');
  var carEventsAnimations = [];
  var carEventsAway = false;
  var carEventsResizeFrame = null;

  function carEventsClearRace() {
    carEventsAnimations.forEach(function (animation) { animation.cancel(); });
    carEventsAnimations = [];
    carEventsLayer.replaceChildren();
  }

  function carEventsPauseRace() {
    carEventsAnimations.forEach(function (animation) {
      if (document.hidden || carEventsAway) animation.pause();
      else animation.play();
    });
  }

  function carEventsBuildRace() {
    carEventsClearRace();
    if (carEventsMotion.matches || carEventsAway) return;
    var count = carEventsMobile.matches ? 2 : 4;
    for (var index = 0; index < count; index++) {
      var car = document.createElement('span');
      car.className = 'car-events-racing-car car-events-racing-car-' + (index + 1);
      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 64 26');
      svg.setAttribute('aria-hidden', 'true');
      svg.setAttribute('focusable', 'false');
      svg.innerHTML = '<path class="car-events-racing-body" d="M5 17v-5l10-2 9-7h19l10 8 7 2v6H5z"/>' +
        '<path d="m20 10 7-5h13l7 6H20zm12-5v6M7 15h5m42 0h5"/>' +
        '<circle cx="17" cy="19" r="5"/><circle cx="49" cy="19" r="5"/>' +
        '<circle cx="17" cy="19" r="2"/><circle cx="49" cy="19" r="2"/>' +
        '<path class="car-events-racing-speed" d="M0 6h12M0 11h7M0 21h6"/>';
      car.appendChild(svg);
      carEventsLayer.appendChild(car);
      var animation = car.animate([
        { transform: 'translate3d(-90px,0,0)', opacity: 0, offset: 0 },
        { opacity: 0.8, offset: 0.08 },
        { opacity: 0.8, offset: 0.92 },
        { transform: 'translate3d(' + (window.innerWidth + 90) + 'px,0,0)', opacity: 0, offset: 1 }
      ], { duration: [11500, 9000, 12500, 10000][index], iterations: Infinity, easing: 'linear' });
      animation.currentTime = [0, 1200, 5400, 6500][index];
      carEventsAnimations.push(animation);
    }
    carEventsPauseRace();
  }

  document.addEventListener('visibilitychange', carEventsPauseRace);
  carEventsMotion.addEventListener('change', carEventsBuildRace);
  carEventsMobile.addEventListener('change', carEventsBuildRace);
  window.addEventListener('resize', function carEventsResizeRace() {
    window.cancelAnimationFrame(carEventsResizeFrame);
    carEventsResizeFrame = window.requestAnimationFrame(carEventsBuildRace);
  });
  window.addEventListener('pagehide', function carEventsStopRace() {
    carEventsAway = true;
    window.cancelAnimationFrame(carEventsResizeFrame);
    carEventsClearRace();
  });
  window.addEventListener('pageshow', function carEventsResumeRace() {
    carEventsAway = false;
    if (!carEventsAnimations.length) carEventsBuildRace();
  });
  carEventsBuildRace();
})();

(function () {
  var form = document.querySelector("[data-booking-form]");
  if (!form) {
    return;
  }

  var guestsInput = form.querySelector("#attendee-count");
  var budgetInput = form.querySelector("#budget");
  var venueSelect = form.querySelector("#venue");
  var packageSelect = form.querySelector("#package");
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

  function cost(element, attendees) {
    var price = parseFloat(element.dataset.price);
    return element.dataset.basis === "per_guest" ? price * attendees : price;
  }

  function chosen(select) {
    var option = select.options[select.selectedIndex];
    return option && option.value ? option : null;
  }

  function fitsAttendees(option, attendees) {
    var minAttendees = parseInt(option.dataset.minAttendees, 10);
    var maxAttendees = parseInt(option.dataset.maxAttendees, 10);
    if (minAttendees && attendees < minAttendees) {
      return false;
    }
    if (maxAttendees && attendees > maxAttendees) {
      return false;
    }
    return true;
  }

  function setAvailable(element, available, reason) {
    element.disabled = !available;
    element.title = available ? "" : reason;
    var label = element.closest("label");
    if (label) {
      label.classList.toggle("is-unavailable", !available);
    }
  }

  function cheapest(select, attendees) {
    var best = null;
    Array.prototype.forEach.call(select.options, function (option) {
      if (!option.value || !fitsAttendees(option, attendees)) {
        return;
      }
      var value = cost(option, attendees);
      best = best === null ? value : Math.min(best, value);
    });
    return best;
  }

  function update() {
    var attendees = parseInt(guestsInput.value, 10);
    var budget = parseFloat(budgetInput.value);
    var haveAttendees = attendees > 0;
    var haveBudget = budget > 0;
    var venue = chosen(venueSelect);
    var pack = chosen(packageSelect);
    var picked = services.filter(function (box) {
      return box.checked;
    });

    if (!haveAttendees) {
      setSubmitBlocked(false);
      totalOutput.textContent = "Rs 0";
      noteOutput.textContent =
        "Enter your expected attendees to see your estimate.";
      [venueSelect, packageSelect].forEach(function (select) {
        Array.prototype.forEach.call(select.options, function (option) {
          if (option.value) {
            setAvailable(option, true, "");
          }
        });
      });
      services.forEach(function (box) {
        setAvailable(box, true, "");
      });
      return;
    }

    var venueCost = venue ? cost(venue, attendees) : 0;
    var packageCost = pack ? cost(pack, attendees) : 0;
    var serviceCost = picked.reduce(function (sum, box) {
      return sum + cost(box, attendees);
    }, 0);
    var total = venueCost + packageCost + serviceCost;
    totalOutput.textContent = money(total);
    setSubmitBlocked(haveBudget && total > budget);

    // The budget never locks a choice: customers can freely mix venues,
    // packages and services (or raise the budget) until the total fits.
    // Only attendee limits make an option unavailable.
    function updateOptions(select) {
      Array.prototype.forEach.call(select.options, function (option) {
        if (!option.value) {
          return;
        }
        setAvailable(
          option,
          option.selected || fitsAttendees(option, attendees),
          "Not available for this attendee count"
        );
      });
    }

    updateOptions(venueSelect);
    updateOptions(packageSelect);
    services.forEach(function (box) {
      setAvailable(box, true, "");
    });

    var venueFloor = cheapest(venueSelect, attendees);
    var packageFloor = cheapest(packageSelect, attendees);

    if (venueFloor === null || packageFloor === null) {
      noteOutput.textContent =
        "No venue or package is available for this number of attendees.";
    } else if (haveBudget && venueFloor + packageFloor > budget) {
      noteOutput.textContent =
        "For " + attendees + " attendees the lowest possible total is " +
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
