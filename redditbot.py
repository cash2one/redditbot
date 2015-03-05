import os
import time
import praw
import re
import logging as log
from time import sleep
from itertools import groupby

log.basicConfig(level=log.DEBUG)

re_name = re.compile('\[([^]]*)\]')
re_perm = re.compile('\(([^]]*)\)')
re_user = re.compile('/u/([^\s]*)')

class SortableLine:
    def __init__(self, msg):
        self.original = msg

        self.name = re_name.findall(msg)
        if not self.name: self.name = 'BAD entry format'
        else: self.name = self.name[0]

        self.permlink = re_perm.findall(msg)
        if not self.permlink: self.permlink= 'BAD entry format'
        else: self.permlink= self.permlink[0]

        self.sortby = self.name.lower()

def sort_wiki_page(page, tag):
    tmp = [ SortableLine(line) for line in page.split('\n') if line and not line.startswith('#') ]
           
    keys = []
    groups = []

    for k, g in groupby(tmp, lambda x: x.sortby):
        keys.append(k)
        groups.append(list(g))

    # first element of every group should hold correctly capitalized title
    
    lines = [x[0] for x in sorted(groups, key=lambda x: x[0].sortby)]
    return  format_for_wiki(lines, tag)

#works on already sorted SortableLines
def format_for_wiki(lines, tag):
    anchor = None
    ret = []
    ret.append('#%s' % tag)
    ret.append('\n\n')

    # add anchors based on first letter of the name
    for line in lines:
        if line.name[0].lower() != anchor:
            anchor = line.name[0].lower()
            ret.append('\n\n')
            ret.append('##%s' % anchor.upper())
            ret.append('\n\n')
        ret.append("* [%s](%s)\n" % (line.name, line.permlink))

    return "".join(ret)



class TagBot:
    def __init__(self, subreddit):
        self.subreddit = subreddit
        self.last_seen = 0
        
        self.account = praw.Reddit(user_agent='redditbot 0.1 by /u/HFY_tag_bot')
        self.account.login(os.environ['REDDIT_USER'], os.environ['REDDIT_PASS'])

        self.tags = self.get_accepted_tags()
        self.volunteers = self.get_volunteers()

    def get_volunteers(self):
        return re_user.findall(self.get_wiki_page('volunteers').content_md)

    
    def get_accepted_tags(self):
        return re_name.findall(self.get_wiki_page('accepted').content_md)


    def sort_wiki_page(page):
        tmp = [ SortableLine(line) for line in page.split('\n') if line ]

        keys = []
        groups = []

        for k, g in groupby(tmp, lambda x: x.lower):
            keys.append(k)
            groups.append(list(g))

        # first element of every group should hold correctly capitalized title
        return "".join(["%s\n" % x[0].original for x in groups])
             
    def has_tagging_permissions(self, user):
        pass

    def has_new_tags(self, comment):
        return comment.body.startswith('test:') and comment.created > self.last_seen


    def sleep(self):
        sleep(5) 

    def update_wiki_page(self, comment):
        tags = [ x for x in comment.body.split() if x in self.tags ]

        log.debug("found tags: %s" % ",".join(tags))

        for tag in tags:
            text = ""

            try :
                text = self.get_wiki_page(tag).content_md
            except:
                pass

            text += '* [%s](%s)\n' % (comment.submission.title, comment.submission.permalink)
            self.edit_wiki_page(tag, sort_wiki_page(text, tag))

        
        links = [ "[%s](/r/%s/wiki/tags/%s)" % (tag, self.subreddit, tag) for tag in tags ]
        msg = "Verified tags: %s" % ", ".join(links)
        msg += '/n/nAccepted list of tags can be found here: /r/HFYBeta/wiki/tags/accepted'
        comment.reply(msg)

        self.last_seen = comment.created

    def edit_wiki_page(self, tag, text):
        log.debug('updating wiki page %s' % (self.subreddit + '/tags/'+tag,))
        return self.account.edit_wiki_page(self.subreddit, 'tags/'+tag, text)

    def get_comments(self):
        self.sleep()
        return self.account.get_comments(self.subreddit, limit=50)

    def get_wiki_page(self, tag):
        self.sleep()
        return self.account.get_wiki_page(self.subreddit, 'tags/'+tag)

    def save_last_seen(self):
        self.sleep()
        return self.account.edit_wiki_page(self.subreddit, 'tags/last_seen', self.last_seen)

    def get_last_seen(self):
        self.sleep()
        return self.account.get_wiki_page(self.subreddit, 'tags/last_seen')
        
    def run(self):

        while True:
            self.last_seen = float(self.get_last_seen().content_md)
            comments = self.get_comments()

            try:
                for tag_comment in  [ x for x in comments if self.has_new_tags(x) ]:
                    log.debug('Processing comment %s' % x.permalink)
                    self.update_wiki_page(tag_comment)
            finally:
                self.save_last_seen()

            sleep(30)


def main():
        TagBot('HFYBeta').run()

def test1():
    test = """* [Test Imgur Link](http://www.reddit.com/r/HFYBeta/comments/2gaib5/test_imgur_link/)
    * [Text](http://www.reddit.com/r/HFYBeta/comments/2j10eo/text/)
    * [Welcome to HFYBeta](http://www.reddit.com/r/HFYBeta/comments/2my43g/welcome_to_hfybeta/)
    * [Test](http://www.reddit.com/r/HFYBeta/comments/2xxjwh/test/)
    * [test](http://www.reddit.com/r/HFYBeta/comments/2xxjwh/test/)
    * [Abd](http://www.reddit.com/r/HFYBeta/comments/2xxjwh/test/)
    * [tesT](http://www.reddit.com/r/HFYBeta/comments/2xxjwh/test/)
    * [Abc](http://www.reddit.com/r/HFYBeta/comments/2xxjwh/test/)
    """

    print sort_wiki_page(test)


if __name__ == '__main__':
    main()        
