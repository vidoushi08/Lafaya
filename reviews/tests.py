from django.test import TestCase
from django.urls import reverse


class ReviewsPageTests(TestCase):
    def test_reviews_page_renders_the_reference_inspired_content(self):
        response = self.client.get("/reviews/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer Reviews")
        self.assertContains(response, "128 verified reviews")
        self.assertContains(response, "Rating Distribution")
        self.assertContains(response, "Write Your Review")
        self.assertContains(response, "Seaside Luxury Redefined")
        self.assertContains(response, "reviews/css/reviews.css")
        self.assertContains(response, "reviews/js/reviews.js")
        self.assertContains(
            response,
            f'href="{reverse("customer_dashboard:customer_dashboard")}"',
        )

    def test_review_submission_is_not_claimed_as_persistent(self):
        response = self.client.get("/reviews/")

        self.assertContains(response, "Review posting is not connected yet")
        self.assertContains(response, 'aria-checked="false"')
