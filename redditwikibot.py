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

re_title = re.compile('(\[|\()(oc|pi|jenkinsverse|j-verse|jverse|misc|nsfw)(\]|\))', re.IGNORECASE)

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
        log.error('no title linking to that series found on %s' % wiki.page)
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

def add_one_shot(post):
    page = account.get_wiki_page('authors/%s')
    if not page:
        create_autor_page(post)
    else:
        update_author_page(post)


def create_author_page(post):
    authors_wiki = 'http://www.reddit.com/r/' + account.subname + '/wiki/authors/' + post.author.name

    log.debug('creating wiki page for %s' % post.author.name)

    txt = """
/u/%s

####[One Shots](%s)

* [%s](%s)


    """ % (post.author.name, authors_wiki + '/one-shots', sanitize_title(post.title), post.permalink)

    account.edit_wiki_page(account.subname, 'authors/'+post.author.name, txt)

    log.debug('create one-shots wiki page for %s' % post.author.name)

    txt = """

##[/u/%s](%s) - One Shots

* [%s](%s)


    """ % (post.author.name, authors_wiki, sanitize_title(post.title), post.permalink)

    account.edit_wiki_page(account.subname, 'authors/'+post.author.name+'/one-shots', txt)

    log.debug('author %s added to the wiki' % post.author.name)


def update_authors_page(wiki_page, post):
    authors_wiki = 'http://www.reddit.com/r/' + account.subname + '/wiki/authors/' + post.author.name
    
    q = pq(unescape_tags(wiki_page.content_html))
    ul = find_series_list(q, authors_wiki + '/one-shots')

    if not ul: 
        log.error('unable to find suitable list for %s on %s!' % (authors_wiki + '/one-shots', wiki.page))
        return 

    ul.append(q('<li>%s</li>' % format_series_link(post.title, post.permalink)))

    log.debug('appending to %s' % wiki.page)

    q('.toc').remove() # reddit auto generates toc
    q('ul li:empty').remove()

    wiki_page.edit(html2md.handle(q.html())) #convert to markdown and edit page
    update_series_section(account.get_wiki_page(account.subname, 'authors/%s/one-shots' % post.author.name), post, authors_wiki)


def create_series_section(wiki_page, post, name):
    new_name = re.sub('[^0-9a-zA-Z]+', '_', name)
    series_url = 'http://www.reddit.com/r/' + account.subname + '/wiki/series/' + new_name
    authors_wiki = 'http://www.reddit.com/r/' + account.subname + '/wiki/authors/' + post.author.name

    log.debug('creating series %s in location: /series/%s' % (name, new_name))

    q = pq(unescape_tags(wiki_page.content_html))

    if q('a[href^="%s"]' % series_url[:-1]):
        log.debug('series title already exist! updating instead')
        update_series_section(wiki_page, post, series_url, q)
        return

    head = q('div.wiki')
    if not q('#wiki_series'):
        head.append('<h2>Series</h2>')

    head.append('<p/>')
    head.append('<h4><a href="%s">%s</a></h4>' % (series_url, name.title()))
    head.append('<ul></ul>')

    try:
        series_page = account.get_wiki_page(account.subname, '/series/' + new_name)
        qq = pq(unescape_tags(series_page.content_html))

        if not qq('a[href^="%s"]' % post.permalink[:-1]):
            qq('div.wiki').append('<h2><a href="%s">%s</a></h2>' % (authors_wiki, name))
            qq('div.wiki').append('<ul></ul>')
    except:
        qq = pq('<h2><a href="%s">%s</a></h2><ul/>')
    

    update_series_section(wiki_page, post, series_url, q)


def update_series_section(wiki_page, post, series_url, q=None):
    log.debug('editing series for %s on %s' % (series_url, wiki_page.page))

    if not q: q = pq(unescape_tags(wiki_page.content_html))

    log.debug('updating series %s' % series_url)

    #remove link if it is in one shots
    q('a[href^="%s"]' % post.permalink[:-1]).remove() 

    ul = find_series_list(q, series_url)
    if not ul: 
        log.error('unable to find suitable list for %s on %s!' % (series_url, wiki_page.page))
        return 
    
    ul.append(q('<li>%s</li>' % format_series_link(post.title, post.permalink)))

    log.debug('appending to wiki')

    q('ul li:empty').remove()
    q('.toc').remove() # reddit auto generates toc

    wiki_page.edit(html2md.handle(q.html())) #convert to markdown and edit page

page = account.get_submission("http://www.reddit.com/r/HFYBeta/comments/2yfnci/oc_pancakes_test_nsfw/")
wiki = account.get_wiki_page("hfybeta", "authors/other-guy")
