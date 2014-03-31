from django.shortcuts import render
from core.models import HistoryNode
from django.core import serializers
from django.http import HttpResponse
from string import split
from django.utils import simplejson
from django.http import Http404

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

def reduce_bubble_tree(child, level):
	templist = []
	children = []
	urls = child['url']
	count = 1
	removed = 0

	for i in range(len(urls)):
		if len(urls[i]['url']) < level:
			removed += 1
			continue
		if i+1 >= len(urls) or urls[i][level-1] != urls[i+1][level-1]:
			templist.append(urls[i])
			children.append({'node_count':count,'name':('/'.join(urls[i][:level])),'urls':templist})
			templist = []
			count = 1
		else:
			templist.append(hn_list[i])
			count+=1
	return children

def update_bubble_tree(children, level):
	for child in children:
		children = reduce_user_dict(child, level)
		if children:
			child['children'] = children
		update_bubble_tree(children, level+1)

def send_bubble(user):
	bubble_root = {}
	hn_list = list(HistoryNode.objects.values('url', 'extension_id'))
	hn_list = filter(filter_http, hn_list)
	hn_list = sorted(hn_list, key=lambda hn: hn['url'])
	extension_ids = set(map(lambda hn: hn['extension_id'], hn_list))

	user_urls = set(map(lambda hn: hn['url'], filter(lambda hn: hn['extension_id']==user, hn_list)))
	hn_list = map(split_url, hn_list)

	if user not in extension_ids:
		raise Http404

	user_hn_list = filter(lambda hn: hn['extension_id']==user, hn_list)

	bubble_root['node_count'] = 0
	bubble_root['name'] = 'top_level'
	bubble_root['urls'] = map(lambda hn: hn['url'], user_hn_list)


	update_bubble_tree([bubble_root], 1)
	return bubble_root

	return 