from pyquery import PyQuery as pq
from HTMLParser import HTMLParser
import logging as log
import html2text

from help import *

unescape_tags = HTMLParser().unescape
headers = ['h%s' % x for x in range(1,10) ]
html2md = html2text.HTML2Text()
html2md.body_width = 0


#TODO: allow to format entries (i'm looking at you someguynamedted)
def format_series_link(name, link):
    return '<p><a href="%s" rel="nofollow">%s</a></p>'% (link, name)

def find_suitable_list(title):
    #simple way: d(b.parents(':header').nextAll('ul')[0]).append('<li>test</li>')
    #alas we have multiple lists under a single header sometimes (i'm looking at you someguynamedted)
    #ok now we get the last ul element before encountering another header
    #so a loop will have to do

    ul = None
    el = title.next()

    while True:
        if not el: break

        if el[0].tag.lower() == 'ul': ul = el
        if el[0].tag.lower() in headers: break
        
        el = el.next()

def update_series(wiki, story, series_url):
    q = pq(unescape_tags(wiki.content_html))
    if series_url.endswith('/'): series_url = series_url[:-1]

    log.debug('updating series %s' % series_url)

    a =  q('a[href^="%s"]' % series_url) 
    title = q(a.parents(':header'))

    if not title:
        log.error('no title linking to that series found on %s' % wiki.page)
        return 

    log.debug('found matching title')

    ul = find_suitable_list(title)    
    if not ul: 
        log.error('unable to find suitable list on %s!' % wiki.page)
        return 
    
    ul.append(q('<li>%s</li>' % format_series_link(story.title, story.permalink)))
    q('.toc').remove() # reddit auto generates toc

    log.debug('appending to wiki')

    wiki.edit(html2md.handle(q.html())) #convert to markdown and edit page
