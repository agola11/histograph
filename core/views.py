from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core import serializers
from core.models import HistoryNode, Extension, ExtensionID, BlockedSite, create_history_nodes_from_json, HistographUser, get_value_graph, update_rank_tables, insert_nodes, delete_nodes
from datetime import datetime
from django.template import RequestContext, loader
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.models import Session
from django.utils import simplejson
from django.db.models import Max
from django.contrib.auth import logout as django_logout
from itertools import islice
from rec_utils import *
from django.views.decorators.csrf import csrf_exempt, requires_csrf_token
import django_facebook
import json
import rec_algo
import jsonpickle

# TODO: change to simplejson?
# def send_history(request, user_id):
#   resp = HttpResponse()
#   serializers.serialize('json', HistoryNode.objects.filter(user__id=int(user_id)), stream=resp)
#   return HttpResponse(resp, content_type="application/json")

@csrf_exempt
@requires_csrf_token
def send_most_recent_history_time(request, extension_id):
  if request.user.is_authenticated():
    hn = HistoryNode.objects.filter(extension_id=extension_id, user=request.user)
    if len(hn) == 0:
      t = {'visit_time__max': 0}
    else:
      t = hn.aggregate(Max('visit_time'))
    return HttpResponse(simplejson.dumps(t), content_type="application/json")
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

@csrf_exempt
@requires_csrf_token
def send_blocked_sites(request):
  if request.user.is_authenticated():
    sites = BlockedSite.objects.filter(user=request.user).values('url', 'block_links')
    return HttpResponse(simplejson.dumps(list(sites)), content_type="application/json")
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

def store_blocked_sites(request):
  if request.user.is_authenticated():
    payload = json.loads(request.body)

    if payload['blocked']:
      try:
        bs = BlockedSite.objects.get(user=request.user, url=payload['url'])
      except BlockedSite.DoesNotExist:
        bs = BlockedSite()
        bs.url = payload['url']
        bs.user = request.user

      bs.block_links = payload['block_links']

      bs.save()

      re = '^https?://' + bs.url + '.*'
      hn = HistoryNode.objects.filter(user=request.user, url__regex=re, is_blocked=False)
      # delete_nodes(hn)
      hn.update(is_blocked=True)

      if bs.block_links:
        hn = HistoryNode.objects.filter(user=request.user, referrer__url__regex=re, is_blocked=False)
        # delete_nodes(hn)
        hn.update(is_blocked=True)

    else:
      try:
        bs = BlockedSite.objects.get(user=request.user, url=payload['url']).delete()
        re = '^https?://' + payload['url'] + '.*'
        hn = HistoryNode.objects.filter(user=request.user, url__regex=re, is_blocked=True)
        # insert_nodes(hn)
        hn.update(is_blocked=False)
      except BlockedSite.DoesNotExist:
        pass
  
    resp = HttpResponse()
    resp.status_code = 200
    return resp
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

@csrf_exempt
@requires_csrf_token
def send_ext_locked(request):
  if request.user.is_authenticated():
    payload = json.loads(request.body)
    extid = Extension.objects.get(extension_id=payload['extension_id'])

    data = {}
    data['lock'] = extid.lock
    return HttpResponse(simplejson.dumps(data), content_type="application/json")
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

@csrf_exempt
@requires_csrf_token
def send_new_extension_id(request):
  if request.user.is_authenticated():
    extid = ExtensionID.objects.get(pk=1)
    extid_next = extid.next_id
    data = {'extension_id': extid_next}
    extid.next_id = extid.next_id + 1
    extid.save()

    ext_obj = Extension(extension_id=extid_next, lock=False)
    ext_obj.save()

    return HttpResponse(simplejson.dumps(data), content_type="application/json")
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

# def send_user_id(request):
#   if request.user.is_authenticated():
#     data = {'user_id': request.user.id, 'is_auth': 1}
#     return HttpResponse(simplejson.dumps(data), content_type="application/json")
#   else:
#     data = {'user_id': 0, 'is_auth': 0}
#     return HttpResponse(simplejson.dumps(data), content_type="application/json")

@csrf_exempt
@requires_csrf_token
def store_history(request):
  if request.user.is_authenticated():
    payload = json.loads(request.body)

    if len(payload) > 0:
      ext = Extension.objects.get(extension_id=payload[0]['extension_id'])
      
      if ext.lock:
        resp = HttpResponse()
        resp.status_code = 409
        return resp

      else:
        ext.lock = True
        ext.save()

        create_history_nodes_from_json(payload, request.user)

        ext = Extension.objects.get(extension_id=payload[0]['extension_id'])
        ext.lock = False
        ext.save()

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

def login(request):
  if request.user.is_authenticated():
    return redirect(home)
  template = loader.get_template('core/login.html')
  context = RequestContext(request)
  return HttpResponse(template.render(context))

def broken_link(request):
  template = loader.get_template('core/broken_link.html')
  context = RequestContext(request)
  return HttpResponse(template.render(context))

def logout(request):
  django_logout(request)
  return redirect(login)

