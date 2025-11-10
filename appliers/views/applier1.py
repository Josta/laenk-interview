from django.views import View
from django.db.models import Count, Subquery
from django.http import JsonResponse
from appliers.models import Applier, ScreeningQuestion

class Applier1ViewSet(View):
    def get(self, request, *args, **kwargs):
        appliers_query = Applier.objects.annotate(
            question_count=Count("screening_questions")
        ).filter(question_count__gt=16)

        sql = str(appliers_query.query);

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