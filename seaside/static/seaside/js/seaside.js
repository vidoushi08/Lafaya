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
