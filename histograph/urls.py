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
    url(r'^accounts/', include('django_facebook.auth_urls')),    
    url(r'^facebook/', include('django_facebook.urls'))

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

