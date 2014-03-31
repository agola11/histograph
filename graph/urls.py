from django.conf.urls import patterns, url
from graph import views

urlpatterns = patterns('',
    url(r'^bubble/(?P<user_id>\d+)$', views.send_user_bubble, name='user_bubble'),
    url(r'^bubble$', views.send_bubble, name='bubble')
)
