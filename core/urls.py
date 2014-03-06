from django.conf.urls import patterns, url
from core import views

urlpatterns = patterns('',
    url(r'^$', views.store_history, name='store_history')
)
