from django.urls import path
from .views import technical_analysis_api

urlpatterns = [
    path("api/technical-analysis/", technical_analysis_api),
]
