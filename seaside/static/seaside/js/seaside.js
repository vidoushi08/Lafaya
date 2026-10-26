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

// Seaside-only decorative animation, independent of booking and pricing logic.
(function seasideShellCelebration() {
  var seasideLayer = document.querySelector('.seaside-shell-layer');
  if (!seasideLayer || !document.querySelector('.seaside-page') ||
      typeof seasideLayer.animate !== 'function') {
    return;
  }

  var seasideMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var seasideMobile = window.matchMedia('(max-width: 600px)');
  var seasideParticles = new Map();
  var seasideTimer = null;
  var seasidePageAway = false;
  var seasideColours = ['sand', 'pearl', 'coral', 'aqua'];
  var seasideShapes = ['motif-1', 'motif-2', 'motif-3', 'motif-4'];
  var seasideIconPaths = ["<path d=\"M9 19C-4 7 6-2 12 6c6-8 16 1 3 13zm3-13v13M5 6l6 13M19 6l-6 13M9 19v2h6v-2\"/>","<path d=\"M17 19C2 24-3 7 7 3c9-4 18 6 12 12-5 6-13-1-8-5 4-3 7 3 3 4\"/><path d=\"m4 10 3 1m-1 7 3-2m8-11-1 3\"/>","<path d=\"m3 20 3-8 3 1 2-8 3 2 3-5 4 9-5 5-7 1-6 3zm3-8 3 5m2-12 5 11m1-14 4 9\"/>","<path d=\"M4 16C0 7 8 0 12 6c4-6 12 1 8 10l-8 5zm8-10v15M6 6l6 15m6-15-6 15M4 16h16\"/>"];
  var seasideSizes = ['small', 'medium', 'large'];

  function seasideRandom(min, max) {
    return min + Math.random() * (max - min);
  }

  function seasideCanCelebrate() {
    return !seasideMotion.matches && !document.hidden && !seasidePageAway;
  }

  function seasideClearShell() {
    window.clearTimeout(seasideTimer);
    seasideTimer = null;
    seasideParticles.forEach(function (animation, particle) {
      animation.cancel();
      particle.remove();
    });
    seasideParticles.clear();
  }

  function seasideShellBurst(x, y, requestedCount, direction) {
    if (!seasideCanCelebrate()) return;
    var seasideLimit = seasideMobile.matches ? 24 : 48;
    var seasideCount = Math.min(requestedCount, seasideLimit - seasideParticles.size);
    for (var index = 0; index < seasideCount; index++) {
      var particle = document.createElement('span');
      particle.className = 'seaside-shell-particle seaside-shell-' +
        seasideShapes[index % seasideShapes.length] + ' seaside-shell-' +
        seasideColours[Math.floor(seasideRandom(0, seasideColours.length))] +
        ' seaside-shell-particle-' + seasideSizes[Math.floor(seasideRandom(0, 3))];
      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 24 24');
      svg.setAttribute('aria-hidden', 'true');
      svg.setAttribute('focusable', 'false');
      svg.innerHTML = seasideIconPaths[index % seasideIconPaths.length];
      particle.appendChild(svg);
      seasideLayer.appendChild(particle);

      var spread = seasideRandom(25, Math.min(110, window.innerWidth * 0.2));
      var drift = direction ? direction * spread : seasideRandom(-spread, spread);
      var rise = seasideRandom(40, y > window.innerHeight * 0.8 ? 220 : 140);
      var fall = seasideRandom(70, seasideMobile.matches ? 130 : 180);
      var rotation = seasideRandom(-25, 25);
      var turn = seasideRandom(-40, 40);
      var duration = seasideRandom(2200, 3800);
      var animation = particle.animate([
        { transform: 'translate3d(' + x + 'px,' + y + 'px,0) rotate(' + rotation + 'deg) scale(0.4)', opacity: 0, offset: 0 },
        { transform: 'translate3d(' + (x + drift * 0.45) + 'px,' + (y - rise) + 'px,0) rotate(' + (rotation + turn * 0.3) + 'deg) scale(1)', opacity: 0.9, offset: 0.25 },
        { transform: 'translate3d(' + (x + drift * 0.8) + 'px,' + (y - rise * 0.25 + fall * 0.35) + 'px,0) rotate(' + (rotation + turn * 0.7) + 'deg)', opacity: 0.7, offset: 0.65 },
        { transform: 'translate3d(' + (x + drift) + 'px,' + (y + fall) + 'px,0) rotate(' + (rotation + turn) + 'deg) scale(0.8)', opacity: 0, offset: 1 }
      ], { duration: duration, easing: 'cubic-bezier(0.2, 0.55, 0.45, 1)', fill: 'both' });

      seasideParticles.set(particle, animation);
      (function seasideReleaseParticle(node, motion) {
        function seasideRemoveParticle() {
          seasideParticles.delete(node);
          node.remove();
        }
        motion.onfinish = seasideRemoveParticle;
        motion.oncancel = seasideRemoveParticle;
      })(particle, animation);
    }
  }

  function seasideScheduleBurst() {
    window.clearTimeout(seasideTimer);
    if (!seasideCanCelebrate()) return;
    seasideTimer = window.setTimeout(function seasideRecurringBurst() {
      var right = Math.random() > 0.5;
      var position = Math.random();
      var x = window.innerWidth * (position > 0.85 ? seasideRandom(0.25, 0.75) : (right ? 0.94 : 0.06));
      var y = window.innerHeight * (position < 0.15 ? 0.9 :
        position < 0.6 ? seasideRandom(0.35, 0.7) : 0.14);
      seasideShellBurst(x, y, seasideMobile.matches ? 4 : 8, right ? -1 : 1);
      seasideScheduleBurst();
    }, seasideMobile.matches ? seasideRandom(7000, 11000) : seasideRandom(4000, 7000));
  }

  function seasideRefreshCelebration() {
    seasideClearShell();
    seasideScheduleBurst();
  }

  document.querySelectorAll('.seaside-hero-actions a[href="#seaside-enquiry"], .seaside-book-cta a, .seaside-button-submit')
    .forEach(function (button) {
      button.addEventListener('click', function seasideBookingShell() {
        if (button.disabled) return;
        var bounds = button.getBoundingClientRect();
        seasideShellBurst(bounds.left + bounds.width / 2, bounds.top,
          seasideMobile.matches ? 6 : 10, 0);
        // The original click, anchor navigation and form submission continue normally.
      });
    });

  document.addEventListener('visibilitychange', seasideRefreshCelebration);
  seasideMotion.addEventListener('change', seasideRefreshCelebration);
  window.addEventListener('pagehide', function seasidePauseCelebration() {
    seasidePageAway = true;
    seasideClearShell();
  });
  window.addEventListener('pageshow', function seasideResumeCelebration() {
    seasidePageAway = false;
    if (seasideTimer === null) seasideScheduleBurst();
  });

  // A single welcome celebration: stronger at the edges, light at the centre.
  seasideShellBurst(window.innerWidth * 0.06, window.innerHeight * 0.2,
    seasideMobile.matches ? 5 : 8, 1);
  seasideShellBurst(window.innerWidth * 0.94, window.innerHeight * 0.2,
    seasideMobile.matches ? 5 : 8, -1);
  seasideShellBurst(window.innerWidth * 0.5, window.innerHeight * 0.25,
    seasideMobile.matches ? 3 : 5, 0);
  seasideScheduleBurst();
})();
