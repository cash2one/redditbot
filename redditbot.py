import os
import time
import praw
import re
import logging as log
from time import sleep
from itertools import groupby

#TODO:

# - error messages when config is missing

log.basicConfig(level=log.DEBUG)

re_user = re.compile('/u/([^\s]*)')
re_subreddit = re.compile('/r/([^/]*)')
re_lock = re.compile('\* ([^\s]*)')
re_name = re.compile('\[(.*)\]')
re_perm = re.compile('\(([^]]*)\)')
re_title = re.compile('](.*)')

class SortableLine:
    def __init__(self, msg):
        self.original = msg

        import ipdb
        ipdb.set_trace()


        self.name = re.findall(re_name, msg)
        if not self.name: 
            self.name = 'BAD entry format'
        else: 
            if self.name[0].startswith('['): self.name = re.findall(re_title, self.name[0])
            self.name = self.name[0].strip()

        self.permalink = re_perm.findall(msg)
        if not self.permalink: self.permalink= 'BAD entry format'
        else: self.permalink= self.permalink[-1]

        self.sortby = self.name.lower()

def sort_wiki_page(page, tag, permalink=None):
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

def strip_title(title):
    i = title.rfind(']') + 1
    return title[i:].strip()

#works on already sorted SortableLines
def format_for_wiki(lines, tag):
    anchor = None
    if tag.startswith('-'): tag = tag[1:]
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
        self.codex_keeper = self.get_codex_keeper().replace('/u/','').replace('/','')
        self.read_locked()

    def get_codex_keeper(self):
        return re_user.findall(self.get_wiki_page('codexkeeper').content_md)[0]

    def get_mods(self):
        self.sleep()
        return [x.name for x in self.account.get_subreddit(self.subreddit).get_moderators()]

    def get_volunteers(self):
        return re_user.findall(self.get_wiki_page('volunteers').content_md)
    
    def get_accepted_tags(self):
        return re_name.findall(self.get_wiki_page('accepted').content_md)

    def has_new_tags(self, comment):
        return comment.body.startswith('tags:') \
               and comment.created > self.last_seen \
               and not comment.edited


    def sleep(self):
        sleep(5) 

    def update_wiki_page(self, comment):
        if comment.submission.url in self.locked:
            comment.reply("This submission is no longer accepting tags")
            return
        reply = ''
        tmp = comment.body.replace(",", " ")
        added = [ x.title() for x in tmp.split() if x.lower() in self.tags ]
        removed = [ x.title() for x in tmp.split() if  x.startswith('-') and re.sub(r'^-','',x).lower() in self.tags ]

        log.debug("found tags: %s" % ",".join(added + removed))

        if comment.author.name != comment.submission.author.name and comment.author.name not in self.mods:
            removed = []
            reply += 'Only the submitter or one of the mods can remove tags! sorry!\n\n'


        for tag in added + removed:
            text = ""
            basetag = tag

            if tag.startswith('-'): basetag = tag[1:]

            text = self.get_wiki_page(basetag).content_md

            if tag.startswith('-'):
                self.edit_wiki_page(basetag, sort_wiki_page(text, tag, comment.submission.permalink))
            else:
                text += '* [%s](%s)\n' % (comment.submission.title, comment.submission.permalink)
                self.edit_wiki_page(tag, sort_wiki_page(text, tag))

        
        links = [ "[%s](/r/%s/wiki/tags/%s)" % (tag.title(), self.subreddit, tag.title()) for tag in added]
        if links: reply = "Verified tags: %s" % ", ".join(links)

        reply += '\n\n'

        if removed: reply += "Removed tags: %s" % ", ".join(removed)

        reply += '\n\nAccepted list of tags can be found here: /r/HFYBeta/wiki/tags/accepted'
        comment.reply(reply)


    def edit_wiki_page(self, tag, text):
        log.debug('updating wiki page %s' % (self.subreddit + '/tags/'+tag,))
        return self.account.edit_wiki_page(self.subreddit, 'tags/'+tag, text)

    def get_comments(self):
        return self.account.get_comments(self.subreddit, limit=50)

    def get_wiki_page(self, tag):
        self.sleep()
        try:
            return self.account.get_wiki_page(self.subreddit, 'tags/'+tag)
        except:
            log.exception('No such page?')

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
            log.exception('Captcha exception?')

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
            log.exception('Not a submission?')

    def check_messages(self):
        self.sleep()
        messages = list(self.account.get_unread())

        log.debug('checking messages')

        for msg in messages:
            if msg.subject == 'reload':
                self.read_config()
                msg.reply("Settings have been reloaded")
                msg.mark_as_read()
                continue

            submission = self.get_submission(msg.subject)
            log.debug('checking %s' % msg.subject)
            if not submission:
                msg.mark_as_read()
                log.debug('discarding')
                continue

            log.debug('message subject %s' % msg.subject)
            msg.submission = submission

            if msg.body.startswith('tags:'):
                self.update_wiki_page(msg)
                msg.mark_as_read()

            if msg.body.startswith('lock:'):
                if msg.author.name != submission.author.name and msg.author.name not in self.mods:
                    msg.mark_as_read()
                    msg.reply('Only author or mod can lock a thread')

                else:
                    content = ''
                    locked = self.get_wiki_page('locked')
                    if locked: content = locked.content_md

                    content += '* %s' % submission.url
                    content += '\n\n'

                    content = content.split('* ')
                    content = ''.join(["* %s" % x for x in sorted(set(content)) if x])
                    
                    self.update_wiki_page(msg)
                    self.edit_wiki_page('locked', content)
                    msg.mark_as_read()
                    msg.reply("The submission tags can no longer be changed by volunteers")


            log.debug("discarding")
            msg.mark_as_read()

    def read_locked(self):
        locked = self.get_wiki_page('locked')
        self.locked = re.findall(re_lock, locked.content_md)
        
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
            sleep(140)

if __name__ == '__main__':
    main()        
