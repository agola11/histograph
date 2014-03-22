from __future__ import division
from core.models import HistoryNode
from urlparse import urlparse
from django.http import Http404
import numpy
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

# TODO: implement caching
# TODO: add linked websites (using referrers?)
# TODO: fiddle with constants
WEIGHT = 0.5

# user's frequency dictionary
user_dict = {}

# url mapped to rank
url_dict = {}


def filter_http(hn):
	l = urlparse(hn['url'])
	return(l.scheme == 'http')

def split_url(hn):
	url = hn['url']
	if url.startswith('http://'):
		url = url[7:]
	url = url.split('/')
	if url[-1] == '':
		del(url[-1])
	hn['url'] = url
	return hn

# Remove consecutive urls in sorted hn_list
# Return a list of list of categorized urls
# TODO: incorporate accumulation here, return score in tuple
def reduce_user_dict(hn_list, level):
	l = []
	templist = []
	count = 1
	removed = 0

	for i in range(len(hn_list)):
		if len(hn_list[i]['url']) < level:
			removed += 1
			continue
		if i+1 >= len(hn_list) or hn_list[i]['url'][level-1] != hn_list[i+1]['url'][level-1]:
			templist.append(hn_list[i])
			l.append(templist)
			user_dict[('/'.join(hn_list[i]['url'][:level]))] = (count/(len(hn_list)-removed))
			templist = []
			count = 1
		else:
			templist.append(hn_list[i])
			count+=1
	return l

def reduce_url_dict(hn_list_tuple, level):
	l = []
	templist = []
	reserved = []
	count = 1
	removed = 0

	hn_list = hn_list_tuple[0]
	prev_score = hn_list_tuple[1]

	for i in range(len(hn_list)):
		if len(hn_list[i]['url']) < level:
			url = '/'.join(hn_list[i]['url'])
			if url not in url_dict:
				url_dict[url] = prev_score
			else:
				url_dict[url] += prev_score
			removed += 1
			continue
		if i+1 >= len(hn_list) or hn_list[i]['url'][level-1] != hn_list[i+1]['url'][level-1]:
			templist.append(hn_list[i])
			freq = (count/(len(hn_list)-removed))
			url = '/'.join(hn_list[i]['url'][:level])
			if url not in user_dict:
				score = 0 + 0.2 * (level-1)
			else:
				user_freq = user_dict['url']
				score = min(freq, user_freq)/max(freq, user_freq) + 0.2 * (level-1)
			if score > 0:
				l.append((templist, score+prev_score+(WEIGHT*level)))
			templist = []
			count = 1
		else:
			templist.append(hn_list[i])
			count+=1
	return l

# DEFINITON: Depth starts at 1.
# TEMPORARY FUNCTION for debugging.  Use to make sure user_dict is accurate
def get_frequencies():
	global user_dict
	user_dict = {}

	hn_list = list(HistoryNode.objects.values('url', 'extension_id'))
	hn_list = filter(filter_http, hn_list)
	hn_list = sorted(hn_list, key=lambda hn: hn['url'])
	hn_list = map(split_url, hn_list)

	update_user_dict([hn_list], 1)

	return list(reversed(sorted(user_dict.items(), key=lambda (x,y): x)))

# Recursive helper function to update user_dict
def update_user_dict(hn_lists, level):
	for hn_list in hn_lists:
		lists = reduce_user_dict(hn_list, level)
		update_user_dict(lists, level+1)

# Recursive helper function to update url_dict
def update_url_dict(hn_list_tuples, level):
	for hn_list_tuple in hn_list_tuples:
		lists = reduce_url_dict(hn_list_tuple, level)
		update_url_dict(lists, level+1)

# TODO: determine if we continue to recursively search even though score is 0.  
# what is threshold?
# TODO: change extension_id to user_id once user auth is implemented
# TODO: maybe only need to sort once? Set a min number of urls?
def rank_urls(user):
	# Initialize global variables to empty here
	global user_dict
	user_dict = {}

	global url_dict
	url_dict = {}

	hn_list = list(HistoryNode.objects.values('url', 'extension_id'))
	hn_list = filter(filter_http, hn_list)
	hn_list = sorted(hn_list, key=lambda hn: hn['url'])

	extension_ids = set(map(lambda hn: hn['extension_id'], hn_list))

	if user not in extension_ids:
		raise Http404

	user_hn_list = filter(lambda hn: hn['extension_id']==user, hn_list)
	user_urls = set(map(lambda hn: hn['url'], user_hn_list))

	user_hn_list = map(split_url, user_hn_list)
	update_user_dict([user_hn_list], 1)

	hn_list = map(split_url, hn_list)

	extension_ids.remove(user)
	for extension_id in extension_ids:
		filtered_hns = filter(lambda hn: hn['extension_id']==extension_id, hn_list)
		update_url_dict([(filtered_hns,0)], 1)

	ranked_urls = url_dict.items()
	ranked_urls = filter(lambda (x,y): x not in user_urls, rank_urls)

	return list(reversed(sorted(ranked_urls, key=lambda (x,y): x)))



