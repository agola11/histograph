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

# Compute Bhattacharya Distance between two distributions
def bhatta_dist(d1, d2):
	cumul = 0
	for url in d1:
		if url not in d2:
			cumul += 0
		else:
			cumul += sqrt(d1[url]*d2[url])
	return log(1+cumul,2)

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
		self.levels = {}

	def create(self):
		self.levels[0] = 1
		root = graph_node("root", 0, 0)
		self.root = root
		return root

	# TODO: put a full URl field using '/'.join()
	def rec_insert(self,top_root, hn, level, curr_root):
		if len(hn['url']) < level:
			return top_root
		url_snip = hn['url'][level-1]
		if curr_root.children == None:
			curr_root.children = {}
			child = graph_node(url_snip, 1, level)
			curr_root.children[url_snip] = child
		else:
			if url_snip not in curr_root.children:
				child = graph_node(url_snip, 1, level)
				curr_root.children[url_snip] = child
			else:
				child = curr_root.children[url_snip]
				child.node_count += 1
	
		if level not in self.levels:
			self.levels[level] = 1
		else:
			self.levels[level] += 1
		self.rec_insert(top_root, hn, level+1, child)

	def insert(self, root, hn):
		hn = clean_url(hn)
		hn = split_url(hn)
		root = self.rec_insert(root, hn, 1, root)
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
	return graph

def update_rank_table(ug, g, rank_table):
	ulevel_dict = ug.levels
	level_dict = g.levels
	_update_rank_table(ug.root, g.root, ulevel_dict, level_dict, 0, 0, rank_table)

def _update_rank_table(ug, g, ulevel_dict, level_dict, level, prev_bd, prev_score, rank_table):
	# if other's root is null, return
	if g == None:
		return
	# if other's root's children is null, put the url in the rank_table
	if g.children == None:
		if g.full_url in rank_table:
			rank_table[g.full_url]+=prev_score
		else:
			rank_table[g.full_url]=prev_score
		return
	# if user's root/childrens is null
	if ug == None or ug.children == None:
		if prev_bd > 0.7:
			for child in g.children.values()
			_update_rank_table(None, child, level+1, prev_bd-0.02, prev_score+prev_bd, rank_table)
		else:
			return
	else:
		# compute two dictionaries of frequencies: (use levels)
		# compute bhatta_dist between two dicts
		# if bd is over 0.4, iterate over keys of other's graph (g), filling in the blanks with None
		d1 = {}
		d2 = {}
		for key, value in ug.children:
			d1[key] = (value.node_count)/ulevel_dict[level]
		for key, value in g.children:
			d2[key] = (value.node_count)/level_dict[level]
		bd = bhatta_dist(d1, d2)
		if bd >= 0.4:
			for key in g.children.keys():
				if key not in ug:
					ug_child = None:
				else:
					ug_child = ug.children[key]
				g_child = g.children[key]
				_update_rank_table(ug_child, g_child, level_dict, level+1, bd, bd, rank_table)

def recommend_urls(user):
	user_hn_list = list(HistoryNode.objects.values('url', 'last_title', 'user__id'))
	ug = construct_graph(user_hn_list)
	user_ids = set(map(lambda hn: hn['user__id'], hn_list))
	rank_table = {}
	for user_id in user_ids:
		filtered_hns = filter(lambda hn: hn['user__id']==user_id, hn_list)
		g = construct_graph(filtered_hns)
		update_rank_table(ug, g, rank_table)

	ranked_urls = list(rank_table.items())
	ranked_urls = filter((lambda (x,y): x not in user_urls), ranked_urls)
	return ranked_urls

