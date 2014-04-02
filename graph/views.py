from django.shortcuts import render
from core.models import HistoryNode, create_history_nodes_from_json
from django.core import serializers
from django.http import HttpResponse
from string import split
from django.utils import simplejson
from django.contrib.sites.models import get_current_site
from django.template import RequestContext, loader
from datetime import datetime
import json
from django.http import Http404
from urlparse import urlparse
import graph_utils

def circle(request):
  domain = get_current_site(request).domain
  template = loader.get_template('graph/circle.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        })
  return HttpResponse(template.render(context))

def pie(request): 
  domain = get_current_site(request).domain
  template = loader.get_template('graph/pie.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        })
  return HttpResponse(template.render(context))

def sunburst(request): 
  domain = get_current_site(request).domain
  template = loader.get_template('graph/sunburst.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        })
  return HttpResponse(template.render(context))

def send_user_bubble(request, user_id):
	hn_list = list(HistoryNode.objects.filter(extension_id=int(user_id)).values('url','extension_id'))
	bubble_tree = graph_utils.send_bubble(hn_list)
	return HttpResponse(simplejson.dumps(bubble_tree), content_type='application/json')

def send_bubble(request):
	hn_list = list(HistoryNode.objects.values('url','extension_id'))
	bubble_tree = graph_utils.send_bubble(hn_list)
	return HttpResponse(simplejson.dumps(bubble_tree), content_type='application/json')
