from django.shortcuts import render
from core.models import HistoryNode
from django.core import serializers
from django.http import HttpResponse
from string import split
from django.utils import simplejson
from django.http import Http404
from urlparse import urlparse
import graph_utils

def send_user_bubble(request, user_id):
	hn_list = list(HistoryNode.objects.filter(extension_id=int(user_id)).values('url','extension_id'))
	bubble_tree = graph_utils.send_bubble(hn_list)
	return HttpResponse(simplejson.dumps(bubble_tree), content_type='application/json')

def send_bubble(request):
	hn_list = list(HistoryNode.objects.values('url','extension_id'))
	bubble_tree = graph_utils.send_bubble(hn_list)
	return HttpResponse(simplejson.dumps(bubble_tree), content_type='application/json')