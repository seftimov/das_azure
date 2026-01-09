from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('', views.login_user, name='login'),
    path('login_user/', views.login_user, name='login'),
    path('logout_user/', views.logout_user, name='logout'),
    path('signup_user/', views.signup_user, name='signup'),
    path('coin/<str:symbol>/', views.coin_detail, name='coin_detail'),
    path("technical-analysis/", views.technical_analysis_page, name="technical_analysis_page"),
    path("lstm/", views.lstm_page, name="lstm_page"),
    path("onchain-sentiment/", views.onchain_sentiment_page, name="onchain_sentiment_page"),
    path("onchain-sentiment/refresh/", views.trigger_onchain_sentiment_pipeline, name="trigger_onchain_sentiment_pipeline"),
]
