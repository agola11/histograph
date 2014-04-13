from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core import serializers
from core.models import HistoryNode, ExtensionID, BlockedSite, create_history_nodes_from_json, HistographUser
from datetime import datetime
from django.template import RequestContext, loader
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.models import Session
from django.utils import simplejson
from django.db.models import Max
from django.contrib.auth import logout as django_logout
from itertools import islice
import django_facebook
import json
import rec_algo

# TODO: change to simplejson?
def send_history(request, user_id):
  resp = HttpResponse()
  serializers.serialize('json', HistoryNode.objects.filter(user__id=int(user_id)), stream=resp)
  return HttpResponse(resp, content_type="application/json")

def send_most_recent_history_time(request, extension_id):
  hn = HistoryNode.objects.filter(extension_id=extension_id)
  if len(hn) == 0:
    t = {'visit_time__max': 0}
  else:
    t = hn.aggregate(Max('visit_time'))
  return HttpResponse(simplejson.dumps(t), content_type="application/json")

def send_blocked_sites(request):
  if request.user.is_authenticated():
    sites = BlockedSite.objects.filter(user=request.user)
    urls = map(lambda x: x.url, sites)
    return HttpResponse(simplejson.dumps(urls), content_type="application/json")
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

def store_blocked_sites(request):
  payload = json.loads(request.body)
  bs = BlockedSite()
  bs.url = payload['url']
  bs.user = request.user
  bs.save()

def send_new_extension_id(request):
  extid = ExtensionID.objects.get(pk=1)
  data = {'extension_id': extid.next_id}
  extid.next_id = extid.next_id + 1
  extid.save()
  return HttpResponse(simplejson.dumps(data), content_type="application/json")

def send_user_id(request):
  if request.user.is_authenticated():
    data = {'user_id': request.user.id, 'is_auth': 1}
    return HttpResponse(simplejson.dumps(data), content_type="application/json")
  else:
    data = {'user_id': 0, 'is_auth': 0}
    return HttpResponse(simplejson.dumps(data), content_type="application/json")

def store_history(request):
  if request.user.is_authenticated():
    payload = json.loads(request.body)
    create_history_nodes_from_json(payload, request.user)
  
    resp = HttpResponse()
    resp.status_code = 200
    return resp
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

def home(request):
  if (request.user.is_authenticated() == False):
    return redirect(login)
  if (request.user.ext_downloaded == False):
    return redirect(install)
  domain = get_current_site(request).domain
  template = loader.get_template('core/home.html')
  userT = request.user
  things = dir(userT)
  downloaded = dir(request.user)
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'authenticated': request.user.is_authenticated(),
        'user_fullname' : request.user.get_full_name(),
        'downloaded' : request.user.ext_downloaded,
        'id': request.user.id,
        # 'friends': django_facebook.api.facebook_profile_data(),
  })
  return HttpResponse(template.render(context))

def explore(request):
  domain = get_current_site(request).domain
  template = loader.get_template('core/explore.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_fullname' : request.user.get_full_name(),
  })
  return HttpResponse(template.render(context))

def testLoad(request):
  domain = get_current_site(request).domain
  template = loader.get_template('core/testLoad.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
  })
  return HttpResponse(template.render(context))

def login(request):
  if request.user.is_authenticated():
    return redirect(home)
  template = loader.get_template('core/login.html')
  context = RequestContext(request)
  return HttpResponse(template.render(context))

def logout(request):
    django_logout(request)
    return redirect(login)

def team(request):
  domain = get_current_site(request).domain
  template = loader.get_template('core/team.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_fullname' : request.user.get_full_name(),
  })
  return HttpResponse(template.render(context))

def about(request):
  domain = get_current_site(request).domain
  template = loader.get_template('core/about.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_fullname' : request.user.get_full_name(),
  })
  return HttpResponse(template.render(context))

def install(request):
  domain = get_current_site(request).domain
  template = loader.get_template('core/install.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_fullname' : request.user.get_full_name(),
        'user': request.user
  })
  return HttpResponse(template.render(context))

def setextension(request):
  domain = get_current_site(request).domain
  request.user.ext_downloaded = True
  request.user.save()
  if (request.user.is_authenticated() == True):
    return redirect(home)
  else: return redirect(login)


def recommendations(request):
  template = loader.get_template('core/recommendations.html')
  url_dict = rec_algo.rank_urls(request.user.id)
  context = RequestContext(request, {
      'first' : url_dict[:25]
    })
  return HttpResponse(template.render(context))

def manage(request):
  domain = get_current_site(request).domain
  template = loader.get_template('core/manage.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_id' : request.user.id,
  })
  return HttpResponse(template.render(context))

def send_frequencies(request, user_id):
  freq_dict = rec_algo.get_frequencies(int(user_id))
  return HttpResponse(simplejson.dumps(freq_dict), content_type='application/json')

def send_ranked_urls(request):
  url_dict = rec_algo.rank_urls(request.user.id)
  return HttpResponse(simplejson.dumps(url_dict), content_type='application/json')

