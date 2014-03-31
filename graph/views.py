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

def send_bubble(request):
  resp = HttpResponse()

  all_nodes = HistoryNode.objects.all()
  
  bubble_root = {}
  bubble_root['name'] = 'top_level'
  bubble_root['node_count'] = 0
  bubble_root['children'] = {}
  
  for node in all_nodes:
    urls = split(node.url, '://', 1)
    if len(urls) == 1:
      url = urls[0]
    else:
      url = urls[1]
    
    bubble_node = bubble_root

    bubble_root['node_count'] = bubble_root['node_count'] + 1

    while True:
      if '/' in url:
        url_split = split(url, '/', 1)
        name = url_split[0]
      else:
        name = url

      # initialize node if empty
      if not name in bubble_node['children']:
        bubble_node['children'][name] = {}
        bubble_node = bubble_node['children'][name]
        bubble_node['name'] = name
        bubble_node['node_count'] = 0
        bubble_node['children'] = {}
      else:
        bubble_node = bubble_node['children'][name]

      bubble_node['node_count'] = bubble_node['node_count'] + 1

      if not '/' in url:
        break

      url = url_split[1]

  return HttpResponse(simplejson.dumps(bubble_root), content_type='application/json')

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