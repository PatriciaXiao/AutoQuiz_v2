/*
 * brainstorm tool, adapted from Wise4 stuff
 */
// jshint jquery:true

// TODO
//   write the server stuff, duh: see refreshResponses()

llab.bs = {};
llab.bs.nodes = [];

// /////////


// starting point, after page load
llab.bs.buildNodes = function() {
	$("div.brainstorm-data").each(function(i) {
		var bsdatadiv = $(this);

		if (bsdatadiv.attr("src")) {
			// bsdatadiv is external to page...
			$.get(bsdatadiv.attr("src"), function(bsdatadiv, status) {
				llab.bs.buildNode(bsdatadiv, i, true)
			}).fail(function(jqxhr, textstatus, err) {
				llab.bs.revealDataDivError(bsdatadiv, i, textstatus);
			});

		} else {
			// bsdatadiv is internal, build away
			llab.bs.buildNode(bsdatadiv, i, false);
		}
	});
}

// either didn't get the data, or the data is broken somehow
llab.bs.revealDataDivError = function(bsdatadiv, i, error) {
	// TODO -- you know, write a div saying 'whoops' or something
	$(bsdatadiv).addClass("remote-data-error")
	   .append("<hr><p>Failed to get this brainstorm specification. Don't code like Afroman.</p>"
	           + "<p>Error: "+error+"</p>");
}




/////////////////////////
// model and view

// TODO put inside llab.bs!  MV! Bring into the second decade of the 2nd millennium!


//bsdatadiv is a div with the relevant data (see example.brainstorm)
//i is the index of brainstorm on page, fetched if it was pulled remotely.
llab.bs.buildNode = function(bsdatadiv, i, fetched) {
	var bsnode = new BRAINSTORM(bsdatadiv, i);
	llab.bs.nodes[i] = bsnode;
	// node.render();
	bsnode.show();
}



//TODO separate model and view, yo
// and, fix that cyclomatic complexity, yo-lol.
var BRAINSTORM = function(bsdatadiv, i) {

	this.bsdatadiv = bsdatadiv;
	this.indexOnPage = i;
	
	var bsdiv = $(llab.bs.getContentTemplate(i)).insertAfter(bsdatadiv);
	this.bsdiv = bsdiv;
	bsdiv.attr("indexOnPage", i);
	
	
	this.id = bsdatadiv.id;
	this.showtitle = true;
	this.title = bsdatadiv.find(".title").html();
	if (this.title === "" || this.title === null) {
		this.showtitle = false;
	}
	if (this.showtitle) {
		bsdiv.find(".title").html(this.title).css('display', 'block');
	}

	
	// returns true if too short
	var tooshort = function(thing) {
	    if (typeof thing === 'undefined' || thing === "" || thing === null ) {
	        return true;
	    } else if (!(typeof thing === 'string')) {
	        thing = String(thing);   
	    }
	    return (thing.length < 6);
	}
	
    // now that we have id and title, set the 'real' id
    var tempid;
    if (!(tooshort(this.id))) {
        tempid = "id" + String(this.id);
    } else if (!(tooshort(this.title))) {
        tempid = "title" + this.title;
    } else {
        tempid = bsdatadiv.html();
    } 
    // TODO we really need to include course in here, or id will be the same across courses!
    // NOTE THIS DOESN't WORK RIGHT NOW.  
	this.id = tempid + llab.getCourseTitle();
	this.id = SHA1(this.id); // regularlize length, make things mysterious,
								// etc.

	this.prompt = bsdatadiv.find(".prompt").html();
	if (this.prompt === "" || this.prompt === null) {
		// TODO should treat this like ajax failure, really
		this.prompt = "ERROR: MISCONFIGURATION OF PROMPT";
	}
	bsdiv.find(".prompt").html(this.prompt);

	// height of textarea
	var inputarea = bsdiv.find(".input").find(".inputarea");
	var numlines = inputarea.attr('rows');
	var numlines_toset = bsdatadiv.attr('expected-lines');
	if (numlines_toset !== "" || numlines_toset !== null) {
		numlines = numlines_toset;
	}
	inputarea.attr('rows', numlines);

	////// event listeners
	
	var savebutt = bsdiv.find(".input input[type=button]");
	savebutt.click(function() {
		llab.bs.saveResponse(bsdiv);
	});
	bsdiv.find(".responseButton > img").click(function() {
		llab.bs.refreshResponses(bsdiv);
	});
	bsdiv.find(".settings > img").click(function() {
		llab.bs.showSettings(bsdiv);
	});
	var txtarea = bsdiv.find(".inputarea");
	txtarea.on('keyup', function() {
		// enable/disable savebutt
		if (txtarea.val().trim() != '') {
			savebutt.attr('disabled', false);
			savebutt.removeClass('disabled');
		} else {
			savebutt.attr('disabled', true);
			savebutt.addClass('disabled');
		}
	});
	
	/////// responses
	this.userResponse = {'username' : "(Your Response)"};
	var responses = this.responses = [];
	bsdatadiv.find(".canned-responses").children().each(function(i, cannedResp) {
		responses.push(llab.bs.makeCannedResponse(cannedResp, i));
	});
	
	
}


