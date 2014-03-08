from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from core.models import HistoryNode
from datetime import datetime
from django.views.generic import TemplateView
import json

def send_history(request):
  resp = HttpResponse()
  serializers.serialize('json', HistoryNode.objects.all(), stream=resp)
  return HttpResponse(resp, content_type="application/json")

def store_history(request):
  payload = json.loads(request.body)

  # TODO: should timestamp be an int or double?
  visit_time = datetime.fromtimestamp(int(payload['visit_time']))

  try:
    referrer = HistoryNode.objects.get(extension_id=int(payload['extension_id']), browser_id=int(payload['referrer_id']))
  except HistoryNode.DoesNotExist:
    referrer = None

  hn = HistoryNode(url=payload['url'], last_title=payload['last_title'], visit_time=visit_time, transition_type=int(payload['transition_type']), browser_id=int(payload['browser_id']), referrer=referrer, extension_id=int(payload['extension_id']))
  hn.save()
  return HttpResponse("OK")

class AboutView(TemplateView):
    template_name = "about.html"