const navbarOverlay = document.querySelector(".navbar-overlay");

function setNavbarOverlay(visible) {
  if (!navbarOverlay) {
    return;
  }
  navbarOverlay.classList.toggle("navbar-overlay-visible", visible);
  navbarOverlay.setAttribute("aria-hidden", visible ? "false" : "true");
}

const navbarToggle = document.querySelector(".navbar-toggle");
const navbarLinks = document.querySelector(".navbar-links");

function setMobileMenu(open) {
  if (!navbarLinks || !navbarToggle) {
    return;
  }
  navbarLinks.classList.toggle("active", open);
  navbarToggle.setAttribute("aria-expanded", open ? "true" : "false");
  const icon = navbarToggle.querySelector("i");
  if (icon) {
    icon.classList.toggle("fa-bars", !open);
    icon.classList.toggle("fa-xmark", open);
  }
  setNavbarOverlay(open);
}

if (navbarToggle) {
  navbarToggle.addEventListener("click", function (event) {
    event.stopPropagation();
    setMobileMenu(!navbarLinks.classList.contains("active"));
  });
}

document.querySelectorAll(".navbar-dropdown-toggle").forEach(function (toggle) {
  toggle.addEventListener("click", function (event) {
    event.stopPropagation();
    const dropdown = toggle.closest(".navbar-dropdown");
    const isOpen = dropdown.classList.toggle("active");
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    setNavbarOverlay(isOpen);
  });
});

document.addEventListener("click", function () {
  const openDropdown = document.querySelector(".navbar-dropdown.active");
  if (openDropdown) {
    openDropdown.classList.remove("active");
    const toggle = openDropdown.querySelector(".navbar-dropdown-toggle");
    toggle.setAttribute("aria-expanded", "false");
    setNavbarOverlay(false);
  }
  setMobileMenu(false);
});
