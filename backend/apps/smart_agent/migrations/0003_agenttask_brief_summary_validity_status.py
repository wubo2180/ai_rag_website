from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("smart_agent", "0002_alter_smartagent_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="agenttask",
            name="brief_summary",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="配方简要"),
        ),
        migrations.AddField(
            model_name="agenttask",
            name="validity_status",
            field=models.CharField(
                choices=[("pending", "待确认"), ("valid", "有效"), ("invalid", "无效")],
                default="pending",
                max_length=20,
                verbose_name="是否有效配方",
            ),
        ),
    ]
