from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0011_resumejobmatch_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobpost",
            name="views_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]