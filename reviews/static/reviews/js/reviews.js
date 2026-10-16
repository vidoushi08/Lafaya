const ratingButtons = document.querySelectorAll(".reviews-rating-button");
const reviewForm = document.querySelector(".reviews-form");
const reviewFormStatus = document.querySelector(".reviews-form-status");

ratingButtons.forEach(function (button) {
  button.addEventListener("click", function () {
    const selectedRating = Number(button.dataset.rating);

    ratingButtons.forEach(function (ratingButton) {
      const isSelected = Number(ratingButton.dataset.rating) <= selectedRating;
      const icon = ratingButton.querySelector("i");

      ratingButton.classList.toggle("reviews-rating-button-selected", isSelected);
      ratingButton.setAttribute("aria-checked", String(Number(ratingButton.dataset.rating) === selectedRating));
      icon.classList.toggle("fa-solid", isSelected);
      icon.classList.toggle("fa-regular", !isSelected);
    });
  });
});

reviewForm.addEventListener("submit", function (event) {
  event.preventDefault();
  reviewFormStatus.textContent =
    "Review submission is not connected yet. Your review has not been submitted.";
});
