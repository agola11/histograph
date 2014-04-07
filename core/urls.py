from django.conf.urls import patterns, url
from core import views

urlpatterns = patterns('',
    url(r'^store$', views.store_history, name='store_history'),
    url(r'^send/(?P<user_id>\d+)$', views.send_history, name='send_history'),
    url(r'^about$', views.about, name='about'),
    url(r'^testLoad$', views.testLoad, name='testLoad'),
    url(r'^login$', views.login, name='login'),
    url(r'^logout$', views.logout, name='logout'),
    url(r'^blocked_sites/(?P<user_id>\d+)$', views.send_blocked_sites, name='send_blocked_sites'),
    url(r'^last_time/(?P<extension_id>\d+)$', views.send_most_recent_history_time, name='send_most_recent_history_time'),    
    url(r'^new_ext_id$', views.send_new_extension_id, name='send_new_extension_id'),
    url(r'^team$', views.team, name='team'),
    url(r'^what$', views.what, name='what'),
    url(r'^manage$', views.manage, name='manage'),
    url(r'^freq/(?P<user_id>\d+)$', views.send_frequencies, name='send_frequencies'),
    url(r'^rank/(?P<user_id>\d+)$', views.send_ranked_urls, name='send_ranked_urls'),
)
