from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('', views.login, name='login'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('coin/<str:symbol>/', views.coin_detail, name='coin_detail'),
]
