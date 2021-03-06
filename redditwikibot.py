import logging as log
import re
import html2text
import praw
from pyquery import PyQuery as pq
from HTMLParser import HTMLParser
from time import sleep
from requests.exceptions import HTTPError
from timeit import default_timer as timer


log.basicConfig(level=log.DEBUG)

unescape_tags = HTMLParser().unescape
html2md = html2text.HTML2Text()
html2md.body_width = 0


account = praw.Reddit(user_agent='hfywikibot 0.1 by /u/HFY_wiki_bot')
account.login('hfy_wiki_bot','dupa.8')
account.subname = 'hfybeta'
account.last_author = ''
account.one_shots = set()
account.series = set()

re_title = re.compile('(\[|\()(oc|pi|jenkinsverse|j-verse|jverse|misc|nsfw)(\]|\))', re.IGNORECASE)

class InvalidURLError(Exception): pass
class UnableToInitSectionError(Exception): pass

class NewWikiPage:
    def __init__(self, new_page):
        self.page = 'new'
        self.new_page = new_page

def is_header(el):
    headers = ['h%s' % x for x in range(1,10) ]
    for h in headers:
        if el.is_(h): return True

    return False

def one_shots_link(author):
    return '/r/%s/wiki/authors/%s/one-shots' % (account.subname, author)

def series_section_link():
    return '/r/%s/wiki/series/' %s account.subname

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

def reddit_link(link):
    link.lower()
    
    i = link.index('/r/'+account.subname.lower())

    if not i: return False

    if link[-1] == '/': link = link[:-1]

    return link[i:]


def sanitize_title(original):
    title = re.sub(re_title, '', original)
    title = re.sub('\[.*?\]', '', title)
    title = title.strip()

    if not title:
        return original

    return title


def sanitize_series_name(name):
    return re.sub('[^0-9a-zA-Z]+', '_', name)

#TODO: allow to format entries (i'm looking at you someguynamedted)
def format_series_link(name, link):
    return '<p><a href="%s" rel="nofollow">%s</a></p>'% (link, sanitize_title(name))

def find_series_list(q, series_url):
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
        if is_header(el): break
        
        el = el.next()

    if ul is None:
        log.debug("no list under title found, creating...")
        ul = pq('<ul></ul>')
        title.after(ul)

    return ul

def format_for_edit(post, wiki_page_name, series_url, init_section):
    q = query_wiki_page(wiki_page_name)
    if not q:
        q = init_section()

    ul = find_series_list(q, series_url)

    if not ul: #page exists but no link to series found in <h> element
        log.debug('list for %s not found on author page - creating' % series_url)
        ul = init_section(q)

        if not ul: raise UnableToInitSectionError("Unable to Init section %s" % series_url)

    if find_link(ul, post.permalink):
        log.error('link already in %s section' % series_url)
        return

    ul.append('<li><a href="%s">%s</a></li>' % (post.permalink, sanitize_title(post.title)))
    return q

def init_section(html):
    def dummy(q=None):
        if not q: 
            #TODO: pq(html)('ul:first')
            log.debug('creating new page')
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

def add_one_shot(post):
    wiki_page_name = 'authors/%s' % (post.author.name)
    series_url = one_shots_link(post.author.name) 
    init = init_section('<h2><a href="%s">One Shots</a></h2><ul/>' % series_url)
    save_wiki_page(post, wiki_page_name, series_url, init)

    wiki_page_name = 'authors/%s/one-shots' % (post.author.name)
    series_url = '/r/%s/wiki/authors/%s' % (account.subname, post.author.name)
    init = init_section('<h2>One Shots - by: <a href="%s">%s</a></h2><ul/>' % (series_url, post.author.name))
    save_wiki_page(post, wiki_page_name, series_url, init)


def init_series_section(name, series_url):
    def dummy(q=None):
        html = '<h4><a href="%s">%s</a></h4><ul/>' % (series_url, name)

        if not q: 
            log.debug('creating new page')
            q = pq('<h2 id="wiki_series">Series</h2>\n\n%s' % (html))
            return q('ul')

        section = q('#wiki_series')
        series = q(':header a[href*="/wiki/series/"]') 
        ul = find_series_list(q, series_url)

        if series: 
            log.debug('found existing series adding a new one')
            h = series.parents(':header:first')[0].tag
            html = html.replace('h4', h)
            header = pq(html)
            
            # add after last header with a link to the story
            #el = q(':header:last a[href*="/wiki/series/"]').parents(':header:first')
            #while True:
                #tmp = el.next()
                #if not tmp: break
                #if tmp(':header'): break
                
            #el.after(header)
            series.parents(':header').before(header)
        else:
            log.debug('creating series section')
            q.append('<h2 id="wiki_series">Series</h2>')
            header = pq(html)
            q.append(header)

        return header('ul')

    return dummy

