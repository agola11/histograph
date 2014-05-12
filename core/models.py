from django.db import models, transaction
from django_facebook.models import FacebookModel
from django.contrib.auth.models import AbstractUser, UserManager
from open_facebook import OpenFacebook
from picklefield.fields import PickledObjectField
from urlparse import urlparse
from datetime import datetime, timedelta
import functools
import logging
import time
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache
from django.dispatch import receiver
import re

# user class extended from Django user
class HistographUser(AbstractUser, FacebookModel):
  objects = UserManager()
  state = models.CharField(max_length=255, blank=True, null=True)
  ext_downloaded = models.BooleanField(default=False)

  # get users that are facebook friends with this user
  def get_friends(self):
    graph = self.get_offline_graph()
    friends = graph.get('me/friends')
    friend_ids = map(lambda x: x['id'], friends['data'])
    friend_users = HistographUser.objects.filter(facebook_id__in=friend_ids)
    return friend_users

# model to store weighting preferences between users, determined from feedback
class UserWeight(models.Model):
  to_user = models.ForeignKey(HistographUser, related_name = 'userweight_to')
  from_user = models.ForeignKey(HistographUser, related_name = 'userweight_from')
  weight = models.FloatField()

# model representing a single visit to a URL; most users have between 20ka nd 60k of these
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

  url = models.URLField(max_length=2048)
  last_title = models.CharField(max_length=256) # page title last time it was visited
  visit_time = models.BigIntegerField() # time visited since the UNIX epoch in milliseconds
  transition_type = models.IntegerField(choices=TRANSITION_CHOICES) # type of transition from the referrer to this node
  browser_id = models.IntegerField() # id assigned within the browser
  extension_id = models.IntegerField()
  referrer = models.ForeignKey('HistoryNode', blank=True, null=True)
  user = models.ForeignKey(HistographUser)
  is_blocked = models.BooleanField(default=False)

  class Meta:
    unique_together = ('user', 'extension_id', 'browser_id')

# incrementing extension ID for distributing IDs to new extensions
class ExtensionID(models.Model):
  next_id = models.IntegerField()

# model to store whether an extension is currently working on a node import
class Extension(models.Model):
  extension_id = models.IntegerField()
  lock = models.BooleanField()

# represents a single blocked url or set of urls a user can block
class BlockedSite(models.Model):
  url = models.URLField(max_length=2048)
  user = models.ForeignKey(HistographUser)
  block_links = models.BooleanField()

# translate link type enum into human-readable form
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

# function that inserts newly received history nodes
def create_history_nodes_from_json(payload, user):
  # strip non-http(s) urls and remove trailing '/'
  payload = filter(filter_http_s, payload)
  payload = map(remove_trail, payload)

  # compile blocked sites regexs
  blocked_sites = BlockedSite.objects.filter(user=user)
  blocked_res = []
  for bs in blocked_sites:
    blocked_res.append(re.compile('https?://' + bs.url + '.*'))

  # add new nodes
  with transaction.atomic():
    for node in payload:
      # check if this node has already been imported and update
      try:
        existing_hn = HistoryNode.objects.get(browser_id=node['browser_id'], extension_id=node['extension_id'], user=user)

        trunc_title = node['last_title']
        if len(trunc_title) > 256:
          trunc_title = trunc_title[:253] + '...'

        existing_hn.last_title = trunc_title
        existing_hn.visit_time = node['visit_time']
        existing_hn.save()

        continue
      # add a new node
      except HistoryNode.DoesNotExist:
        # truncate title 256 characters
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

  # connect referrers
  with transaction.atomic():
    for node in payload:
      try:
        referrer = HistoryNode.objects.get(extension_id=node['extension_id'], browser_id=node['referrer_id'], user=user)
        HistoryNode.objects.filter(extension_id=node['extension_id'], browser_id=node['browser_id'], user=user).update(referrer=referrer)
      except HistoryNode.DoesNotExist:
        continue

  # update caching
  version = cache.get(str(user.id))
  if not version:
    version = 1
  else:
    version = version + 1
  cache.set(str(user.id), version)
