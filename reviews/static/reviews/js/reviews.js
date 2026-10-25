const ratingButtons = document.querySelectorAll(".reviews-rating-button");
const reviewForm = document.querySelector(".reviews-form");

if (reviewForm) {
  const ratingInput = reviewForm.querySelector('[name="rating"]');
  const hint = reviewForm.querySelector(".reviews-rating-hint");

  function selectRating(rating) {
    ratingInput.value = rating;
    ratingButtons.forEach(function (button) {
      const value = Number(button.dataset.rating);
      const active = value <= rating;
      const icon = button.querySelector("i");
      button.classList.toggle("reviews-rating-button-selected", active);
      button.setAttribute("aria-checked", String(value === rating));
      icon.classList.toggle("fa-solid", active);
      icon.classList.toggle("fa-regular", !active);
    });
    hint.textContent = `${rating} out of 5 stars selected`;
  }

  ratingButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      selectRating(Number(button.dataset.rating));
    });
  });

  if (ratingInput.value) selectRating(Number(ratingInput.value));
}
