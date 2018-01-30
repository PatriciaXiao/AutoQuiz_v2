if (typeof llab === 'undefined') {
    llab = {};
    llab.paths = {};
    llab.paths.css_files = [];
    llab.loaded = {};
}

/**
 ****************************
 ******** LLAB CONFIG *******
 ****************************
 */

/**
 *  THIS is an example of what your config file can or should contain.
 *
 *  Make a copy of this file, name it "llab-config.js", and put it
 *  in the directory that contains the llab repository.  That is, do not
 *  put it inside the "llab" directory, but at the same level as that directory.
 *  Capiche?
 *
 *  //TODO this should probably be refactored into yaml.  maybe.
 */



llab.config = {};

// TODO:
//  need to be careful about "paths" versus "urls".
//    in the buildless system, we don't need actual "paths" anywhere, right?
//    but in node.js (build system or whatever), we'll want paths sometimes, I think.
//


/////////////////////
/// PATHS AND URLS

// if the website isn't at the root of the server, add the path here.
// starting / means this is an absolute link, yo
llab.rootURL = "/bjc-r/";

// change if llab scripts are installed in a different path *within* rootURL.
llab.install_directory = "llab/";

// absolute path to llab files -- think before you edit this.  Hell, think before
//  you do anything, but especially this one time.
llab.llab_path = llab.rootURL + llab.install_directory;

//courses -- path to folder containing courses.
//a course 'name', when prepended with this, will be an absolute link
llab.courses_path = llab.rootURL + "course/";

//TOPICS (old style) stuff.
//place where you put (oldstyle) X.topic files, used when building menus on curriculum pages
llab.topics_path = llab.rootURL + "topic/";



///////////////////////////
//  SPECIFIC FILES

// identify your custom CSS files.  You got some choices:
//   start without a slash, and these will come from within llab install directory.
//   start with a slash, and these will come from your server root
//   start with two slashes and a domain name, and these can come from the whole world wide web
//  Multiple CSS files is fine, include a separate push for each

//llab.paths.css_files.push('css/3.3.0/bootstrap-theme.min.css');
//llab.paths.css_files.push("/css/this-will-make-my-course-beautiful.css");
//llab.paths.css_files.push('//netdna.bootstrapcdn.com/bootstrap/3.0.3/css/bootstrap.min.css');


// Used when referring to a topic page -- you could change this location
// TODO -- a little more detail about what this is, programmer guys?  I got nothing.
llab.topic_launch_page = llab.llab_path + "html/topic.html";
llab.alt_topic_page = llab.rootURL + "topic/topic.html";

// Page templates.
//  You could put custom version in your course repo and refer to them here.

// TODO - need to distinguish btw URL and paths !!
// TODO - someday my jsrender will come
llab.empty_topic_page_path = llab.llab_path + "html/empty-topic-page.html";
llab.empty_curriculum_page_path = llab.llab_path + "html/empty-curriculum-page.html";
llab.empty_matchsequence_page_URL = llab.llab_path + "html/empty-matchsequence-page.html";




//////////////////////////////
//  DEFAULT VALUES AND STRINGS
// look in defaults.js, inside llab/script, to see what you can abuse.
// Values set here will override those, because llab/script/defaults is loaded first.

// e.g:
//  llab.strings.clickNav = "Navigation&nbsp;";



//////////////////////////
// google analytics tokens

llab.GAuse = true;
llab.GACode = 'UA-47210910-3';
llab.GAurl = 'berkeley.edu';




///////////////////////////
// User, course, etc

// year, month, day, hour, etc...   Remember, month is 0-11. (07 is august).
llab.config.defaultCourseStartTime = new Date(2015, 7, 20, 12);


llab.user = {};
//// Ug, this configuration needs to be done at end of load, after USER objects
//// are defined.  Need a syntax for this.  For now just doing it in user.js
// llab.user.user = new USER_NO_AUTH();  // simple user


/*
 ******************************
 ********* END CONFIG *********
 ******************************
 */
// don't delete this!
llab.loaded['config'] = true;