from __future__ import division
from core.models import HistoryNode
from urlparse import urlparse
from django.http import Http404
from math import log1p, sqrt
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

def clean_url(hn):
	url = hn['url']
	if url[-1] == '/':
		url = url[:-1]
	if url.startswith('http://'):
		url = url[7:]
	if url.startswith('https://'):
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

def rec_insert(top_root, hn, level, curr_root):
	if len(hn['url']) < level:
		return top_root
	url_snip = hn['url'][level-1]
	if curr_root.children == None:
		curr_root.children = {}
		child = graph_node(url_snip, 1, level)
		curr_root.children[url_snip] = child
		rec_insert(top_root, hn, level+1, child)
	else:
		if url_snip not in curr_root.children:
			child = graph_node(url_snip, 1, level)
			curr_root.children[url_snip] = child
			rec_insert(top_root, hn, level+1, child)
		else:
			child = curr_root.children[url_snip]
			child.node_count += 1
			rec_insert(top_root, hn, level+1, child)

class graph_node:
	def __init__(self, name, node_count, level):
		self.name = name
		self.node_count = node_count
		#self.full_url = full_url
		self.level = level
		self.children = None

class url_graph:
	def __init__(self):
		self.root = None

	def create(self):
		return graph_node("root", 0, 0)

	def insert(self, root, hn):
		hn = clean_url(hn)
		hn = split_url(hn)
		root = rec_insert(root, hn, 1, root)
		return root

def filter_http(hn):
	l = urlparse(hn['url'])
	return(l.scheme == 'http')

def construct_graph(hn_list):
	hn_list = filter(filter_http, hn_list)
	graph = url_graph()
	root = graph.create()
	for hn in hn_list:
		graph.insert(root, hn)
	return root


