from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'histograph.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^core/', include('core.urls')),
    url(r'^testapp/', include('testapp.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^homeApp/', include('homeApp.urls')),
)

