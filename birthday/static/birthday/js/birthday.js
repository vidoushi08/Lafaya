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
        var form = document.getElementById("birthday-enquiry");
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
// Birthday-only decorative animation, independent of booking and pricing logic.
(function birthdayConfettiCelebration() {
  var birthdayLayer = document.querySelector('.birthday-confetti-layer');
  if (!birthdayLayer || !document.body.classList.contains('birthday-theme') ||
      typeof birthdayLayer.animate !== 'function') {
    return;
  }

  var birthdayMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var birthdayMobile = window.matchMedia('(max-width: 600px)');
  var birthdayParticles = new Map();
  var birthdayTimer = null;
  var birthdayPageAway = false;
  var birthdayColours = ['coral', 'pink', 'yellow', 'turquoise', 'purple', 'blue', 'orange'];
  var birthdayShapes = ['rectangle', 'circle', 'streamer', 'star'];
  var birthdaySizes = ['small', 'medium', 'large'];

  function birthdayRandom(min, max) {
    return min + Math.random() * (max - min);
  }

  function birthdayCanCelebrate() {
    return !birthdayMotion.matches && !document.hidden && !birthdayPageAway;
  }

  function birthdayClearConfetti() {
    window.clearTimeout(birthdayTimer);
    birthdayTimer = null;
    birthdayParticles.forEach(function (animation, particle) {
      animation.cancel();
      particle.remove();
    });
    birthdayParticles.clear();
  }

  function birthdayConfettiBurst(x, y, requestedCount, direction) {
    if (!birthdayCanCelebrate()) return;
    var birthdayLimit = birthdayMobile.matches ? 32 : 72;
    var birthdayCount = Math.min(requestedCount, birthdayLimit - birthdayParticles.size);
    for (var index = 0; index < birthdayCount; index++) {
      var particle = document.createElement('span');
      particle.className = 'birthday-confetti-particle birthday-confetti-' +
        birthdayShapes[index % birthdayShapes.length] + ' birthday-confetti-' +
        birthdayColours[Math.floor(birthdayRandom(0, birthdayColours.length))] +
        ' birthday-confetti-particle-' + birthdaySizes[Math.floor(birthdayRandom(0, 3))];
      birthdayLayer.appendChild(particle);

      var spread = birthdayRandom(35, Math.min(180, window.innerWidth * 0.25));
      var drift = direction ? direction * spread : birthdayRandom(-spread, spread);
      var rise = birthdayRandom(40, y > window.innerHeight * 0.8 ? 220 : 140);
      var fall = birthdayRandom(100, birthdayMobile.matches ? 210 : 300);
      var rotation = birthdayRandom(-100, 100);
      var turn = birthdayRandom(-120, 120);
      var duration = birthdayRandom(2200, 3800);
      var animation = particle.animate([
        { transform: 'translate3d(' + x + 'px,' + y + 'px,0) rotate(' + rotation + 'deg) scale(0.4)', opacity: 0, offset: 0 },
        { transform: 'translate3d(' + (x + drift * 0.45) + 'px,' + (y - rise) + 'px,0) rotate(' + (rotation + turn * 0.3) + 'deg) scale(1)', opacity: 0.9, offset: 0.25 },
        { transform: 'translate3d(' + (x + drift * 0.8) + 'px,' + (y - rise * 0.25 + fall * 0.35) + 'px,0) rotate(' + (rotation + turn * 0.7) + 'deg)', opacity: 0.7, offset: 0.65 },
        { transform: 'translate3d(' + (x + drift) + 'px,' + (y + fall) + 'px,0) rotate(' + (rotation + turn) + 'deg) scale(0.8)', opacity: 0, offset: 1 }
      ], { duration: duration, easing: 'cubic-bezier(0.2, 0.55, 0.45, 1)', fill: 'both' });

      birthdayParticles.set(particle, animation);
      (function birthdayReleaseParticle(node, motion) {
        function birthdayRemoveParticle() {
          birthdayParticles.delete(node);
          node.remove();
        }
        motion.onfinish = birthdayRemoveParticle;
        motion.oncancel = birthdayRemoveParticle;
      })(particle, animation);
    }
  }

  function birthdayScheduleBurst() {
    window.clearTimeout(birthdayTimer);
    if (!birthdayCanCelebrate()) return;
    birthdayTimer = window.setTimeout(function birthdayRecurringBurst() {
      var right = Math.random() > 0.5;
      var position = Math.random();
      var x = window.innerWidth * (right ? 0.96 : 0.04);
      var y = window.innerHeight * (position < 0.15 ? 0.94 :
        position < 0.6 ? birthdayRandom(0.35, 0.7) : 0.14);
      birthdayConfettiBurst(x, y, birthdayMobile.matches ? 7 : 14, right ? -1 : 1);
      birthdayScheduleBurst();
    }, birthdayMobile.matches ? birthdayRandom(7000, 11000) : birthdayRandom(4000, 7000));
  }

  function birthdayRefreshCelebration() {
    birthdayClearConfetti();
    birthdayScheduleBurst();
  }

  document.querySelectorAll('.birthday-hero-actions a[href="#birthday-enquiry"], .birthday-book-cta a, .birthday-button-submit')
    .forEach(function (button) {
      button.addEventListener('click', function birthdayBookingConfetti() {
        if (button.disabled) return;
        var bounds = button.getBoundingClientRect();
        birthdayConfettiBurst(bounds.left + bounds.width / 2, bounds.top,
          birthdayMobile.matches ? 6 : 10, 0);
        // The original click, anchor navigation and form submission continue normally.
      });
    });

  document.addEventListener('visibilitychange', birthdayRefreshCelebration);
  birthdayMotion.addEventListener('change', birthdayRefreshCelebration);
  window.addEventListener('pagehide', function birthdayPauseCelebration() {
    birthdayPageAway = true;
    birthdayClearConfetti();
  });
  window.addEventListener('pageshow', function birthdayResumeCelebration() {
    birthdayPageAway = false;
    if (birthdayTimer === null) birthdayScheduleBurst();
  });

  // A single welcome celebration: stronger at the edges, light at the centre.
  birthdayConfettiBurst(window.innerWidth * 0.06, window.innerHeight * 0.2,
    birthdayMobile.matches ? 8 : 18, 1);
  birthdayConfettiBurst(window.innerWidth * 0.94, window.innerHeight * 0.2,
    birthdayMobile.matches ? 8 : 18, -1);
  birthdayConfettiBurst(window.innerWidth * 0.5, window.innerHeight * 0.25,
    birthdayMobile.matches ? 5 : 10, 0);
  birthdayScheduleBurst();
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
