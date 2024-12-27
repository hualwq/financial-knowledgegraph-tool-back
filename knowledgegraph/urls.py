"""knowledgegraph URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('addnode/', views.add_node, name='add_node'),
    path('addnodeexcel/', views.add_node_excel, name='add_node_excel'),
    path('querynode/', views.query_node, name='query_node'),
    path('deletenode/', views.delete_node, name='delete_node'),
    path('addrelationshipexcel/', views.add_relationship_excel, name='add_relationship'),
    path('queryrelationship/', views.query_relationship, name='query_relationship'),
    path('querynodeexcel/', views.query_node_excel, name='query_node_excel'),
    path('comparename/', views.compare_name, name='compare_name'),
    path('test/', views.test, name='test'),
    path('fuzzymatch/', views.fuzzymatch, name='fuzzymatch'),
    path('generatequery/', views.generatequery, name='generatequery'),
    path('getprogress/',  views.getprogress, name='getprogress')
]

























