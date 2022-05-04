from re import template
from django.contrib import admin
from django.urls import path
from gee import views

urlpatterns = [
    
    path('', views.index, name="index"),
    path('map/', views.map, name="map"),
    path('ee/', views.asyncEE, name="asyncEE")
]
