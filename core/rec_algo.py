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

freq_dict = []

# user's frequency dictionary
user_dict = []

# everybody else's user_id mapped to a dictionary
cumul_dict = {}


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
def reduce_update_user_dict(hn_list, level):
	l = []
	templist = []
	count = 1
	removed = 0

	for i in range(len(hn_list)):
		if len(hn_list[i]['url']) < level:
			# if not in dict, put in dict
			removed += 1
			continue
		if i+1 >= len(hn_list) or hn_list[i]['url'][level-1] != hn_list[i+1]['url'][level-1]:
			templist.append(hn_list[i])
			l.append(templist)
			user_dict.append((('/'.join(hn_list[i]['url'][:level])), {'level':level, 'freq':(count/(len(hn_list)-removed))}))
			templist = []
			count = 1
		else:
			templist.append(hn_list[i])
			count+=1
	return l

def reduce_update_cumul_dict(hn_list, level):
	l = []
	templist = []
	count = 1
	removed = 0

	for i in range(len(hn_list)):
		if len(hn_list[i]['url']) < level:
			# if not in dict, put in dict
			removed += 1
			continue
		if i+1 >= len(hn_list) or hn_list[i]['url'][level-1] != hn_list[i+1]['url'][level-1]:
			templist.append(hn_list[i])
			l.append(templist)
			freq_dict.append((level, ('/'.join(hn_list[i]['url'][:level])), count, (count/(len(hn_list)-removed))))
			templist = []
			count = 1
		else:
			templist.append(hn_list[i])
			count+=1
	return l

# TODO: use values (not objects.all()) to rid unused values
# TODO: maybe get rid of max_depth?
# DEFINITON: Depth starts at 1.
def get_frequencies():
	global user_dict
	user_dict = []

	hn_list = list(HistoryNode.objects.values('url', 'extension_id'))
	hn_list = filter(filter_http, hn_list)
	hn_list = sorted(hn_list, key=lambda hn: hn['url'])
	hn_list = map(split_url, hn_list)

	rec_update_freq([hn_list], 1, reduce_update_user_dict)

	return sorted(user_dict, key=lambda (w,x): w)

# Recursive helper function
def rec_update_freq(hn_lists, level, reducer):
	for hn_list in hn_lists:
		lists = reducer(hn_list, level)
		rec_update_freq(lists, level+1, reducer)

# TODO: determine if we continue to recurseively search even though score is 0.  
# what is threshold?
# TODO: change extension_id to user_id once user auth is implemented
def rank_urls(user):
	# Initialize global variables to empty here
	global user_dict
	user_dict = []

	hn_list = list(HistoryNode.objects.values('url', 'extension_id'))
	extension_ids = set(map(lambda hn: hn['extension_id'], hn_list))

	if user not in extension_ids:
		raise Http404

	user_hn_list = filter(lambda hn: hn['extension_id']==user, hn_list)



	for extension_id in extension_ids:
		pass

