// ==UserScript==
// @name         My Fancy New Userscript
// @namespace    http://your.homepage/
// @version      0.1
// @description  enter something useful
// @author       You
// @include        http://www.reddit.com/r/hfy*
// @grant        none
// ==/UserScript==
//
//


/*================================================================================
 *  * @name: bPopup - if you can't get it up, use bPopup
 *  * @author: (c)Bjoern Klinggaard (twitter@bklinggaard)
 *  * @demo: http://dinbror.dk/bpopup
 *  * @version: 0.11.0.min
 * ================================================================================*/
 (function(c){c.fn.bPopup=function(A,E){function L(){a.contentContainer=c(a.contentContainer||b);switch(a.content){case "iframe":var d=c('<iframe class="b-iframe" '+a.iframeAttr+"></iframe>");d.appendTo(a.contentContainer);t=b.outerHeight(!0);u=b.outerWidth(!0);B();d.attr("src",a.loadUrl);l(a.loadCallback);break;case "image":B();c("<img />").load(function(){l(a.loadCallback);F(c(this))}).attr("src",a.loadUrl).hide().appendTo(a.contentContainer);break;default:B(),c('<div class="b-ajax-wrapper"></div>').load(a.loadUrl,a.loadData,function(d,b,e){l(a.loadCallback,b);F(c(this))}).hide().appendTo(a.contentContainer)}}function B(){a.modal&&c('<div class="b-modal '+e+'"></div>').css({backgroundColor:a.modalColor,position:"fixed",top:0,right:0,bottom:0,left:0,opacity:0,zIndex:a.zIndex+v}).appendTo(a.appendTo).fadeTo(a.speed,a.opacity);C();b.data("bPopup",a).data("id",e).css({left:"slideIn"==a.transition||"slideBack"==a.transition?"slideBack"==a.transition?f.scrollLeft()+w:-1*(x+u):m(!(!a.follow[0]&&n||g)),position:a.positionStyle||"absolute",top:"slideDown"==a.transition||"slideUp"==a.transition?"slideUp"==a.transition?f.scrollTop()+y:z+-1*t:p(!(!a.follow[1]&&q||g)),"z-index":a.zIndex+v+1}).each(function(){a.appending&&c(this).appendTo(a.appendTo)});G(!0)}function r(){a.modal&&c(".b-modal."+b.data("id")).fadeTo(a.speed,0,function(){c(this).remove()});a.scrollBar||c("html").css("overflow","auto");c(".b-modal."+e).unbind("click");f.unbind("keydown."+e);k.unbind("."+e).data("bPopup",0<k.data("bPopup")-1?k.data("bPopup")-1:null);b.undelegate(".bClose, ."+a.closeClass,"click."+e,r).data("bPopup",null);clearTimeout(H);G();return!1}function I(d){y=k.height();w=k.width();h=D();if(h.x||h.y)clearTimeout(J),J=setTimeout(function(){C();d=d||a.followSpeed;var e={};h.x&&(e.left=a.follow[0]?m(!0):"auto");h.y&&(e.top=a.follow[1]?p(!0):"auto");b.dequeue().each(function(){g?c(this).css({left:x,top:z}):c(this).animate(e,d,a.followEasing)})},50)}function F(d){var c=d.width(),e=d.height(),f={};a.contentContainer.css({height:e,width:c});e>=b.height()&&(f.height=b.height());c>=b.width()&&(f.width=b.width());t=b.outerHeight(!0);u=b.outerWidth(!0);C();a.contentContainer.css({height:"auto",width:"auto"});f.left=m(!(!a.follow[0]&&n||g));f.top=p(!(!a.follow[1]&&q||g));b.animate(f,250,function(){d.show();h=D()})}function M(){k.data("bPopup",v);b.delegate(".bClose, ."+a.closeClass,"click."+e,r);a.modalClose&&c(".b-modal."+e).css("cursor","pointer").bind("click",r);N||!a.follow[0]&&!a.follow[1]||k.bind("scroll."+e,function(){if(h.x||h.y){var d={};h.x&&(d.left=a.follow[0]?m(!g):"auto");h.y&&(d.top=a.follow[1]?p(!g):"auto");b.dequeue().animate(d,a.followSpeed,a.followEasing)}}).bind("resize."+e,function(){I()});a.escClose&&f.bind("keydown."+e,function(a){27==a.which&&r()})}function G(d){function c(e){b.css({display:"block",opacity:1}).animate(e,a.speed,a.easing,function(){K(d)})}switch(d?a.transition:a.transitionClose||a.transition){case "slideIn":c({left:d?m(!(!a.follow[0]&&n||g)):f.scrollLeft()-(u||b.outerWidth(!0))-200});break;case "slideBack":c({left:d?m(!(!a.follow[0]&&n||g)):f.scrollLeft()+w+200});break;case "slideDown":c({top:d?p(!(!a.follow[1]&&q||g)):f.scrollTop()-(t||b.outerHeight(!0))-200});break;case "slideUp":c({top:d?p(!(!a.follow[1]&&q||g)):f.scrollTop()+y+200});break;default:b.stop().fadeTo(a.speed,d?1:0,function(){K(d)})}}function K(d){d?(M(),l(E),a.autoClose&&(H=setTimeout(r,a.autoClose))):(b.hide(),l(a.onClose),a.loadUrl&&(a.contentContainer.empty(),b.css({height:"auto",width:"auto"})))}function m(a){return a?x+f.scrollLeft():x}function p(a){return a?z+f.scrollTop():z}function l(a,e){c.isFunction(a)&&a.call(b,e)}function C(){z=q?a.position[1]:Math.max(0,(y-b.outerHeight(!0))/2-a.amsl);x=n?a.position[0]:(w-b.outerWidth(!0))/2;h=D()}function D(){return{x:w>b.outerWidth(!0),y:y>b.outerHeight(!0)}}c.isFunction(A)&&(E=A,A=null);var a=c.extend({},c.fn.bPopup.defaults,A);a.scrollBar||c("html").css("overflow","hidden");var b=this,f=c(document),k=c(window),y=k.height(),w=k.width(),N=/OS 6(_\d)+/i.test(navigator.userAgent),v=0,e,h,q,n,g,z,x,t,u,J,H;b.close=function(){r()};b.reposition=function(a){I(a)};return b.each(function(){c(this).data("bPopup")||(l(a.onOpen),v=(k.data("bPopup")||0)+1,e="__b-popup"+v+"__",q="auto"!==a.position[1],n="auto"!==a.position[0],g="fixed"===a.positionStyle,t=b.outerHeight(!0),u=b.outerWidth(!0),a.loadUrl?L():B())})};c.fn.bPopup.defaults={amsl:50,appending:!0,appendTo:"body",autoClose:!1,closeClass:"b-close",content:"ajax",contentContainer:!1,easing:"swing",escClose:!0,follow:[!0,!0],followEasing:"swing",followSpeed:500,iframeAttr:'scrolling="no" frameborder="0"',loadCallback:!1,loadData:!1,loadUrl:!1,modal:!0,modalClose:!0,modalColor:"#000",onClose:!1,onOpen:!1,opacity:.7,position:["auto","auto"],positionStyle:"absolute",scrollBar:!0,speed:250,transition:"fadeIn",transitionClose:!1,zIndex:9997}})(jQuery);

