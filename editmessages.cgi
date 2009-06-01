#!/usr/bin/perl
# editlists.cgi


# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
require './dansguardian-lib.pl';
use POSIX;
use warnings;
use strict qw(subs vars);
our $return = &getcleanreturn();
our $pagename = "$text{'index_viewedit'} $text{'index_editmessages'}";

# if we're just being returned to, pass it through to our parent
&passthroughautoreturn();

&webminheader();

# Check user acl
&checkmodauth('editmessages');

if (($config{'messages_path'} =~ m/follow/i) || ($config{'log_format'} =~ m/follow/i)) {
  if (! &checkdgconf) {
    print "<span style='color: brown'>$text{'error_confnotfound'}<br>($text{'index_location'}: " . &group2conffilepath(0) . ")</span><p>\n";
  }
}

our ($languagedir, $language, $filepath);
our $whereisit = $config{'messages_path'};
if (($whereisit =~ m/follow/i) || (! $whereisit)) {
    $languagedir = &getconfigvalue('languagedir');
    $language = &getconfigvalue('language');
    $filepath ="$languagedir/$language/messages";   
} else {
    $filepath = $whereisit;
}
$filepath = &canonicalizefilepath($filepath);
if (! (-e $filepath)) {
	print "<span style='color: brown'>$text{'error_messagesnotfound'}<br>$text{'index_location'}: $filepath</span><p>\n";
}


print "<br><br>\n";

print "<center>\n";

print "<form action='./editfile.cgi' method='GET' name=proceedform id=proceedform>";
print "<input type='hidden' name='file' value='$filepath'>";
print "<input type='hidden' name='return' value='$return'>";
print "<input type=submit name=button value='$text{'button_proceed'}'>";
print "</form>\n";

print "<form action='./index.cgi' method='GET' name=cancelform id=cancelform>";
print "<input type=submit name=button value='$text{'button_cancel'}'>";
print "</form>\n";

print "<form action='/help.cgi/dansguardian/messages' method='GET' name=helpform id=helpform>";
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
    &ui_print_header($pagename, $text{'index_title'}, undef, 'messages', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, 'onLoad="document.helpform.button.focus();"', "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}

