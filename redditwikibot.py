import logging as log
import re
import html2text
import praw
from pyquery import PyQuery as pq
from HTMLParser import HTMLParser
from time import sleep


log.basicConfig(level=log.DEBUG)

unescape_tags = HTMLParser().unescape
headers = ['h%s' % x for x in range(1,10) ]
html2md = html2text.HTML2Text()
html2md.body_width = 0

account = praw.Reddit(user_agent='hfywikibot 0.1 by /u/HFY_wiki_bot')
account.login('hfy_wiki_bot','dupa.8')
account.subname = 'hfybeta'
account.last_author = ''

re_title = re.compile('(\[|\()(oc|pi|jenkinsverse|j-verse|jverse|misc|nsfw)(\]|\))', re.IGNORECASE)

class InvalidURLError(Exception): pass

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

        if href == link: return a

def sanitize_title(title):
    return re.sub(re_title, '', title)

#TODO: allow to format entries (i'm looking at you someguynamedted)
def format_series_link(name, link):
    return '<p><a href="%s" rel="nofollow">%s</a></p>'% (link, sanitize_title(name))

#simple way: d(b.parents(':header').nextAll('ul')[0]).append('<li>test</li>')
#alas we have multiple lists under a single header sometimes (i'm looking at you someguynamedted)
#ok now we get the last ul element before encountering another header
#so a loop will have to do
def find_series_list(q, series_url):
    if series_url.endswith('/'): series_url = series_url[:-1]

    a =  q('a[href^="%s"]' % series_url) 
    title = q(a.parents(':header'))

    if not title:
        log.error('no title linking to that series found')
        return 

    log.debug('found matching title')

    ul = None
    el = title.next()

    while True:
        if not el: break

        if el[0].tag.lower() == 'ul': ul = el
        if el[0].tag.lower() in headers: break
        
        el = el.next()

    return ul

def new_series_section(post):
    authors_wiki = 'http://www.reddit.com/r/' + account.subname + '/wiki/authors/' + post.author.name

    content = """
<h2><a href="%s">%s</a></h2>
    """ % (post.author.name, authors_wiki + '/one-shots', sanitize_title(post.title), post.permalink)

    return pq(content)

def new_series_page(post):
    authors_wiki = 'http://www.reddit.com/r/' + account.subname + '/wiki/authors/' + post.author.name

    content = """
<h2>One Shots - by: <a href="%s">%s</a></h2>
    """ % (authors_wiki, post.author.name)

    return pq(content)


def add_one_shot(post):
    authors_link = 'http://www.reddit.com/r/' + account.subname + '/wiki/authors/' + post.author.name
    one_shots_link = 'http://www.reddit.com/r/' + account.subname + '/wiki/authors/' + post.author.name + '/one-shots'

    log.debug('adding one shot %s for %s' % (post.permalink, post.author.name))

    try:
        authors_wiki = account.get_wiki_page(account.subname, 'authors/%s/%s' % (post.author.name, 'one-shots'))
        q = pq(unescape_tags(authors_wiki.content_html))
        ul = find_series_list(q, authors_wiki + '/one-shots')
    if not ul: 
        log.error('unable to find suitable list for %s on %s! creating...' % (authors_wiki + '/one-shots', wiki.page))
        return 

    except:
        log.exception('unable to get wiki page for %s' % authors_link)

    md = html2md(new_series_section().html())
    account.edit_wiki_page(account.subname, 'authors/'+post.author.name, md)

    log.debug('create one-shots wiki page for %s' % post.author.name)

    md = html2md(new_series_page().html())
    account.edit_wiki_page(one_shots_link, md)

    log.debug('author %s added to the wiki' % post.author.name)


def update_authors_page(wiki_page, post):
    log.debug('updating authors page for %s' % post.author.name)
    authors_wiki = 'http://www.reddit.com/r/' + account.subname + '/wiki/authors/' + post.author.name
    
    q = pq(unescape_tags(wiki_page.content_html))
    ul = find_series_list(q, authors_wiki + '/one-shots')

    if not ul: 
        log.error('unable to find suitable list for %s on %s! creating...' % (authors_wiki + '/one-shots', wiki.page))
        return 

    if find_link(ul, post.permalink) is not None: 
        log.debug('link alredy in correct place')
        return

    ul.append(q('<li>%s</li>' % format_series_link(post.title, post.permalink)))

    log.debug('appending to %s' % wiki_page.page)

    q('.toc').remove() # reddit auto generates toc
    q('ul li:empty').remove()

    account.edit_wiki_page(account.subname, wiki_page.page, html2md.handle(q.html()))
    update_series_section(account.get_wiki_page(account.subname, 'authors/%s/one-shots' % post.author.name), post, authors_wiki)

