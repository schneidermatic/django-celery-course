from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.payload_list, name='list'),
    path('detail/<int:pk>/', views.payload_detail, name='detail'),
]
