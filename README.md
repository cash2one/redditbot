This bot has been created to allow some fashion of tagging submitted stories.

It works by reading all comments on a defined subreddit looking for specifically formatted ones. If a comment starts with the word "tags:" it assumes that the rest of the words are tags.


Accepted tags can be found here /r/HFYBeta/wiki/tags/accepted. If the words following text "tags:" are within this list it proceeds to update a wiki page /r/HFYBeta/wiki/tags/tag-name with a link to the story on which the comment was found.

Only comments from volunteers, mods (and author of the current story) are taken into account the current list of volunteers can be found on /r/HFYBeta/wiki/tags/volunteers and is regularly updated by CodexKeeper - in this case /u/Lord_Fuzzy. 

So to tag a story with Pancakes, Fantasy, Comedy you would leave a comment:

    tags: Pancakes Fantasy Comedy        

In this case a link to the story will be added to /r/HFYBeta/wiki/tags/Pancakes and /r/HFYBeta/wiki/tags/Comedy /r/HFYBeta/wiki/tags/Fantasy.

If you happen to be the author or a mod you can also use syntax:

    tags: Pancakes -Fantasy Comedy        

to add the story to /r/HFYBeta/wiki/tags/Pancakes and /r/HFYBeta/wiki/tags/Comedy and remove it from /r/HFYBeta/wiki/tags/Fantasy.


If the story is archived you can still use the bot by sending it a private message. The message subject has to contain (only) a link to the story and the body of the message is the same as in the case of a comment.


If you are the author of a story and do not want it included by volunteers on the wiki tags you should send the bot a private message to tag it yourself replacing the word "tags:" on the beginning of the message body changed to "lock:" followed by a list of your tags.


If you are the mod and change the volunteer list or accepted tags list you can send the bot a message with subject "reload" to have it immediately update said lists. Bot will update itself but it will take some time.