def update_series(post, name):
    wiki_page_name = 'authors/%s' % (post.author.name)

    if name.startswith('http://'):
        series_url = name
        name = name.split('/')[-1].replace('_', ' ').title()
    else:
        series_url = series_url = '/r/%s/wiki/series/%s' % (account.subname, sanitize_series_name(name))

    init = init_series_section(name, series_url)
    save_wiki_page(post, wiki_page_name, series_url, init, True)

    wiki_page_name = 'series/%s' % (sanitize_series_name(name))
    authors_wiki_link = '/r/%s/wiki/authors/%s' % (account.subname, post.author.name)
    init = init_section('<h2>%s - by: <a href="%s">%s</a></h2><ul/>' % (name, authors_wiki_link, post.author.name))
    save_wiki_page(post, wiki_page_name, authors_wiki_link, init)

    remove_one_shot(post)

def save_wiki_page(post, wiki_page_name, series_url, init, remove=False):
    q = format_for_edit(post, wiki_page_name, series_url, init)
    if remove:
        remove_from_one_shots(q, post)
        
    if q is not None and q.html() is not None:
        edit_wiki_page(wiki_page_name, q)

# remove from one shot section
def remove_from_one_shots(q, post):
    try:
        ul = find_series_list(q,  one_shots_link(post.author.name))
        find_link(ul, post.permalink).parents('li:first').remove()
        log.debug('removed %s from one shots section' % post.permalink)
    except:
        log.warning('Unable to remove %s from one shots section' % post.permalink)
        #TODO: some error message migt be in order but neither of those elements *has* to exist

# remove from one shots page
def remove_one_shot(post):
    try:
        q = query_wiki_page('authors/%s/one-shots' % post.author.name)
        if not q: return

        ul = find_series_list(q, '/r/%s/wiki/authors/%s' % (account.subname, post.author.name))
        find_link(ul, post.permalink).parents('li:first').remove()
        edit_wiki_page('authors/%s/one-shots'% post.author.name, q)

        log.debug('removed %s from one shots page' % post.permalink)
    except:
        log.warning('Unable to remove %s from one shots page' % post.permalink)
        #TODO: some error message migt be in order but neither of those elements *has* to exist

def to_pq(wiki_page):
    ret = pq(unescape_tags(wiki_page.content_html))
    return ret

def clean_dom(q):
    q('.toc').remove()
    q('ul li:empty').remove()
    q('strong').replace_with(lambda x,y: y.text)

def query_wiki_page(page_name):
    try:
        while is_cached('/r/%s/wiki/%s' % (account.subname, page_name)): sleep(10)

        w = account.get_wiki_page(account.subname, page_name)
        return to_pq(w)
    except HTTPError, e:
        if e.message.startswith('404'): # page does not exist
            return None
        else:
            raise
    except Exception, e:
        raise

def edit_wiki_page(page_name, q):
    clean_dom(q)
    return account.edit_wiki_page(account.subname, page_name, html2md.handle(q.html()))

def clear_cache():
    cls = praw.DefaultHandler
    for key in list(cls.timeouts):
        if timer() - cls.timeouts[key] > 30:
            del cls.timeouts[key]
            del cls.cache[key]

def is_cached(url):
    if url[-1] == '/': url = url[:-1]

    clear_cache()
    return filter(lambda x: x[0].endswith(url), praw.DefaultHandler.timeouts.keys())

def add_author(post):
    q = query_wiki_page('authors')
    if not q:
        q = pq('<h2>Authors</h2>')

    letter = post.author.name[0].lower()

    header = q('wiki_'+ letter)

    if not header:
        header = pq('<h5>%s</h5><ul/>' % letter)
        q.append(header)

    ul = header('ul')
    ul.append('<li><a href="/r/%s/wiki/authors/%s">%s</a></li>' % (account.subname, post.author.name, post.author.name))

    lis = list(header('ul li'))
    lis.sort(key=lambda x: x.text.strip().lower()) 

    
