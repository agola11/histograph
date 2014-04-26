from django.conf.urls import patterns, url
from graph import views

urlpatterns = patterns('', 
    url(r'^bubble/(?P<user_id>\d+)$', views.send_user_bubble, name='user_bubble'),
    url(r'^bubble/(?P<starttime>\d+)/(?P<endtime>\d+)$', views.send_bubble, name='bubble'), 
    url(r'^pie$', views.pie, name='pie'),
    url(r'^line/(?P<starttime>\d+)/(?P<endtime>\d+)$', views.send_line_plot, name='line'),
    url(r'^line/(?P<user_id>\d+)$', views.send_user_line_plot, name='user_line'),
    url(r'^lineplot$', views.line_plot, name='line_plot'),
    url(r'^sunburst/(?P<user_id>\d+)$', views.user_sunburst, name='user_sunburst'),
    url(r'^sunburst$', views.sunburst, name='sunburst'),
    url(r'^circle$', views.circle, name='circle'), 
    url(r'^digraphdata/(?P<starttime>\d+)/(?P<endtime>\d+)$', views.send_digraph, name='send_digraph'),
    url(r'^digraph$', views.digraph, name='digraph'),
    url(r'^friends$', views.friends, name='friends'),
)
