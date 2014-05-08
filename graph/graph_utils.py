from __future__ import division
from django.shortcuts import render
from core.models import *
from django.core import serializers
from django.http import HttpResponse
from string import split
from django.utils import simplejson
from django.http import Http404
from datetime import datetime
from urlparse import urlparse
import tldextract
from core.rec_utils import *
try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

def compare_to_friend(user, o_user):
    user_hns = HistoryNode.objects.filter(user=user)
    other_hns = HistoryNode.objects.filter(user=o_user)
    u_graph = UrlGraph()
    u_root = u_graph.create()
    o_graph = UrlGraph()
    o_root = o_graph.create()
    for user_hn in user_hns:
        u_graph.insert(u_root, user_hn)
    for other_hn in other_hns:
        o_graph.insert(o_root, other_hn)
    if u_graph == None or o_graph == None:
        return 0
    if u_graph.root == None or o_graph.root == None:
        return 0
    d1, d2 = {}, {}
    for key in u_graph.root.gchildren:
        d1[key] = (u_graph.root.gchildren[key].node_count)/(u_graph.levels[1])
    for key in o_graph.root.gchildren:
        d2[key] = (o_graph.root.gchildren[key].node_count)/(o_graph.levels[1])
    return bhatta_dist(d1, d2)

def filter_http_s(hn):
    l = urlparse(hn.url)
    return(l.scheme == 'http' or l.scheme == 'https')

def chop_protocol(hn):
    url = hn.url
    if url[-1] == '/':
        url = url[:-1]
    if url.startswith('http://'):
        url = url[7:]
    if url.startswith('https://'):
        url = url[8:]
    hn.url = url
    return hn

def get_chop_protocol(url):
    if url[-1] == '/':
        return url[:-1]
    if url.startswith('http://'):
        return url[7:]
    if url.startswith('https://'):
        return url[8:]

def split_url(hn):
    url = hn.url
    url = url.split('/')
    if url[-1] == '':
        del(url[-1])
    hn.url = url
    return hn

def format_date(hn):
    ms = hn.visit_time
    date = datetime.fromtimestamp(ms/1000.0).strftime('%Y-%m-%d')
    hn.visit_time = date
    return hn

def get_value_graph(root):
  if root.gchildren == None:
    return
  root.gchildren = root.gchildren.values()
  for child in root.gchildren:
    get_value_graph(child)

def get_formatted_blocked(root):
    DUMMY = 333
    if root.gchildren == None:
        return
    if DUMMY in root.gchildren:
        del(root.gchildren[DUMMY])
    root.gchildren = root.gchildren.values()
    for child in root.gchildren:
        get_formatted_blocked(child)

def send_line_plot(hn_list):
    hn_list = filter(filter_http_s, hn_list)
    hn_list = map(chop_protocol, hn_list)
    hn_list = map(format_date, hn_list)
    hn_list = sorted(hn_list, key=lambda hn: hn.visit_time)
    hn_list = map(split_url, hn_list)
    domains = map(lambda hn: hn.url[0], hn_list)
    all_domains = dict.fromkeys(domains, 0)
    dates = map(lambda hn: hn.visit_time, hn_list)
    line_dict = OrderedDict.fromkeys(dates)
    
    for hn in hn_list:
        all_domains[hn.url[0]] += 1

    ranked_domains = list(all_domains.items())
    ranked_domains  = list(reversed(sorted(ranked_domains, key=lambda (x,y): y)))
    filtered_domains_list = map(lambda (x,y): x, ranked_domains[:10])
    filtered_domains = set(filtered_domains_list)

    for hn in hn_list:
        if line_dict[hn.visit_time] == None:
            line_dict[hn.visit_time] = OrderedDict.fromkeys(filtered_domains, 0)
        if hn.url[0] in filtered_domains:
            line_dict[hn.visit_time][hn.url[0]] += 1

    return({'sorted_domains':filtered_domains_list, 'line_dict':line_dict})

def send_digraph(hn_list):
    # hn_list = filter(filter_http, hn_list)
    domains = set(map(lambda hn: tldextract.extract(hn.url).domain, hn_list))
    # domains = list(OrderedDict.fromkeys(domains, 0))

    hn_list = map(chop_protocol, hn_list)

    urls = set(map(lambda hn: hn.url, hn_list))
    # hn_list = map(split_url, hn_list)

    domain_id_dict = {}
    i = 0
    for domain in domains:
        domain_id_dict[domain] = i
        i += 1

    url_dict = {}
    for url in urls:
        url_dict[url] = {}

    for hn in hn_list:
        if not hn.referrer is None:
            ref_url = get_chop_protocol(hn.referrer.url)
            if ref_url in url_dict and ref_url != hn.url:
                hn_url_obj = url_dict[hn.url]
                ref_url_obj = url_dict[ref_url]

                if ref_url in hn_url_obj:
                    hn_url_obj[ref_url]['count'] += 1
                else:
                    hn_url_obj[ref_url] = {'count': 1, 'type': set([get_link_type_name(hn.transition_type)]), 'valid': True}

                if hn.url in ref_url_obj:
                    ref_url_obj[hn.url]['count'] += 1
                    ref_url_obj[hn.url]['type'].add(get_link_type_name(hn.transition_type))
                else:
                    ref_url_obj[hn.url] = {'count': 1, 'type': set([get_link_type_name(hn.transition_type)]), 'valid': True}

    for n_key in url_dict.keys():
        n = url_dict[n_key]

        if len(n) == 0:
            del(url_dict[n_key])

    nodes = []
    links = []
    id_dict = {}
    i = 0
    for url in url_dict:
        nodes.append({'name':url, 'group':domain_id_dict[tldextract.extract(url).domain]})
        id_dict[url] = i
        i += 1

    for url in url_dict:
        link_list = url_dict[url]
        for url2 in link_list:
            link = link_list[url2]
            link2 = url_dict[url2][url]
            if link['valid']:
                links.append({'source':id_dict[url], 'target':id_dict[url2], 'value': 5 * link['count'], 'type': ' | '.join(link['type'])})
                link['valid'] = False
                link2['valid'] = False

    return {'nodes':nodes, 'links':links}