from django.shortcuts import render
from core.models import HistoryNode, create_history_nodes_from_json
from django.core import serializers
from django.http import HttpResponse
from string import split
from django.utils import simplejson
from django.contrib.sites.models import get_current_site
from django.template import RequestContext, loader
from datetime import datetime
from core.rec_utils import *
import time
import json
from django.http import Http404
from urlparse import urlparse
import graph_utils
from django.db.models import Q, Count
import jsonpickle
import math

#display bubble graph
def circle(request):
  if (request.user.is_authenticated() == False):
    return redirect(login)
  domain = get_current_site(request).domain
  template = loader.get_template('graph/bubble.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_id': request.user.id,
        })
  return HttpResponse(template.render(context))

#display friends digraph
def friends(request): 
  if (request.user.is_authenticated() == False):
    return redirect(login)
  domain = get_current_site(request).domain
  template = loader.get_template('graph/friends.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        })
  return HttpResponse(template.render(context))

#display sites digraph
def digraph(request):
  if request.user.is_authenticated():
    domain = get_current_site(request).domain
    template = loader.get_template('graph/digraph.html')
    context = RequestContext(request, {
          'domain': get_current_site(request).domain,
          })
    return HttpResponse(template.render(context))  
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

#display line plot
def line_plot(request): 
  if (request.user.is_authenticated() == False):
    return redirect(login)
  domain = get_current_site(request).domain
  template = loader.get_template('graph/line.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_id': request.user.id,
        })
  return HttpResponse(template.render(context))

#display sunburst
def sunburst(request): 
  if (request.user.is_authenticated() == False):
    return redirect(login)

  domain = get_current_site(request).domain
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        })

  if HistoryNode.objects.filter(user=request.user, is_blocked=False).count() == 0:
    template = loader.get_template('graph/nodata.html')
    return HttpResponse(template.render(context))
  
  template = loader.get_template('graph/sunburst.html')
  return HttpResponse(template.render(context))

#request bubble data
def send_bubble(request, timesetting):
  time_dict = {'1y':365, '6m':180, '3m':90, '1m':30, '1w':7}
  if request.user.is_authenticated():
    now = time.mktime(datetime.now().timetuple()) * 1000
    startstamp = now - time_dict[timesetting] * 24 * 3600 * 1000
    endstamp = now - 0 * 24 * 3600 * 1000
    hns = HistoryNode.objects.filter(user=request.user, is_blocked=False, visit_time__range=(startstamp, endstamp))
    graph_data = UrlGraph()
    root = graph_data.create()
    for hn in hns:
      graph_data.insert(root, hn)
    graph_utils.get_value_graph(graph_data.root)
    return HttpResponse(jsonpickle.encode(graph_data.root, unpicklable=False), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

#request all user bubble data for settings graph
def send_bubble_blocked(request):
  if request.user.is_authenticated():
    hns = HistoryNode.objects.filter(user=request.user).annotate(Count('historynode')).filter(Q(referrer__isnull=False) | Q(historynode__count__gt=0))
    graph_data = UrlGraph()
    root = graph_data.create()
    for hn in hns:
      graph_data.insert(root, hn)
    graph_utils.get_formatted_blocked(graph_data.root)
    return HttpResponse(jsonpickle.encode(graph_data.root, unpicklable=False), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

#request line plot data
def send_line_plot(request):
  if request.user.is_authenticated():
    hn_objs = HistoryNode.objects.filter(user=request.user, is_blocked=False)
    line_data = graph_utils.send_line_plot(hn_objs)
    return HttpResponse(simplejson.dumps(line_data), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

#request digraph data
def send_digraph(request, timesetting):
  time_dict = {'1y':365, '6m':180, '3m':90, '1m':30, '1w':7}
  if request.user.is_authenticated():
    now = time.mktime(datetime.now().timetuple()) * 1000
    startstamp = now - time_dict[timesetting] * 24 * 3600 * 1000
    endstamp = now - 0 * 24 * 3600 * 1000
    hn_objs = HistoryNode.objects.filter(user=request.user, is_blocked=False, visit_time__range=(startstamp, endstamp)).annotate(Count('historynode')).filter(Q(referrer__isnull=False) | Q(historynode__count__gt=0))
    digraph_data = graph_utils.send_digraph(hn_objs)
    return HttpResponse(simplejson.dumps(digraph_data), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

#request friends digraph data
def send_friends(request):
  if request.user.is_authenticated():
    me = request.user
    friends = me.get_friends()

    nodes = []
    links = []

    nodes.append({'name':me.first_name + ' ' + me.last_name, 'id':me.facebook_id})
    i = 1
    for f in friends:
      nodes.append({'name':f.first_name + ' ' + f.last_name, 'id':f.facebook_id})
      links.append({'source':0, 'target':i, 'value': 2 / (1 + math.exp((graph_utils.compare_to_friend(me, f) - 0.7)*10))})
      i += 1

    friend_data = {'nodes':nodes, 'links':links}

    return HttpResponse(simplejson.dumps(friend_data), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp