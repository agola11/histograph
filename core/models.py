from django.db import models, transaction
from django_facebook.models import FacebookModel
from django.contrib.auth.models import AbstractUser, UserManager
from open_facebook import OpenFacebook
from picklefield.fields import PickledObjectField
from urlparse import urlparse
from rec_utils import *
from datetime import datetime, timedelta
import functools
import logging
import time
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import re

class HistographUser(AbstractUser, FacebookModel):
  objects = UserManager()
  state = models.CharField(max_length=255, blank=True, null=True)
  ext_downloaded = models.BooleanField(default=False)
  # new_user = models.BooelanField(default=True)

  # Graphs
  year_graph_http = PickledObjectField(default=None, compress=False, null=True)
  year_graph = PickledObjectField(default=None, compress=False, null=True)
  six_graph = PickledObjectField(default=None, compress=False, null=True)
  three_graph = PickledObjectField(default=None, compress=False, null=True)
  one_graph = PickledObjectField(default=None, compress=False, null=True)
  week_graph = PickledObjectField(default=None, compress=False, null=True)

  # Rank table for ranks
  rank_table = PickledObjectField(default=[], compress=False, null=True)

  # weights for each user to be used in ranking
  weight_table = PickledObjectField(default={}, compress=False, null=True)

  # blocked graph
  blocked_graph = PickledObjectField(default=None, compress=False, null=True)

  def get_friends(self):
    graph = self.get_offline_graph()
    friends = graph.get('me/friends')
    friend_ids = map(lambda x: x['id'], friends['data'])
    friend_users = HistographUser.objects.filter(facebook_id__in=friend_ids)
    return friend_users

class HistoryNode(models.Model):
  # choices for the transition type field
  LINK = 0
  TYPED = 1
  AUTO_BOOKMARK = 2
  AUTO_SUBFRAME = 3
  MANUAL_SUBFRAME = 4
  GENERATED = 5
  AUTO_TOPLEVEL = 6
  FORM_SUBMIT = 7
  RELOAD = 8
  KEYWORD = 9
  KEYWORD_GENERATED = 10
  TRANSITION_CHOICES = (
    (LINK, 'link'),
    (TYPED, 'typed'),
    (AUTO_BOOKMARK, 'auto_bookmark'),
    (AUTO_SUBFRAME, 'auto_subframe'),
    (MANUAL_SUBFRAME, 'manual_subframe'),
    (GENERATED, 'generated'),
    (AUTO_TOPLEVEL, 'auto_toplevel'),
    (FORM_SUBMIT, 'form_submit'),
    (RELOAD, 'reload'),
    (KEYWORD, 'keyword'),
    (KEYWORD_GENERATED, 'keyword_generated'),
    )

  # fields
  url = models.URLField(max_length=2048)
  last_title = models.CharField(max_length=256)
  visit_time = models.BigIntegerField()
  transition_type = models.IntegerField(choices=TRANSITION_CHOICES)
  browser_id = models.IntegerField()
  extension_id = models.IntegerField()
  referrer = models.ForeignKey('HistoryNode', blank=True, null=True)
  user = models.ForeignKey(HistographUser)
  is_blocked = models.BooleanField(default=False)

  # field for graph
  in_year_http = models.BooleanField(default=False)
  in_year = models.BooleanField(default=False)
  in_six = models.BooleanField(default=False)
  in_three = models.BooleanField(default=False)
  in_one = models.BooleanField(default=False)
  in_week = models.BooleanField(default=False)
  in_blocked_graph = models.BooleanField(default=False)

  class Meta:
    unique_together = ('user', 'extension_id', 'browser_id')

class ExtensionID(models.Model):
  next_id = models.IntegerField()

class Extension(models.Model):
  extension_id = models.IntegerField()
  lock = models.BooleanField()

class BlockedSite(models.Model):
  url = models.URLField(max_length=2048)
  user = models.ForeignKey(HistographUser)
  block_links = models.BooleanField()

def get_link_type_name(value):
  if value == 0:
    return 'link'
  if value == 1:
    return 'typed'
  if value == 2:
    return 'auto_bookmark'
  if value == 3:
    return 'auto_subframe'
  if value == 4:
    return 'manual_subframe'
  if value == 5:
    return 'generated'
  if value == 6:
    return 'auto_toplevel'
  if value == 7:
    return 'form_submit'
  if value == 8:
    return 'reload'
  if value == 9:
    return 'keyword'
  if value == 10:
    return 'keyword_generated'

# Pre-insertion helper functions
def filter_http_s(hn):
  l = urlparse(hn['url'])
  return(l.scheme == 'http' or l.scheme == 'https')

def remove_trail(hn):
  url = hn['url']
  if url[-1] == '/':
    url = url[:-1]
  hn['url'] = url
  return hn

