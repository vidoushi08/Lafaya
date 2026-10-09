from django.shortcuts import render

from common.decorators import account_type_required


@account_type_required("customer")
def index(request):
    return render(request, "customer_dashboard/dashboard.html")
