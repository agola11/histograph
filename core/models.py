from django.db import models

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

class ExtensionID(models.Model):
  next_id = models.IntegerField()

def create_history_nodes_from_json(payload):
  for node in payload:
    hn = HistoryNode(url=node['url'], last_title=node['last_title'], visit_time=node['visit_time'], transition_type=node['transition_type'], browser_id=node['browser_id'], extension_id=node['extension_id'])
    hn.save()

  # connect referrers
  for node in payload:
    try:
      referrer = HistoryNode.objects.get(extension_id=node['extension_id'], browser_id=node['referrer_id'])
      HistoryNode.objects.filter(extension_id=node['extension_id'], browser_id=node['browser_id']).update(referrer=referrer)
    except HistoryNode.DoesNotExist:
      continue
