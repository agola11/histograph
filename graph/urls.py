from django.conf.urls import patterns, url
from graph import views

urlpatterns = patterns('', 
    url(r'^bubble/(?P<user_id>\d+)$', views.send_user_bubble, name='user_bubble'),
    url(r'^bubble$', views.send_bubble, name='bubble'), 
    url(r'^pie$', views.pie, name='pie'),
    url(r'^line$', views.send_line_plot, name='line'),
    url(r'^line/(?P<user_id>\d+)$', views.send_user_line_plot, name='user_line'),
    url(r'^sunburst/(?P<user_id>\d+)$', views.user_sunburst, name='user_sunburst'),
    url(r'^sunburst$', views.sunburst, name='sunburst'),
    url(r'^circle$', views.circle, name='circle'), 
    url(r'^digraph/(?P<user_id>\d+)$', views.user_digraph, name='user_digraph'),
)
