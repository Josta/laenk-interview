from django.views import View
from django.db.models import Count, OuterRef, Subquery, IntegerField
from django.http import JsonResponse
from appliers.models import Applier, ScreeningQuestion


class Applier2ViewSet(View):
    def get(self, request, *args, **kwargs):
        # this avoids an expensive post-join/aggregate having clause by performing a subquery first
        questions_query = ScreeningQuestion.objects.values("application_id").annotate(
            question_count=Count("id")
        ).filter(question_count__gt=16)
        
        ids = list(map(lambda x: x["application_id"], questions_query))
        appliers_query = Applier.objects.filter(id__in=ids)

        data = []
        for applier in appliers_query:
            data.append(
                {
                    "applier_id": applier.id,
                    "external_id": applier.external_id,
                    "qualified": applier.qualified,
                    "user": {
                        "user_id": applier.user.id,
                        "first_name": applier.user.first_name,
                        "last_name": applier.user.last_name,
                        "email": applier.user.email,
                    },
                    "source": applier.source,
                    "created_at": applier.created_at,
                }
            )

        return JsonResponse(data, safe=False)
