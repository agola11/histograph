from django.conf.urls import patterns, url
from graph import views

urlpatterns = patterns('', 
    url(r'^bubble/(?P<timesetting>\w+)$', views.send_bubble, name='bubble'), 
    url(r'^bubble_blocked$', views.send_bubble_blocked, name='bubble_blocked'), 
    url(r'^line$', views.send_line_plot, name='user_line'),
    url(r'^lineplot$', views.line_plot, name='line_plot'),
    url(r'^sunburst$', views.sunburst, name='sunburst'),
    url(r'^circle$', views.circle, name='circle'), 
    url(r'^digraphdata/(?P<timesetting>\w+)$', views.send_digraph, name='send_digraph'),
    url(r'^digraph$', views.digraph, name='digraph'),
    url(r'^friends$', views.friends, name='friends'),
    url(r'^friendsdata$', views.send_friends, name='send_friends'),
)
