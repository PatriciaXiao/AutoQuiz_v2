/*
 * Common functions for any llab page
 *
 * CANNOT RELY ON JQUERY OR ANY OTHER LLAB LIBRARY
 */


// retrieve llab or create an empty version.
llab = llab || {};
llab.loaded = llab.loaded || {};



//These are STRINGS that are selectors of classes of container page elements.
//We want to store them in a single place because it's easier to update, but might
llab.selectors = {};
llab.selectors.FULL = ".llab-full";                  // the whole page and nuthing but the page
llab.selectors.NAVSELECT = ".llab-nav";              // container for the navigation pulldown
llab.selectors.PROGRESS = ".llab-full-bottom-bar";   // that bottom progress bar




// returns the current domain with a cors proxy if needed

llab.getSnapRunURL = function(targeturl) {
    if (!targeturl) { return ''; }

    if (targeturl.indexOf('http') == 0 || targeturl.indexOf('//') == 0) {
        // pointing to some non-local resource...  do nothing!!
        return targeturl;
    }

    // internal resource!
    var finalurl = llab.snapRunURLBase;
    var currdom = document.domain;
    if (llab.CORSCompliantServers.indexOf(currdom) == -1) {
        finalurl += llab.CORSproxy;
    }
    // Make sure protocol exists incase https:// connections
    currdom = window.location.protocol + '//' + currdom;
    if (targeturl.indexOf("..") != -1 || targeturl.indexOf(llab.rootURL) == -1) {
        var path = window.location.pathname;
        path = path.split("?")[0];
        path = path.substring(0, path.lastIndexOf("/") + 1);
        currdom += path;
    }
    finalurl = finalurl + currdom + targeturl;

    return finalurl;
};



// TODO move to topic.js
/** Strips comments off the line in a topic file. */
llab.stripComments = function(line) {
    var index = line.indexOf("//");
    // the second condition makes this ignore urls (http://...)
    if (index !== -1 && line[index - 1] !== ":") {
        line = line.slice(0, index);
    }
    return line;
};



/** Truncate a STR to an output of N chars.
 *  N does NOT include any HTML characters in the string.
 */
llab.truncate = function(str, n) {
    // Ensure string is 'proper' HTML by putting it in a div, then extracting.
    var clean = document.createElement('div');
        clean.innerHTML = str;
        clean = clean.textContent || clean.innerText || '';

    // TODO: Be smarter about stripping from HTML content
    // This, doesn't factor HTML into the removed length
    // Perhaps match postion of nth character to the original string?
    // &#8230; is a unicode ellipses
    if (clean.length > n) {
        return clean.slice(0, n - 1) + '&#8230;';
    }

    return str; // return the HTML content if possible.
};





llab.spanTag = function(content, className) {
    return '<span class="' + className + '">' + content + '</span>'
}



/////////////////////////////////
/* Google Analytics Tracking
 * To make use of this code, the two ga() functions need to be called
 * on each page that is loaded, which means this file must be loaded.
 */
llab.GAfun = function(i,s,o,g,r,a,m) { i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){ (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m) };

llab.GA = function() {
    llab.GAfun(window,document,'script','//www.google-analytics.com/analytics.js','ga');
};

// GA Function Calls -- these do the real work!:
if (llab.GACode) {
    llab.GA();
    ga('create', llab.GACode, llab.GAUrl);
    ga('send', 'pageview');
}



//////////////////////////////////
// query string stuff


/** Returns the value of the URL parameter associated with NAME. */
llab.getQueryParameter = function(paramName) {
    var params = llab.getURLParameters();
    if (params.hasOwnProperty(paramName)) {
        return params[paramName];
    } else {
        return '';
    }
};


/*!
    query-string
    Parse and stringify URL query strings
    https://github.com/sindresorhus/query-string
    by Sindre Sorhus
    MIT License
*/
// Modiefied for LLAB. Inlined to reduce requests
var queryString = {};

