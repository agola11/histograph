from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static


from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'histograph.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^core/', include('core.urls')),
    url(r'^graph/', include('graph.urls')),
    url(r'^admin/', include(admin.site.urls)),
    

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

