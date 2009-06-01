// these functions only go specifically with the one particular page that collects scheme information
// they are not generic and are almost certainly of no use with any other page

// shared variables
var shutoffcheckflag = 0;

// these variables are used throughout as easier-to-access versions of what is supplied by the inputs
// they make the rest of the JavaScript simpler
// note that like most JavaScript variables they are NOT passed on to the next module
// event routines on the various inputs set these variables to their new values as soon as possible,
//  then do all the display based on them (so they'd better be correct)
var js_mingroups;
var js_filtergroups;
var js_filtergroupsdefaultnoweb;
var js_filtergroupshighestallweb;
var js_firstvariablegroup;
var js_lastvariablegroup;

// these variables are used to implement a "not changed recently" timer on the 
//  number of filter groups field
var filtergroups_counter = 0;
var filtergroups_pointer;

function shutoffcheck()
{
	shutoffcheckflag = 1;
}
function checkinput(theform)
{
	if (shutoffcheckflag) { return true; }
	// scheme always ok because radio button and something always selected
	// default always ok because either setting is legitimate
	//var howmany = theform.filtergroups.value;
	if ((js_filtergroups < js_mingroups) || (js_filtergroups > 99)) {
		alert('Please specify a number of filter groups between ' + mingroups + ' and 99 then try again.');
	        setupfirstgroup(theform.filtergroupsdefaultnoweb);
	        setuplastgroup(theform.filtergroupshighestallweb);
		theform.filtergroupsdefaultnoweb.focus();
		theform.filtergroups.focus();
		return false;
	}
	var inputfieldname;
	var inputfield;
	if (js_filtergroups <= 9) {
		for (i=1; i<=js_filtergroups; ++i) {
			inputfieldname = 'groupnamef' + i;
			inputfield = theform.eval(inputfieldname);
			if (inputfield.value == '') {
				alert('Please specify a name for each filter group then try again.');
				setupfirstgroup(theform.filtergroupsdefaultnoweb);
				setuplastgroup(theform.filtergroupshighestallweb);
				theform.filtergroupsdefaultnoweb.focus();
				inputfield.focus();
				return false;
			}
		}
	}
	// panels of lists always ok 
	//  partly because all lists will always be there (we're coded that way)
	//  and partly because it's too hard to check
	return true;
}
function getcurrentfromradiolist(schemeinputlist)
{
	var numberofchoices = schemeinputlist.length;
	for (var i=0; i<numberofchoices; ++i) {
		if (schemeinputlist[i].checked) { return schemeinputlist[i] };
	}
	return null; 
}
function adjustlistslist(schemeinput)
{
	var showsharedlists = schemeinput.form.showsharedlists;
	var showuniquelists = schemeinput.form.showuniquelists;
	var restrictionarray = restrictionarrays[schemeinput.value];
	prunelist(showsharedlists, showuniquelists, restrictionarray);
	endislist(showsharedlists, restrictionarray);
}
function endislist(selectelement, restricteditems)
{
	var numberofoptions = selectelement.length;
	var currentoption;
	for (var i=0; i<numberofoptions; ++i) {
		currentoption = selectelement.options[i];
		if (contains(restricteditems, currentoption.value)) {
			currentoption.disabled = true;
		} else {
			currentoption.disabled = false;
		}
	}
}
function prunelist(putoptionshere, prunethisselect, restricteditems)
{
	var numberofoptions = prunethisselect.length;
	var currentoption;
	for (var i=0; i<numberofoptions; ) {
		currentoption = prunethisselect.options[i];
		if (contains(restricteditems, currentoption.value)) {
			moveoption(prunethisselect, i, putoptionshere, 1); 
			// we changed list, so it's shorter than it was
			--numberofoptions;
		} else {
			// bump to next slot only if we did _not_ remove 
			++i;
		}
	}
}
function contains(array, searchstring)
{
	var i = array.length;
	while (i--) {
		if (array[i] == searchstring) { return true; }
	}
	return false;
}
function initform()
{
	var theform = document.getElementById('theform');
	adjustnumberofgroups(theform.filtergroups);
	setupfirstgroup(theform.filtergroupsdefaultnoweb);
	setuplastgroup(theform.filtergroupshighestallweb);
	changeshowlistslegends(getcurrentfromradiolist(theform.filtergroupsschemelists));
	adjustlistslist(getcurrentfromradiolist(theform.filtergroupsschemelists));
}
function setupfirstgroup(checkinput)
{
	var firstgroupname = checkinput.form.groupnamef1;
	if (checkinput.checked) {
		proposed_mingroups = 2 + js_filtergroupshighestallweb;
		if (proposed_mingroups > js_filtergroups) {
			alert('Please first specify more filter groups if you wish to reserve the default filter group for no web access.');
			checkinput.checked = false;
			js_filtergroupsdefaultnoweb = 0;
			checkinput.form.filtergroups.focus();
		} else {
			if (firstgroupname.value == '') { firstgroupname.value = 'No_Web_Access'; }
			firstgroupname.disabled = true;
			js_firstvariablegroup = 2;
			js_filtergroupsdefaultnoweb = 1;
		}
	} else {
		if (firstgroupname.value == 'No_Web_Access') { firstgroupname.value = ''; }
		firstgroupname.disabled = false;
		jsfirstvariablegroup = 1;
		js_filtergroupsdefaultnoweb = 0;
	}
	js_mingroups = 1 + js_filtergroupsdefaultnoweb + js_filtergroupshighestallweb;
}
function setuplastgroup(checkinput)
{
	var lastgroupnamename = 'groupnamef' + js_filtergroups;
	var lastgroupname = (js_filtergroups <= 9) ? checkinput.form.eval(lastgroupnamename) : null;
	if (checkinput.checked) {
		proposed_mingroups = 2 + js_filtergroupsdefaultnoweb;
		if (proposed_mingroups > js_filtergroups) {
			alert('Please first specify more filter groups if you wish to reserve the highest numbered filter group for unrestricted web access.');
			checkinput.checked = false;
			js_filtergroupshighestallweb = 0;
			checkinput.form.filtergroups.focus();
		} else {
			if ((js_filtergroups <= 9) && (lastgroupname.value == '')) { lastgroupname.value = 'All_Web_Access'; }
			if (js_filtergroups <= 9) { lastgroupname.disabled = true; }
			lastvariablegroup = js_filtergroups - 1;
			js_filtergroupshighestallweb = 1;
		}
	} else {
		if ((js_filtergroups <= 9) && (lastgroupname.value == 'All_Web_Access')) { lastgroupname.value = ''; }
		if (js_filtergroups <= 9) { lastgroupname.disabled = false; }
		lastvariablegroup = js_filtergroups;
		js_filtergroupshighestallweb = 0;
	}
	js_mingroups = 1 + js_filtergroupsdefaultnoweb + js_filtergroupshighestallweb;
}
function inputtonumberofgroups(numberinput)
{
	++filtergroups_counter;
	filtergroups_pointer = numberinput;
	setTimeout('adjustnumberofgroups(filtergroups_pointer)', 600);
}
// if filtergroups > 9 the group names we pass are all wrong (or missing)
// setupfiltergroups.cgi knows to create its own groupnames if filtergroups > 9
//  rather than try to use the ones we pass in
function adjustnumberofgroups(numberinput)
{
	if (numberinput.value == '') { return; }
	var proposed_filtergroups = numberinput.value;
	var displaygroupnames;
	if ((proposed_filtergroups < js_mingroups) || (proposed_filtergroups > 99)) {
		alert('Please choose a number of filter groups between ' + js_mingroups + ' and 99');
		numberinput.value = js_filtergroups;
		numberinput.focus();
		return;
	}
	if (js_filtergroups <= 9) {
		var old_lastgroupnamename = 'groupnamef' + js_filtergroups;	// OLD value
		var old_lastgroupname = numberinput.form.eval(old_lastgroupnamename);
		if (old_lastgroupname.value == 'All_Web_Access') { old_lastgroupname.value = ''; }
		old_lastgroupname.disabled = false;
	}
	// tentative value has passed vetting and we're done using old value, so set new value in global
	js_filtergroups = proposed_filtergroups;
	js_lastvariablegroup = (js_filtergroupshighestallweb) ? (js_filtergroups - 1) : js_filtergroups;
	if (js_filtergroups > 9) {
		displaygroupnames = 0;
		document.getElementById('zeronote').className = 'show';
	} else {
		displaygroupnames = js_filtergroups;
		document.getElementById('zeronote').className = 'hide';
	}
	for (var i=1; i<=9; ++i) {
		newclass = (i <= displaygroupnames) ? 'show' : 'hide';
		document.getElementById('f'+i).className = newclass;
	}
	setupfirstgroup(numberinput.form.filtergroupsdefaultnoweb);
	setuplastgroup(numberinput.form.filtergroupshighestallweb);
}
function marshallforsubmit(theform)
{
	var showsharedlists = theform.showsharedlists;
	var showuniquelists = theform.showuniquelists;
	var showsharedlistslength = showsharedlists.length;
	var showuniquelistslength = showuniquelists.length;
	var sharedlists = theform.sharedlists;
	var uniquelists = theform.uniquelists;
	var stringvar;
	// this includes the DISABLED items in the dropdown lists
	// this is contrary to the usual behavior of a web browser
	// however it's exactly right for our purposes
	stringvar = '';
	for (var i=0; i<showsharedlistslength; ++i) {
		stringvar += ' ' + showsharedlists.options[i].value;
	}
	sharedlists.value = stringvar;
	stringvar = '';
	for (var i=0; i<showuniquelistslength; ++i) {
		stringvar += ' ' + showuniquelists.options[i].value;
	}
	uniquelists.value = stringvar;
}
function moveoption(sourceselect, targetindex, destselect, where)
{
	var sourceselectnumber = (targetindex == 0) ? sourceselect.selectedIndex: targetindex;
	var destselectnumber = destselect.selectedIndex;
	if (sourceselectnumber < 0) {
		alert('Please select the list that should be moved into the other panel.');
		return;
	}
	var movingoption = sourceselect.options[sourceselectnumber];
	var referenceoption;
	if (where < 0) {
		referenceoption = destselect.options[0];
	} else if (where > 0) {
		referenceoption = null;
	} else {
		if (destselectnumber >= 0) {
			var referenceoption = destselect.options[destselectnumber + 1];
		} else {
			var referenceoption = null;
		}
	}
	sourceselect.remove(sourceselectnumber);
	destselect.add(movingoption, referenceoption);
}
function changeshowlistslegends(currentoption)
{
	var whichone = currentoption.value;
	document.getElementById('sharednestedlegend').className = (whichone == 1) ? 'show' : 'hide';
	document.getElementById('sharedseparatelegend').className = (whichone == 2) ? 'show' : 'hide';
	document.getElementById('sharedcommonlegend').className = (whichone == 3) ? 'show' : 'hide';
	document.getElementById('uniquenestedlegend').className = (whichone == 1) ? 'show' : 'hide';
	document.getElementById('uniqueseparatelegend').className = (whichone == 2) ? 'show' : 'hide';
	document.getElementById('uniquecommonlegend').className = (whichone == 3) ? 'show' : 'hide';
}
