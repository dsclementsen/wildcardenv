var env_status_map =  {
	'': 'Not running',
	'CREATE_IN_PROGRESS': 'Starting...',
	'CREATE_COMPLETE': 'Running',
	'UPDATE_COMPLETE': 'Running',
	'DELETE_IN_PROGRESS': 'Stopping...',
	'DELETED': 'Stopped',
	'ROLLBACK_COMPLETE': 'Failed to start',
	'DELETE_FAILED': 'Failed'
}
var all_status_classes = "CREATE_IN_PROGRESS CREATE_COMPLETE DELETE_IN_PROGRESS DELETED";
var context = {
	stacks: [],
	templates: []
};
var id_token = null;
var page = 'stacks';

var API_BASE_URL = 'https://3mq1qnh4p2.execute-api.ap-southeast-2.amazonaws.com/dev/';
var debug = false;
var email = "";


function onSignIn(googleUser) {
	// Useful data for your client-side scripts:
	var profile = googleUser.getBasicProfile();
	console.log("ID: " + profile.getId()); // Don't send this directly to your server!
	console.log('Full Name: ' + profile.getName());
	console.log('Given Name: ' + profile.getGivenName());
	console.log('Family Name: ' + profile.getFamilyName());
	console.log("Image URL: " + profile.getImageUrl());
	console.log("Email: " + profile.getEmail());
	email = profile.getEmail();

	if (email.endsWith("@innablr.com")) {
		console.log("Authorized");
		id_token = googleUser.getAuthResponse().id_token;
	}
	else {
		console.log("Unauthorized");
		id_token = null;
	}
};

$(document).ready(function() {
	$('.navbar-toggle').on('click', function() {
		$('body').toggleClass('menu');
	});

	// mark links to current page as active
	$("#menu a").each(function() {
		console.log(this.href);
		if (this.href == window.location.href) {
			$(this).addClass("active");
		}
	});

	// make external links open in new tab/page
	$(document.links).filter(function() {
		return this.hostname != window.location.hostname;
	}).attr('target', '_blank');


	$('#fancy-hover li').on('mouseleave', function(a,b,c) {
		$('#fancy-hover-active').css({
			width: 0
		});
	});
	$('#fancy-hover li').on('mouseenter', function(event) {
		event.stopPropagation();

		var $this = $(this);

		var pos = $this.position();

		$('#fancy-hover-active').css({
			top: pos.top,
			height: $this.height(),
			width: '6px'
		});

	});

	$("#main").on("click", ".template-start", function(event) {
		console.log('template-start');
		var $env = $(this).closest(".environment");
		var id = $env.attr("id").split("-");
		id.shift();
		var templateName = id.join('-');

		$('#template-modal .modal-title span').text(templateName);
		$('#template-modal').modal();
	});

	$("#template-modal .btn-primary").on("click", function(event) {
		let templateName = $("#template-modal .modal-title span").text();
		let stackName = $("#stackname").val();
		// $env = $('#env-' + stackName);
		$('#template-modal').modal('hide');


		console.log([templateName, stackName]);
		$.ajax({
			dataType: "json",
			url: API_BASE_URL + 'api/templates/' + templateName + '/quicklaunch/' + stackName,
			headers: {
				"Authorization": id_token
			},
			success: function(data){
				console.log(data);
				page = "stacks";
				loadStacks();
				// updateEnvironmentStatus($env, data.status);
			}
		});
	});


	$(".env-start").on("click", function(event) {
		var $env = $(this).closest(".environment");
		var [_, pk] = $env.attr("id").split("-");
		console.log(pk);
		$.ajax({
			dataType: "json",
			url: API_BASE_URL + 'api/stacks/' + pk + '/launch/', 
			headers: {
				"Authorization": id_token
			},
			success: function(data) {
				console.log(data);
				updateEnvironmentStatus($env, data.status);
			}
		});
	});

	$("#main").on("click", ".env-stop", function(event) {
		console.log('stop');
		var $env = $(this).closest(".environment");
		var id = $env.attr("id").split("-");
		id.shift();
		var stackName = id.join('-');

		console.log(stackName);
		//https://1h6df94d9e.execute-api.ap-southeast-2.amazonaws.com/dev
		$.ajax({
			dataType: "json",
			url: API_BASE_URL + 'api/stacks/' + stackName + '/stop', 
			headers: {
				"Authorization": id_token
			},
			success: function(data){
				console.log(data);
				updateEnvironmentStatus($env, "DELETE_IN_PROGRESS");
			}
		});
	});

	// refreshEnvironments();
	loadStacks();
	loadTemplates();
	// var tid = setInterval(refreshEnvironments, 15000);

	$('#nav-templates').click(function(ev) {
		ev.preventDefault();
		page = 'templates';
		refresh();
	})
	$('#nav-environments').click(function(ev) {
		ev.preventDefault();
		page = 'stacks';
		refresh();
	})

});

function loadTemplates() {
	$.getJSON(API_BASE_URL + 'api/templates', function(data){
		var templates = data.templates
		for (var i=0; i < templates.length; i++) {
			let template = templates[i];
			console.log(template)
			context.templates.push(template);
		}
		refresh();
	});
}
function loadStacks() {
	context.stacks = [];
	$.getJSON(API_BASE_URL + 'api/stacks', function(data){
		console.log(data)
		for (let i=0; i<data.length; i++) {
			let stack = data[i];
			if (stack.StackName.indexOf('Stack-') > 0) {
				continue;
			}
			stack.StackStatusDisplay = env_status_map[stack.StackStatus];
			context.stacks.push(stack);
		}
		refresh();
	});
}
function refresh() {
	if (page == 'stacks') {
		showStacks();
	}
	else if (page == 'templates') {
		showTemplates();
	}

}
function showTemplates() {
	var source   = document.getElementById("templates-template").innerHTML;
	var template = Handlebars.compile(source);
	var html    = template(context);
	$('#main > div > div').first().html(html);
}
function showStacks() {
	var source   = document.getElementById("environments-template").innerHTML;
	var template = Handlebars.compile(source);
	var html    = template(context);
	$('#main > div').html(html);
}
function refreshEnvironments() {
	$.getJSON(API_BASE_URL + 'api/stacks', function(data){
		console.log(data)
		for (let i=0; i<data.length; i++) {
			let stack = data[i];
			let $env = $('#env-' + stack.StackName);
			updateEnvironmentStatus($env, stack.StackStatus);
		}
	})
}

function refreshEnvironmentStatus(env) {
	var $env = $(env);
	var id = $env.attr("id").split("-");
	id.shift();
	var stackName = id.join('-');
	//var pk = id.split("-")[1];

	$.getJSON(API_BASE_URL + 'api/stacks/' + stackName, function(data){
		updateEnvironmentStatus($env, data.StackStatus);
	});
}

function updateEnvironmentStatus($env, status) {
	$env.removeClass(all_status_classes);
	$env.addClass(status);
	$env.find('.actions .dropdown-toggle').text(env_status_map[status]);
}