;(function (ns, undefined) {
    var tags = [];
	var modhash = "";

    function add_global_style(css) {
        var head, style;
        head = document.getElementsByTagName('head')[0];
        if (!head) { return; }
        style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = css;
        head.appendChild(style);
    }

    function send_pm() {
        var checked = $('ul.tag-list :checked').map(function() { return $(this).val() }).toArray();

        $.post('http://www.reddit.com/api/compose', 
               {
                    api_type: 'json',
                    subject: document.URL,
					uh : modhash,
					text: "tags: " + checked.join(' '),
					to: 'hfy_tag_bot',
               }, 
               function(response) {
                    console.log(response);
					$('#tag-popup').bPopup().close();
               }, 
               'json');

    };

    function leave_comment() {
        var checked = $('ul.tag-list :checked').map(function() { return $(this).val() }).toArray();

        $.post('http://www.reddit.com/api/comment', 
               {
                    api_type: 'json',
                    text: "tags: " + checked.join(' '),
					uh : modhash,
                    thing_id: $('.self').data().fullname
               }, 
               function(response) {
                    console.log(response);
					$('#tag-popup').bPopup().close();
               }, 
               'json');

    };


    function show_popup() {
        var ul = $('<ul class="tag-list">');
        for(var i=0;i<tags.length;i++) {
            ul.append($('<li><input class="tagbox" type="checkbox" value="'+tags[i].name+'"><span class="tag">'+tags[i].name+'</span></input><span>'+tags[i].desc+'</span></li>'));
        }
        var div = $('<div class="tag-list" id="tag-popup">')

        div.append(ul);
        
        var top = Math.max(0, (($(window).height() - $(div).outerHeight()) / 2) + $(window).scrollTop());

        top -= 250;
        left = 200;

        var pm = $('<input type="button" value="Send PM"></input>');
        pm.click(send_pm);

        var msg = $('<input type="button" value="Leave comment"></input>');
        msg.click(leave_comment);

        div.append(pm);
        div.append(msg);

        div.bPopup({follow: [false, false], transition: 'slideDown', position: [left, top]});
    }

    function get_accepted_tags() {
		if (tags.length > 0) {
			show_popup();
			return;
		}
        $.getJSON('http://www.reddit.com/r/hfy/wiki/tags/accepted.json', function(data) { 
            console.log(data); 
            var tmp = data.data.content_md.split('\n');
            for(var i=0; i < tmp.length; i++) {
                var s = tmp[i];
                if(s.indexOf('*') != 0) continue;
                var b = s.indexOf('[');
                var e = s.indexOf(']');
                var c = s.lastIndexOf(')');

                tags.push({name: s.substring(b+1,e), desc: s.substring(c+1)});

            }
			show_popup();
        });
    };


    ns.init = function() {
        add_global_style('div.tag-list { padding: 10px; background: white; -moz-border-radius: 10px; -webkit-border-radius: 10px;border-radius: 10px;}');
        add_global_style('div.tag-list input[type="button"] { margin: 8px;}');
        add_global_style('span.tag { color: #c53716; font-size: 14px; font-weight: bold}');


	    var a = $('<li style="cursor: pointer; cursor: hand"><a>tag</a></li>');
	    $('#siteTable ul.flat-list').append(a);
	    a.click(function() {
			get_accepted_tags();
	    });

        $.getJSON('http://www.reddit.com/api/me.json', function(data) { 
				console.log(data);
				modhash = data.data.modhash;
            }
        );


    };

})(window.taglib = window.taglib || {});


$(document).ready(function() {
    if(!reddit.logged) return;

    taglib.init();
});

// https://www.uploady.com/download/XPAzjUaxeuZ/Dl~awcKgqzzj5vj1
// https://www.uploady.com/download/DKNkpd9Mav8/8bekhYjGjhH6461r
