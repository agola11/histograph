from django.db import models, transaction
from django_facebook.models import FacebookModel
from django.contrib.auth.models import AbstractUser, UserManager
from open_facebook import OpenFacebook
from picklefield.fields import PickledObjectField
from urlparse import urlparse
from rec_utils import *
import logging
import time

class HistographUser(AbstractUser, FacebookModel):
  objects = UserManager()
  state = models.CharField(max_length=255, blank=True, null=True)
  ext_downloaded = models.BooleanField(default=False)

  # Graphs
  year_graph_http = PickledObjectField(default=None, compress=False, null=True)
  year_graph = PickledObjectField(default=None, compress=False, null=True)
  six_graph = PickledObjectField(default=None, compress=False, null=True)
  three_graph = PickledObjectField(default=None, compress=False, null=True)
  one_graph = PickledObjectField(default=None, compress=False, null=True)
  week_graph = PickledObjectField(default=None, compress=False, null=True)
  rank_table = PickledObjectField(default=[], compress=False, null=True)

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

  # field for graph
  deleted_year_http = models.BooleanField(default=False)
  deleted_year = models.BooleanField(default=False)
  deleted_six = models.BooleanField(default=False)
  deleted_three = models.BooleanField(default=False)
  deleted_one = models.BooleanField(default=False)
  deleted_week = models.BooleanField(default=False)


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

def filter_http_s(hn):
  l = urlparse(hn['url'])
  return(l.scheme == 'http' or l.scheme == 'https')

def filter_http(hn):
  l = urlparse(hn['url'])
  return(l.scheme == 'http')

def remove_trail(hn):
  url = hn['url']
  if url[-1] == '/':
    url = url[:-1]
  hn['url'] = url
  return hn

def strip_scheme(hn):
  url = hn['url']
  parsed = urlparse(url)
  scheme = "%s://" % parsed.scheme
  hn['url'] = parsed.geturl().replace(scheme, '', 1)
  return hn

def split_url(hn):
  url = hn['url']
  url = url.split('/')
  if url[-1] == '':
    del(url[-1])
  hn['url'] = url
  return hn 

def create_history_nodes_from_json(payload, user):
  logger = logging.getLogger("core")
  logger.info("test1")
  start_time = time.time()
 
  # strip non-http(s) urls and remove trailing '/'
  payload = filter(filter_http_s, payload)
  payload = map(remove_trail, payload)

  with transaction.atomic():
    for node in payload:
      # if node is already in the database, replace it with the newer one
      try:
        existing_hn = HistoryNode.objects.get(browser_id=node['browser_id'], extension_id=node['extension_id'], user=user)
        existing_hn.delete()
      except HistoryNode.DoesNotExist:
        continue

  with transaction.atomic():
      trunc_title = node['last_title']
      if len(trunc_title) > 256:
        trunc_title = trunc_title[:253] + '...'

      # get rid of anchors
      url = node['url'].split('#')[0]
      hn = HistoryNode(url=url, last_title=trunc_title, visit_time=node['visit_time'], transition_type=node['transition_type'], browser_id=node['browser_id'], extension_id=node['extension_id'], user=user)
      hn.save()

  # connect referrers
  with transaction.atomic():
    for node in payload:
      try:
        referrer = HistoryNode.objects.get(extension_id=node['extension_id'], browser_id=node['referrer_id'], user=user)
        HistoryNode.objects.filter(extension_id=node['extension_id'], browser_id=node['browser_id'], user=user).update(referrer=referrer)
      except HistoryNode.DoesNotExist:
        continue
  
  http_payload = filter(filter_http, payload)

  payload = map(strip_scheme, payload)
  http_payload = map(strip_scheme, http_payload)

  payload = map(split_url, payload)
  # http_payload = map(split_url, http_payload)

  # Insert into url_graphs
  if user.year_graph_http == None:
    graph = UrlGraph()
    root = graph.create()
    for node in http_payload:
      graph.insert(root, node)
    user.year_graph_http = graph
  else:
    graph = user.year_graph_http
    root = graph.root
    for node in http_payload:
      graph.insert(root, node)
    user.year_graph_http = graph

  if user.year_graph == None:
    graph = UrlGraph()
    root = graph.create()
    for node in payload:
      graph.insert(root, node)
    user.year_graph = graph
  else:
    graph = user.year_graph
    root = graph.root
    for node in payload:
      graph.insert(root, node)
    user.year_graph = graph

  if user.six_graph == None:
    graph = UrlGraph()
    root = graph.create()
    for node in payload:
      graph.insert(root, node)
    user.six_graph = graph
  else:
    graph = user.six_graph
    root = graph.root
    for node in payload:
      graph.insert(root, node)
    user.six_graph = graph

  if user.three_graph == None:
    graph = UrlGraph()
    root = graph.create()
    for node in payload:
      graph.insert(root, node)
    user.three_graph = graph
  else:
    graph = user.three_graph
    root = graph.root
    for node in payload:
      graph.insert(root, node)
    user.three_graph = graph

  if user.one_graph == None:
    graph = UrlGraph()
    root = graph.create()
    for node in payload:
      graph.insert(root, node)
    user.one_graph = graph
  else:
    graph = user.one_graph
    root = graph.root
    for node in payload:
      graph.insert(root, node)
    user.one_graph = graph

  if user.week_graph == None:
    graph = UrlGraph()
    root = graph.create()
    for node in payload:
      graph.insert(root, node)
    user.week_graph = graph
  else:
    graph = user.week_graph
    root = graph.root
    for node in payload:
      graph.insert(root, node)
    user.week_graph = graph

  user.save()
  
  end_time = time.time()
  logger.info("test")#'Added ' + str(len(payload)) + ' nodes in ' + str(end_time - start_time) + ' s')

# AUTOMATE WITH CELERY
def update_rank_tables():
  user_set = HistographUser.objects.all()
  # update rank tables and save user
  for user in user_set:
    rank_table = {}
    for o_user in user_set:
      if o_user != user:
        update_rank_table(user.year_graph_http, o_user.year_graph_http, rank_table)
    ranked_urls = list(rank_table.items())
    ranked_urls = filter((lambda (x,y): x not in user_urls), ranked_urls)
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