llab.bs.getNode = function(bsDiv) {
	return (llab.bs.nodes[bsDiv.attr("indexOnPage")]);
}




BRAINSTORM.prototype.show = function() {
	var bsnode = this;
	this.bsdatadiv.hide(125, function() {
		bsnode.bsdatadiv.remove();
	});
	bsnode.bsdiv.show(125);
}


// TODO arg!  move to jsrender, yo
llab.bs.getContentTemplate = function(indexOnPage) {
	// template needs to start with '<' !! no spaces, sigh
	var template = '<div class="brainstorm" indexOnPage="' + indexOnPage + '">'
			+ '   <div class="settings">'
			+ '      <img src="' + llab.llab_path + 'img/brainstorm-gear.png" alt="Settings" />'
			+ '   </div>'
			+ '   <div class="title"></div>'
			+ '   <div class="prompt"></div>'
			+ '   <div class="input">'
			+ '      <p>My Response: </p>'
			+ '      <textarea class="inputarea" rows="4" cols="100"></textarea>'
			+ '      <input class="disabled" type="button" value="save" disabled />'
			+ '      <div class="inputnotification"></div> '
			+ '   </div>'
			+ '   <div class="responseArea">'
			+ '      <p>Responses: </p>'
			+ '      <div class="responsebutton">'
			+ '         <img src="' + llab.llab_path + 'img/brainstorm-refresh-responses.png" alt="Refresh responses" />'
			+ '      </div> ' 
			+ '      <div class="responses">'
			+ '         <div class="responsePlaceholder"></div>'
			+ '      </div>' 
			+ '   </div>' 
			+ '</div>';
	return template;
}




////////////////////////
/// responses

llab.bs.makeCannedResponse = function(crDataDiv, i) {
	// adds 1-14 days to passed date
	var addSomeDays = function (date) {
		var d = new Date(date);
		var days2add = Math.floor(Math.random() * 13 + 1);
		d.setDate(d.getDate() + days2add);
		return(new Date(d));
	}
	// index needs to reflect sequence place in bsnode.responses
	var resp = {
			'canned':true,
			'time':addSomeDays(llab.getCourseStartTime()),
			'username': $(crDataDiv).attr("name"),
			'responseText': $(crDataDiv).html(),
			'index' : i
			};
	return resp;
}




// button is supposed to be disabled/enabled above, so we don't really need to 
// check here
llab.bs.saveResponse = function(bsdiv) {
	var responseText = bsdiv.find(".inputarea").val().trim();
	if (responseText) {
		var bsnode = llab.bs.getNode(bsdiv);
		if (typeof bsnode.userResponse['responseText'] !== 'undefined') {
			// an edit!  note, we only save responseText, not username, time
			if (bsnode.userResponse['edits']) {
				bsnode.userResponse['edits'].push(bsnode.userResponse['responseText']);
			} else {
			bsnode.userResponse['edits'] = [ bsnode.userResponse['responseText'] ];
			}
		}
		bsnode.userResponse['time'] = new Date();
		bsnode.userResponse['responseText'] = responseText;
		bsnode.userResponse['index'] = "user";    //not necessary

		llab.bs.syncResponsesView(bsdiv, bsnode);
		$(".brainstorm .input").hide(125);
		$(".brainstorm .responseArea").show(125);
	}
}

// hide the whole response area while editing? Well, ok.
llab.bs.editResponse = function(bsdiv) {
	console.log("so you want to edit your response, eh?");
	
	$(bsdiv).find(".input input[type=button]").val("edit");
	$(bsdiv).find(".brainstorm .responseArea").hide(125);
	$(bsdiv).find(".brainstorm .input").show(125);
}


