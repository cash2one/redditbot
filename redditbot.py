import os
import time
import praw
import re
import logging as log
from time import sleep
from itertools import groupby

#TODO:

# - a way to remove stories from tag pages
# - if submitter comments treat it as a final tagging
# - error messages when config is missing

log.basicConfig(level=log.DEBUG)

re_name = re.compile('\[([^]]*)\]')
re_perm = re.compile('\(([^]]*)\)')
re_user = re.compile('/u/([^\s]*)')
re_subreddit = re.compile('/r/([^/]*)')


class SortableLine:
    def __init__(self, msg):
        self.original = msg

        self.name = re_name.findall(msg)
        if not self.name: self.name = 'BAD entry format'
        else: self.name = self.name[0]

        self.permalink = re_perm.findall(msg)
        if not self.permalink: self.permalink= 'BAD entry format'
        else: self.permalink= self.permalink[0]

        self.sortby = self.name.lower()

def sort_wiki_page(page, tag, permalink):
    tmp = [ SortableLine(line) for line in page.split('\n') if line and not line.startswith('#') ]

    if tag.startswith('-'): tmp = [ x for x in tmp if x.permalink != permalink ]
           
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
        ret.append("* [%s](%s)\n" % (line.name, line.permalink))

    return "".join(ret)


class TagBot:
    def __init__(self, subreddit):
        self.subreddit = subreddit
        self.last_seen = 0
        
        self.account = praw.Reddit(user_agent='redditbot 0.1 by /u/HFY_tag_bot')
        self.account.login(os.environ['REDDIT_USER'], os.environ['REDDIT_PASS'])

        self.read_config()

    def read_config(self):
        self.tags = [ x.lower() for x in self.get_accepted_tags() ]
        self.volunteers = self.get_volunteers()
        self.mods = self.get_mods()
        self.codex_keeper = self.get_kodex_keeper().replace('/u/','').replace('/','')

    def get_kodex_keeper(self):
        return re_user.findall(self.get_wiki_page('volunteers').content_md)[0]

    def get_mods(self):
        self.sleep()
        return [x.name for x in self.account.get_subreddit(self.subreddit).get_moderators()]

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
        return comment.body.startswith('tags:') and comment.created > self.last_seen


    def sleep(self):
        sleep(5) 

    def update_wiki_page(self, comment):
        tmp = comment.body.replace(",", " ")
        tags = [ x.title() for x in tmp.split() if x.lower() in self.tags or '-%s'%x.lower() in self.tags]

        log.debug("found tags: %s" % ",".join(tags))

        for tag in tags:
            text = ""
            basetag = tag

            if tag.startswith('-'): basetag = tag[1:]

            try :
                text = self.get_wiki_page(basetag).content_md
            except:
                pass

            if tag.startswith('-'):
                self.edit_wiki_page(basetag, sort_wiki_page(text, tag))
            else:
                text += '* [%s](%s)\n' % (comment.submission.title, comment.submission.permalink)
                self.edit_wiki_page(tag, sort_wiki_page(text, tag))

        
        links = [ "[%s](/r/%s/wiki/tags/%s)" % (tag.title(), self.subreddit, tag.title()) for tag in tags if not tag.startswith('-')]
        if links: msg = "Verified tags: %s" % ", ".join(links)

        msg += '\n\n'

        removed = [tag.title for tag in tags if tag.startswith('-') ]
        if removed :msg += "Removed tags: %s" % ", ".join(removed)

        msg += '\n\nAccepted list of tags can be found here: /r/HFYBeta/wiki/tags/accepted'
        comment.reply(msg)


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

    def send_message(self, recipient, subject, message):
        self.sleep()
        try:
            return self.account.send_message(recipient, subject, message, raise_captcha_exception=True)
        except Exception, e:
            log.exception(e, 'Captcha exception?')

    def verify_user(self, comment):
        if comment.author.name not in self.volunteers + [comment.submission.author.name] + self.mods:
            log.debug("Unauthorized tagging attempt")
            comment.reply("You need to contact /u/%s  to be able to volunteer tags!" % self.codex_keeper)
            return False
        else:
            return True

    def get_submission(self, permalink):
        self.sleep()

        try:
            submission = self.account.get_submission(permalink)
            subreddit = re_subreddit.findall(permalink)

            if subreddit and subreddit[0] == self.subreddit:  return submission

            log.debug('got message with subject %s for bot configured on subreddit %s' % (permalink, self.subreddit))
        except Exception, e:
            log.exception(e, 'Not a submission?')

    def check_messages(self):
        self.sleep()
        messages = list(self.account.get_unread())

        log.debug('checking messages')

        for msg in messages:
            submission = self.get_submission(msg.subject)
            if not submission:
                msg.mark_as_read()
                log.debug('discarding')
                continue

            log.debug('message subject %s' % msg.subject)
            msg.submission = submission

            if msg.body.startswith('tags:'):
                self.update_wiki_page(msg)
                msg.mark_as_read()

            log.debug("discarding")
            msg.mark_as_read()
        
    def run(self):
        config_counter = 0

        while True:
            log.debug('waking up')
            self.last_seen = float(self.get_last_seen().content_md)
            comments = self.get_comments()

            try:
                for tag_comment in  [ x for x in comments if self.has_new_tags(x) ]:
                    log.debug('Processing comment %s' % tag_comment.permalink)
                    if self.verify_user(tag_comment): 
                        self.update_wiki_page(tag_comment)

                    if tag_comment.created > self.last_seen:
                        self.last_seen = tag_comment.created

                self.check_messages();
            finally:
                self.save_last_seen()

            log.debug('sleeping...')
            sleep(30)

            if config_counter == 5:
                self.read_config()
                conifg_counter = 0


def main():
    while True:
        try:
            TagBot('HFYBeta').run()
        except Exception, e:
            log.exception(e)
            sleep(120)

if __name__ == '__main__':
    main()        