def check_submissions_():
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

def check_submissions():
    while True:
        log.debug('waking up!')
        new = account.get_subreddit(account.subname).get_new(limit=50)

        for submission in new:
            try:
                log.debug('checking submission %s', submission.permalink)
                add_one_shot(submission)
            except:
                log.exception('Error processing %s' % submission.permalink)

        log.debug('going to sleep...')


def sort_authors_index(page_name='authors'):
    q = query_wiki_page(page_name)

    q('strong').replace_with(lambda x,y: y.text)

    ul = q('ul li h5').parents('ul:first')
    lis = list(q('ul li h5').parents('li'))
    lis.sort(key=lambda x: pq(x)('h5').text())
    new = pq('<ul>')

    for x in lis :
        tmp = pq(x)
        sort_authors_names(tmp('ul'))
        new.append(tmp)

    ul.replace_with(new)

    edit_wiki_page(page_name, q)

def sort_authors_names(ul):
    links = list(ul('li a[href*="/wiki/authors/"]'))
    links.sort(key=lambda x: x.text.strip().lower()) 

    new = pq('<ul>')
    for a in links:
        li = pq('<li>')
        li.append(pq(a))
        new.append(li)

    ul.replace_with(new)

def sort_series_index(page_name='series'):
    q = query_wiki_page(page_name)

    q('strong').replace_with(lambda x,y: y.text)

    ul = q('ul li h5').parents('ul:first')
    lis = list(q('ul li h5').parents('li'))
    lis.sort(key=lambda x: pq(x)('h5').text())

    new = pq('<ul>')

    for x in lis :
        tmp = pq(x)
        sort_series_names(tmp('ul'))
        new.append(tmp)

    n = new('#wiki_numbers').parents('li:first')
    if n:
        n.remove()
        new.prepend(n)

    ul.replace_with(new)

    edit_wiki_page(page_name, q)

def sort_series_names(ul):
    links = list(ul('li a[href*="/wiki/series"]'))
    links.sort(key=lambda x: x.text.strip().lower()) 

    new = pq('<ul>')
    for a in links:
        li = pq('<li>')
        li.append(pq(a))
        new.append(li)

    ul.replace_with(new)

def get_fixed_section(q, author, names, link):
    res = q('#wiki_one_shots')
    if not res:
        for x name in names:
            res = q(':contains("%s")' %s name)
            if res: break
     
    if not res: 
        return False
    
    if is_header(res): 
        a = q('<a href="%s">%s</a>' % (link, res.text()))
        res.empty();
        res.append(a)
        return res
    elif res.is_('a'):
        p = res.parent()
        if not is_header(p):
            res.attr('href', link)
            h = pq('<h2>').append(res)
            res.replace_with(h)
    else:
        h = pq('<h2><a href=%s>%s</a></h2>' % (link, res.text()))
        res.replace_with(h)

    return True
    
def fix_page(author):
    q = query_wiki_page('authors/'+pagename)
    clean_dom(q)

    names = ['ONE SHOTS', 'one shots', 'One Shots', 'One shots'] 
    names += [ x.replace(' ', '-') for x in names ]

    one_shots_section = get_fixed_section(q, author, names, one_shots_link(author))

    names = ['Series', 'SERIES', 'series']
    
    series_section = get_fixed_section(q, author, names, series_section_link())

    series = q('a[href*="/wiki/series/"]')

    stories = q('a[href*="/r/%s//comments/"]')



def main():
    while True:
        try:
            check_submissions()
        except:
            log.exception("Unknown Error")

#sub = account.get_submission('http://www.reddit.com/r/HFYBeta/comments/2z7qy5/octhe_history_of_humans_1011/')
#sub1= account.get_submission('http://www.reddit.com/r/HFYBeta/comments/2yk6ef/test/')
#sub2= account.get_submission('http://www.reddit.com/r/HFYBeta/comments/2ygn5q/ocjenkinsverse_salvage_chapter_78_going_commando/')
sub3 = account.get_submission('http://www.reddit.com/r/HFYBeta/comments/320x4h/octhe_manp2the_restrained/')
sub4 = account.get_submission('http://www.reddit.com/r/HFYBeta/comments/320x2e/ocone_shotpretty_short_the_great_filter/')
#q = query_wiki_page('authors/other-guy')

#main()
