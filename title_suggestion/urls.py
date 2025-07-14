from django.urls import path
from .views import TitleSuggestionView

urlpatterns = [
    path('suggest-titles/', TitleSuggestionView.as_view(), name='suggest-titles'),
]