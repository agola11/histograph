from django.conf.urls import patterns, url
from core import views

urlpatterns = patterns('',
    url(r'^store', views.store_history, name='store_history')
    url(r'^send', views.store_history, name='send_history')

)
