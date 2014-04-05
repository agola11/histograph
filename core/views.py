from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from core.models import HistoryNode, ExtensionID, BlockedSite, create_history_nodes_from_json
from datetime import datetime
from django.template import RequestContext, loader
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.models import Session
from django.utils import simplejson
from django.db.models import Max
import json
import rec_algo

# TODO: change to simplejson?
def send_history(request):
  resp = HttpResponse()
  serializers.serialize('json', HistoryNode.objects.all(), stream=resp)
  return HttpResponse(resp, content_type="application/json")

def send_most_recent_history_time(request, extension_id):
  hn = HistoryNode.objects.filter(extension_id=extension_id)
  if len(hn) == 0:
    t = {'visit_time__max': 0}
  else:
    t = hn.aggregate(Max('visit_time'))
  return HttpResponse(simplejson.dumps(t), content_type="application/json")

def send_blocked_sites(request, user_id):
  sites = BlockedSite.objects.filter(user__id=user_id)
  urls = map(lambda x: x.url, sites)
  return HttpResponse(simplejson.dumps(urls), content_type="application/json")

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
    create_history_nodes_from_json(payload)
  
    resp = HttpResponse()
    resp.status_code = 200
    return resp
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

def about(request):
  domain = get_current_site(request).domain
  template = loader.get_template('core/about.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
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
    return HttpResponse("AUTHENTICATED")
  template = loader.get_template('core/login.html')
  context = RequestContext(request)
  return HttpResponse(template.render(context))

def send_frequencies(request, user_id):
  freq_dict = rec_algo.get_frequencies(int(user_id))
  return HttpResponse(simplejson.dumps(freq_dict), content_type='application/json')

def send_ranked_urls(request, user_id):
  url_dict = rec_algo.rank_urls(int(user_id))
  return HttpResponse(simplejson.dumps(url_dict), content_type='application/json')

