from django.urls import path

from appliers.views import ApplierViewSet

urlpatterns = [
    path("list/", ApplierViewSet.as_view()),
]
