from django.contrib import messages
from django.shortcuts import redirect, render

from common.decorators import account_type_required

from .forms import ReviewForm
from .models import Review, ReviewShowcase


@account_type_required("customer")
def index(request):
    form = ReviewForm(request.POST or None, customer=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request,
            "Thank you. Your review was submitted and is awaiting moderation.",
        )
        return redirect("reviews:reviews")

    published = Review.objects.filter(status=Review.Status.PUBLISHED).select_related(
        "customer", "booking"
    )
    review_cards = [
        {
            "author_name": review.customer.get_full_name() or review.customer.username,
            "created_at": review.created_at,
            "rating": review.rating,
            "event_name": review.booking.event_name or review.booking.event_type,
            "event_type": review.booking.event_type,
            "event_date": review.booking.event_date,
            "comment": review.comment,
        }
        for review in published
    ]
    review_cards.extend(
        {
            "author_name": snapshot.display_name,
            "created_at": snapshot.created_at,
            "rating": snapshot.rating,
            "event_name": snapshot.event_type,
            "event_type": snapshot.event_type,
            "event_date": snapshot.event_date,
            "comment": snapshot.comment,
        }
        for snapshot in ReviewShowcase.objects.all()
    )
    review_cards.sort(key=lambda card: card["created_at"], reverse=True)
    review_count = len(review_cards)
    average_rating = (
        sum(card["rating"] for card in review_cards) / review_count
        if review_count
        else 0
    )
    rating_distribution = {
        rating: sum(card["rating"] == rating for card in review_cards)
        for rating in range(5, 0, -1)
    }
    own_reviews = Review.objects.filter(customer=request.user).select_related("booking")
    return render(
        request,
        "reviews/reviews.html",
        {
            "form": form,
            "reviews": review_cards[:20],
            "average_rating": average_rating,
            "review_count": review_count,
            "rating_distribution": rating_distribution,
            "own_reviews": own_reviews,
            "eligible_booking_count": form.fields["booking"].queryset.count(),
        },
    )
