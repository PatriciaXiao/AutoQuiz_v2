/////////// FIXME -- put this in a better place.
// Polyfills for older browsers
if (!String.prototype.endsWith) {
  Object.defineProperty(String.prototype, 'endsWith', {
    value: function(searchString, position) {
      var subjectString = this.toString();
      if (position === undefined || position > subjectString.length) {
        position = subjectString.length;
      }
      position -= searchString.length;
      var lastIndex = subjectString.indexOf(searchString, position);
      return lastIndex !== -1 && lastIndex === position;
    }
  });
}









/* LLAB Loader
 * Lightweight Labs system.
 * This file is the entry point for all build-less llab pages.
 * The build system build html files that already have this generated.
 */

// TODO
// build system will bypass this and insert script/link references directly,
//   but we'll likely keep both
// move to require.js, simple stuff!
// could conditionally load a lot of this stuff based on components on the page
// we really should change 'path' to URL...  it confuses me!


var THIS_FILE = 'loader.js';

llab = {};
llab.loader = {}   // FIXME -- move stuff into this namespace, for this file
llab.loaded = {};  // keys are true if that script file is loaded
llab.paths  = {};
llab.paths.stage_complete_functions = [];
llab.paths.scripts = [];  // holds the scripts to load, in stages below
llab.paths.css_files = [];
llab.rootURL = "";  // to be overridden in llab-config.js
llab.install_directory = "";  // to be overridden in llab-config.js


// This file is referenced at the same level as the llab install directory, not within it
// llab.CONFIG_FILE_PATH = "../apcsa/llab-config.js";
llab.CONFIG_FILE_PATH = "../llab.js";

// This file must always be at the same level as the llab install directory
llab.BUILD_FILE_PATH = "./llab-complied.js";

llab.altFiles = {};
// Syntax Highlighting support
llab.altFiles.syntax_highlights_js = "lib/highlightjs/highlight.pack.js";
llab.altFiles.syntax_highlights_css = "lib/highlightjs/styles/tomorrow-night-blue.css";
// Math / LaTeX rendering
llab.altFiles.math_katex_js = "lib/katex.min.js";
llab.altFiles.math_katex_css = "css/katex.min.css";



/////////////////////////
// reference your custom CSS files, from within llab install directory.
// Multiple CSS files is fine, include a separate push for each
llab.paths.css_files.push('lib/bootstrap/dist/css/bootstrap.min.css');
llab.paths.css_files.push('lib/bootstrap/dist/css/bootstrap-theme.min.css');
// llab.paths.css_files.push('css/brainstorm.css');
// llab.paths.css_files.push('css/matchsequence.css');
llab.paths.css_files.push('css/default.css');



///////////////////////// pre stage 0
llab.paths.defaults_file = "script/defaults.js";

///////////////////////// stage 0
llab.paths.scripts[0] = [];
llab.paths.scripts[0].push(llab.CONFIG_FILE_PATH);
llab.paths.scripts[0].push("lib/jquery/dist/jquery.min.js");

llab.loaded['config'] = false;
llab.paths.stage_complete_functions[0] = function() {
    return ( typeof jQuery === 'function' && llab.loaded['config'] );
}


/////////////////
///////////////// stage 1
llab.paths.scripts[1] = [];
llab.paths.scripts[1].push("script/library.js");
llab.paths.scripts[1].push("lib/bootstrap/dist/js/bootstrap.min.js");
// matchsequence
// llab.paths.scripts[1].push("lib/jquery-ui-custom/jquery-ui.min.js");
llab.paths.scripts[1].push("lib/sha1.js");     // for brainstorm

llab.loaded['library'] = false;
llab.paths.stage_complete_functions[1] = function() {
    return ( llab.loaded['library'] );
}



////////////////////
//////////////////// stage 2
// all these scripts depend on jquery, loaded in stage 1
// all quiz item types should get loaded here
llab.paths.scripts[2] = [];
llab.paths.scripts[2].push("script/curriculum.js");
llab.paths.scripts[2].push("script/course.js");
llab.paths.scripts[2].push("script/topic.js");
llab.paths.scripts[2].push("script/quiz/multiplechoice.js");
// llab.paths.scripts[2].push("script/user.js");

llab.loaded['multiplechoice'] = false;
llab.paths.stage_complete_functions[2] = function() {
    return ( llab.loaded['multiplechoice'] ); //&& llab.loaded['user']
}




////////////////
////////////////  stage 3
// quiz.js depends on each of the quiz item types having loaded
llab.paths.scripts[3] = [];
llab.paths.scripts[3].push("script/quiz.js");
// llab.paths.scripts[3].push("script/matchsequence_all.js");
// llab.paths.scripts[3].push("script/brainstorm.js");

llab.paths.stage_complete_functions[3] = function() {
    return true; // the last stage, no need to wait
}

//////////////

llab.getPathToThisScript = function() {
    var scripts = document.scripts;
    for (var i = 0; i < scripts.length; i += 1) {
        var src = scripts[i].src;
        if (src.endsWith('/' + THIS_FILE)) {
            return src;
        }
    }
    return '';
};

llab.pathToLlab = llab.getPathToThisScript().replace(THIS_FILE, "");


llab.loader.getTag = function(name, src, type, onload) {
    var tag = document.createElement(name);

    if (src.substring(0, 2) === "//") {
        // external server, carry on..
    } else if (src.substring(0,1) === "/") {
        // root on this server
        src = window.location.href.replace(window.location.pathname, src);
    } else {
        // relative link
        src = llab.pathToLlab +  src;
    }

    var link  = name === 'link' ? 'href' : 'src';
    tag[link] = src;
    tag.type  = type;
    tag.onload = onload;
    tag.async = true;

    return tag;
}


// ///// SETUP INIT
// load defaults, then go to initial setup
llab.preSetUp = function() {
    var tag = llab.loader.getTag('script', llab.paths.defaults_file,
            "text/javascript", function() {
                // onload
                llab.initialSetup();
            });
    document.head.appendChild(tag);
}


// TODO use promises composed of a stage's onload callbacks to trigger next stage.
llab.initialSetup = function() {
    var headElement = document.head;
    var tag, i, src;

    // start the process
    loadScriptsAndLinks(0);

    function loadScriptsAndLinks(stage_num) {
        var i, tag;

        // load css files
        while (llab.paths.css_files.length != 0) {
            tag = llab.loader.getTag("link", llab.paths.css_files.shift(), "text/css");
            tag.rel = "stylesheet";
            headElement.appendChild(tag);
        }

        // load scripts
        llab.paths.scripts[stage_num].forEach(function(scriptfile) {
            tag = llab.loader.getTag("script", scriptfile, "text/javascript");
            headElement.appendChild(tag);
        });

        if ((stage_num + 1) < llab.paths.scripts.length) {
            proceedWhenComplete(stage_num);
        }
    }

    // TODO use promises; they work in basically all browsers now
    function proceedWhenComplete(stage_num) {
        if (llab.paths.stage_complete_functions[stage_num]()) {
            if ((stage_num + 1) < llab.paths.scripts.length) {
                loadScriptsAndLinks(stage_num + 1);
            }
        } else {
            setTimeout(function() {
                proceedWhenComplete(stage_num);
            }, 5);
        }
    }
};

/////////////////////

llab.preSetUp();

