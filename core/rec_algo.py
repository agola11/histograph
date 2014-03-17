from core.models import HistoryNode
from urlparse import urlparse
import numpy
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

freq_dict = []
debug_list = []

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
def consec_dedupe(hn_list, level):
	l = []
	templist = []
	count = 1
	for i in range(len(hn_list)):
		if len(hn_list[i]['url']) < level:
			continue
		if i+1 >= len(hn_list) or hn_list[i]['url'][level-1] != hn_list[i+1]['url'][level-1]:
			templist.append(hn_list[i])
			l.append(templist)
			freq_dict.append((level, ('/'.join(hn_list[i]['url'][:level])), count))
			templist = []
			count = 1
		else:
			templist.append(hn_list[i])
			count+=1
	return l

# TODO: change extension_id to user_id once user auth is implemented
# TODO: use values (not objects.all()) to rid unused values
# DEFINITON: Depth starts at 1.
def get_frequencies(max_depth):
	global freq_dict
	freq_dict = []

	hn_list = list(HistoryNode.objects.values('url'))
	hn_list = filter(filter_http, hn_list)
	hn_list = sorted(hn_list, key=lambda hn: hn['url'])
	hn_list = map(split_url, hn_list)

	rec_update_freq([hn_list], max_depth, 1)

	return sorted(freq_dict, key=lambda (x,y,z): y)

# Recursive helper function
def rec_update_freq(hn_lists, max_depth, level):
	if level > max_depth:
		return

	for hn_list in hn_lists:
		lists = consec_dedupe(hn_list, level)
		debug_list.append(lists)
		rec_update_freq(lists, max_depth, level+1)


def rank_users(user):
	pass
