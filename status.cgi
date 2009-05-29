#!/usr/bin/perl

# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
require './dansguardian-lib.pl';
use warnings;
use strict qw(subs vars);

our $action = $in{'action'};
$action = 'status' if ! $action;

our $forceflag =0;	# default
$forceflag = 1 if (($action eq 'start') || ($action eq 'restart') || ($action eq 'reload'));
$forceflag = -1 if ($action eq 'stop');

&webminheader();

&dgprocess($action);

# double-check
#  (especially useful when `dansguardian -g` fails silently)
if (($action eq 'start') || ($action eq 'restart') || ($action eq 'reload')) {
    &checkdgisrunning();
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
    &ui_print_header($text{"${action}_title"}, $text{'index_title'}, undef, 'status', 1, 0, 0, &restart_button($forceflag).'<br>'.&help_search_link("dansguardian", "man"), undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}

