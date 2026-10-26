const slides = document.querySelectorAll(".homepage-events-hero-slide");
const dots = document.querySelectorAll(".homepage-events-hero-dot");
const slideshow = document.querySelector(".homepage-events-hero");
let currentIndex = 0;
const AUTO_SCROLL_MS = 3000;
let autoScrollTimer = null;
let isHovered = false;

// Trusted, local SVG paths: four distinct outline motifs per event, used twice.
const eventDecorationPaths = {
  birthday: [
    '<path d="m4 4 2 4m7-5-2 4m5 5 3 2M4 17l4-2"/><circle cx="17" cy="5" r="1"/>',
    '<path d="m12 3 2.5 5 5.5.8-4 4 1 5.7-5-2.7-5 2.7 1-5.7-4-4L9.5 8z"/>',
    '<ellipse cx="12" cy="8" rx="5" ry="6"/><path d="m12 14-1 2h2l-1-2m0 2q-3 3 0 6"/>',
    '<path d="M4 10h16v11H4zm-1-4h18v4H3zm9 0v15m0-15C3 6 6-2 12 6c6-8 9 0 0 0"/>'
  ],
  seaside: [
    '<path d="M10 19C-4 7 6-2 12 6c6-8 16 1 2 13zm2-13v13M5 6l6 13M19 6l-6 13"/>',
    '<path d="m12 2 3 7 7 1-5 5 1 7-6-4-6 4 1-7-5-5 7-1z"/>',
    '<path d="M2 8q3-4 6 0t6 0t8 0M2 15q3-4 6 0t6 0t8 0"/>',
    '<circle cx="8" cy="13" r="3"/><circle cx="17" cy="9" r="2"/><circle cx="18" cy="17" r="1"/>'
  ],
  concert: [
    '<path d="M8 17V5l12-3v12M8 8l12-3"/><ellipse cx="5" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="15" rx="3" ry="2"/>',
    '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><path d="M5 11a7 7 0 0 1 6-6m2 14a7 7 0 0 0 6-6"/>',
    '<path d="M4 10v7m4-12v16m4-18v18m4-15v12m4-9v6"/>',
    '<path d="m14 2-9 12h7l-2 8 9-13h-7z"/>'
  ],
  wedding: [
    '<circle cx="12" cy="12" r="2"/><path d="M10 10C1 8 7 1 12 8c5-7 11 0 2 2 9 2 5 10-1 5-1 9-10 5-5-1-9-1-5-9 2-4z"/>',
    '<path d="M4 21 20 3M8 16C-2 10 6 3 12 12m1-2c-3-9 6-11 7-7m-6 11c9 2 10-7 5-8"/>',
    '<circle cx="9" cy="14" r="6"/><circle cx="16" cy="14" r="6"/><path d="m6 5 3-3 3 3-3 3z"/>',
    '<circle cx="6" cy="12" r="2"/><circle cx="13" cy="8" r="2.5"/><circle cx="19" cy="14" r="2"/>'
  ],
  car: [
    '<path d="M2 15v-5l4-1 3-5h7l3 5 3 1v5H2zm4-6h13M10 5l-2 4m6-4v4"/><circle cx="6" cy="16" r="2"/><circle cx="18" cy="16" r="2"/>',
    '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><path d="m12 3 0 6m0 6v6M3 12h6m6 0h6M6 6l4 4m4 4 4 4M6 18l4-4m4-4 4-4"/>',
    '<path d="M5 22V3q7-4 14 0v11q-7-4-14 0m4-12v10m5-11v11M5 6h14M5 10h14"/>',
    '<path d="M3 6h15M6 12h15M2 18h14"/>'
  ],
  conference: [
    '<path d="M2 4q5-2 10 1 5-3 10-1v15q-5-2-10 1-5-3-10-1zm10 1v15M5 8l4 1m6 0 4-1"/>',
    '<rect x="4" y="3" width="16" height="13" rx="1"/><path d="m4 16-3 4h22l-3-4M8 7h8"/>',
    '<path d="m4 20 1-5L17 3l4 4L9 19zm1-5 4 4M15 5l4 4"/>',
    '<path d="M3 3h18v13H3zm9 13v6m-5 0 5-3 5 3M7 12l4-4 3 2 4-4"/>'
  ]
};

const decorationFrame = slideshow.querySelector('.homepage-events-frame');
const decorationLayers = new Map();
Object.entries(eventDecorationPaths).forEach(function ([theme, paths]) {
  const layer = document.createElement('div');
  layer.className = 'homepage-event-decorations';
  layer.dataset.theme = theme;
  for (let index = 0; index < 8; index++) {
    const icon = document.createElement('span');
    icon.className = 'homepage-event-decoration';
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    svg.innerHTML = paths[index % paths.length];
    icon.appendChild(svg);
    layer.appendChild(icon);
  }
  decorationFrame.appendChild(layer);
  decorationLayers.set(theme, layer);
});

function showSlide(index) {
  slideshow.dataset.eventTheme = slides[index].dataset.eventTheme;
  decorationLayers.forEach(function (layer, theme) {
    layer.classList.toggle('homepage-event-decorations-active',
      theme === slideshow.dataset.eventTheme);
  });
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

showSlide(currentIndex);
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
