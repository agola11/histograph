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

def user_sunburst(request, user_id): 
  domain = get_current_site(request).domain
  template = loader.get_template('graph/sunburst-user.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_id': user_id,
        })
  return HttpResponse(template.render(context))

def sunburst(request): 
  domain = get_current_site(request).domain
  template = loader.get_template('graph/sunburst.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        #'user_id': request.user.id,
        })
  return HttpResponse(template.render(context))

def send_user_bubble(request, user_id):
	hn_list = list(HistoryNode.objects.filter(user__id=int(user_id)).values('url'))
	bubble_tree = graph_utils.send_bubble(hn_list)
	return HttpResponse(simplejson.dumps(bubble_tree), content_type='application/json')

def send_bubble(request):
	hn_list = list(HistoryNode.objects.values('url'))
	bubble_tree = graph_utils.send_bubble(hn_list)
	return HttpResponse(simplejson.dumps(bubble_tree), content_type='application/json')

def send_user_line_plot(request, user_id):
	hn_list = list(HistoryNode.objects.filter(user__id=int(user_id)).values('url','visit_time'))
	line_data = graph_utils.send_line_plot(hn_list)
	return HttpResponse(simplejson.dumps(line_data), content_type='application/json')

def send_line_plot(request):
	hn_list = list(HistoryNode.objects.values('url','visit_time'))
	line_data = graph_utils.send_line_plot(hn_list)
	return HttpResponse(simplejson.dumps(line_data), content_type='application/json')

def user_digraph(request, user_id):
	hn_list = list(HistoryNode.objects.filter(user__id=int(user_id)).values('url','referrer'))
	digraph_data = graph_utils.send_digraph(hn_list)
	return HttpResponse(simplejson.dumps(digraph_data), content_type='application/json')
