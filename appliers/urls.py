from django.urls import path

from appliers.views.list1 import Applier1ViewSet
from appliers.views.list2 import Applier2ViewSet
from appliers.views.search import SearchViewSet

urlpatterns = [
    path("list/", Applier1ViewSet.as_view()),
    path("list2/", Applier2ViewSet.as_view()),
    path("search", SearchViewSet.as_view(), name="appliers-search"),
]
