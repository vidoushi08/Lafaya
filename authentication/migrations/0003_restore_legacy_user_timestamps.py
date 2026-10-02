from django.db import migrations


def restore_legacy_timestamps(apps, schema_editor):
    connection = schema_editor.connection
    existing_tables = set(connection.introspection.table_names())
    if "auth_user" not in existing_tables:
        return

    legacy_user_table = connection.ops.quote_name("auth_user")
    user_table = connection.ops.quote_name("authentication_user")
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {user_table} "
            f"SET last_login = (SELECT last_login FROM {legacy_user_table} "
            f"WHERE {legacy_user_table}.id = {user_table}.id), "
            f"date_joined = (SELECT date_joined FROM {legacy_user_table} "
            f"WHERE {legacy_user_table}.id = {user_table}.id) "
            f"WHERE id IN (SELECT id FROM {legacy_user_table})"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0002_repoint_admin_log_user"),
    ]

    operations = [
        migrations.RunPython(restore_legacy_timestamps, migrations.RunPython.noop),
    ]