# Post-save, post-delete helper functions
def filter_http(hn):
  l = urlparse(hn.url)
  return(l.scheme == 'http')

def strip_scheme(hn):
  url = hn.url
  parsed = urlparse(url)
  scheme = "%s://" % parsed.scheme
  hn.url = parsed.geturl().replace(scheme, '', 1)
  return hn

def split_url(hn):
  url = hn.url
  url = url.split('/')
  if url[-1] == '':
    del(url[-1])
  hn.url = url
  return hn 

def date_in_range(now, bound, hn):
  ms = hn.visit_time
  then = datetime.fromtimestamp(ms/1000.0)
  return ((now-then).days <= bound)

def insert_nodes(hn_list):
  if hn_list == None:
    return

  hn_list = filter(lambda node: not node.is_blocked, hn_list)

  if len(hn_list) == 0:
    return

  http_payload = filter(filter_http, hn_list)
  user = hn_list[0].user
  
  # payload = map(strip_scheme, hn_list)
  # http_payload = map(strip_scheme, http_payload)

  # payload = map(split_url, payload)

  now = datetime.now()
  payload = filter(functools.partial(date_in_range, now, 365), hn_list)
  http_payload = filter(functools.partial(date_in_range, now, 365), http_payload)

  # Insert into url_graphs
  if user.year_graph_http == None:
    graph = UrlGraph()
    root = graph.create()
  else:
    graph = user.year_graph_http
    root = graph.root
  for node in http_payload:
    graph.insert(root, node)
    node.in_year_http=True
    # HistoryNode.objects.filter(pk=node.id).update(in_year_http=True)
  user.year_graph_http = graph

  if user.year_graph == None:
    graph = UrlGraph()
    root = graph.create()
  else:
    graph = user.year_graph
    root = graph.root
  for node in payload:
    graph.insert(root, node)
    node.in_year=True
    # HistoryNode.objects.filter(pk=node.id).update(in_year=True)
  user.year_graph = graph

  if user.blocked_graph == None:
    graph = UrlGraph()
    root = graph.create()
  else:
    graph = user.blocked_graph
    root = graph.root
  for node in payload:
    graph.insert(root, node)
    node.in_blocked_graph=True
    # HistoryNode.objects.filter(pk=node.id).update(in_blocked_graph=True)
  user.blocked_graph = graph

  payload = filter(functools.partial(date_in_range, now, (6*30)), payload)

  if user.six_graph == None:
     graph = UrlGraph()
     root = graph.create()
  else:
    graph = user.six_graph
    root = graph.root
  for node in payload:
    graph.insert(root, node)
    node.in_six=True
    # HistoryNode.objects.filter(pk=node.id).update(in_six=True)
  user.six_graph = graph

  payload = filter(functools.partial(date_in_range, now, (3*30)), payload)

  if user.three_graph == None:
    graph = UrlGraph()
    root = graph.create()
  else:
    graph = user.three_graph
    root = graph.root
  for node in payload:
    graph.insert(root, node)
    node.in_three=True
    # HistoryNode.objects.filter(pk=node.id).update(in_three=True)
  user.three_graph = graph

  payload = filter(functools.partial(date_in_range, now, (30)), payload)

  if user.one_graph == None:
    graph = UrlGraph()
    root = graph.create()
  else:
    graph = user.one_graph
    root = graph.root
  for node in payload:
    graph.insert(root, node)
    node.in_one=True
    # HistoryNode.objects.filter(pk=node.id).update(in_one=True)
  user.one_graph = graph

  payload = filter(functools.partial(date_in_range, now, 7), payload)

  if user.week_graph == None:
    graph = UrlGraph()
    root = graph.create()
  else:
    graph = user.week_graph
    root = graph.root
  for node in payload:
    graph.insert(root, node)
    node.in_week=True
    # HistoryNode.objects.filter(pk=node.id).update(in_week=True)
  user.week_graph = graph

  with transaction.atomic():
    for node in hn_list:
      node.save()

  user.save()

def delete_nodes(hn_list):
  if hn_list == None or len(hn_list) == 0:
    return

  user = hn_list[0].user

  for node in hn_list:
    if node.in_year_http:
      graph = node.user.year_graph_http
      if graph != None:
        root = graph.root
        graph.delete(root, node)
        node.user.year_graph_http = graph
        node.in_year_http = False
    
    if node.in_year:
      graph = node.user.year_graph
      if graph != None:
        root = graph.root
        graph.delete(root, node)
        node.user.year_graph = graph
        node.in_year = False

    if node.in_six:
      graph = node.user.six_graph
      if graph != None:
        root = graph.root
        graph.delete(root, node)
        node.user.six_graph = graph
        node.in_six = False

    if node.in_three:
      graph = node.user.three_graph
      if graph != None:
        root = graph.root
        graph.delete(root, node)
        node.user.three_graph = graph
        node.in_three = False

    if node.in_one:
      graph = node.user.one_graph
      if graph != None:
        root = graph.root
        graph.delete(root, node)
        node.user.one_graph = graph
        node.in_one = False

    if node.in_week:
      graph = node.user.week_graph
      if graph != None:
        root = graph.root
        graph.delete(root, node)
        node.user.week_graph = graph
        node.in_week = False

  user.year_graph_http._clean_graph(user.year_graph_http.root)
  user.year_graph._clean_graph(user.year_graph.root)
  user.six_graph._clean_graph(user.six_graph.root)
  user.three_graph._clean_graph(user.three_graph.root)
  user.one_graph._clean_graph(user.one_graph.root)
  user.week_graph._clean_graph(user.week_graph.root)

  with transaction.atomic():
    for node in hn_list:
      node.save()
  
  user.save()  

