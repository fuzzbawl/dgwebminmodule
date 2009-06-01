#!/usr/bin/perl
# setupfiltergroupsinput.cgi


# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
our (%groupsconfigurationlists, %sharedgroupsconfigurationlists, %notsharedgroupsconfigurationlists);
our (%sharedonlynestedconfigurationlists, %sharedonlyseparateconfigurationlists, %sharedonlycommonconfigurationlists);
our ($EFFECTIVE_USER_ID);
require './dansguardian-lib.pl';
use POSIX;
use warnings;
use strict qw(subs vars);
our $pagename = $text{'index_setupfiltergroups'};
our $return = 'index.cgi';	# after this, go clear back to main as this is a one-time process


&bailifcallercancelled();


&webminheader();



# check error conditions (some continue, others exit)

# Make sure user has access to this file
&checkmodauth('setupfiltergroups');

# check if running as root
if ($EFFECTIVE_USER_ID == 0) {
    print "<p><span style='color: brown'>$text{'error_superuser'}</span><br>\n";
}

# Check if DansGuardian conf file is there
if (! &checkdgconf) {
    print "<span style='color: magenta'>$text{'error_confnotfound'}<br>($text{'index_location'}: " . &group2conffilepath(0) . ")</span><p>\n";
    &showackandret();
    &webminfooterandexit();
}

# check if number of filter groups is more than one
our $filtergroups = &readconfigoptionlimited('filtergroups', 0);
if ($filtergroups > 1) {
    print "<p><span style='color: brown'>$text{'error_multiplefgs'}</span><br>\n";
}

# check if multiple filter groups scheme already set up
our $filtergroupsschemelists = &readconfigoptionlimited('filtergroupsschemelists', 0);
if ($filtergroupsschemelists) {
    print "<p><span style='color: magenta'>$text{'error_schemealready'}</span><br>\n";
    &showackandret();
    &webminfooterandexit();
}

# do not do such a major reconfiguration when running
if (&dgisrunning()) {
    print "<p><span style='color: red'>$text{'error_running'}</span><br>\n";
    &showackandret();
    &webminfooterandexit();
}

# data that we own but pass to the client-side scripting for use
# (this depends on all Javascript portions sharing the same namespace
#  so variables set up in any portion are available to all other portions too> 
# these are lists of items that _must_ not be in the unique category for various schemes
print "<script type=text/javascript>\n";
print "var sharedonlynested = new Array ( ";
our $atleastoneitemoutput = 0;
foreach my $list (keys %sharedonlynestedconfigurationlists) {
    print "," if $atleastoneitemoutput;
    print " '$list' ";
    $atleastoneitemoutput = 1;
}
print ");\n";
$atleastoneitemoutput = 0;
print "var sharedonlyseparate = new Array ( ";
foreach my $list (keys %sharedonlyseparateconfigurationlists) {
    print "," if $atleastoneitemoutput;
    print "'$list', ";
    $atleastoneitemoutput = 1;
}
print ");\n";
$atleastoneitemoutput = 0;
print "var sharedonlycommon = new Array ( ";
foreach my $list (keys %sharedonlycommonconfigurationlists) {
    print "," if $atleastoneitemoutput;
    print "'$list', ";
    $atleastoneitemoutput = 1;
}
print ");\n";
print "var restrictionarrays = new Array ( 'zerothentryforerror', sharedonlynested, sharedonlyseparate, sharedonlycommon );\n";
print "</script>\n";

# the following CSS instructions _must_ be present in order for the Javascript to work correctly
print "<style type=text/css>\n";
print ".hide { visibility: hidden; display: none; }\n";
print ".show { visibility: visible; }\n";
print "</style>\n";

