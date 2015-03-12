window.get_accepted_tags = (function() {
    return { 
        tags = [],
        get_accepted_tags: function() {
            $.getJSON('http://www.reddit.com/r/hfy/wiki/tags/accepted.json', function(data) { console.log(data); });
            var tmp = data.content_md.split('\n');
            for(var i=0; i < this.tags.length) {
                var s = tags[i];
                if(s.indexOf('*') != 0) continue;
            }
        }
    }
})();