// mashing around the dom here a bunch...
// userClass's are inline here; using ".responsesPlaceholder" to keep track of insertions, etc.
llab.bs.syncResponsesView = function(bsdiv, bsnode) {
	// make the view reflect the model, har har
	var responses = $(bsdiv).find(".responses");
	var placeholder = $(bsdiv).find(".responsePlaceholder");
	// user first
	var respDivUser = llab.bs.setResponseDiv(bsdiv, bsnode.userResponse, responses.find(".response.user"), "user");
	// make sure user is first, and placeholder is next.
	$(respDivUser).parent().prepend(respDivUser);
	$(respDivUser).after(placeholder);
	// canned and others
	$.each(bsnode.responses, function(i, resp) {
		var userClass = (resp.canned ? "canned" : "other");
		var responseDiv = $(responses).find(".response" + "." + userClass + "[index='"+i+"']");
		llab.bs.setResponseDiv(bsdiv, resp, responseDiv, userClass);
	});
	// note, we don't remove respDivs that no longer have resp objects.  cool? 
	//  to do so would make updating index's a pain. Let's never get rid of resp objects!  Woot.
}




//  resp: response json model, 
//  div: jquery response div (could be empty/null, which means it needs to be created)
//  userClass: "user", "canned", or "other"
// returns div (same one if it existed already, just updated)
// TODO should we let username change?  right now it can
// jsrender and jsview here, please
llab.bs.setResponseDiv = function(bsdiv, resp, responseDiv, userClass) {
	if (typeof responseDiv === "undefined" || responseDiv === null
			|| $.isEmptyObject(responseDiv) || responseDiv.length == 0) {
		responseDiv = $(llab.bs.getResponseTemplate(resp, userClass));
		// insert after the placeholder
		$(bsdiv).find(".responsePlaceholder").after(responseDiv);
	} else {
		// would be cool if, when this is actually changing an existing div it
		// does some sort of cool flip or something, so the div looks like 
		// its changed. (will look good when things auto update)
		$(responseDiv)
		   .find(".username").val(resp['username']).end()
		   .find(".time").val(llab.bs.respTimePretty(resp['time'])).end()
		   .find(".responseTextArea").html(resp['responseText']);
		// do the flip!
	}
	return (responseDiv);
}



//userClass is "user", "canned", or "other" 
llab.bs.getResponseTemplate = function(resp, userClass) {
	var template = ''
		    + '<div index="' + resp['index'] + '" class="response ' + userClass + '">'
			+ '  <div class="responseTitle"> ' 
			+ '    <span class="username">' + resp['username'] + '</span> '
			+ '';
	if (userClass === "user") {
		template += ''
			+ '    <span class="edit"> '
			+ '       <input type="button" value="edit" />'
			+ '    </span>'
	};
	template += ''
			+ '    <span class="time">' + llab.bs.respTimePretty(resp['time']) + '</span> '
			+ '  </div>'
			+ '  <div class="responseTextArea">' + resp['responseText'] + '</div>'
			+ '</div> '
			+ '';
	template = $(template);
	template.find("input[type=button]").click(function() {
		llab.bs.editResponse($(this).parents(".brainstorm"));
	});
	return template;
}



//returns time as displaying string 
llab.bs.respTimePretty = function (time) {
	return (time.toDateString());
}

//////////////////////////////////////////////////
//////////////// pull responses from server, yikes.
llab.bs.refreshResponses = function(bsdiv) {
	var indexOnPage = $(bsdiv).attr("indexOnPage");
	var bsnode = llab.bs.nodes[indexOnPage];

	// first, need to update the new bsnode.responses array, adding new responses
	//  and changing the responseText of existing ones.  Going to have to key those
	//  responsedata on user/bs/course, or some other group other than course.
	// second
	llab.bs.syncResponsesView(bsdiv, bsnode);
	
	
	console.log("refresh?  for the " + indexOnPage + "th brainstorm? someday, someday...");

}

/////////////////
// options

//TODO
llab.bs.showSettings = function(bsdiv) {
	console.log("no settings control yet...");
}

// show user, do user stuff
// sort by X, Y
// flag for teacher



/////////////////////////////////////////

$(document).ready(function() {
	llab.bs.buildNodes();
});

