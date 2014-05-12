from __future__ import division
from urlparse import urlparse
from math import log, sqrt, exp, e
from core.models import HistoryNode, HistographUser, UserWeight
import copy
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict
import tldextract

# split a node's url into an array of segments delineated by slashes
def get_split_url(hn):
	url = hn.url
	parsed = urlparse(url)
	scheme = "%s://" % parsed.scheme
	url = parsed.geturl().replace(scheme, '', 1)
	url = url.split('/')
	if url[-1] == '':
		del(url[-1])
	return url

# run the recommendations algorithm
def run_algorithm(user):
  user_hns = HistoryNode.objects.filter(user = user, url__regex = 'http://.*', is_blocked=False)
  user_urls = HistoryNode.objects.filter(user = user).values('url')
  user_urls = set(map(lambda hn : hn['url'], user_urls))
  uws = user.userweight_to.all()
  weight_dict = {}
  for uw in uws:
  	weight_dict[uw.from_user.id] = uw.weight
  
  all_users = HistographUser.objects.all()
  user_graph = UrlGraph()
  u_root = user_graph.create()
  rank_table = {}
  for user_hn in user_hns:
    user_graph.insert(u_root, user_hn)
  for o_user in all_users:
    if o_user != user:
      other_hns = o_user.historynode_set.filter(url__regex = 'http://.*', is_blocked=False)
      other_graph = UrlGraph()
      o_root = other_graph.create()
      for other_hn in other_hns:
        other_graph.insert(o_root, other_hn)
      update_rank_table(user_graph, other_graph, rank_table, o_user.id, weight_dict)

  ranked_urls = list(rank_table.items())
  ranked_urls = filter((lambda (x,y): ('https://' + x) not in user_urls and ('http://' + x) not in user_urls), ranked_urls)
  ranked_urls = list(reversed(sorted(ranked_urls, key=lambda (x,y): y['score'])))
  return ranked_urls

# Compute Bhattacharya Distance between two distributions
def bhatta_dist(d1, d2):
	if d1 == None or d2 == None:
		return 0
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
		self.last_title = None
		self.is_dummy = False

class UrlGraph:
	def __init__(self):
		self.root = None
		self.levels = {}

	def create(self):
		self.levels[0] = 1
		root = GraphNode('root', 1, 0, '')
		self.root = root
		return root

	def _rec_insert(self,top_root, hn, url, level, curr_root):
		DUMMY = 333
		if len(url) < level:
			return top_root
		url_snip = url[level-1]
		if curr_root.gchildren == None:
			curr_root.gchildren = {}
			child = GraphNode(url_snip, 1, level, '/'.join(url[:level]))
			if len(url) == level:
				child.last_title = hn.last_title
				if child.gchildren == None:
					child.gchildren = {}
				if DUMMY in child.gchildren:
					child.gchildren[DUMMY].node_count += 1
				else:
					dummy_node = GraphNode('dummy', 1, level+1, '/'.join(url[:level]))
					dummy_node.is_dummy = True
					child.gchildren[DUMMY] = dummy_node
			curr_root.gchildren[url_snip] = child
		else:
			if url_snip not in curr_root.gchildren:
				child = GraphNode(url_snip, 1, level, '/'.join(url[:level]))
				if len(url) == level:
					child.last_title = hn.last_title
					if child.gchildren == None:
						child.gchildren = {}
					if DUMMY in child.gchildren:
						child.gchildren[DUMMY].node_count += 1
					else:
						dummy_node = GraphNode('dummy', 1, level+1, '/'.join(url[:level]))
						dummy_node.is_dummy = True
						child.gchildren[DUMMY] = dummy_node
				curr_root.gchildren[url_snip] = child
			else:
				child = curr_root.gchildren[url_snip]
				child.node_count += 1
				if len(url) == level:
					child.last_title = hn.last_title
					if child.gchildren == None:
						child.gchildren = {}
					if DUMMY in child.gchildren:
						child.gchildren[DUMMY].node_count += 1
					else:
						dummy_node = GraphNode('dummy', 1, level+1, '/'.join(url[:level]))
						dummy_node.is_dummy = True
						child.gchildren[DUMMY] = dummy_node
	
		if level not in self.levels:
			self.levels[level] = 1
		else:
			self.levels[level] += 1
		self._rec_insert(top_root, hn, url, level+1, child)

	def _rec_delete(self, top_root, hn, url, level, curr_root):
		if curr_root == None:
			return top_root
		if curr_root.gchildren == None or len(url) < level:
			return top_root
		url_snip = url[level-1]
		if url_snip not in curr_root.gchildren:
			return top_root
		else:
			child = curr_root.gchildren[url_snip]
			child.node_count -= 1
			self.levels[level] -= 1
			self._rec_delete(top_root, hn, url, level+1, child)

	# Remove nodes with node_count of 0
	def _clean_graph(self, curr_root):
		if curr_root == None or curr_root.gchildren == None:
			return
		copied = copy.deepcopy(curr_root.gchildren)
		for key in copied:
			child = curr_root.gchildren[key]
			if child.node_count <= 0:
				del(curr_root.gchildren[key])
		for key in curr_root.gchildren:
			self._clean_graph(curr_root.gchildren[key])

	def insert(self, root, hn):
		url = get_split_url(hn)
		self._rec_insert(root, hn, url, 1, root)
		return self.root

	# Same format as insert.  Expects a HistoryNode object with a split url and stripped scheme
	# in object form.
	def delete(self, root, hn):
		url = get_split_url(hn)
		root = self._rec_delete(self.root, hn, url, 1, root)
		# self._clean_graph(self.root)
		return self.root

