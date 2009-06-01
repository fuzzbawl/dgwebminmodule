#!/usr/bin/perl
# editplugconf.cgi


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
our $pagename = "$text{'index_viewedit'} $text{'index_editplugconf'}";
&webminheader();

# Make sure user has access to this functionality
&checkmodauth('editplugconf');

# Check if DansGuardian conf file is there
if (! &checkdgconf) {
    print "<span style='color: brown'>$text{'error_confnotfound'}<br>($text{'index_location'}: " . &group2conffilepath(0) . ")</span><p>\n";
}

print "<br><br><center>($text{'error_changeseldom'})</center><br>\n";

our @filecolumns = ('List', 'List Location', '');
print &ui_columns_start(\@filecolumns);

## Files for all versions
our @configuration_files = ('authplugin', 'downloadmanager', 'contentscanner');

foreach my $conf_file (@configuration_files) {
    &edit_file_row($conf_file, 0, $conf_file, $return);
}

print &ui_columns_end();
## End of tabs

print &ui_tabs_end(1);
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
    &ui_print_header($pagename, $text{'index_title'}, undef, 'editplugconf', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}

