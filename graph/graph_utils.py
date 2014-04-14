from django.shortcuts import render
from core.models import HistoryNode
from django.core import serializers
from django.http import HttpResponse
from string import split
from django.utils import simplejson
from django.http import Http404
from datetime import datetime
from urlparse import urlparse
try:
	from collections import OrderedDict
except ImportError:
	# python 2.6 or earlier, use backport
	from ordereddict import OrderedDict

def filter_http(hn):
	l = urlparse(hn['url'])
	return(l.scheme == 'http' or l.scheme == 'https')

def chop_protocol(hn):
	url = hn['url']
	if url.startswith('http://'):
		url = url[7:]
	elif url.startswith('https://'):
		url = url[8:]
	hn['url'] = url
	return hn

def split_url(hn):
	url = hn['url']
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
			children.append({'node_count':count,'name':urls[i][level-1],'urls':templist, 'full_url':('/'.join(urls[i][:level]))})
			templist = []
			count = 1
		else:
			templist.append(urls[i])
			count+=1
	return children

def update_bubble_tree(children, level):
	if level > 4:
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
	hn_list = map(chop_protocol, hn_list)
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
	hn_list = map(chop_protocol, hn_list)
	hn_list = map(format_date, hn_list)
	hn_list = sorted(hn_list, key=lambda hn: hn['visit_time'])
	hn_list = map(split_url, hn_list)
	domains = map(lambda hn: hn['url'][0], hn_list)
	dates = map(lambda hn: hn['visit_time'], hn_list)
	line_dict = OrderedDict.fromkeys(dates)
	
	for hn in hn_list:
		if line_dict[hn['visit_time']] == None:
			line_dict[hn['visit_time']] = OrderedDict.fromkeys(domains, 0)
		line_dict[hn['visit_time']][hn['url'][0]] += 1

	return(line_dict)

def send_digraph(hn_list):
	hn_list = filter(filter_http, hn_list)
	hn_list = map(chop_protocol, hn_list)
	hn_list = map(split_url, hn_list)
	domains = map(lambda hn: hn['url'][0], hn_list)
	domains = list(OrderedDict.fromkeys(domains, 0))

	nodes = []
	id_dict = {}
	i=0

	for hn in hn_list:
		nodes.append({'name':'/'.join(hn['url']), 'group':domains.index(hn['url'][0])})
		id_dict[hn['id']] = i
		i+=1

	links = []
	for hn in hn_list:
		if hn['referrer'] != None:
			links.append({'source':id_dict[hn['referrer']], 'target':id_dict[hn['id']], 'value': 1})

	return {'nodes':nodes, 'links':links}




