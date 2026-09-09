"""
URL configuration for Lafaya project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("homepage.urls")),
    path("authentication/", include("authentication.urls")),
    path("customer_dashboard/", include("customer_dashboard.urls")),
    path("staff/", include("staff.urls")),
    path("birthday/", include("birthday.urls")),
    path("wedding/", include("wedding.urls")),
    path("concert/", include("concert.urls")),
    path("seaside/", include("seaside.urls")),
    path("conference/", include("conference.urls")),
    path("car_events/", include("car_events.urls")),
    path("payments/", include("payments.urls")),
    path("reviews/", include("reviews.urls")),
    path("booking/", include("booking.urls")),
    path("admin/", admin.site.urls),
]
