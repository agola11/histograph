from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from core.models import HistoryNode, create_history_nodes_from_json
from datetime import datetime
from django.template import RequestContext, loader
from django.contrib.sites.models import get_current_site
from django.utils import simplejson
import rec_algo

# TODO: change to simplejson?
def send_history(request):
  resp = HttpResponse()
  serializers.serialize('json', HistoryNode.objects.all(), stream=resp)
  return HttpResponse(resp, content_type="application/json")

def store_history(request):
  payload = simplejson.loads(request.body)
  create_history_nodes_from_json(payload)
  
  return HttpResponse("OK")

def about(request):
  domain = get_current_site(request).domain
  template = loader.get_template('core/about.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
  })
  return HttpResponse(template.render(context))

def send_frequencies(request):
  freq_dict = rec_algo.get_frequencies(10)
  return HttpResponse(simplejson.dumps(freq_dict), content_type='application/json')
