from django.contrib import messages
from django.db.models import Avg, Count
from django.shortcuts import redirect, render

from common.decorators import account_type_required

from .forms import ReviewForm
from .models import Review


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
    summary = published.aggregate(average=Avg("rating"), count=Count("id"))
    distribution = {
        rating: published.filter(rating=rating).count()
        for rating in range(5, 0, -1)
    }
    own_reviews = Review.objects.filter(customer=request.user).select_related("booking")
    return render(
        request,
        "reviews/reviews.html",
        {
            "form": form,
            "reviews": published[:20],
            "average_rating": summary["average"] or 0,
            "review_count": summary["count"],
            "rating_distribution": distribution,
            "own_reviews": own_reviews,
            "eligible_booking_count": form.fields["booking"].queryset.count(),
        },
    )
