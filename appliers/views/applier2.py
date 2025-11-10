from django.views import View
from django.db.models import Count
from django.http import JsonResponse
from appliers.models import Applier, ScreeningQuestion
from appliers.serializers import ApplierSerializer


class Applier2ViewSet(View):
    def get(self, request, *args, **kwargs):
        # this avoids an expensive post-join/aggregate having clause by performing a subquery first
        questions_query = ScreeningQuestion.objects.values("application_id").annotate(
            question_count=Count("id")
        ).filter(question_count__gt=16)

        ids = list(map(lambda x: x["application_id"], questions_query))
        appliers_query = Applier.objects.select_related("user").filter(id__in=ids)

        data = [ApplierSerializer.to_dict(applier) for applier in appliers_query]

        return JsonResponse(data, safe=False)
