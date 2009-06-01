#!/usr/bin/perl
# viewfiltergroups.cgi


# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
our (%sharedgroupsconfigurationlists, %notsharedgroupsconfigurationlists);
require './dansguardian-lib.pl';
use POSIX;
use warnings;
use strict qw(subs vars);
our $pagename = $text{'index_viewfiltergroups'};
our $return = 'index.cgi';	# after this, go clear back to main


&bailifcallercancelled();


# read variables from config
our $filtergroups= &readconfigoptionlimited('filtergroups', 0);
our $filtergroupsschemelists = &readconfigoptionlimited('filtergroupsschemelists', 0);
our $filtergroupsdefaultnoweb = &readconfigoptionlimited('filtergroupsdefaultnoweb', 0);
our $filtergroupshighestallweb = &readconfigoptionlimited('filtergroupshighestallweb', 0);
for (my $i=1; $i<=99; ++$i) {
    my $variablename = "groupnamef$i";
    $$variablename = ($i <= $filtergroups) ? &readconfigoptionlimited('groupname', $i) : '';
}

our $nestedclass = 'other';
$nestedclass = 'chosen' if $filtergroupsschemelists == 1;
our $separateclass = 'other';
$separateclass = 'chosen' if $filtergroupsschemelists == 2;
our $commonclass = 'other';
$commonclass = 'chosen' if $filtergroupsschemelists == 3;
our $defaultnoclass = 'other';
$defaultnoclass = 'chosen' if $filtergroupsdefaultnoweb ne 'on';
our $defaultyesclass = 'other';
$defaultyesclass = 'chosen' if $filtergroupsdefaultnoweb eq 'on';
our $highestnoclass = 'other';
$highestnoclass = 'chosen' if $filtergroupshighestallweb ne 'on';
our $highestyesclass = 'other';
$highestyesclass = 'chosen' if $filtergroupshighestallweb eq 'on';


&webminheader();



# check error conditions (some continue, others exit)

# Make sure user has access to this file
&checkmodauth('viewfiltergroups');

# Check if DansGuardian conf file is there
if (! &checkdgconf) {
    print "<span style='color: red'>$text{'error_confnotfound'}<br>($text{'index_location'}: " . &group2conffilepath(0) . ")</span><p>\n";
    &showackandret();
    &webminfooterandexit();
}

if (! $filtergroupsschemelists) {
    if ($filtergroups != 1) {
        print "<p><span style='color: magenta'>$text{'error_foreignschemealready'}</span></p>\n";
    } else {
        print "<p><span style='color: magenta'>$text{'error_noschemealready'}</span><p>\n";
    }
    &showackandret();
    &webminfooterandexit();
}

if ($filtergroups == 1) {
    print "<p><span style='color: magenta'>$text{'error_changedscheme'}</span><p>\n";
    &showackandret();
    &webminfooterandexit();
}

# the following CSS instructions _must_ be present in order for the Javascript to work correctly
print "<style type=text/css>\n";
print ".hide { visibility: hidden; display: none; }\n";
print ".chosen { visibility: visible; background-color: #ffffd0; color: #181818; }\n";
print ".other { visibility: visible; background-color: #e8e8e8; color: #989898; }\n";
print "</style>\n";

