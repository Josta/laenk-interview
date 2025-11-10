from django.views import View
from django.db.models import Count
from django.http import JsonResponse
from appliers.models import Applier
from appliers.serializers import ApplierSerializer


class Applier1ViewSet(View):
    def get(self, request, *args, **kwargs):
        appliers_query = (
            Applier.objects.select_related("user")
            .annotate(question_count=Count("screening_questions"))
            .filter(question_count__gt=16)
        )

        data = [ApplierSerializer.to_dict(applier) for applier in appliers_query]

        return JsonResponse(data, safe=False)