queryString.parse = function (str) {
    if (typeof str !== 'string') {
        return {};
    }

    str = str.trim().replace(/^(\?|#)/, '');

    if (!str) {
        return {};
    }

    return str.trim().split('&').reduce(function (ret, param) {
        var parts = param.replace(/\+/g, ' ').split('=');
        var key = parts[0];
        var val = parts[1];

        key = decodeURIComponent(key);
        // missing `=` should be `null`:
        // http://w3.org/TR/2012/WD-url-20120524/#collect-url-parameters
        val = val === undefined ? null : decodeURIComponent(val);

        if (!ret.hasOwnProperty(key)) {
            ret[key] = val;
        } else if (Array.isArray(ret[key])) {
            ret[key].push(val);
        } else {
            ret[key] = [ret[key], val];
        }

        return ret;
    }, {});
};

queryString.stringify = function (obj) {
    return obj ? Object.keys(obj).map(function (key) {
        var val = obj[key];

        if (Array.isArray(val)) {
            return val.map(function (val2) {
                if (!val2) { // Mod: Don't have =null values in URL params
                    return encodeURIComponent(key);
                }
                return encodeURIComponent(key) + '=' + encodeURIComponent(val2);
            }).join('&');
        }

        if (!val) { // Mod: Don't have =null values in URL params
            return encodeURIComponent(key);
        }

        return encodeURIComponent(key) + '=' + encodeURIComponent(val);
    }).join('&') : '';
};
/*! End Query String */

llab.QS = queryString;


// Return a new object with the combined properties of A and B.
// Desgined for merging query strings
// B will clobber A if the fields are the same.
llab.merge = function(objA, objB) {
    var result = {}, prop;
    for (prop in objA) {
        if (objA.hasOwnProperty(prop)) {
            result[prop] = objA[prop];
        }
    }
    for (prop in objB) {
        if (objB.hasOwnProperty(prop)) {
            result[prop] = objB[prop];
        }
    }
    return result;
};

llab.getURLParameters = function() {
    return llab.QS.parse(location.search);
};

llab.getAttributesForElement = function(elm) {
    var map = elm.attributes,
        ignore = ['class', 'id', 'style'],
        attrs = {},
        item,
        i = 0,
        len = map.length;

    for (; i < len; i += 1) {
        item = map.item(i);
        if (ignore.indexOf(item.name) === -1) {
            attrs[item.name] = item.value;
        }
    }
    return attrs;
};




//////////////////////////////
// Cool array level operations
llab.any = function(A) {
    return A.reduce(function(x, y) {return x || y;});
}

llab.all = function(A) {
    return A.reduce(function(x, y) {return x && y;});
}

llab.which = function(A) {
    for (i = 0; i < A.length; i++) {
        if (A[i]) {
            return i;
        }
    }
    return -1;
}



////////////////////
// cookie stuff
// someday my framework will come, but for now, stolen blithely from http://www.quirksmode.org/js/cookies.html
llab.createCookie = function(name,value,days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        var expires = "; expires="+date.toGMTString();
    }
    else var expires = "";
    document.cookie = name+"="+value+expires+"; path=/";
}

llab.readCookie = function(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

llab.eraseCookie = function(name) {
    llab.createCookie(name,"",-1);
}





////////////////////
// course utils

/*
 * course obj: 
 *    startTime: Date
 *    ...
 */

llab.getCourseTitle = function(usercontext, resource) {
    // if given a ... url?  user cookie? user donut?  dunno.
    //brainstorm really wants this.
    return null;
}


// might return null if pages are loaded without course context, 
//  but can't return undefined
llab.getCurrentCourse = function() {
	// TODO do something here based on url.
	// last resort, use something from config file. User?  who knows.
	return null;
}



// used inside brainstorm for now
llab.getCourseStartTime = function(course) {
	var time = llab.config.defaultCourseStartTime;
	
	if (typeof course == 'undefined') {
		course = llab.getCurrentCourse();
	}
	if (course != null 
			&& (typeof course['starttime'] != 'undefined') 
			&& course['startime'] != null) {
		time = course['starttime'];
	}
	return time;
}


/////////////////////  END

llab.loaded['library'] = true;
