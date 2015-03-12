// ==UserScript==
// @name         My Fancy New Userscript
// @namespace    http://your.homepage/
// @version      0.1
// @description  enter something useful
// @author       You
// @include        http://www.reddit.com/r/hfy/*
// @grant        none
// ==/UserScript==

window.dupa = (function() {
    return { 
        tags : [],
        get_accepted_tags: function() {
            tags = this.tags;
            $.getJSON('http://www.reddit.com/r/hfy/wiki/tags/accepted.json', function(data) { 
                console.log(data); 
                var tmp = data.data.content_md.split('\n');
                for(var i=0; i < tmp.length; i++) {
                    var s = tmp[i];
                    if(s.indexOf('*') != 0) continue;
                    var b = s.indexOf('[');
                    var e = s.indexOf(']');
                    tags.push(s.substring(b+1,e));
                }
                console.log(tags);
                var a = $('<li style="cursor: pointer; cursor: hand"><a>tag</a></li>');
                
                $('#siteTable ul.flat-list').append(a);
                a.click(function() {
                    alert(tags);
                });
            });
            
        }
    }
})();

