from django.conf.urls import patterns, url
from graph import views

urlpatterns = patterns('',
    url(r'^bubble$', views.send_bubble, name='bubble'),
)
