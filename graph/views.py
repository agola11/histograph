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
	bubble_tree = graph_utils.send_bubble(int(user_id))
	return HttpResponse(simplejson.dumps(bubble_tree), content_type='application/json')

