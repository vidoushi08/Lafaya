from django.db import migrations, models
from django.db.models import Q


def clear_superuser_account_types(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    User.objects.using(schema_editor.connection.alias).filter(
        is_superuser=True,
    ).update(account_type="")


def restore_superuser_account_types(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    User.objects.using(schema_editor.connection.alias).filter(
        is_superuser=True,
    ).update(account_type="customer")


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0005_alter_user_gender"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="account_type",
            field=models.CharField(
                blank=True,
                choices=[("customer", "Customer"), ("staff", "Staff")],
                default="customer",
                max_length=10,
            ),
        ),
        migrations.RunPython(
            clear_superuser_account_types,
            restore_superuser_account_types,
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=(
                    Q(is_superuser=True, account_type="")
                    | Q(
                        is_superuser=False,
                        account_type__in=["customer", "staff"],
                    )
                ),
                name="user_account_type_matches_superuser",
            ),
        ),
    ]
