from django.shortcuts import render
from django.http import HttpResponse
import datetime
from django.core import serializers
import json


def respond(request):
    now = datetime.datetime.now()
    return HttpResponse(html)

# Create your views here.

# YEAH YEAH WOO
