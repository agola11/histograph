from __future__ import division
from urlparse import urlparse
from django.http import Http404
from math import log, sqrt
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict
import tldextract

def remove_trail(hn):
	url = hn['url']
	if url[-1] == '/':
		url = url[:-1]
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

class GraphNode:
	def __init__(self, name, node_count, level, full_url):
		self.name = name
		self.gchildren = None
		self.node_count = node_count
		self.gdepth= level
		self.full_url = full_url

class UrlGraph:
	def __init__(self):
		self.root = None
		self.levels = {}

	def create(self):
		self.levels[0] = 1
		root = GraphNode('root', 0, 0, '')
		self.root = root
		return root

	def rec_insert(self,top_root, hn, level, curr_root):
		if len(hn['url']) < level:
			return top_root
		url_snip = hn['url'][level-1]
		if curr_root.gchildren == None:
			curr_root.gchildren = {}
			child = GraphNode(url_snip, 1, level, '/'.join(hn['url'][:level]))
			curr_root.gchildren[url_snip] = child
		else:
			if url_snip not in curr_root.gchildren:
				child = GraphNode(url_snip, 1, level, '/'.join(hn['url'][:level]))
				curr_root.gchildren[url_snip] = child
			else:
				child = curr_root.gchildren[url_snip]
				child.node_count += 1
	
		if level not in self.levels:
			self.levels[level] = 1
		else:
			self.levels[level] += 1
		self.rec_insert(top_root, hn, level+1, child)

	def _contains(self, root, hn, level):
		pass

	def rec_delete(self, top_root, hn, level, curr_root):
		pass

	def insert(self, root, hn):
		hn = split_url(hn)
		root = self.rec_insert(root, hn, 1, root)
		return root

	'''
	def delete(self, root, hn):
		hn['url'] = strip_scheme(hn['url'])
		hn = split_url(hn)
		root = self.rec_delete(root, hn, 1, root)
		return root
	'''

def strip_scheme(url):
	parsed = urlparse(url)
	scheme = "%s://" % parsed.scheme
	return parsed.geturl().replace(scheme, '', 1)

def construct_graph(hn_list):
	hn_list = filter(filter_http, hn_list)
	graph = UrlGraph()
	root = graph.create()
	for hn in hn_list:
		graph.insert(root, hn)
	return graph

def update_rank_table(ug, g, rank_table):
	ulevel_dict = ug.levels
	level_dict = g.levels
	_update_rank_table(ug.root, g.root, ulevel_dict, level_dict, 1, 0, 0, rank_table)

def _update_rank_table(ug, g, ulevel_dict, level_dict, level, prev_bd, prev_score, rank_table):
	# if other's root is null, return
	if g == None:
		return
	# if other's root's children is null, put the url in the rank_table
	if g.gchildren == None:
		if tldextract.extract(g.full_url).domain == 'reddit':
			prev_score = prev_score*30
		if g.full_url in rank_table:
			rank_table[g.full_url]+=prev_score
		else:
			rank_table[g.full_url]=prev_score
		return
	# if user's root/childrens is null
	if ug == None or ug.gchildren == None:
		if prev_bd > 0.001:
			for child in g.gchildren.values():
				_update_rank_table(None, child, ulevel_dict, level_dict, level+1, prev_bd-0.001, prev_score+prev_bd, rank_table)
		else:
			return
	else:
		# compute two dictionaries of frequencies: (use levels)
		# compute bhatta_dist between two dicts
		# if bd is over 0.4, iterate over keys of other's graph (g), filling in the blanks with None
		d1 = {}
		d2 = {}
		for key in ug.gchildren:
			d1[key] = (ug.gchildren[key].node_count)/ulevel_dict[level]
		for key in g.gchildren:
			d2[key] = (g.gchildren[key].node_count)/level_dict[level]
		bd = bhatta_dist(d1, d2)
		if bd >= 0.001:
			for key in g.gchildren:
				if key not in ug.gchildren:
					ug_child = None
				else:
					ug_child = ug.gchildren[key]
				g_child = g.gchildren[key]
				_update_rank_table(ug_child, g_child, ulevel_dict, level_dict, level+1, bd, prev_score+bd, rank_table)