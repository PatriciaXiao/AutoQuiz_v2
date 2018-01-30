/////////////////////////
// DEFAULTS

// all of these can be overridden/changed in the llab-config file, which gets loaded after.






//These are common strings that need not be build and should be reused!
llab.strings = {};
llab.strings.goMain = 'Go to the Course Page';
//&#8230; is ellipsis
llab.strings.clickNav = 'Click here to navigate&nbsp;&nbsp;';



//These are code fragments which are reusable components.
llab.fragments = {};
llab.fragments.bootstrapSep = '<li class="divider list_item" role="presentation"></li>';
llab.fragments.bootstrapCaret = '<span class="caret"></span>';
llab.fragments.hamburger = '<span class="sr-only">Toggle navigation</span><span class="icon-bar"></span><span class="icon-bar"></span><span class="icon-bar"></span>';






/////////////////
// CORS, joy.


// these are used in llab.getSnapRunURL(), inside library.js

llab.CORSproxy = "https://bjcredir.herokuapp.com/";

llab.CORSCompliantServers = [];
llab.CORSCompliantServers.push("bjc.berkeley.edu");
llab.CORSCompliantServers.push("bjc.eecs.berkeley.edu");
llab.CORSCompliantServers.push("snap.berkeley.edu");
llab.CORSCompliantServers.push("inst.eecs.berkeley.edu");
llab.CORSCompliantServers.push("cs10.berkeley.edu");
llab.CORSCompliantServers.push("beautyjoy.github.io");
llab.CORSCompliantServers.push("cs10.github.io");
llab.CORSCompliantServers.push("localhost");
llab.CORSCompliantServers.push("0.0.0.0");
// Testing so that dev is like the server.
llab.CORSCompliantServers.push("localhost:8000");


llab.snapRunURLBase = "http://snap.berkeley.edu/snapsource/snap.html#open:";
//llab.snapRunURLBase = "http://bjc.edc.org/snapsource/snap.html#open:";




