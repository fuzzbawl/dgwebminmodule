#!/usr/bin/perl
# editfiltegroupassignments.cgi


# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
our (%mainconfigurationlists, %groupsconfigurationlists);
our (%sharedgroupsconfigurationlists, %notsharedgroupsconfigurationlists);
our (%sharedonlynestedconfigurationlists, %sharedonlyseparateconfigurationlists, %sharedonlycommonconfigurationlists);
our ($EFFECTIVE_USER_ID);
require './dansguardian-lib.pl';
use POSIX;
use warnings;
use strict qw(subs vars);
our $return = &getcleanreturn();
our $pagename = "$text{'index_viewedit'} $text{'index_editfiltergroupassignments'}";

# if we're just being returned to, pass it through to our parent
&passthroughautoreturn();

&webminheader();

# Check user acl
&checkmodauth('editfiltergroupassignments');

our $userfilepath = &canonicalizefilepath("$config{'conf_dir'}/lists/filtergroupslist");
if (! (-e $userfilepath)) {
    print "<p><span style='color: brown'>$text{'error_fgusernotfound'}<br>($text{'index_location'}: $userfilepath)</span><p>\n";
}
our $computerfilepath = &canonicalizefilepath("$config{'conf_dir'}/lists/authplugins/ipgroups");
if (! (-e $computerfilepath)) {
    print "<p><span style='color: brown'>$text{'error_fgcomputernotfound'}<br>($text{'index_location'}: $computerfilepath)</span><p>\n";
}

our $computerauths = 0;
our $userauths = 0;
our $proxyauths = 0;
our @authlines = &readconfiglinedetails('authplugin');
foreach my $authlineref (@authlines) {
    my $authname = $$authlineref[0];
    my $authvalue = $$authlineref[1];
    next if $authname =~ m/^\s*#/;
    ++$proxyauths if $authvalue =~ m{/proxy-};
    ++$userauths if $authvalue =~ m/(basic|digest|ntlm|ident)\./;
    ++$computerauths if $authvalue =~ m/ip\.conf/;
}

our $useravailable = $userauths ? '' : 'disabled';
our $computeravailable = $computerauths ? '' : 'disabled';

if ((! $userauths) && (! $computerauths)) {
    print "<p><span style='color: magenta'>$text{'error_noauthyet'}</span><p>\n";
}

print "<br><br>\n";

print "<center>\n";

# using 'disabled' on these buttons works and looks okay,
# just need the logic to decide what to do

print "<table border=0 cellpadding=10 cellspacing=0><tr><td width=50% align=right valign=bottom>\n";
print "<form action='./editfile.cgi' method='GET' name=proceeduserform id=proceeduserform>";
print "<input type='hidden' name='file' value='$userfilepath'>";
print "<input type='hidden' name='return' value='$return'>";
print "<input type=submit name=button value='$text{'button_proceed_username'}' $useravailable>";
print "</form>\n";
print "</td><td width=50% align=left valign=bottom name=proceedcomputerform id=proceedcomputerform>\n";
print "<form action='./editfile.cgi' method='GET'>";
print "<input type='hidden' name='file' value='$computerfilepath'>";
print "<input type='hidden' name='return' value='$return'>";
print "<input type=submit name=button value='$text{'button_proceed_computerIP'}' $computeravailable>";
print "</form>\n";
print "</td></tr></table>\n";

print "<form action='./index.cgi' method='GET' name=cancelform id=cancelform>";
print "<input type=submit name=button value='$text{'button_cancel'}'>";
print "</form>\n";

print "<form action='/help.cgi/dansguardian/editfiltergroupassignments' method='GET' name=helpform id=helpform>";
print "<input type=submit name=button value='$text{'button_help'}'>";
print "</form>\n";

print "</center><br><br>\n";


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
    &ui_print_header($pagename, $text{'index_title'}, undef, 'editfiltergroupassignments', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, 'onload="document.helpform.button.focus();"', "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}

