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
