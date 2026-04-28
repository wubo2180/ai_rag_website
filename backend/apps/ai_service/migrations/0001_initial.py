# Generated manually for KnowledgeExtractionHistory model
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='KnowledgeExtractionHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(db_index=True, default='anonymous', max_length=128, verbose_name='用户标识')),
                ('file_name', models.CharField(max_length=255, verbose_name='文件名')),
                ('file_type', models.CharField(blank=True, default='', max_length=20, verbose_name='文件类型')),
                ('file_size', models.BigIntegerField(default=0, verbose_name='文件大小(字节)')),
                ('status', models.CharField(choices=[('success', '成功'), ('failed', '失败')], default='success', max_length=20, verbose_name='抽取状态')),
                ('item_count', models.IntegerField(default=0, verbose_name='抽取条目数')),
                ('elapsed_time', models.FloatField(blank=True, null=True, verbose_name='耗时(秒)')),
                ('error_message', models.TextField(blank=True, default='', verbose_name='错误信息')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '知识抽取历史',
                'verbose_name_plural': '知识抽取历史',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='knowledgeextractionhistory',
            index=models.Index(fields=['user_id', '-created_at'], name='ai_service__user_id_313cb6_idx'),
        ),
    ]
