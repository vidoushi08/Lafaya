from django.contrib import messages
from django.shortcuts import redirect, render

from common.decorators import account_type_required
from .forms import StaffProfileForm


@account_type_required("staff")
def index(request):
	form = StaffProfileForm(request.POST or None, instance=request.user)
	if request.method == "POST":
		if form.is_valid():
			form.save()
			messages.success(request, "Your profile has been updated.")
			return redirect("staff_profile:profile")

	return render(
		request,
		"staff_profile/profile.html",
		{"form": form},
	)
