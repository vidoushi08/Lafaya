from django.db import migrations


def repoint_admin_log_user(apps, schema_editor):
    LogEntry = apps.get_model("admin", "LogEntry")
    User = apps.get_model("authentication", "User")
    old_field = LogEntry._meta.get_field("user")
    new_field = old_field.clone()
    new_field.remote_field.model = User
    new_field.remote_field.field_name = User._meta.pk.name
    new_field.set_attributes_from_name("user")
    new_field.model = LogEntry
    schema_editor.alter_field(LogEntry, old_field, new_field, strict=True)


class Migration(migrations.Migration):
    dependencies = [
        ("admin", "0003_logentry_add_action_flag_choices"),
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(repoint_admin_log_user, migrations.RunPython.noop),
    ]