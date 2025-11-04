from django.contrib import admin
from .models import Knowledge
# Register your models here.
@admin.register(Knowledge)
class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'updated_at')
