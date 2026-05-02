from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.events.views import EventViewSet
from apps.sports.views import OrganizationViewSet, SportViewSet
from config.views import health_check

router = DefaultRouter()
router.register("sports", SportViewSet, basename="sport")
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("events", EventViewSet, basename="event")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]
