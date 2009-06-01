#!/usr/bin/perl
# searchinput.cgi

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
our $pagename = $text{'index_search'};

# if we're just being returned to, pass it through to our parent
&passthroughautoreturn();

&webminheader();

# Make sure user has access to this file
&checkmodauth('search');

# Check if DansGuardian conf file is there
if (! &checkdgconf) {
    print "<span style='color: brown'>$text{'error_confnotfound'}<br>($text{'index_location'}: " . &group2conffilepath(0) . ")</span><p>\n";
}

# Check if files to be searched seem to be there
our $confdir = &canonicalizefilepath($config{'conf_dir'});
our $blacklistpath = &canonicalizefilepath("$confdir/lists/blacklists");
our $phraselistpath = &canonicalizefilepath("$confdir/lists/phraselists");
if ((! -r $blacklistpath) || (! -r $phraselistpath)) {
    print "<span style='color: brown'>$text{'error_listsnotfound'}<br>$text{'search_questionable'}</span><p>\n";
}

#########################################################################
#
#    THE MEAT
#
#########################################################################
print "<br><br><form action='search.cgi' method=post name=theform id=theform>\n";
print "<table border=0 cellpadding=5 cellspacing=0>\n";
print "<tr><td></td><td width=25></td>";
print "<td align=center colspan=2>$text{'search_interpret'}:</td></tr>\n";
print "<td align=center valign=middle>";
print "$text{'search_input'}:<br><br>";
print "<input type=text name=search size=40 maxsize=80>";
print "</td><td></td>\n";
print "<td align=right>\n";
print "<input type=radio name=interpret value=detect checked><br><br>\n";
print "<input type=radio name=interpret value=permute><br>\n";
print "<input type=radio name=interpret value=phrase><br>\n";
print "<input type=radio name=interpret value=domain><br>\n";
print "<input type=radio name=interpret value=url><br>\n";
print "<input type=radio name=interpret value=regexp><br>\n";
print "<input type=radio name=interpret value=modify><br>\n";
print "</td><td align=left>\n";
print "$text{'search_detect'}<br><br>\n";
print "$text{'search_permute'}<br>\n";
print "$text{'search_phrase'}<br>\n";
print "$text{'search_domain'}<br>\n";
print "$text{'search_url'}<br>\n";
print "$text{'search_regexp'}<br>\n";
print "$text{'search_modify'}<br>\n";
print "</td></tr>\n";
print "<tr><td colspan=4>&nbsp;</td></tr>\n";
print "<tr><td align=center colspan=3>";
print "<input type=submit name=button value='$text{'button_search'}'></td></tr>\n";
print "</table>\n";
print "<input type=hidden name=return value='$return'>\n";
print "</form><br><br>\n";


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
    &ui_print_header($pagename, $text{'index_title'}, undef, 'search', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, 'onLoad="document.theform.search.focus();"', "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}
