from django.urls import path
from . import views

app_name = 'pdf_loader'

urlpatterns = [
    path('', views.index, name='index'),
]
