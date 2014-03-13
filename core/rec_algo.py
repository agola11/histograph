from core.models import HistoryNode
from urlparse import urlparse
from django.utils import simpleson
import numpy

def filter_http(hn):
	l = hn['url'].split(':')
	return(l[0] == 'http')

def clean_url(hn):
	url = hn['url']
	if url.startswith('http://'):
		hn['url'] = url[7:]
	return hn

# TODO: change extension_id to user_id once user auth is implemented
# TODO: use values (not objects.all()) to rid unused values
def get_frequencies(depth):
	hn_list = list(HistoryNode.objects.all())
	hn_list = map(clean_url, filter(filter_http, hn_list))
	hn_list = sorted(hn_list, key=lambda hn: hn['url'])


def rank_users(user):
	pass