print <<EOF1;
<br><br><hr><br><br>
<form name=theform id=theform action=setupfiltergroups.cgi method=POST onSubmit="this.groupnamef1.disabled=false;if(js_filtergroups<=9){this.eval('groupnamef' + js_filtergroups).disabled=false;};marshallforsubmit(this);return checkinput(this);">
<input type=hidden name=return value='$return'>
<h3>Step 1: Choose Multiple Filter Groups Scheme</h3>
<h5>Step 1a: Choose 
EOF1
print &hlink('Overall Scheme', 'filtergroupsschemelists');
print <<EOF2;
</h5>
<table border=0 cellpadding=0 cellspacing=8>
<tr>
<td align=right>nested</td><td style='padding-right: 3em'><input type=radio name=filtergroupsschemelists value=1 checked onClick="adjustlistslist(this);changeshowlistslegends(this);"></td><td width=500>
Each list file affects not only
its own filter group but also all other filter groups
below (or above) it. So for example if your filter groups are 
"temps", "employees", "managers", and "executives", any 
change to the exception... lists for "managers" will also 
automatically affect "executives", and any changes to the
banned... lists for "managers" will also automatically
affect "employees" and "temps".
</td>
</tr>
<tr>
<td align=right>separate</td><td style='padding-right: 3em'><input type=radio name=filtergroupsschemelists value=2 onClick="adjustlistslist(this);changeshowlistslegends(this);"></td><td>
Each filter group will have its
own completely independent lists, which will neither affect nor be
affected by any other filter group. 
</td>
</tr>
<tr>
<td align=right>common</td><td style='padding-right: 3em'><input type=radio name=filtergroupsschemelists value=3 onClick="adjustlistslist(this);changeshowlistslegends(this);"></td><td>
Each filter group will have its own lists,
yet each will <u>also</u> reference a list which is common
to all filter groups. In other words there are common
"base" lists on which each filter group elaborates.
</td>
</tr>
</table>
<input type=hidden name=filtergroupsschemelists_set value=on>
<h5>Step 1b: Choose 
EOF2
print &hlink('Use of Default Group', 'filtergroupsdefaultnoweb');
print <<EOF3;
</h5>
<table border=0 cellpadding=0 cellspacing=10>
<tr>
<td width=40></td>
<td align=middle style='padding-right: 3em;'>
<input type=checkbox name=filtergroupsdefaultnoweb value=on checked onChange="setupfirstgroup(this)">
</td>
<td width=500>
Check for default group to have no web access. 
Unexpected or improperly configured users won't be able to use anything
until they see you to get the problem corrected.
<br><br>
(Not checked means you can use the Default Group [f1] 
for the majority of your users,
or anything else you wish.)
</td></tr></table>
<input type=hidden name=filtergroupsdefaultnoweb_set value=on>
<h5>Step 1c: Choose 
EOF3
print &hlink('To Set Aside Unrestricted Group', 'filtergroupshighestallweb');
print <<EOF4;
</h5>
<table border=0 cellpadding=0 cellspacing=10>
<tr>
<td width=40></td>
<td align=middle style='padding-right: 3em;'>
<input type=checkbox name=filtergroupshighestallweb value=on checked onChange="setuplastgroup(this)">
</td>
<td width=500>
Check to reserve highest group to have access to all the web.
<br><br>
(Not checked means the highest numbered filter group will be just like
any lower numbered filter group
and you can use it for anything you wish.)
</td></tr></table>
<input type=hidden name=filtergroupshighestallweb_set value=on>
<br><br><hr><br><br>
<h3>Step 2: Choose Filter Groups</h3>
<h5>Step 2a: Number of Filter Groups</h5>
<input type=text name=filtergroups size=2 value=5 onKeyup="inputtonumberofgroups(this)">
<input type=hidden name=filtergroups_set value=on>
<h5>Step 2b: Name of Each Filter Group</h5>
<p id=zeronote>You've specified more than nine Filter Groups, 
so rather than asking you to specify a name for each one,
we'll just assign to them the names "f1"..."f9"..."f99".
<div id=f1>Name of Filter Group f1:&nbsp;<input type=text size=25 name=groupnamef1></div>
<div id=f2>Name of Filter Group f2:&nbsp;<input type=text size=25 name=groupnamef2></div>
<div id=f3>Name of Filter Group f3:&nbsp;<input type=text size=25 name=groupnamef3></div>
<div id=f4>Name of Filter Group f4:&nbsp;<input type=text size=25 name=groupnamef4></div>
<div id=f5>Name of Filter Group f5:&nbsp;<input type=text size=25 name=groupnamef5></div>
<div id=f6>Name of Filter Group f6:&nbsp;<input type=text size=25 name=groupnamef6></div>
<div id=f7>Name of Filter Group f7:&nbsp;<input type=text size=25 name=groupnamef7></div>
<div id=f8>Name of Filter Group f8:&nbsp;<input type=text size=25 name=groupnamef8></div>
<div id=f9>Name of Filter Group f9:&nbsp;<input type=text size=25 name=groupnamef9></div>
<br><br><hr><br><br>
<h3>Step 3: Choose Shared-vs.-Individual Lists</h3>
<input type=hidden name=sharedlists>
<input type=hidden name=uniquelists>
<table border=0 cellspacing=10 cellpadding=0>
<tr>
<th align=right valign=bottom width=250>
<p id=sharednestedlegend>Only One Copy Of These Lists Will Be Shared By All Filter Groups
<p id=sharedseparatelegend>Only One Copy Of These Lists Will Be Shared By All Filter Groups
<p id=sharedcommonlegend>Only One Copy Of These Lists Will Be Shared By All Filter Groups
</th>
<th>&nbsp;</th>
<th align=left valign=bottom width=250>
<p id=uniquenestedlegend>Each Filter Group's Own List Will Be Added To Adjacent Filter Groups
<p id=uniqueseparatelegend>Each Filter Group Will Have Its Own Completely Independent List
<p id=uniquecommonlegend>Each Filter Group Will Have Its Own List Which Builds From A Common List
</th>
</tr>
<tr>
<td align=right>
<select size=28 style='width: 12em' name=showsharedlists id=showsharedlists>
EOF4
our $discriminator = qr/(exception(?!file)|banned|grey|weighted).*(site|url|regexpurl|phrase)/;
foreach my $option (sort bytype keys %groupsconfigurationlists) {
    next if $option =~ $discriminator;
    print "<option>$option</option>\n";
}
print <<EOF5;
</select>
</td>
<td valign=middle nowrap>
<input type=submit name=button value='&larr;' style='font-size: x-large' onClick="moveoption(this.form.showuniquelists, 0, this.form.showsharedlists, 0);return false;">&nbsp;&nbsp;
<br><br>
&nbsp;&nbsp;<input type=submit name=button value='&rarr;' style='font-size: x-large' onClick="moveoption(this.form.showsharedlists, 0, this.form.showuniquelists, 0);return false;">
</td>
<td align=left>
<select size=28 style='width: 12em' name=showuniquelists id=showuniquelists>
EOF5
foreach my $option (sort bytype keys %groupsconfigurationlists) {
    next if $option !~ $discriminator;
    print "<option>$option</option>\n";
}
print <<EOF6;
</select>
</td>
</tr>
</table>
<p align=center>
<span style='font-size: smaller'>(use the arrow buttons to move lists back and forth between the two panes above until your choices are accurately reflected)</span>
<br><br><hr><br><br>
<input type=submit name=button value="$text{'button_proceed'}">
<img src="images/transparent1x1.gif" border=0 width=15>
<input type=submit name=button value="$text{'button_cancel'}" onClick="shutoffcheck();">
</form>
<p><span style='color: green'><span style='font-size: larger'>Once started, this process may take several minutes to complete, please be patient - </span><br>&nbsp;(do not interfere with the process and do not bang on the mouse or keyboard)</span>
<!-- <br><br><hr><br><br> -->
EOF6

