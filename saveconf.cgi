#!/usr/bin/perl
# saveconf.cgi

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
our $conffilepath = $in{'conffilepath'};
our $configsection = $in{'configsection'};
our $button = $in{'button'};
our $group = $in{'group'};


(our $label, undef) = split ' ', $text{'button_cancelchange'};
if ((our $button =~ m/$label/i) or ($in{'invoke'} =~ m/cancel/)) {
	our $rawreturnto = &un_urlize($in{'return'});
        $rawreturnto .= ($rawreturnto !~ m/\?/) ? '?' : '&';
	$rawreturnto .= 'invoke=cancelreturn';
	&redirect($rawreturnto);
	exit;
}

&webminheader();


# Make sure user is allowed to edit conf first
&checkmodauth('editconf') if $group == 0;
&checkmodauth('editgroupsconf') if $group != 0;


# Check if DansGuardian conf file is there
&checkdgconf();


# read the file lines (or get a reference to them if already read)
#  (most likely the main config file really was already read... but we're not sure,
#   and more importantly none of the group config files have been read)
#  (it's a red herring thinking that the file was probably already read after all,
#   as that was in a previous program, not this one)
our $cfref = &read_file_lines_just_once($conffilepath);

# following is a _very_large_ subroutine which in fact does almost all the work
our $lineschanged = &update_config_lines(\%in, $cfref);

if ($lineschanged > 0) {
    # write out the modified version of the dansguardian.conf file

    # but first, make a backup copy
    &makebackupcopy($conffilepath);

    #  (note documentation of following function is wrong,
    #   it actually requires an argument which is the filename to be flushed)
    &flush_file_lines($conffilepath);
    print "<p>$text{'saveconf_configfile'}: $conffilepath<br>\n";

    &handlerefresh($conffilepath);
} else {
    print "<p>$text{'saveconf_noupdate'}<br>\n";
}

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
    &ui_print_header("$text{'saveconf_title'}", $text{'index_title'}, undef, undef, 0, 1, 1, &restart_button, undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
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
        &ui_print_footer('index.cgi', $text{'index_return'}, 'editconf.cgi', "$text{'index_viewedit'} $text{'index_editconf'}", 'editgroupsconf.cgi', "$text{'index_viewedit'} $text{'index_editgroupsconf'}" );
    }

    exit;
}

