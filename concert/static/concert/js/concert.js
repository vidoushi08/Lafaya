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
        var form = document.getElementById("concert-enquiry");
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
      noteOutput.textContent =
        "Enter your expected guests to see your estimate.";
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
      noteOutput.textContent =
        "No venue or package is available for this number of guests.";
    } else if (haveBudget && venueFloor + packageFloor > budget) {
      noteOutput.textContent =
        "For " + guests + " guests the lowest possible total is " +
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

// Concert-only decorative animation, independent of booking and pricing logic.
(function concertNeonCelebration() {
  var concertLayer = document.querySelector('.concert-neon-layer');
  if (!concertLayer || !document.querySelector('.concert-page') ||
      typeof concertLayer.animate !== 'function') {
    return;
  }

  var concertMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var concertMobile = window.matchMedia('(max-width: 600px)');
  var concertParticles = new Map();
  var concertTimer = null;
  var concertPageAway = false;
  var concertColours = ['violet', 'pink', 'cyan', 'blue'];
  var concertShapes = ['motif-1', 'motif-2', 'motif-3', 'motif-4'];
  var concertIconPaths = ["<path d=\"m14 2-9 12h7l-2 8 9-13h-7z\"/>","<path d=\"M8 17V5l12-3v12M8 8l12-3\"/><ellipse cx=\"5\" cy=\"18\" rx=\"3\" ry=\"2\"/><ellipse cx=\"17\" cy=\"15\" rx=\"3\" ry=\"2\"/>","<path d=\"M4 8v9m5-13v17m5-15v13m5-9v7\"/>","<circle cx=\"12\" cy=\"12\" r=\"8\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/><path d=\"m5 3 2 2m12 14 2 2\"/>"];
  var concertSizes = ['small', 'medium', 'large'];

  function concertRandom(min, max) {
    return min + Math.random() * (max - min);
  }

  function concertCanCelebrate() {
    return !concertMotion.matches && !document.hidden && !concertPageAway;
  }

  function concertClearNeon() {
    window.clearTimeout(concertTimer);
    concertTimer = null;
    concertParticles.forEach(function (animation, particle) {
      animation.cancel();
      particle.remove();
    });
    concertParticles.clear();
  }

  function concertNeonBurst(x, y, requestedCount, direction) {
    if (!concertCanCelebrate()) return;
    var concertLimit = concertMobile.matches ? 24 : 48;
    var concertCount = Math.min(requestedCount, concertLimit - concertParticles.size);
    for (var index = 0; index < concertCount; index++) {
      var particle = document.createElement('span');
      particle.className = 'concert-neon-particle concert-neon-' +
        concertShapes[index % concertShapes.length] + ' concert-neon-' +
        concertColours[Math.floor(concertRandom(0, concertColours.length))] +
        ' concert-neon-particle-' + concertSizes[Math.floor(concertRandom(0, 3))];
      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 24 24');
      svg.setAttribute('aria-hidden', 'true');
      svg.setAttribute('focusable', 'false');
      svg.innerHTML = concertIconPaths[index % concertIconPaths.length];
      particle.appendChild(svg);
      concertLayer.appendChild(particle);

      var spread = concertRandom(25, Math.min(110, window.innerWidth * 0.2));
      var drift = direction ? direction * spread : concertRandom(-spread, spread);
      var rise = concertRandom(40, y > window.innerHeight * 0.8 ? 220 : 140);
      var fall = concertRandom(70, concertMobile.matches ? 130 : 180);
      var rotation = concertRandom(-25, 25);
      var turn = concertRandom(-40, 40);
      var duration = concertRandom(2200, 3800);
      var animation = particle.animate([
        { transform: 'translate3d(' + x + 'px,' + y + 'px,0) rotate(' + rotation + 'deg) scale(0.4)', opacity: 0, offset: 0 },
        { transform: 'translate3d(' + (x + drift * 0.45) + 'px,' + (y - rise) + 'px,0) rotate(' + (rotation + turn * 0.3) + 'deg) scale(1)', opacity: 0.9, offset: 0.25 },
        { transform: 'translate3d(' + (x + drift * 0.8) + 'px,' + (y - rise * 0.25 + fall * 0.35) + 'px,0) rotate(' + (rotation + turn * 0.7) + 'deg)', opacity: 0.7, offset: 0.65 },
        { transform: 'translate3d(' + (x + drift) + 'px,' + (y + fall) + 'px,0) rotate(' + (rotation + turn) + 'deg) scale(0.8)', opacity: 0, offset: 1 }
      ], { duration: duration, easing: 'cubic-bezier(0.2, 0.55, 0.45, 1)', fill: 'both' });

      concertParticles.set(particle, animation);
      (function concertReleaseParticle(node, motion) {
        function concertRemoveParticle() {
          concertParticles.delete(node);
          node.remove();
        }
        motion.onfinish = concertRemoveParticle;
        motion.oncancel = concertRemoveParticle;
      })(particle, animation);
    }
  }

  function concertScheduleBurst() {
    window.clearTimeout(concertTimer);
    if (!concertCanCelebrate()) return;
    concertTimer = window.setTimeout(function concertRecurringBurst() {
      var right = Math.random() > 0.5;
      var position = Math.random();
      var x = window.innerWidth * (position > 0.85 ? concertRandom(0.25, 0.75) : (right ? 0.94 : 0.06));
      var y = window.innerHeight * (position < 0.15 ? 0.9 :
        position < 0.6 ? concertRandom(0.35, 0.7) : 0.14);
      concertNeonBurst(x, y, concertMobile.matches ? 4 : 7, right ? -1 : 1);
      concertScheduleBurst();
    }, concertMobile.matches ? concertRandom(7000, 11000) : concertRandom(4000, 7000));
  }

  function concertRefreshCelebration() {
    concertClearNeon();
    concertScheduleBurst();
  }

  document.querySelectorAll('.concert-hero-actions a[href="#concert-enquiry"], .concert-book-cta a, .concert-button-submit')
    .forEach(function (button) {
      button.addEventListener('click', function concertBookingNeon() {
        if (button.disabled) return;
        var bounds = button.getBoundingClientRect();
        concertNeonBurst(bounds.left + bounds.width / 2, bounds.top,
          concertMobile.matches ? 6 : 10, 0);
        // The original click, anchor navigation and form submission continue normally.
      });
    });

  document.addEventListener('visibilitychange', concertRefreshCelebration);
  concertMotion.addEventListener('change', concertRefreshCelebration);
  window.addEventListener('pagehide', function concertPauseCelebration() {
    concertPageAway = true;
    concertClearNeon();
  });
  window.addEventListener('pageshow', function concertResumeCelebration() {
    concertPageAway = false;
    if (concertTimer === null) concertScheduleBurst();
  });

  // A single welcome celebration: stronger at the edges, light at the centre.
  concertNeonBurst(window.innerWidth * 0.06, window.innerHeight * 0.2,
    concertMobile.matches ? 6 : 10, 1);
  concertNeonBurst(window.innerWidth * 0.94, window.innerHeight * 0.2,
    concertMobile.matches ? 6 : 10, -1);
  concertNeonBurst(window.innerWidth * 0.5, window.innerHeight * 0.25,
    concertMobile.matches ? 3 : 5, 0);
  concertScheduleBurst();
})();
