from django.shortcuts import render
from core.models import HistoryNode
from django.core import serializers
from django.http import HttpResponse
from string import split
from django.utils import simplejson

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
