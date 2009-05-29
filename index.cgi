#!/usr/bin/perl
# index.cgi

# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
our ($EFFECTIVE_USER_ID);
# Load module functions
require './dansguardian-lib.pl';
use POSIX;
use warnings;
use strict qw(subs vars);


# initialize our list of modules
our @olinks = ( 'status.cgi', 'logs.cgi', 'searchinput.cgi', 'editconf.cgi', 'editplugconf.cgi', 'editlists.cgi', 'editmessages.cgi', 'editfiltergroupassignments.cgi', 'editgroupsconf.cgi', 'editgroupslists.cgi', 'viewfiltergroups.cgi', 'setupfiltergroupsinput.cgi' );
our @okeeps = @olinks;
our $return = &getcleanreturn();

# Read webmin module ACL
our %access = &get_module_acl();

if (!(&checkwbconf)) {
	&ui_print_header("NO Webmin-DansGuardian CONFIG - INSTALLATION PROBLEM?", "", undef, 0, 0);
	&webminfooterandexit();
}

## Print the Header (start the page)
&webminheader();

# display page title
print "<br><h1 align=center>$text{'index_heading'}</h1>\n";

# make all checks and display all warning messages
if (!(&checkdgbinary)) {
	print "<p>";
	print "<span style='color: brown'>$text{'error_binnotfound'}<br>($text{'index_location'}: $config{'binary_file'})</span><p>\n";
        @okeeps = &prunearrayonly(\@okeeps, [ 'logs.cgi', 'editmessages.cgi', 'searchinput.cgi', 'viewfiltergroups.cgi', 'setupfiltergroupsinput.cgi' ], '');
}

if (!(&checkdgver())) {
	print "<p>";
	print "<span style='color: brown'>$text{'error_version_notsupp'}<br>$text{'index_modulever'} $modulever $text{'index_moduleversupports'}<br>$text{'index_dgversion'} $dg_version<p>\n";
        @okeeps = &prunearrayonly(\@okeeps, [ 'status.cgi', 'logs.cgi', 'editmessages.cgi', 'editfiltergroupassignments.cgi', 'searchinput.cgi', 'viewfiltegroups.cgi', 'setupfiltergroupsinput.cgi' ], '');
}

if (! &checkdgconf) {
    print "<span style='color: brown'>$text{'error_confnotfound'}<br>($text{'index_location'}: " . &group2conffilepath(0) . ")</span><p>\n";
    @okeeps = &prunearrayonly(\@okeeps, [ 'status.cgi', 'logs.cgi', 'editmessages.cgi', 'searchinput.cgi' ], '');
}

if ($EFFECTIVE_USER_ID == 0) {
    print "<p><span style='color: brown'>$text{'error_superuser'}</span><br>\n";
}

our $filtergroupsschemelists = &readconfigoptionlimited('filtergroupsschemelists', 0);
if (defined $filtergroupsschemelists) {
    @okeeps = &prunearraynot(\@okeeps, [ 'setupfiltergroupsinput.cgi' ], '');
}

# Set the arrays for the links, titles, and icons of each option
#
# NOTE: The .cgi file names MUST be the same as the title and icon for the 
# button! There are two exceptions that modify this rule:
# 1) if you put the word edit in front of the filename, i.e. editconf.cgi
#    then all will be ok, as the edit is stripped later.
# 2) if you add the word 'input' at the back of the filename (not the extension),
#    i.e. searchinput.cgi, this will be stripped from icon and title names.
# Otherwise, if you try to get around the rule, problems will occur.

my ($t, $i);
our ($title, $titletext);
our @otitles = map { $t=$_; $t=~s/(input)?.cgi//; "$t" } @olinks;
for(my $i=0; $i<@otitles; $i++) {
  $title = $otitles[$i];
  #$title =~ s/plug//;
  if (!$access{$title}) {
    splice(@otitles, $i, 1);
    splice(@olinks, $i, 1);
    $i--;
  }
  else {
    if (($otitles[$i] =~ m/conf/) || ($otitles[$i] =~ m/lists/) || ($otitles[$i] =~ m/messages/) || ($otitles[$i] =~ m/edit/)) {
        $titletext = "$text{'index_viewedit'} "; 
    } elsif ($otitles[$i] =~ m/view/) {
        $titletext = "$text{'index_view'} ";
    } else {
        $titletext = '';
    }
    $titletext .= $text{"index_$otitles[$i]"};
    $otitles[$i] = $titletext;
  }
}
@olinks = &prunearrayonly(\@olinks, \@okeeps, '#');
our @oicons =  map { $t=$_; $t=~s/cgi/gif/; $t=~s/input\././; $t=~s/^#$/null.gif/; "images/$t" } @olinks;

&icons_table(\@olinks, \@otitles, \@oicons);

&webminfooterandexit();

###########################################################################
#
#    UTILITY SUBROUTINES
#
###########################################################################

##################
sub prunearrayonly
##################
{
    my ($listref, $allowedref, $replaceordelete) = @_;
    # third argument may be either
    #  a) a string, which will be used as the replacement for unallowed items
    #  b) empty string, meaning delete unallowed items entirely
    my @result = ();

    LIST: foreach my $list (@$listref) {
        foreach my $allowed (@$allowedref) {
            if ($list eq $allowed) {
                push @result, $list;
                next LIST;
            }
        }
        # not found in list of keepers, so delete (or replace)
        push @result, $replaceordelete if $replaceordelete;
    }

    return @result;
}

#################
sub prunearraynot
#################
{
    my ($listref, $deniedref, $replaceordelete) = @_;
    # third argument may be either
    #  a) a string, which will be used as the replacement for unallowed items
    #  b) empty string, meaning delete unallowed items entirely
    my @result = ();

    LIST: foreach my $list (@$listref) {
        foreach my $denied (@$deniedref) {
            if ($list ne $denied) {
                push @result, $list;
                next LIST;
            }
        }
        # not found in list of keepers, so just ignore
    }

    return @result;
}

################
sub webminheader
################
{
    &ui_print_header('', $text{'index_title'}, undef, 'index', 1, 1, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    print "<br><br><p align=center>" . &hlink("<span style='color: #77B; font-size: 80%'>($text{'index_enhancements'})</span>", "readme") . "<br>\n";

    &ui_print_footer();	# entirely omit/suppress the return arrow

    exit;
}

