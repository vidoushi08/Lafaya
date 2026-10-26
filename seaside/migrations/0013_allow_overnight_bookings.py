from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("seaside", "0012_clarify_package_features"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="seasidebookingrequest",
            name="seaside_request_end_after_start",
        ),
        migrations.AddConstraint(
            model_name="seasidebookingrequest",
            constraint=models.CheckConstraint(
                condition=~models.Q(("end_time", models.F("start_time"))),
                name="seaside_request_end_differs_from_start",
            ),
        ),
    ]