print <<"EOF1";
<h3>Multiple Filter Groups Scheme</h3>
<h5>
EOF1
print &hlink('Overall Scheme', 'filtergroupsschemelists');
print <<"EOF2";
</h5>
<table border=0 cellpadding=10 cellspacing=0>
<tr>
<td align=right class=$nestedclass>nested</td><td style='padding-right: 3em' class=$nestedclass>&nbsp;</td><td width=500 class=$nestedclass>
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
<td align=right class=$separateclass>separate</td><td style='padding-right: 3em' class=$separateclass>&nbsp;</td><td class=$separateclass>
Each filter group will have its
own completely independent lists, which will neither affect nor be
affected by any other filter group. 
</td>
</tr>
<tr>
<td align=right class=$commonclass>common</td><td style='padding-right: 3em' class=$commonclass>&nbsp;</td><td class=$commonclass>
Each filter group will have its own lists,
yet each will <u>also</u> reference a list which is common
to all filter groups. In other words there are common
"base" lists on which each filter group elaborates.
</td>
</tr>
</table>
<h5>
EOF2
print &hlink('Use of Default Group', 'filtergroupsdefaultnoweb');
print <<"EOF3";
</h5>
<table border=0 cellpadding=10 cellspacing=0>
<tr>
<td width=40 class=$defaultyesclass>&nbsp;</td>
<td align=middle style='padding-right: 3em;' class=$defaultyesclass>&nbsp;
</td>
<td width=500 class=$defaultyesclass>
The default filter group (f1) has no web access. 
Unexpected or improperly configured users aren't able to use anything
until they see you to get the problem corrected.
</td></tr>
<td class=$defaultnoclass>&nbsp;</td><td class=$defaultnoclass>&nbsp;</td>
<td width=500 class=$defaultnoclass>
The default filter group [f1] is just like
any higher numbered filter group
and can be used for anything.
</td></tr></table>
<h5>
EOF3
print &hlink('Set Aside Unrestricted Group', 'filtergroupshighestallweb');
print <<"EOF4b";
</h5>
<table border=0 cellpadding=10 cellspacing=0>
<tr>
<td width=40 class=$highestyesclass>&nbsp;</td>
<td align=middle style='padding-right: 3em;' class=$highestyesclass>&nbsp;
</td>
<td width=500 class=$highestyesclass>
The highest numbered filter group is reserved to have access to all the web.
</td></tr>
<tr><td class=$highestnoclass>&nbsp;</td><td class=$highestnoclass>&nbsp;</td>
<td width=500 class=$highestnoclass>
The highest numbered filter group is just like
any lower numbered filter group
and can be used for anything.
</td></tr></table>
<br><br><hr><br><br>
<h3>Filter Groups</h3>
<table border=0 cellspacing=0 cellpadding=15 class=chosen><tr><td>
<h5>Number of Filter Groups: <big>$filtergroups</big></h5>
</td></tr></table>
EOF4b
if ($filtergroups <= 9) {
    print "<h5>Filter Group Names</h5>\n";
    print "<table border=0 cellspacing=0 cellpadding=15 class=chosen><tr><td>\n";
    for (my $i=1; $i<=$filtergroups; ++$i) {
        my $variablename = "groupnamef$i";
        print "<small>Name of Filter Group f$i:</small> $$variablename<br>\n";
    }
} else {
    print <<EOF4c;
<table border=0 cellspacing=0 cellpadding=15 class=chosen><tr><td>
There are more than nine Filter Groups, 
so we've just assigned the names "f1"..."f9"..."f99".
EOF4c
}
print <<EOF4;
</td></tr></table>
<br><br><hr><br><br>
<h3>Shared-vs.-Individual Lists</h3>
<table border=0 cellspacing=10 cellpadding=0>
<tr>
<th align=center valign=bottom width=350>
<p>One Copy Of These Lists Is Shared By All Groups
</th>
<th>&nbsp;</th>
<th align=center valign=bottom width=350>
<p>Each Group Has Its Own Copy Of These Lists<br>
<small>(which may in turn be related to other filter groups)</small>
</th>
</tr>
<tr>
<td align=center>
<select size=28 style='width: 12em' name=showsharedlists id=showsharedlists class=chosen>
EOF4
foreach my $option (sort bytype keys %sharedgroupsconfigurationlists) {
    print "<option>$option</option>\n";
}
print <<EOF5;
</select>
</td>
<td valign=middle nowrap width=10>&nbsp;</td>
<td align=center>
<select size=28 style='width: 12em' name=showuniquelists id=showuniquelists class=chosen>
EOF5
foreach my $option (sort bytype keys %notsharedgroupsconfigurationlists) {
    print "<option>$option</option>\n";
}
print <<EOF6;
</select>
</td>
</tr>
</table>
<p align=center>
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

&showackandret();

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
    &ui_print_header($pagename, $text{'index_title'}, undef, 'viewfiltergroups', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}
