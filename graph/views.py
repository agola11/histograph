from django.shortcuts import render
from core.models import HistoryNode, create_history_nodes_from_json
from django.core import serializers
from django.http import HttpResponse
from string import split
from django.utils import simplejson
from django.contrib.sites.models import get_current_site
from django.template import RequestContext, loader
from datetime import datetime
import time
import json
from django.http import Http404
from urlparse import urlparse
import graph_utils
from django.db.models import Q, Count
import jsonpickle

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

def friends(request): 
  if (request.user.is_authenticated() == False):
    return redirect(login)
  domain = get_current_site(request).domain
  template = loader.get_template('graph/friends.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        })
  return HttpResponse(template.render(context))

def pie(request): 
  if (request.user.is_authenticated() == False):
    return redirect(login)
  domain = get_current_site(request).domain
  template = loader.get_template('graph/pie.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        })
  return HttpResponse(template.render(context))

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

def user_sunburst(request, user_id): 
  if (request.user.is_authenticated() == False):
    return redirect(login)
  domain = get_current_site(request).domain
  template = loader.get_template('graph/sunburst-user.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_id': user_id,
        })
  return HttpResponse(template.render(context))

def sunburst(request): 
  if (request.user.is_authenticated() == False):
    return redirect(login)

  domain = get_current_site(request).domain
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        })

  if HistoryNode.objects.filter(user=request.user).count() == 0:
    template = loader.get_template('graph/nodata.html')
    return HttpResponse(template.render(context))
  
  template = loader.get_template('graph/sunburst.html')
  return HttpResponse(template.render(context))

'''
def send_user_bubble(request, user_id):
  if request.user.is_authenticated():
    hn_list = list(HistoryNode.objects.filter(user__id=int(user_id)).values('url'))
    bubble_tree = graph_utils.send_bubble(hn_list)
    return HttpResponse(simplejson.dumps(bubble_tree), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp
'''

def send_bubble(request):
  if request.user.is_authenticated():
    # now = time.mktime(datetime.now().timetuple()) * 1000
    # startstamp = now - int(starttime) * 24 * 3600 * 1000
    # endstamp = now - int(endtime) * 24 * 3600 * 1000
    hn_objs = HistoryNode.objects.filter(user=request.user) #, visit_time__range=(startstamp, endstamp))
    bubble_tree = graph_utils.send_bubble(request.user)
    return HttpResponse(jsonpickle.encode(bubble_tree, unpicklable=False), content_type="application/json")
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

def send_user_line_plot(request, user_id):
  if request.user.is_authenticated():
    hn_objs = HistoryNode.objects.filter(user__id=int(user_id)).values('url','visit_time')
    line_data = graph_utils.send_line_plot(hn_objs)
    return HttpResponse(simplejson.dumps(line_data), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

def send_line_plot(request):
  if request.user.is_authenticated():
    hn_objs = HistoryNode.objects.filter(user=request.user)
    line_data = graph_utils.send_line_plot(hn_objs)
    return HttpResponse(simplejson.dumps(line_data), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

def send_digraph(request):
  if request.user.is_authenticated():
    now = time.mktime(datetime.now().timetuple()) * 1000
    startstamp = now - 7 * 24 * 3600 * 1000
    endstamp = now - 0 * 24 * 3600 * 1000
    hn_objs = HistoryNode.objects.filter(user=request.user, visit_time__range=(startstamp, endstamp)).annotate(Count('historynode')).filter(Q(referrer__isnull=False) | Q(historynode__count__gt=0))
    digraph_data = graph_utils.send_digraph(hn_objs)
    return HttpResponse(simplejson.dumps(digraph_data), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

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
      links.append({'source':0, 'target':i, 'value': 0.5 / graph_utils.compare_to_friend(me, f)})
      i += 1

    friend_data = {'nodes':nodes, 'links':links}

    return HttpResponse(simplejson.dumps(friend_data), content_type='application/json')
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp