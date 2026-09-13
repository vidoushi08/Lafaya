document.querySelectorAll(".navbar-dropdown-toggle").forEach(function (toggle) {
  toggle.addEventListener("click", function (event) {
    event.stopPropagation();
    var dropdown = toggle.closest(".navbar-dropdown");
    var isOpen = dropdown.classList.toggle("active");
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });
});

document.addEventListener("click", function () {
  document
    .querySelectorAll(".navbar-dropdown.active")
    .forEach(function (dropdown) {
      dropdown.classList.remove("active");
      var toggle = dropdown.querySelector(".navbar-dropdown-toggle");
      toggle.setAttribute("aria-expanded", "false");
    });
});
