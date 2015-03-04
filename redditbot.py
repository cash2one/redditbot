import os
import time
import praw
import logging as log
from time import sleep



class TagBot:
    def __init__(self, subreddit, tags):
        self.subreddit = subreddit
        self.tags = tags
        self.last_seen = 0
        
        self.account = praw.Reddit(user_agent='redditbot 0.1 by /u/HFY_tag_bot')
        self.account.login(os.environ['REDDIT_USER'], os.environ['REDDIT_PASS'])

    def has_new_tags(self, comment):
        return comment.body.startswith('tags:') and comment.created > self.last_seen


    def sleep(self):
        sleep(5) 

    def update_wiki_page(self, comment):
        tags = [ x for x in comment.body.split() if x in self.tags ]

        print "found tags: %s" % ",".join(tags)

        for tag in tags:
            text = ""

            try :
                text = self.get_wiki_page(tag).content_md
            except:
                pass

            text += '* [%s](%s)\n' % (comment.submission.title, comment.submission.permalink)
            self.edit_wiki_page(tag, text)

        
        links = [ "[%s](/r/%s/wiki/tags/%s)" % (tag, self.subreddit, tag) for tag in tags ]
        comment.reply("Verified tags: %s" % ",".join(links))

        self.last_seen = comment.created

    def edit_wiki_page(self, tag, text):
        print 'updating wiki page %s' % (self.subreddit + '/tags/'+tag,)
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
                    print 'Processing comment %s' % x.permalink
                    self.update_wiki_page(tag_comment)
            finally:
                self.save_last_seen()

            sleep(30)


def main():
        subreddit = 'HFYBeta'
        tags = ['Comedy','Serious','Fantasy','Invasion','Humanitarianism','TechnologicalSupremacy',
                     'Pancakes','Biology','DeathWorlds','LectureOrReport','CultureShock','Military','Altercation',
                     'Horror','ComeBack','Feels','Politics','Legacy','Completed','Hiatus']

        TagBot(subreddit, tags).run()


if __name__ == '__main__':
    main()
            
