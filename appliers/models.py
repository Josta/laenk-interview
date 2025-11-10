from django.db import models
from django.contrib.gis.db import models as gis_models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(TimeStampedModel):
    external_id = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    resume = models.FileField(upload_to="resumes/")
    cover_letter = models.TextField()
    country = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Applier(TimeStampedModel):
    QUALIFIED_CHOICES = [
        ("YES", "Yes"),
        ("NO", "No"),
        ("PENDING", "Pending"),
    ]

    external_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.JSONField(null=True, blank=True)
    qualified = models.CharField(
        max_length=20, choices=QUALIFIED_CHOICES, null=True, blank=True
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    # PostGIS PointField for efficient spatial queries
    # Using geography=True for accurate distance calculations on Earth's surface
    location = gis_models.PointField(geography=True, null=True, blank=True, srid=4326)


class ScreeningQuestion(TimeStampedModel):
    application = models.ForeignKey(
        Applier, on_delete=models.CASCADE, related_name="screening_questions"
    )
    question = models.TextField()
    type = models.CharField(max_length=50)
    answer = models.TextField(null=True, blank=True)
    is_skipped = models.BooleanField(default=False)

    def __str__(self):
        return self.id

    class Meta:
        ordering = ["-id"]