# section presenting master->slaves scaffolding files
print <<EOF7;
<p>&nbsp;<p><hr><p><hr><center><div style='margin-left: 80px; margin-right: 80px; margin-top: 15px; margin-bottom: 15px; font-size: 85%; color: #998'>
<p>$text{'view_masterslavesfiles_title'}
<p>Multiple filter groups and master&rArr;slaves systems are largely orthogonal.
You can have either one without the other.
But they appear together often enough, this seems a good place to offer some
support for setting up a master&rArr;slaves configuration
in the form of these example files.
<p>To download the files through your browser, 
right-click on each link and select 'save link as...' from the menu.
<br><span style='font-size: 90%'>(If you want to 'view' a file rather than download it, 
start by left-clicking on the link, 
view the file, then click your browser's 'back' button when you're done.)</span>
<p><a href=scaffold/rsyncenabledaemon.scaffold>$text{'view_masterenablefile_link'}</a>
<br><a href=scaffold/rsyncconfdaemon.scaffold>$text{'view_masterconffile_link'}</a>
<br><a href=scaffold/rsyncidentdaemon.scaffold>$text{'view_masteridentfile_link'}</a>
<br><a href=scaffold/rsyncslavesupdate.scaffold>$text{'view_slavesfile_link'}</a>
<p>After obtaining the example files, make a copy of them and edit as necessary.
<p></div></center><hr>
EOF7

# Load all the client-side scripting that makes this particular page work
&loadschemejslib();

################# end #####################

&webminfooterandexit();

###########################################################################
#
#    UTILITY SUBROUTINES
#
###########################################################################

################
sub webminheader
################
{
    &ui_print_header($pagename, $text{'index_title'}, undef, 'setupfiltergroups', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, 'onLoad="initform();document.theform.filtergroupsschemelists[0].focus();"', "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}
