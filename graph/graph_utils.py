from django.shortcuts import render
from core.models import *
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

def _get_value_graph(root):
  if root.gchildren == None:
    return
  root.gchildren = root.gchildren.values()
  for child in root.gchildren:
    _get_value_graph(child)

def send_bubble(user):
  graph = user.url_graph
  _get_value_graph(graph.root)
  return graph.root

def send_line_plot(hn_list):
	hn_list = filter(filter_http, hn_list)
	hn_list = map(chop_protocol, hn_list)
	hn_list = map(format_date, hn_list)
	hn_list = sorted(hn_list, key=lambda hn: hn['visit_time'])
	hn_list = map(split_url, hn_list)
	domains = map(lambda hn: hn['url'][0], hn_list)
	all_domains = dict.fromkeys(domains, 0)
	dates = map(lambda hn: hn['visit_time'], hn_list)
	line_dict = OrderedDict.fromkeys(dates)
	
	for hn in hn_list:
		all_domains[hn['url'][0]] += 1

	ranked_domains = list(all_domains.items())
	ranked_domains  = list(reversed(sorted(ranked_domains, key=lambda (x,y): y)))
	filtered_domains_list = map(lambda (x,y): x, ranked_domains[:10])
	filtered_domains = set(filtered_domains_list)

	for hn in hn_list:
		if line_dict[hn['visit_time']] == None:
			line_dict[hn['visit_time']] = OrderedDict.fromkeys(filtered_domains, 0)
		if hn['url'][0] in filtered_domains:
			line_dict[hn['visit_time']][hn['url'][0]] += 1

	return({'sorted_domains':filtered_domains_list, 'line_dict':line_dict})

def send_digraph(hn_list):
	hn_list = filter(filter_http, hn_list)
	hn_list = map(chop_protocol, hn_list)
	hn_list = map(split_url, hn_list)
	domains = map(lambda hn: hn['url'][0], hn_list)
	domains = list(OrderedDict.fromkeys(domains, 0))

	nodes = []
	id_dict = {}
	trans_dict = {}
	i=0

	for hn in hn_list:
		nodes.append({'name':'/'.join(hn['url']), 'group':domains.index(hn['url'][0])})
		id_dict[hn['id']] = i
		trans_dict[hn['id']] = hn['transition_type']
		i+=1

	links = []
	for hn in hn_list:
		if hn['referrer'] != None and (hn['referrer'] in id_dict and hn['id'] in id_dict):
			links.append({'source':id_dict[hn['referrer']], 'target':id_dict[hn['id']], 'value': 5, 'type':get_link_type_name(trans_dict[hn['id']])})

	return {'nodes':nodes, 'links':links}




