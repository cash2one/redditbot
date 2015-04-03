import os
import time
import praw
import re
import logging as log
from HTMLParser import HTMLParser
from time import sleep


#TODO:

# - error messages when config is missing

log.basicConfig(level=log.DEBUG)

re_user = re.compile('/u/([^\s]*)')
re_subreddit = re.compile('/r/([^/]*)')
re_locked = re.compile('\* ([^\s]*)')
re_list = re.compile('\* [^\n]*')
re_name = re.compile('\[(.*)\]')
re_title = re.compile('(\[|\()(oc|pi|jenkinsverse|j-verse|jverse|misc|nsfw)(\]|\))', re.IGNORECASE)
re_command = re.compile('\[(tags|lock)\]', re.IGNORECASE)
re_perm = re.compile('\((http[^)]*)\)')


class UnableToEditWikiError(Exception): pass
class DummyAuthor:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

# expected format is: "* [title](link) - by: [author](link-to-authors-wiki)"
class SortableLine:
    def __init__(self, line):
        self.title_md = re_title.sub('', line).strip() + '\n\n'

        try:
            self.name = re.findall(re_name, line)
            self.name = re_title.sub('', self.name[0]).strip()

            self.permalink = re_perm.findall(line)
            self.permalink= self.permalink[0]

            self.sortby = self.name.lower()
        except Exception, e:
            log.exception('Incorrect format!')
            self.sortby = line.lower()
            self.name = line

    def __eq__(self, other):
        return self.permalink == other.permalink

    def __hash__(self):
        return hash(self.permalink)


def sort_titles(titles):
    hp = HTMLParser()
    alpha = [x for x in sorted(set(titles), key=lambda x: x.sortby) if x.sortby[0].isalpha() ]
    digit = [x for x in sorted(set(titles), key=lambda x: x.sortby) if x.sortby[0].isdigit() ]
    other = [x for x in sorted(set(titles), key=lambda x: x.sortby) if not x.sortby[0].isdigit() and not x.sortby[0].isalpha() ]


    return digit + other + alpha

def get_anchor(string):
    first = string[0]

    if first.isalpha():
        return first.lower()

    if first.isdigit():
        return 'numbers'

    return 'others'

def format_wiki_page(lines, tag):
    anchor = None
    if tag.startswith('-'): tag = tag[1:]
    ret = []
    ret.append('#%s' % tag)
    ret.append('\n\n')


    hp = HTMLParser()
    # add anchors based on first letter of the name
    for line in lines:
        if get_anchor(line.sortby) != anchor:
            anchor = get_anchor(line.sortby)
            ret.append('\n\n')
            ret.append('##%s' % anchor.upper())
            ret.append('\n\n')
        ret.append(hp.unescape(line.title_md))

    return "".join(ret)

