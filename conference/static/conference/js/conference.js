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

// Conference-only decorative animation, independent of booking and pricing logic.
(function conferenceNotebookCelebration() {
  var conferenceLayer = document.querySelector('.conference-notebook-layer');
  if (!conferenceLayer || !document.querySelector('.conference-page') ||
      typeof conferenceLayer.animate !== 'function') {
    return;
  }

  var conferenceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var conferenceMobile = window.matchMedia('(max-width: 600px)');
  var conferenceParticles = new Map();
  var conferenceTimer = null;
  var conferencePageAway = false;
  var conferenceColours = ['sand', 'pearl', 'coral', 'aqua'];
  var conferenceShapes = ['motif-1', 'motif-2', 'motif-3', 'motif-4'];
  var conferenceIconPaths = ["<rect x=\"5\" y=\"2\" width=\"15\" height=\"20\" rx=\"2\"/><path d=\"M8 2v20M3 6h4M3 11h4M3 16h4M11 7h6m-6 4h6m-6 4h4\"/>","<path d=\"M3 4q5-2 9 1 4-3 9-1v16q-5-2-9 0-4-2-9 0zm9 1v15M6 8l3 1m6 0 3-1M6 12l3 1m6 0 3-1\"/>","<rect x=\"4\" y=\"2\" width=\"16\" height=\"20\" rx=\"2\"/><path d=\"M8 2v20m3-14h6m-6 4h6m-6 4h4M2 6h4m-4 6h4m-4 6h4\"/>","<path d=\"M4 2h15v20H4zm4 0v20m3-16h5m-5 4h5m-5 4h3M16 2v5l-2-1-2 1V2\"/>"];
  var conferenceSizes = ['small', 'medium', 'large'];

  function conferenceRandom(min, max) {
    return min + Math.random() * (max - min);
  }

  function conferenceCanCelebrate() {
    return !conferenceMotion.matches && !document.hidden && !conferencePageAway;
  }

  function conferenceClearNotebook() {
    window.clearTimeout(conferenceTimer);
    conferenceTimer = null;
    conferenceParticles.forEach(function (animation, particle) {
      animation.cancel();
      particle.remove();
    });
    conferenceParticles.clear();
  }

  function conferenceNotebookBurst(x, y, requestedCount, direction) {
    if (!conferenceCanCelebrate()) return;
    var conferenceLimit = conferenceMobile.matches ? 24 : 48;
    var conferenceCount = Math.min(requestedCount, conferenceLimit - conferenceParticles.size);
    for (var index = 0; index < conferenceCount; index++) {
      var particle = document.createElement('span');
      particle.className = 'conference-notebook-particle conference-notebook-' +
        conferenceShapes[index % conferenceShapes.length] + ' conference-notebook-' +
        conferenceColours[Math.floor(conferenceRandom(0, conferenceColours.length))] +
        ' conference-notebook-particle-' + conferenceSizes[Math.floor(conferenceRandom(0, 3))];
      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 24 24');
      svg.setAttribute('aria-hidden', 'true');
      svg.setAttribute('focusable', 'false');
      svg.innerHTML = conferenceIconPaths[index % conferenceIconPaths.length];
      particle.appendChild(svg);
      conferenceLayer.appendChild(particle);

      var spread = conferenceRandom(25, Math.min(110, window.innerWidth * 0.2));
      var drift = direction ? direction * spread : conferenceRandom(-spread, spread);
      var rise = conferenceRandom(40, y > window.innerHeight * 0.8 ? 220 : 140);
      var fall = conferenceRandom(70, conferenceMobile.matches ? 130 : 180);
      var rotation = conferenceRandom(-25, 25);
      var turn = conferenceRandom(-40, 40);
      var duration = conferenceRandom(2200, 3800);
      var animation = particle.animate([
        { transform: 'translate3d(' + x + 'px,' + y + 'px,0) rotate(' + rotation + 'deg) scale(0.4)', opacity: 0, offset: 0 },
        { transform: 'translate3d(' + (x + drift * 0.45) + 'px,' + (y - rise) + 'px,0) rotate(' + (rotation + turn * 0.3) + 'deg) scale(1)', opacity: 0.9, offset: 0.25 },
        { transform: 'translate3d(' + (x + drift * 0.8) + 'px,' + (y - rise * 0.25 + fall * 0.35) + 'px,0) rotate(' + (rotation + turn * 0.7) + 'deg)', opacity: 0.7, offset: 0.65 },
        { transform: 'translate3d(' + (x + drift) + 'px,' + (y + fall) + 'px,0) rotate(' + (rotation + turn) + 'deg) scale(0.8)', opacity: 0, offset: 1 }
      ], { duration: duration, easing: 'cubic-bezier(0.2, 0.55, 0.45, 1)', fill: 'both' });

      conferenceParticles.set(particle, animation);
      (function conferenceReleaseParticle(node, motion) {
        function conferenceRemoveParticle() {
          conferenceParticles.delete(node);
          node.remove();
        }
        motion.onfinish = conferenceRemoveParticle;
        motion.oncancel = conferenceRemoveParticle;
      })(particle, animation);
    }
  }

  function conferenceScheduleBurst() {
    window.clearTimeout(conferenceTimer);
    if (!conferenceCanCelebrate()) return;
    conferenceTimer = window.setTimeout(function conferenceRecurringBurst() {
      var right = Math.random() > 0.5;
      var position = Math.random();
      var x = window.innerWidth * (position > 0.85 ? conferenceRandom(0.25, 0.75) : (right ? 0.94 : 0.06));
      var y = window.innerHeight * (position < 0.15 ? 0.9 :
        position < 0.6 ? conferenceRandom(0.35, 0.7) : 0.14);
      conferenceNotebookBurst(x, y, conferenceMobile.matches ? 4 : 8, right ? -1 : 1);
      conferenceScheduleBurst();
    }, conferenceMobile.matches ? conferenceRandom(7000, 11000) : conferenceRandom(4000, 7000));
  }

  function conferenceRefreshCelebration() {
    conferenceClearNotebook();
    conferenceScheduleBurst();
  }

  document.querySelectorAll('.conference-hero-actions a[href="#conference-enquiry"], .conference-book-cta a, .conference-button-submit')
    .forEach(function (button) {
      button.addEventListener('click', function conferenceBookingNotebook() {
        if (button.disabled) return;
        var bounds = button.getBoundingClientRect();
        conferenceNotebookBurst(bounds.left + bounds.width / 2, bounds.top,
          conferenceMobile.matches ? 6 : 10, 0);
        // The original click, anchor navigation and form submission continue normally.
      });
    });

  document.addEventListener('visibilitychange', conferenceRefreshCelebration);
  conferenceMotion.addEventListener('change', conferenceRefreshCelebration);
  window.addEventListener('pagehide', function conferencePauseCelebration() {
    conferencePageAway = true;
    conferenceClearNotebook();
  });
  window.addEventListener('pageshow', function conferenceResumeCelebration() {
    conferencePageAway = false;
    if (conferenceTimer === null) conferenceScheduleBurst();
  });

  // A single welcome celebration: stronger at the edges, light at the centre.
  conferenceNotebookBurst(window.innerWidth * 0.06, window.innerHeight * 0.2,
    conferenceMobile.matches ? 5 : 8, 1);
  conferenceNotebookBurst(window.innerWidth * 0.94, window.innerHeight * 0.2,
    conferenceMobile.matches ? 5 : 8, -1);
  conferenceNotebookBurst(window.innerWidth * 0.5, window.innerHeight * 0.25,
    conferenceMobile.matches ? 3 : 5, 0);
  conferenceScheduleBurst();
})();
