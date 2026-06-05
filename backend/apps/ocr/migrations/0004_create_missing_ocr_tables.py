from django.db import migrations


def create_missing_ocr_tables(apps, schema_editor):
    existing_tables = set(schema_editor.connection.introspection.table_names())
    ocr_models = list(apps.get_app_config("ocr").get_models())

    for model in ocr_models:
        table_name = model._meta.db_table
        if table_name in existing_tables:
            continue
        schema_editor.create_model(model)
        existing_tables.add(table_name)


def ensure_default_ocr_user(apps, schema_editor):
    User = apps.get_model("ocr", "User")
    User.objects.get_or_create(
        id=1,
        defaults={
            "username": "system",
            "email": "system@example.local",
            "password_hash": "!",
            "real_name": "System",
            "role": "admin",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("ocr", "0003_ensure_sha256_hash_column"),
    ]

    operations = [
        migrations.RunPython(create_missing_ocr_tables, migrations.RunPython.noop),
        migrations.RunPython(ensure_default_ocr_user, migrations.RunPython.noop),
    ]
