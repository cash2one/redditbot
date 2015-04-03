import logging as log
import re
import html2text
import praw
from pyquery import PyQuery as pq
from HTMLParser import HTMLParser
from time import sleep
from requests.exceptions import HTTPError

log.basicConfig(level=log.DEBUG)

unescape_tags = HTMLParser().unescape
html2md = html2text.HTML2Text()
html2md.body_width = 0

account = praw.Reddit(user_agent='hfywikibot 0.1 by /u/HFY_wiki_bot')
account.login('hfy_wiki_bot','dupa.8')
account.subname = 'hfybeta'
account.last_author = ''

re_title = re.compile('(\[|\()(oc|pi|jenkinsverse|j-verse|jverse|misc|nsfw)(\]|\))', re.IGNORECASE)

class InvalidURLError(Exception): pass
class UnableToInitSectionError(Exception): pass

class NewWikiPage:
    def __init__(self, new_page):
        self.page = 'new'
        self.new_page = new_page

def wiki_text(content):
    return html2md(pq(content).html())

def find_link(ul, link):
    if link[-1] == '/': link = link[:-1]
    i = link.rfind('/r/')

    if i == -1:
        log.error('link %s is not a submission' % link)
        return None

    link = link[i:].lower()

    if not link[3:].startswith(account.subname.lower()):
        log.error('link %s is not valid for this subreddit' % link)
        return None

    for a in ul('a'):
        href = a.attrib['href']
        if href[-1] == '/': href = href[:-1]

        href = href[href.rfind('/r/'):].lower()

        if href == link: return pq(a)

def sanitize_title(title):
    return re.sub(re_title, '', title)

def sanitize_series_name(name):
    return re.sub('[^0-9a-zA-Z]+', '*', name)

#TODO: allow to format entries (i'm looking at you someguynamedted)
def format_series_link(name, link):
    return '<p><a href="%s" rel="nofollow">%s</a></p>'% (link, sanitize_title(name))

def find_series_list(q, series_url):
    headers = ['h%s' % x for x in range(1,10) ]
    a = find_link(q, series_url)
    if a is None: return None

    title = q(a.parents(':header'))

    if not title:
        log.error('no title linking to that series found')
        return 

    log.debug('found matching series title for %s' % series_url)

    ul = None
    el = title.next()

    while True:
        if not el: break

        if el[0].tag.lower() == 'ul': ul = el
        if el[0].tag.lower() in headers: break
        
        el = el.next()

    if ul is None:
        log.debug("no list under title found, creating...")
        ul = pq('<ul></ul>')
        title.after(ul)

    return ul

def format_for_edit(post, wiki_page_name, series_url, init_section):
    try:
        wiki = account.get_wiki_page(account.subname, wiki_page_name)
        q = pq(unescape_tags(wiki.content_html))
    except HTTPError, e:
        if e.message.startswith('404'): # page does not exist
            log.debug('%s wiki page does not exist - creating' % wiki_page_name)
            q = init_section()
        else:
            raise
    except Exception, e:
        raise

    ul = find_series_list(q, series_url)

    if not ul: #page exists but no link to series found in <h> element
        log.debug('list for %s not found on author page - creating' % series_url)
        ul = init_section(q)

        if not ul: raise UnableToInitSectionError("Unable to Init section %s" % series_url)

    if find_link(ul, post.permalink):
        log.error('link already in %s section' % series_url)
        return

    ul.append('<li><a href="%s">%s</a></li>' % (post.permalink, sanitize_title(post.title)))

    q('.toc').remove()
    q('ul li:empty').remove()

    return q

def init_section_page(html):
    def dummy(q=None):
        if not q: 
            return pq(html)
        else:
            section = pq(html)
            first_header = q('div.wiki.md :header:first')
            if first_header:
                first_header.before(section)
            else:
                q('div.wiki.md').prepend(section)

            return section('ul:first')

    return dummy
            
def init_author_series(html):
    def dummy(q=None):
        if not q: 
            return pq(html)
        else:
            if not q('#wiki_series'):
                log.debug('appending Series section')
                series = q(':header a[href*="/wiki/series/"]') 

                if series:
                    series.prepend('<h2>Series</h2>')
                else:
                    q.append('<h2>Series</h2>')
    return dummy

def add_one_shot(post):
    authors_wiki = 'authors/%s' % (post.author.name)
    series_url = '/r/%s/wiki/authors/%s/one-shots' % (account.subname, post.author.name)
    init = init_section_page('<h2><a href="%s">One Shots</a></h2><ul/>' % series_url)

    q = format_for_edit(post, authors_wiki, series_url, init)
    if q is not None and q.html() is not None:
        account.edit_wiki_page(account.subname, 'authors/%s' % post.author.name, html2md.handle(q.html()))

    authors_wiki = 'authors/%s/one-shots' % (post.author.name)
    series_url = '/r/%s/wiki/authors/%s' % (account.subname, post.author.name)
    init = init_section_page('<h2>One Shots - by: <a href="%s">%s</a></h2><ul/>' % (series_url, post.author.name))

    q = format_for_edit(post, authors_wiki, series_url, init)
    if q is not None and q.html() is not None:
        account.edit_wiki_page(account.subname, 'authors/%s/one-shots' % post.author.name, html2md.handle(q.html()))

def update_series(post, name):
    section = '/r/%s/wiki/series/%s' % (account.subname, sanitize_series_name(name))


def check_submissions():
    while True:
        log.debug('waking up!')
        new = account.get_subreddit(account.subname).get_new(limit=2)

        for submission in new:
            try:
                log.debug('checking submission %s', submission.permalink)
                if not submission.link_flair_text in ['OC', 'PI']: 
                    log.debug('no flair, continuing')
                    continue
                   
                add_one_shot(submission)
            except:
                log.exception('Error processing %s' % submission.permalink)

        log.debug('going to sleep...')

sub = account.get_submission('http://www.reddit.com/r/HFYBeta/comments/2z7qy5/octhe_history_of_humans_1011/')
sub1= account.get_submission('http://www.reddit.com/r/HFYBeta/comments/2yk6ef/test/')
