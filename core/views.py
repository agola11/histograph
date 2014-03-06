from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
from core.models import HistoryNode
import datetime
import json

def send_history(request):
  resp = HttpResponse()
  serializers.serialize('json', HistoryNode.objects.all(), stream=resp)
  return HttpResponse(resp, content_type="application/json")

def store_history(request):
	pass

