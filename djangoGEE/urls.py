from re import template
from django.contrib import admin
from django.urls import path
from gee import views

urlpatterns = [
    
    path('', views.index, name="index"),
    path('map/', views.map, name="map"),
    path('ee/', views.asyncEE, name="asyncEE"),


    path('water_quality/', views.water_quality_index, name='water_quality_index'),
    path('water_quality_map/', views.water_quality_map, name="water_quality_map"),
    path('water_quality_ee/', views.water_quality_asyncEE, name="water_quality_asyncEE")
]
