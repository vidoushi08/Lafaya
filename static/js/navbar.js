document.querySelectorAll(".navbar-dropdown-toggle").forEach(function (toggle) {
  toggle.addEventListener("click", function (event) {
    event.stopPropagation();
    const dropdown = toggle.closest(".navbar-dropdown");
    const isOpen = dropdown.classList.toggle("active");
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });
});

document.addEventListener("click", function () {
  document
    .querySelectorAll(".navbar-dropdown.active")
    .forEach(function (dropdown) {
      dropdown.classList.remove("active");
      const toggle = dropdown.querySelector(".navbar-dropdown-toggle");
      toggle.setAttribute("aria-expanded", "false");
    });
});