class TagBot:
    def __init__(self, subreddit):
        self.subreddit = subreddit
        self.last_seen = 0
        
        self._account = praw.Reddit(user_agent='redditbot 0.1 by /u/HFY_tag_bot')
        self._account.login(os.environ['REDDIT_USER'], os.environ['REDDIT_PASS'])

        self.wiki_modification_time = {}

        self.read_config()

    def account(self, sleep_time=3):
        sleep(sleep_time)
        return self._account

    def read_config(self):
        while True:
            try:
                self.tags = [ x.lower() for x in self.get_accepted_tags() ]

                for t in self.tags:
                    if t not in self.wiki_modification_time: self.wiki_modification_time[t] = 0

                self.volunteers = self.get_volunteers()
                self.mods = self.get_mods()
                self.codex_keeper = self.get_codex_keeper().replace('/u/','').replace('/','')
                self.read_locked()
                return
            except Exception, e:
                log.exception("Unable to read config file! retrying in 30s")
                sleep(15) 

    def get_codex_keeper(self):
        return re_user.findall(self.get_wiki_page('codexkeeper').content_md)[0]

    def get_mods(self):
        return [x.name for x in self.account().get_subreddit(self.subreddit).get_moderators()]

    def get_volunteers(self):
        return re_user.findall(self.get_wiki_page('volunteers').content_md)
    
    def get_accepted_tags(self):
        return re_name.findall(self.get_wiki_page('accepted').content_md)

    def has_new_tags(self, comment):
        return comment.body.lower().startswith('tags:') and not comment.edited

    def update_wiki_page(self, comment):
        reply = ''

        if comment.submission.url in self.locked:
            comment.reply("This submission is no longer accepting tags")
            return

        tmp = comment.body.replace(",", " ")
        tmp = re_command.sub('', tmp)
        added = [ x.title() for x in tmp.split() if x.lower() in self.tags ]
        removed = [ x[1:].title() for x in tmp.split() if  x.startswith('-') and re.sub(r'^-','',x).lower() in self.tags ]

        log.debug("found tags: %s" % ",".join(added + removed))

        if not comment.author: comment.author = DummyAuthor('deleted')
        if not comment.submission.author: comment.submission.author = DummyAuthor('deleted')

        if comment.author.name != comment.submission.author.name and comment.author.name not in self.mods:
            removed = []
            reply += 'Only the submitter or one of the mods can remove tags! sorry!\n\n'

        for tag in added + removed:
            page = self.get_wiki_page(tag)
            self.wiki_modification_time[tag] = page.revision_date
            
            lines = [ SortableLine(line) for line in re.findall(re_list, page.content_md) ]
            if tag not in removed:
                lines += [ SortableLine('* [%s](%s) - by: [%s](/r/%s/wiki/authors/%s)\n\n' % (comment.submission.title, 
                                                                                              comment.submission.permalink, 
                                                                                              comment.submission.author.name, 
                                                                                              self.subreddit,
                                                                                              comment.submission.author.name)) ]
            else:
                lines = [ x for x in lines if x.permalink != comment.submission.permalink ]

            log.debug("updating %s [removing?: %s] for %s" % (tag, tag in removed, comment.submission.title))
            md = format_wiki_page(sort_titles(lines), tag)

            if md != page.content_md:
                self.edit_wiki_page(tag, md)

        
        links = [ "[%s](/r/%s/wiki/tags/%s)" % (tag.title(), self.subreddit, tag.title()) for tag in added]
        if links: reply = "Verified tags: %s" % ", ".join(links)

        reply += '\n\n'

        if removed: reply += "Removed tags: %s" % ", ".join(removed)

        reply += '\n\nAccepted list of tags can be found here: /r/%s/wiki/tags/accepted' % self.subreddit
        comment.reply(reply)


    # TODO: keeping times in class member seems idiotic i don't know why not just pass it as a parameter
    #       probably have to change that
    def edit_wiki_page(self, tag, text):
        log.debug('updating wiki page %s' % (self.subreddit + '/tags/'+tag,))
        if tag not in self.wiki_modification_time: self.wiki_modification_time[tag] = 0

        log.debug('wiki mod time before edit: %s' % self.wiki_modification_time[tag])

        self.account().edit_wiki_page(self.subreddit, 'tags/'+tag, text)

        # praw is caching wiki or something so we have to be sure that next call
        # to get_wiki_page will actually return the right result
        for i in range(10):
            page = self.account().get_wiki_page(self.subreddit, 'tags/'+tag)
            log.debug('wiki mod time: %s' % page.revision_date)
            if self.wiki_modification_time[tag] < page.revision_date: break
            sleep(2)
        else:
            raise UnableToEditWikiError('Unable to confirm wiki edit. sorry :(')


    def get_comments(self, limit=1000):
        return self.account().get_comments(self.subreddit, limit=limit)

    def get_wiki_page(self, tag):
        try:
            return self.account().get_wiki_page(self.subreddit, 'tags/'+tag)
        except:
            log.exception('No such page?')

    def save_last_seen_comment(self):
        return self.account().edit_wiki_page(self.subreddit, 'tags/last_seen', self.last_seen)

    def get_last_seen(self):
        return self.account().get_wiki_page(self.subreddit, 'tags/last_seen')

    def send_message(self, recipient, subject, message):
        try:
            return self.account().send_message(recipient, subject, message, raise_captcha_exception=True)
        except Exception, e:
            log.exception('Captcha exception?')

    def verify_user(self, comment):
        if not comment.author: comment.author = DummyAuthor('deleted')
        if not comment.submission.author: comment.submission.author = DummyAuthor('deleted')

        if comment.author.name not in self.volunteers + [comment.submission.author.name] + self.mods:
            log.debug("Unauthorized tagging attempt")
            comment.reply("You need to contact /u/%s  to be able to volunteer tags!" % self.codex_keeper)
            return False
        else:
            return True

    def get_submission(self, msg):

        try:
            submission = self.account().get_submission(msg.subject)
            subreddit = re_subreddit.findall(submission.permalink)

            if subreddit and subreddit[0].lower() == self.subreddit.lower():  return submission

            log.debug('got message with subject %s for bot configured on subreddit %s' % (msg.subject, self.subreddit))
            msg.reply("I'can only work on %s this is a submission to %s" % (self.subreddit, subreddit))
        except Exception, e:
            log.exception('Not a submission?')
            msg.reply("I'm sorry i can't seem to get submission from url: %s\n\nYou will have to try again :(\n\n(Error: %s)" % (msg.subject, e.message))
            msg.mark_as_read()

    def check_comments(self):
        log.debug('checking comments')

        comments = self.get_comments()

        for tag_comment in comments:
            try:
                if tag_comment.created <= self.last_seen:
                    break

                if not self.has_new_tags(tag_comment): continue

                log.debug('Processing comment %s' % tag_comment.permalink)
                if self.verify_user(tag_comment): 
                    self.update_wiki_page(tag_comment)
            except Exception, e:
                log.exception("Error processing a comment")
                tag_comment.reply("There was an error processing your comment :( sorry. [%s]" % e.message)
            finally:
                if tag_comment.created > self.new_last_seen:
                    self.new_last_seen = tag_comment.created
     
        self.last_seen = self.new_last_seen
            

    def check_messages(self):
        log.debug('checking messages')

        messages = list(self.account().get_unread())

        for msg in messages:
            try:
                if msg.was_comment: continue

                if msg.subject == 'reload':
                    self.reload_config(msg)

                submission = self.get_submission(msg)
                if not submission: continue # unable to get submision from subject

                # set submission in order to treat PM and comment with the same functions
                msg.submission = submission

                log.debug('Processing message %s' % msg.subject)
                if msg.body.lower().startswith('tags:'):
                    self.update_wiki_page(msg)

                if msg.body.lower().startswith('lock:'):
                    self.lock_wiki_page(msg, submission)

            except Exception, e:
                log.exception('Error processing message')
                msg.reply("There was an error processing your message :( sorry. [%s]" % e.message)
            finally:
                log.debug("marking as read")
                msg.mark_as_read()

    def reload_config(self, msg):
        if  msg.author.name not in self.mods:
            msg.mark_as_read()
            msg.reply("Nice try, but you're not a mod ;)")

        self.read_config()
        msg.reply("Settings have been reloaded")
        msg.mark_as_read()

    def lock_wiki_page(self, msg, submission):
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
            msg.reply("The submission tags can no longer be tagged")

    def read_locked(self):
        locked = self.get_wiki_page('locked')
        self.locked = re.findall(re_locked, locked.content_md)

    def update_global_tags(self):
        tags = self.get_accepted_tags()
        story_tags = {}
        lines = {}

        for tag in tags:
            page = self.get_wiki_page(tag)

            for line in [ SortableLine(line) for line in re.findall(re_list, page.content_md) ]:
                if not line.permalink: continue
                if line.permalink not in story_tags: story_tags[line.permalink] = []
                story_tags[line.permalink] += [tag]

                if line.permalink not in lines: 
                    lines[line.permalink] = line

        for permalink, tags in story_tags.iteritems():
            taglinks = ' '.join(["[#%s](%s)" % (tag, '/r/'+self.subreddit+'/wiki/tags/'+tag) for tag in tags])
            lines[permalink].title_md = lines[permalink].title_md.rstrip() + " " + taglinks + '\n\n'

        md = format_wiki_page(sort_titles(lines.values()), 'All')

        self.edit_wiki_page('all', md)
            
    def run(self):
        config_counter = 0
        all_counter = 0

        while True:
            log.debug('waking up')
            self.last_seen = float(self.get_last_seen().content_md)
            self.new_last_seen = self.last_seen

            self.check_comments()
            self.check_messages();
            self.save_last_seen_comment()

            log.debug('sleeping...')
            sleep(15)

            if config_counter == 5:
                self.read_config()
                config_counter = 0

            if all_counter == 10:
                self.update_global_tags()
                all_counter = 0


            config_counter +=1
            all_counter += 1
def main():
    tagbot = TagBot(os.environ['REDDIT_SUBR'])
    while True:
        try:
           tagbot.run()
        except Exception, e:
            log.exception(e)
            sleep(140)

if __name__ == '__main__':
    main()        
