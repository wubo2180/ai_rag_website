from django.db import migrations


def ensure_sha256_hash_column(apps, schema_editor):
    File = apps.get_model("ocr", "File")
    table_name = File._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        existing_tables = set(schema_editor.connection.introspection.table_names(cursor))

    if table_name not in existing_tables:
        # 兼容空库场景：该迁移仅用于已有 legacy OCR 表结构的平滑对齐。
        return

    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }

    if "sha256_hash" in existing_columns:
        return

    field = File._meta.get_field("sha256_hash")
    schema_editor.add_field(File, field)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("ocr", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(ensure_sha256_hash_column, migrations.RunPython.noop),
    ]
