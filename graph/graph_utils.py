from django.shortcuts import render
from core.models import HistoryNode
from django.core import serializers
from django.http import HttpResponse
from string import split
from django.utils import simplejson
from django.http import Http404
from datetime import datetime
from urlparse import urlparse

def filter_http(hn):
	l = urlparse(hn['url'])
	return(l.scheme == 'http' or l.scheme == 'https')

def split_url(hn):
	url = hn['url']
	if url.startswith('http://'):
		url = url[7:]
	elif url.startswith('https://'):
		url = url[8:]
	url = url.split('/')
	if url[-1] == '':
		del(url[-1])
	hn['url'] = url
	return hn

def format_date(hn):
	ms = hn['visit_time']
	date = datetime.fromtimestamp(ms/1000.0).strftime('%Y-%m-%d')
	hn['visit_time'] = date
	return hn

def reduce_bubble_tree(child, level):
	templist = []
	children = []
	urls = child['urls']
	count = 1
	removed = 0

	for i in range(len(urls)):
		if len(urls[i]) < level:
			removed += 1
			continue
		if i+1 >= len(urls) or urls[i][level-1] != urls[i+1][level-1]:
			templist.append(urls[i])
			children.append({'node_count':count,'name':urls[i][level-1],'urls':templist})
			templist = []
			count = 1
		else:
			templist.append(urls[i])
			count+=1
	return children

def update_bubble_tree(children, level):
	if level > 2:
		return

	for child in children:
		children = reduce_bubble_tree(child, level)
		if children:
			child['children'] = children
		update_bubble_tree(children, level+1)

def remove_urls(bubble_root):
	del(bubble_root['urls'])
	if 'children' in bubble_root:
		for child in bubble_root['children']:
			remove_urls(child)

def send_bubble(hn_list):
	bubble_root = {}
	hn_list = filter(filter_http, hn_list)
	hn_list = sorted(hn_list, key=lambda hn: hn['url'])
	hn_list = map(split_url, hn_list)

	bubble_root['node_count'] = 0
	bubble_root['name'] = 'top_level'
	bubble_root['urls'] = map(lambda hn: hn['url'], hn_list)

	update_bubble_tree([bubble_root], 1)
	remove_urls(bubble_root)
	return bubble_root

def send_line_plot(hn_list):
	hn_list = filter(filter_http, hn_list)
	hn_list = map(format_date, hn_list)
	hn_list = sorted(hn_list, key=lambda hn: hn['visit_time'])
	hn_list = map(split_url, hn_list)
	domains = set(map(lambda hn: hn['url'][0], hn_list))
	return (hn_list, list(domains))