def team(request):
  if (request.user.is_authenticated() == False):
    return redirect(login)
  domain = get_current_site(request).domain
  template = loader.get_template('core/team.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_fullname' : request.user.get_full_name(),
  })
  return HttpResponse(template.render(context))

def about(request):
  if (request.user.is_authenticated() == False):
    return redirect(login)
  domain = get_current_site(request).domain
  template = loader.get_template('core/about.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_fullname' : request.user.get_full_name(),
  })
  return HttpResponse(template.render(context))

def install(request):
  if (request.user.is_authenticated() == False):
    return redirect(login)
  domain = get_current_site(request).domain
  template = loader.get_template('core/install.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'user_fullname' : request.user.get_full_name(),
        'user': request.user
  })
  return HttpResponse(template.render(context))

def set_extension_downloaded(request):
  if request.user.is_authenticated():
    domain = get_current_site(request).domain
    request.user.ext_downloaded = True
    request.user.save()
    if (request.user.is_authenticated() == True):
      return redirect(home)
    else: return redirect(login)
  else:
    resp = HttpResponse()
    resp.status_code = 401
    return resp

def explore(request):
  if (request.user.is_authenticated() == False):
    return redirect(login)
  template = loader.get_template('core/explore.html')
  # url_dict = rec_algo.rank_urls(request.user.id)
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'authenticated': request.user.is_authenticated(),
        'user_fullname' : request.user.get_full_name(),
        'downloaded' : request.user.ext_downloaded,
        'id': request.user.id,
    })
  return HttpResponse(template.render(context))

def settings(request):
  if (request.user.is_authenticated() == False):
    return redirect(login)
  template = loader.get_template('core/settings.html')
  context = RequestContext(request, {
        'domain': get_current_site(request).domain,
        'authenticated': request.user.is_authenticated(),
        'user_fullname' : request.user.get_full_name(),
        'downloaded' : request.user.ext_downloaded,
        'id': request.user.id,
    })
  return HttpResponse(template.render(context))

# TODO: change to a year?
def send_ranked_urls(request):
  user_hns = HistoryNode.objects.filter(user = request.user, url__regex = 'http://.*')
  user_urls = HistoryNode.objects.filter(user = request.user).values('url')
  user_urls = set(map(lambda hn : hn['url'], user_urls))
  users = HistographUser.objects.all()
  user_graph = UrlGraph()
  u_root = user_graph.create()
  rank_table = {}
  for user_hn in user_hns:
    user_graph.insert(u_root, user_hn)
  for user in users:
    if user != request.user:
      other_hns = user.historynode_set.filter(url__regex = 'http://.*')
      other_graph = UrlGraph()
      o_root = other_graph.create()
      for other_hn in other_hns:
        other_graph.insert(o_root, other_hn)
      update_rank_table(user_graph, other_graph, rank_table, user.id, {})

  ranked_urls = list(rank_table.items())
  ranked_urls = filter((lambda (x,y): ('https://' + x) not in user_urls and ('http://' + x) not in user_urls), ranked_urls)
  ranked_urls = list(reversed(sorted(ranked_urls, key=lambda (x,y): y['score'])))

  return HttpResponse(json.dumps(ranked_urls), content_type='application/json')

def send_ranked_urls_u(request, user_id):
  user_hns = HistoryNode.objects.filter(user__id = int(user_id), url__regex = 'http://.*')
  users = HistographUser.objects.all()
  user_graph = UrlGraph()
  u_root = user_graph.create()
  rank_table = {}
  for user_hn in user_hns:
    user_graph.insert(u_root, user_hn)
  for user in users:
    if user.id != int(user_id):
      other_hns = user.historynode_set.filter(url__regex = 'http://.*')
      other_graph = UrlGraph()
      o_root = other_graph.create()
      for other_hn in other_hns:
        other_graph.insert(o_root, other_hn)
      update_rank_table(user_graph, other_graph, rank_table, user.id, {})
  return HttpResponse(json.dumps(rank_table), content_type='application/json')

def up_vote(request):
  # add logic to update user_weight_dict
  if request.method == 'POST':
    index = request.POST['index']

  index = int(index)
  user = request.user
  rank_table = user.rank_table
  weight_table = user.weight_table

  user_dict = rank_table[index][1]['users']
  for o_id in user_dict:
    if o_id in weight_table:
      weight_table[o_id] += user_dict[o_id]
    else:
      weight_table[o_id] = user_dict[o_id]

  user.weight_table = weight_table
  user.save()

  response = HttpResponse()
  response.status_code = 200
  return response

def down_vote(request):
  # add logic to update user_weight_dict

  if request.method == 'POST':
    index = request.POST['index']

  index = int(index)
  user = request.user
  rank_table = user.rank_table
  weight_table = user.weight_table

  user_dict = rank_table[index][1]['users']
  for o_id in user_dict:
    if o_id in weight_table:
      weight_table[o_id] -= user_dict[o_id]
    else:
      weight_table[o_id] = user_dict[o_id]

  user.weight_table = weight_table
  user.save()

  response = HttpResponse()
  response.status_code = 200
  return response