def strip_scheme(url):
	parsed = urlparse(url)
	scheme = "%s://" % parsed.scheme
	return parsed.geturl().replace(scheme, '', 1)

def update_rank_table(ug, g, rank_table, o_id, weight_table):
	if ug == None or g == None:
		return
	ulevel_dict = ug.levels
	level_dict = g.levels
	_update_rank_table(ug.root, g.root, ulevel_dict, level_dict, 1, 0, 0, rank_table, o_id, weight_table)

def _update_rank_table(ug, g, ulevel_dict, level_dict, level, prev_bd, prev_score, rank_table, o_id, weight_table):
	# if other's root is null, return
	if g == None:
		return
	# if other's root has a last_title (meaning full_url), put the url in the rank_table
	if g.last_title != None:
		if o_id in weight_table:
			prev_score = prev_score + weight_table[o_id]*prev_score
		if g.full_url not in rank_table:
			rank_table[g.full_url] = {'score':prev_score, 'last_title': g.last_title, 'users': {o_id:prev_score}}
		else:
			score = rank_table[g.full_url]['score']
			score += prev_score
			rank_table[g.full_url]['score'] = score
			rank_table[g.full_url]['users'][o_id] = prev_score
	if g.gchildren == None:
		return
	# if user's root/childrens is null
	if ug == None or ug.gchildren == None:
		if prev_bd > 0.001:
			for child in g.gchildren.values():
				_update_rank_table(None, child, ulevel_dict, level_dict, level+1, prev_bd-0.005, prev_score+prev_bd, rank_table, o_id, weight_table)
		else:
			return
	else:
		# compute two dictionaries of frequencies: (use levels)
		# compute bhatta_dist between two dicts
		# if bd is over 0.4, iterate over keys of other's graph (g), filling in the blanks with None
		d1 = {}
		d2 = {}
		for key in ug.gchildren:
			if level in ulevel_dict:
				d1[key] = (ug.gchildren[key].node_count)/ulevel_dict[level]
			else:
				d1[key] = 0.0
		for key in g.gchildren:
			if level in level_dict:
				d2[key] = (g.gchildren[key].node_count)/level_dict[level]
			else:
				d2[key] = 0.0
		bd = bhatta_dist(d1, d2)
		if bd >= 0.001:
			for key in g.gchildren:
				if key not in ug.gchildren:
					ug_child = None
					f_u = 0
				else:
					ug_child = ug.gchildren[key]
					if level in ulevel_dict:
						f_u = (ug.gchildren[key].node_count)/ulevel_dict[level]
					else:
						f_u = 0.0
				g_child = g.gchildren[key]
				_update_rank_table(ug_child, g_child, ulevel_dict, level_dict, level+1, bd, (prev_score+bd)*(exp(e*f_u)), rank_table, o_id, weight_table)
	
    
