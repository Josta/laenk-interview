from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appliers', '0002_alter_screeningquestion_options_applier_latitude_and_more'),
    ]

    operations = [
        CreateExtension('postgis'),
    ]
