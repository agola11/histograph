from django.conf.urls import patterns, url
from graph import views

urlpatterns = patterns('',
    url(r'^bubble$', views.send_bubble, name='bubble'),
    url(r'^circle$', views.circle, name='circle'),
    url(r'^pie$', views.pie, name='pie'),
)