def prepare_author_wiki(author_wiki, series_url, name):
    q = pq(unescape_tags(author_wiki.content_html))

    if find_link(q, series_url) is not None:
        log.debug('series title already exist! updating')
    else:
        head = q('div.wiki')

        if not q('#wiki_series'):
            log.debug('appending Series section')
            head.append('<h2>Series</h2>')

        log.debug('appending series title')
        head.append('<p/>')
        head.append('<h4><a href="%s">%s</a></h4>' % (series_url, name.title()))
        head.append('<ul></ul>')

    return q

def prepare_series_wiki(name, new_name, authors_url, author):
    try:
        series_wiki = account.get_wiki_page(account.subname, 'series/' + new_name)
        qq = pq(unescape_tags(series_wiki.content_html))

        if not qq('a[href^="%s"]' % authors_url[:-1]):
            log.debug('Page exists but no title found. adding')
            qq('div.wiki').append('<h2>%s - by: <a href="%s">%s</a></h2>' % (name, authors_url, author))
            qq('div.wiki').append('<ul></ul>')
    except:
        log.debug('creating new wiki page')
        qq = pq('<h2><a href="%s">%s</a></h2><ul/>' % (authors_url, name))
        series_wiki = NewWikiPage('/series/'+new_name)

    return series_wiki, qq

def add_to_series(author_wiki, post, name):
    account.last_author = post.author.name
    new_name = re.sub('[^0-9a-zA-Z]+', '_', name)
    series_url = 'http://www.reddit.com/r/' + account.subname + '/wiki/series/' + new_name
    authors_url = 'http://www.reddit.com/r/' + account.subname + '/wiki/authors/' + post.author.name

    log.debug('creating series %s in location: /series/%s' % (name, new_name))

    q = prepare_author_wiki(author_wiki, series_url, name)
    series_wiki, qq = prepare_series_wiki(name, new_name, authors_url, post.author.name)
    
    if find_link(qq, post.permalink) is not None:
        log.error('series link already on a wiki page')
    else:
        update_series_page(series_wiki, post, authors_url, qq)

    update_series_section(author_wiki, post, series_url, q)


def update_series_page(wiki_page, post, series_url, q):
    update_series_section(wiki_page, post, series_url, q)

def update_series_section(wiki_page, post, series_url, q=None):
    log.debug('editing series for %s on %s' % (series_url, wiki_page.page))

    if not q: q = pq(unescape_tags(wiki_page.content_html))

    log.debug('updating series %s' % series_url)

    ul = find_series_list(q, series_url)
    if not ul: 
        log.error('unable to find suitable list for %s on %s!' % (series_url, wiki_page.page))
        return 

    if find_link(ul, post.permalink) is not None:
        log.error('post already in correct section')
        return

    #remove link if it is in one shots
    q('a[href^="%s"]' % post.permalink[:-1]).remove() 

    ul.append(q('<li>%s</li>' % format_series_link(post.title, post.permalink)))

    log.debug('appending to wiki')

    q('ul li:empty').remove()
    q('.toc').remove() # reddit auto generates toc

    if wiki_page.page == 'new':
        account.edit_wiki_page(account.subname, wiki_page.new_page, html2md.handle(q.html()))
    else:
        account.edit_wiki_page(account.subname, wiki_page.page, html2md.handle(q.html()))

def get_wiki_page(sub, page):
    try:
        return account.get_wiki_page(sub, page)
    except:
        log.exception('error getting wiki page %s' % page)

def check_submissions():
    while True:
        sleep(30)
        log.debug('waking up!')
        new = account.get_subreddit(account.subname).get_new(limit=1)

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

def check_messages():
    pass

check_submissions()
#page = account.get_submission("http://www.reddit.com/r/HFYBeta/comments/2yfnci/oc_pancakes_test_nsfw/")
#wiki = account.get_wiki_page("hfybeta", "authors/other-guy")
