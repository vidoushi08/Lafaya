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

// Wedding-only continuous drift, independent of booking logic.
(function weddingContinuousDrift() {
  var weddingLayer = document.querySelector('.wedding-flower-layer');
  if (!weddingLayer || !document.querySelector('.wedding-page') ||
      typeof weddingLayer.animate !== 'function') return;
  var weddingMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var weddingMobile = window.matchMedia('(max-width: 600px)');
  var weddingAnimations = [];
  var weddingAway = false;
  var weddingResizeFrame = null;
  var weddingColours = ["ivory","blush","rose","champagne","lavender","sage"];
  var weddingShapes = ["petal","flower","leaf","blossom"];


  function weddingClearDrift() {
    weddingAnimations.forEach(function (animation) { animation.cancel(); });
    weddingAnimations = [];
    weddingLayer.replaceChildren();
  }
  function weddingPauseDrift() {
    weddingAnimations.forEach(function (animation) {
      if (document.hidden || weddingAway) animation.pause();
      else animation.play();
    });
  }
  function weddingBuildDrift() {
    weddingClearDrift();
    if (weddingMotion.matches || weddingAway) return;
    var count = weddingMobile.matches ? 4 : 8;
    for (var index = 0; index < count; index++) {
      var particle = document.createElement('span');
      particle.className = 'wedding-flower-particle wedding-flower-' +
        weddingShapes[index % weddingShapes.length] + ' wedding-flower-' +
        weddingColours[index % weddingColours.length] +
        ' wedding-flower-drifter wedding-flower-drifter-' + (index + 1);

      weddingLayer.appendChild(particle);
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
      weddingAnimations.push(animation);
    }
    weddingPauseDrift();
  }
  document.addEventListener('visibilitychange', weddingPauseDrift);
  weddingMotion.addEventListener('change', weddingBuildDrift);
  weddingMobile.addEventListener('change', weddingBuildDrift);
  window.addEventListener('resize', function weddingResizeDrift() {
    window.cancelAnimationFrame(weddingResizeFrame);
    weddingResizeFrame = window.requestAnimationFrame(weddingBuildDrift);
  });
  window.addEventListener('pagehide', function weddingStopDrift() {
    weddingAway = true;
    window.cancelAnimationFrame(weddingResizeFrame);
    weddingClearDrift();
  });
  window.addEventListener('pageshow', function weddingResumeDrift() {
    weddingAway = false;
    if (!weddingAnimations.length) weddingBuildDrift();
  });
  weddingBuildDrift();
})();
