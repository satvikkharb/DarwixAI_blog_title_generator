from django.contrib import admin
from .models import TitleSuggestionRequest


class TitleSuggestionRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'get_content_preview', 'get_titles_preview')
    list_filter = ('created_at',)
    search_fields = ('content', 'suggested_titles')
    readonly_fields = ('created_at',)
    
    def get_content_preview(self, obj):
        max_length = 100
        if len(obj.content) > max_length:
            return obj.content[:max_length] + '...'
        return obj.content
    get_content_preview.short_description = 'Content Preview'
    
    def get_titles_preview(self, obj):
        titles = obj.get_suggested_titles_list()
        if not titles:
            return '-'
        return ', '.join(titles)
    get_titles_preview.short_description = 'Suggested Titles'


admin.site.register(TitleSuggestionRequest, TitleSuggestionRequestAdmin)