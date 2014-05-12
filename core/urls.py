from django.conf.urls import patterns, url
from core import views

urlpatterns = patterns('',
    url(r'^store$', views.store_history, name='store_history'),
    # url(r'^send/(?P<user_id>\d+)$', views.send_history, name='send_history'),
    url(r'^$', views.home, name='home'),
    # url(r'^testLoad$', views.testLoad, name='testLoad'),
    url(r'^login$', views.login, name='login'),
    url(r'^logout$', views.logout, name='logout'),
    url(r'^blocked_sites$', views.send_blocked_sites, name='send_blocked_sites'),
    url(r'^save_blocked_site$', views.store_blocked_sites, name='store_blocked_sites'),
    url(r'^last_time/(?P<extension_id>\d+)$', views.send_most_recent_history_time, name='send_most_recent_history_time'),    
    url(r'^new_ext_id$', views.send_new_extension_id, name='send_new_extension_id'),
    # url(r'^user_id$', views.send_user_id, name='send_user_id'),
    url(r'^team$', views.team, name='team'),
    url(r'^broken_link$', views.broken_link, name='broken_link'),
    url(r'^about$', views.about, name='about'),
    url(r'^install$', views.install, name='install'),
    url(r'^setextension$', views.set_extension_downloaded, name='set_extension_downloaded'),
    url(r'^rank/(?P<page>\d+)$', views.send_ranked_urls, name='send_ranked_urls'),
    #url(r'^rank/(?P<user_id>\d+)$', views.send_ranked_urls_u, name='send_ranked_urls_u'),
    url(r'^explore$', views.explore, name='explore'),
    url(r'^ext_lock$', views.send_ext_locked, name='send_ext_locked'),
    url(r'^settings$', views.settings, name='settings'),
    url(r'^up_vote$', views.up_vote, name='up_vote'),
    url(r'^down_vote$', views.down_vote, name='down_vote')
)
