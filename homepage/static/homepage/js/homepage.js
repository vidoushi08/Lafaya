var slides = document.querySelectorAll(".homepage-events-hero-slide");
var dots = document.querySelectorAll(".homepage-events-hero-dot");

function showSlide(index) {
  slides.forEach(function (slide, i) {
    slide.classList.toggle("homepage-events-hero-slide-active", i === index);
  });
  dots.forEach(function (dot, i) {
    dot.classList.toggle("homepage-events-hero-dot-active", i === index);
  });
}

dots.forEach(function (dot, index) {
  dot.addEventListener("click", function () {
    showSlide(index);
  });
});
