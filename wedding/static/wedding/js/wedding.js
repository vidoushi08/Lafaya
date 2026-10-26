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
    if (items.length > VISIBLE_COUNT) {
      return;
    }

    button.addEventListener("click", function () {
      var enquiry = document.getElementById("wedding-enquiry");
      if (enquiry) {
        enquiry.scrollIntoView({ behavior: "smooth" });
      }
    });
  });
})();

// Wedding-only decorative animation, independent of booking and pricing logic.
(function weddingFlowersCelebration() {
  var weddingLayer = document.querySelector('.wedding-flower-layer');
  if (!weddingLayer || !document.body.classList.contains('wedding-theme') ||
      typeof weddingLayer.animate !== 'function') {
    return;
  }

  var weddingMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var weddingMobile = window.matchMedia('(max-width: 600px)');
  var weddingParticles = new Map();
  var weddingTimer = null;
  var weddingPageAway = false;
  var weddingColours = ['ivory', 'blush', 'rose', 'champagne', 'lavender', 'sage'];
  var weddingShapes = ['petal', 'flower', 'leaf', 'blossom'];
  var weddingSizes = ['small', 'medium', 'large'];

  function weddingRandom(min, max) {
    return min + Math.random() * (max - min);
  }

  function weddingCanCelebrate() {
    return !weddingMotion.matches && !document.hidden && !weddingPageAway;
  }

  function weddingClearFlowers() {
    window.clearTimeout(weddingTimer);
    weddingTimer = null;
    weddingParticles.forEach(function (animation, particle) {
      animation.cancel();
      particle.remove();
    });
    weddingParticles.clear();
  }

  function weddingFlowersBurst(x, y, requestedCount, direction) {
    if (!weddingCanCelebrate()) return;
    var weddingLimit = weddingMobile.matches ? 24 : 56;
    var weddingCount = Math.min(requestedCount, weddingLimit - weddingParticles.size);
    for (var index = 0; index < weddingCount; index++) {
      var particle = document.createElement('span');
      particle.className = 'wedding-flower-particle wedding-flower-' +
        weddingShapes[index % weddingShapes.length] + ' wedding-flower-' +
        weddingColours[Math.floor(weddingRandom(0, weddingColours.length))] +
        ' wedding-flower-particle-' + weddingSizes[Math.floor(weddingRandom(0, 3))];
      weddingLayer.appendChild(particle);

      var spread = weddingRandom(35, Math.min(180, window.innerWidth * 0.25));
      var drift = direction ? direction * spread : weddingRandom(-spread, spread);
      var rise = weddingRandom(40, y > window.innerHeight * 0.8 ? 220 : 140);
      var fall = weddingRandom(100, weddingMobile.matches ? 210 : 300);
      var rotation = weddingRandom(-45, 45);
      var turn = weddingRandom(-65, 65);
      var duration = weddingRandom(3200, 5200);
      var animation = particle.animate([
        { transform: 'translate3d(' + x + 'px,' + y + 'px,0) rotate(' + rotation + 'deg) scale(0.4)', opacity: 0, offset: 0 },
        { transform: 'translate3d(' + (x + drift * 0.45) + 'px,' + (y - rise) + 'px,0) rotate(' + (rotation + turn * 0.3) + 'deg) scale(1)', opacity: 0.9, offset: 0.25 },
        { transform: 'translate3d(' + (x + drift * 0.8) + 'px,' + (y - rise * 0.25 + fall * 0.35) + 'px,0) rotate(' + (rotation + turn * 0.7) + 'deg)', opacity: 0.7, offset: 0.65 },
        { transform: 'translate3d(' + (x + drift) + 'px,' + (y + fall) + 'px,0) rotate(' + (rotation + turn) + 'deg) scale(0.8)', opacity: 0, offset: 1 }
      ], { duration: duration, easing: 'cubic-bezier(0.2, 0.55, 0.45, 1)', fill: 'both' });

      weddingParticles.set(particle, animation);
      (function weddingReleaseParticle(node, motion) {
        function weddingRemoveParticle() {
          weddingParticles.delete(node);
          node.remove();
        }
        motion.onfinish = weddingRemoveParticle;
        motion.oncancel = weddingRemoveParticle;
      })(particle, animation);
    }
  }

  function weddingScheduleBurst() {
    window.clearTimeout(weddingTimer);
    if (!weddingCanCelebrate()) return;
    weddingTimer = window.setTimeout(function weddingRecurringBurst() {
      var right = Math.random() > 0.5;
      var position = Math.random();
      var x = window.innerWidth * (right ? 0.96 : 0.04);
      var y = window.innerHeight * (position < 0.15 ? 0.94 :
        position < 0.6 ? weddingRandom(0.35, 0.7) : 0.14);
      weddingFlowersBurst(x, y, weddingMobile.matches ? 5 : 10, right ? -1 : 1);
      weddingScheduleBurst();
    }, weddingMobile.matches ? weddingRandom(9000, 14000) : weddingRandom(6500, 9500));
  }

  function weddingRefreshCelebration() {
    weddingClearFlowers();
    weddingScheduleBurst();
  }

  document.querySelectorAll('.wedding-page .seaside-hero-actions a[href="#wedding-enquiry"], .wedding-page .seaside-book-cta a, .wedding-page .seaside-button-submit')
    .forEach(function (button) {
      button.addEventListener('click', function weddingBookingFlowers() {
        if (button.disabled) return;
        var bounds = button.getBoundingClientRect();
        weddingFlowersBurst(bounds.left + bounds.width / 2, bounds.top,
          weddingMobile.matches ? 6 : 10, 0);
        // The original click, anchor navigation and form submission continue normally.
      });
    });

  document.addEventListener('visibilitychange', weddingRefreshCelebration);
  weddingMotion.addEventListener('change', weddingRefreshCelebration);
  window.addEventListener('pagehide', function weddingPauseCelebration() {
    weddingPageAway = true;
    weddingClearFlowers();
  });
  window.addEventListener('pageshow', function weddingResumeCelebration() {
    weddingPageAway = false;
    if (weddingTimer === null) weddingScheduleBurst();
  });

  // A single welcome celebration: stronger at the edges, light at the centre.
  weddingFlowersBurst(window.innerWidth * 0.06, window.innerHeight * 0.2,
    weddingMobile.matches ? 6 : 12, 1);
  weddingFlowersBurst(window.innerWidth * 0.94, window.innerHeight * 0.2,
    weddingMobile.matches ? 6 : 12, -1);
  weddingFlowersBurst(window.innerWidth * 0.5, window.innerHeight * 0.25,
    weddingMobile.matches ? 4 : 8, 0);
  weddingScheduleBurst();
})();
