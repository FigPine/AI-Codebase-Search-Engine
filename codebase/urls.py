from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_repo, name='upload_repo'),
    path('ask/', views.ask_question, name='ask_question'),
]