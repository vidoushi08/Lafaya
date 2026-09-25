const slides = document.querySelectorAll(".homepage-events-hero-slide");
const dots = document.querySelectorAll(".homepage-events-hero-dot");
let currentIndex = 0;
const AUTO_SCROLL_MS = 3000;
let autoScrollTimer = null;
let isHovered = false;

function showSlide(index) {
  slides.forEach(function (slide, i) {
    slide.classList.toggle("homepage-events-hero-slide-active", i === index);
  });
  dots.forEach(function (dot, i) {
    dot.classList.toggle("homepage-events-hero-dot-active", i === index);
  });
}

function goToSlide(index) {
  showSlide(index);
  currentIndex = index;
}

function nextSlide() {
  goToSlide((currentIndex + 1) % slides.length);
}

function prevSlide() {
  goToSlide((currentIndex - 1 + slides.length) % slides.length);
}

function startAutoScroll() {
  autoScrollTimer = setInterval(nextSlide, AUTO_SCROLL_MS);
}

function resetAutoScroll() {
  clearInterval(autoScrollTimer);
  if (!isHovered) {
    autoScrollTimer = setInterval(nextSlide, AUTO_SCROLL_MS);
  }
}

dots.forEach(function (dot, index) {
  dot.addEventListener("click", function () {
    goToSlide(index);
    resetAutoScroll();
  });
});

document
  .querySelector(".homepage-events-hero-arrow-next")
  .addEventListener("click", function () {
    nextSlide();
    resetAutoScroll();
  });
document
  .querySelector(".homepage-events-hero-arrow-prev")
  .addEventListener("click", function () {
    prevSlide();
    resetAutoScroll();
  });

document
  .querySelector(".homepage-events-hero")
  .addEventListener("mouseenter", function () {
    isHovered = true;
    clearInterval(autoScrollTimer);
  });
document
  .querySelector(".homepage-events-hero")
  .addEventListener("mouseleave", function () {
    isHovered = false;
    resetAutoScroll();
  });

startAutoScroll();

const testimonialsTrack = document.querySelector(
  ".homepage-testimonials-track",
);

testimonialsTrack
  .querySelectorAll(".homepage-testimonials-card")
  .forEach(function (card) {
    testimonialsTrack.appendChild(card.cloneNode(true));
  });

testimonialsTrack.addEventListener("mouseenter", function () {
  testimonialsTrack.classList.add("homepage-testimonials-track-paused");
});

testimonialsTrack.addEventListener("mouseleave", function () {
  testimonialsTrack.classList.remove("homepage-testimonials-track-paused");
});