def create_history_nodes_from_json(payload, user):
  logger = logging.getLogger("core")
  logger.info("test1")
  start_time = time.time()
  now = datetime.now()
 
  # strip non-http(s) urls and remove trailing '/'
  payload = filter(filter_http_s, payload)
  payload = map(remove_trail, payload)

  duplicates = []
  new_nodes = []

  # with transaction.atomic():
  #   for node in payload:
  #     # if node is already in the database, replace it with the newer one
  #     try:
  #       existing_hn = HistoryNode.objects.get(browser_id=node['browser_id'], extension_id=node['extension_id'], user=user)
  #       duplicates.append(existing_hn)
  #     except HistoryNode.DoesNotExist:
  #       continue

  # delete_nodes(duplicates)
  # for node in duplicates:
  #   node.delete()

  # compile blocked sites regexs
  blocked_sites = BlockedSite.objects.filter(user=user)
  blocked_res = []
  for bs in blocked_sites:
    blocked_res.append(re.compile('https?://' + bs.url + '.*'))

  # add new nodes
  with transaction.atomic():
    for node in payload:
      try:
        existing_hn = HistoryNode.objects.get(browser_id=node['browser_id'], extension_id=node['extension_id'], user=user)

        trunc_title = node['last_title']
        if len(trunc_title) > 256:
          trunc_title = trunc_title[:253] + '...'

        existing_hn.last_title = trunc_title
        existing_hn.visit_time = node['visit_time']
        existing_hn.save()

        continue
      except HistoryNode.DoesNotExist:
        trunc_title = node['last_title']
        if len(trunc_title) > 256:
          trunc_title = trunc_title[:253] + '...'

        # get rid of anchors
        url = node['url'].split('#')[0]

        hn = HistoryNode(url=url, last_title=trunc_title, visit_time=node['visit_time'], transition_type=node['transition_type'], browser_id=node['browser_id'], extension_id=node['extension_id'], user=user)
        
        # check if in blocked lists
        for regex in blocked_res:
          if regex.match(hn.url):
            hn.is_blocked = True
            break

        hn.save()
        new_nodes.append(hn)

  insert_nodes(new_nodes)

  # connect referrers
  with transaction.atomic():
    for node in payload:
      try:
        referrer = HistoryNode.objects.get(extension_id=node['extension_id'], browser_id=node['referrer_id'], user=user)
        HistoryNode.objects.filter(extension_id=node['extension_id'], browser_id=node['browser_id'], user=user).update(referrer=referrer)
      except HistoryNode.DoesNotExist:
        continue

  end_time = time.time()
  logger.info("test")#'Added ' + str(len(payload)) + ' nodes in ' + str(end_time - start_time) + ' s')

# AUTOMATE WITH CELERY
def update_rank_tables():
  user_set = HistographUser.objects.all()
  # update rank tables and save user
  for user in user_set:
    # get a list of previously seen urls
    user_urls = HistoryNode.objects.filter(user__id=user.id)
    user_urls = map(strip_scheme, user_urls)
    user_urls = map(lambda hn: hn.url, user_urls)
    user_urls = set(user_urls)
    # intialize a table
    rank_table = {}

    for o_user in user_set:
      if o_user != user:  # <-DOES THIS WORK?!
        update_rank_table(user.year_graph_http, o_user.year_graph_http, rank_table, o_user.id, user.weight_table)

    ranked_urls = list(rank_table.items())
    ranked_urls = filter((lambda (x,y): x not in user_urls), ranked_urls)
    ranked_urls = list(reversed(sorted(ranked_urls, key=lambda (x,y): y['score'])))
    user.rank_table = ranked_urls
    user.save()

def _get_value_graph(root):
  if root.gchildren == None:
    return
  root.gchildren = root.gchildren.values()
  for child in root.gchildren:
    _get_value_graph(child)

def get_value_graph(user):
  r_user = HistographUser.objects.get(pk=user)
  graph = r_user.url_graph
  _get_value_graph(graph.root)
  return graph.root