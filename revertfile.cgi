#!/usr/bin/perl
# revertfile.cgi

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
our $revertfilepath = $in{'revertfilepath'};


&bailifcallercancelled();


&webminheader();

# check error conditions
if ((! $revertfilepath) || (! -e $revertfilepath)) {
    print "<span style='color: brown'>$text{'error_notselected'}</span><br>\n";
    &showackandret();
    &webminfooterandexit();
}

if (! &accessfile($revertfilepath)) {
    print "<p><span style='color: red'>$text{'error_notauthfile'}<br>$text{'index_location'}: $revertfilepath</span><p>\n";
    &showackandret();
    &webminfooterandexit();
}

&revertfile($revertfilepath, 'showmessages');

&handlerefresh($revertfilepath);

&showackandret();

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
    &ui_print_header($text{'revertfile_title'}, $text{'index_title'}, undef, undef, 0, 1, 1, &restart_button, undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    if (exists $in{'return'}) {
        # we have a specific return, issue a message then don't display any manual returns
        &ui_print_footer();	# entirely omit/suppress the return arrow
    } else {
        # no particular return specified, so supply user with lots of manual choices
        &ui_print_footer('index.cgi', $text{'index_return'}, 'editconf.cgi', "$text{'index_viewedit'} $text{'index_editconf'}", 'editplugconf.cgi', "$text{'index_viewedit'} $text{'index_editplugconf'}", 'editlists.cgi', "$text{'index_viewedit'} $text{'index_editlists'}" );
    }

    exit;
}
