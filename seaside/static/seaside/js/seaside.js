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
        var form = document.getElementById("seaside-enquiry");
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

(function () {
  var form = document.querySelector("[data-booking-form]");
  if (!form) {
    return;
  }

  var guestsInput = form.querySelector("#guest-count");
  var budgetInput = form.querySelector("#budget");
  var venueSelect = form.querySelector("#venue");
  var packageSelect = form.querySelector("#package");
  var services = Array.prototype.slice.call(
    form.querySelectorAll('input[name="optional_services"]')
  );
  var totalOutput = form.querySelector("[data-estimate-total]");
  var noteOutput = form.querySelector("[data-estimate-note]");
  var submitButton = form.querySelector('button[type="submit"]');
  var hasPriceOnRequest = services.some(function (box) {
    return box.dataset.priceOnRequest === "true";
  });

  function setEstimateNote(note) {
    noteOutput.textContent = hasPriceOnRequest
      ? note + " Optional services marked price on request will be quoted separately."
      : note;
  }

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

  function setAvailable(element, available, reason) {
    element.disabled = !available;
    element.title = available ? "" : reason;
    var label = element.closest("label");
    if (label) {
      label.classList.toggle("is-unavailable", !available);
    }
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

    if (!haveGuests) {
      setSubmitBlocked(false);
      totalOutput.textContent = "Rs 0";
      setEstimateNote("Enter your expected guests to see your estimate.");
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

    var venueCost = venue ? cost(venue, guests) : 0;
    var packageCost = pack ? cost(pack, guests) : 0;
    var serviceCost = picked.reduce(function (sum, box) {
      return sum + cost(box, guests);
    }, 0);
    var total = venueCost + packageCost + serviceCost;
    totalOutput.textContent = money(total);
    setSubmitBlocked(haveBudget && total > budget);

    // The budget never locks a choice: customers can freely mix venues,
    // packages and services (or raise the budget) until the total fits.
    // Only guest-count limits make an option unavailable.
    function updateOptions(select) {
      Array.prototype.forEach.call(select.options, function (option) {
        if (!option.value) {
          return;
        }
        setAvailable(
          option,
          option.selected || fitsGuests(option, guests),
          "Not available for this guest count"
        );
      });
    }

    updateOptions(venueSelect);
    updateOptions(packageSelect);
    services.forEach(function (box) {
      setAvailable(box, true, "");
    });

    var venueFloor = cheapest(venueSelect, guests);
    var packageFloor = cheapest(packageSelect, guests);

    if (venueFloor === null || packageFloor === null) {
      setEstimateNote("No venue or package is available for this number of guests.");
    } else if (haveBudget && venueFloor + packageFloor > budget) {
      setEstimateNote(
        "For " + guests + " guests the lowest possible total is " +
        money(venueFloor + packageFloor) + ", which is above your budget."
      );
    } else if (!venue || !pack) {
      setEstimateNote("Choose a venue and package to see your estimate.");
    } else if (haveBudget && total > budget) {
      setEstimateNote(
        "This selection is " + money(total - budget) +
        " over your budget. Pick a cheaper venue, package or services, or raise your budget."
      );
    } else if (haveBudget) {
      setEstimateNote("Within your budget. " + money(budget - total) + " remaining.");
    } else {
      setEstimateNote("Enter your budget to check this estimate.");
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

// Seaside-only continuous drift, independent of booking logic.
(function seasideContinuousDrift() {
  var seasideLayer = document.querySelector('.seaside-shell-layer');
  if (!seasideLayer || !document.querySelector('.seaside-page') ||
      typeof seasideLayer.animate !== 'function') return;
  var seasideMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var seasideMobile = window.matchMedia('(max-width: 600px)');
  var seasideAnimations = [];
  var seasideAway = false;
  var seasideResizeFrame = null;
  var seasideColours = ["sand","pearl","coral","aqua"];
  var seasideShapes = ["motif-1","motif-2","motif-3","motif-4"];
    var seasideIconPaths = ["<path d=\"M9 19C-4 7 6-2 12 6c6-8 16 1 3 13zm3-13v13M5 6l6 13M19 6l-6 13M9 19v2h6v-2\"/>","<path d=\"M17 19C2 24-3 7 7 3c9-4 18 6 12 12-5 6-13-1-8-5 4-3 7 3 3 4\"/><path d=\"m4 10 3 1m-1 7 3-2m8-11-1 3\"/>","<path d=\"m3 20 3-8 3 1 2-8 3 2 3-5 4 9-5 5-7 1-6 3zm3-8 3 5m2-12 5 11m1-14 4 9\"/>","<path d=\"M4 16C0 7 8 0 12 6c4-6 12 1 8 10l-8 5zm8-10v15M6 6l6 15m6-15-6 15M4 16h16\"/>"];

  function seasideClearDrift() {
    seasideAnimations.forEach(function (animation) { animation.cancel(); });
    seasideAnimations = [];
    seasideLayer.replaceChildren();
  }
  function seasidePauseDrift() {
    seasideAnimations.forEach(function (animation) {
      if (document.hidden || seasideAway) animation.pause();
      else animation.play();
    });
  }
  function seasideBuildDrift() {
    seasideClearDrift();
    if (seasideMotion.matches || seasideAway) return;
    var count = seasideMobile.matches ? 4 : 8;
    for (var index = 0; index < count; index++) {
      var particle = document.createElement('span');
      particle.className = 'seaside-shell-particle seaside-shell-' +
        seasideShapes[index % seasideShapes.length] + ' seaside-shell-' +
        seasideColours[index % seasideColours.length] +
        ' seaside-shell-drifter seaside-shell-drifter-' + (index + 1);
      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 24 24');
      svg.setAttribute('aria-hidden', 'true');
      svg.setAttribute('focusable', 'false');
      svg.innerHTML = seasideIconPaths[index % seasideIconPaths.length];
      particle.appendChild(svg);
      seasideLayer.appendChild(particle);
      var reverse = index % 2 === 1;
      var start = reverse ? window.innerWidth + 40 : -40;
      var end = reverse ? -40 : window.innerWidth + 40;
      var sway = index % 3 === 0 ? 14 : -12;
      var animation = particle.animate([
        { transform: 'translate3d(' + start + 'px,0,0) rotate(-10deg)', opacity: 0, offset: 0 },
        { transform: 'translate3d(' + (start + (end - start) * 0.12) + 'px,' + sway + 'px,0) rotate(4deg)', opacity: 0.8, offset: 0.12 },
        { transform: 'translate3d(' + (start + (end - start) * 0.5) + 'px,' + (-sway) + 'px,0) rotate(12deg)', opacity: 0.8, offset: 0.5 },
        { transform: 'translate3d(' + (start + (end - start) * 0.88) + 'px,' + sway + 'px,0) rotate(-4deg)', opacity: 0.8, offset: 0.88 },
        { transform: 'translate3d(' + end + 'px,0,0) rotate(-10deg)', opacity: 0, offset: 1 }
      ], { duration: 18000 + (index % 5) * 2200, iterations: Infinity, easing: 'linear' });
      animation.currentTime = index * 2700;
      seasideAnimations.push(animation);
    }
    seasidePauseDrift();
  }
  document.addEventListener('visibilitychange', seasidePauseDrift);
  seasideMotion.addEventListener('change', seasideBuildDrift);
  seasideMobile.addEventListener('change', seasideBuildDrift);
  window.addEventListener('resize', function seasideResizeDrift() {
    window.cancelAnimationFrame(seasideResizeFrame);
    seasideResizeFrame = window.requestAnimationFrame(seasideBuildDrift);
  });
  window.addEventListener('pagehide', function seasideStopDrift() {
    seasideAway = true;
    window.cancelAnimationFrame(seasideResizeFrame);
    seasideClearDrift();
  });
  window.addEventListener('pageshow', function seasideResumeDrift() {
    seasideAway = false;
    if (!seasideAnimations.length) seasideBuildDrift();
  });
  seasideBuildDrift();
})();
