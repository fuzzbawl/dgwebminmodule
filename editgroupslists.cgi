#!/usr/bin/perl
# editgroupslists.cgi


# by declaring all the globals we'll reference (including some in our own
#  libraries) _before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
our (%sharedgroupsconfigurationlists, %notsharedgroupsconfigurationlists);
use POSIX;
require './dansguardian-lib.pl';
use warnings;
use strict qw(subs vars);
&passthroughautoreturn();

our $return = &getcleanreturn();
our $pagename = "$text{'index_viewedit'} $text{'index_editgroupslists'}";


## (Developer Note:)
##  (the "tabs" mechanism is rather brittle- if the list of tabs for the header and the
##   tabs actually created don't _exactly_ match, the system will go so awry it's unusable)


&webminheader();

# Check user acl
&checkmodauth('editgroupslists');

# Check if the right version
if (!(&checkdgver())) {
    print "<span style='color: brown'>$text{'error_version_notsupp'}<br>$text{'index_modulever'} $modulever $text{'index_moduleversupports'}<br>$text{'index_dgversion'} $dg_version<p>\n";
}

## build "tabs" definitions
# first get a couple config values we'll need
our $filtergroups = &readconfigoptionlimited('filtergroups', 0);
$filtergroups = 1 if ! $filtergroups;	# option might not be set!
our $filtergroupsschemelists = &readconfigoptionlimited('filtergroupsschemelists', 0);
$filtergroupsschemelists = 0 if ! $filtergroupsschemelists;	# option might not be set!
our $firstgroupmode = &readconfigoptionlimited('groupmode', 1);
our $firstvariablegroup = ($firstgroupmode == 1) ? 1 : 2;


# start with no tabs
our @tabs = ();

# set up all the active filter groups at once
#  (special handling for none/all are in subroutines &getgroupheading and &getgrouplists_hashref)
our @groups = ( 1 .. $filtergroups );
@groups = map { [ $_, &getgrouptitle($_), '', &getgroupheading($_, 'lists'), &getgrouplists_hashref($_) ] } ( @groups );

# add the whole list of filter group tabs to our master list of tabs
push @tabs, @groups;

if (($filtergroupsschemelists == 1) && (scalar keys %notsharedgroupsconfigurationlists > 0)) {
    &addseparator();
    # for 'nested', lowest level
    push @tabs, [ -1, 'all', '', 'start of all nested filter groups', \%notsharedgroupsconfigurationlists ];
}

if (($filtergroupsschemelists == 3) && (scalar keys %notsharedgroupsconfigurationlists > 0)) {
    &addseparator();
    # for 'common', base
    push @tabs, [ -1, 'base', '', 'filter groups build on this common base', \%notsharedgroupsconfigurationlists ];
}

if ($filtergroupsschemelists && (scalar keys %sharedgroupsconfigurationlists > 0)) {
    &addseparator();
    push @tabs, [ -2, 'shared', '', 'used directly <span style=\'font-size: 80%; font-style: italic\'>(not via .Include)</span> by all filter groups', \%sharedgroupsconfigurationlists ];
}


# display important notes to the user
print "<p>$text{'edit_note_sharedlists'}<br>";
if ($config{'show_fixedlists'}) {
    print "$text{'edit_note_fixedlists'}<br>";
} else {
    print "$text{'edit_note_nofixedlists'}<br>";
}
print "<p>\n";

our $initialtab = $in{'initialtab'};
our $initialtabindex = (($firstvariablegroup-1) <= $#tabs) ? ($firstvariablegroup-1) : $#tabs;
$initialtab = $tabs[$initialtabindex][0] if ! $initialtab;
# following line is the minimal that works, line below that is how it used to be
#  (note we must already have a complete list of tabs by here, else tabs display goes awry)
#  (the third parameter is the handle of the initially selected tab)
print &ui_tabs_start(\@tabs);

# replace the function the system gave us with a slightly modified one,
#  and define an additional useful function of our own
# this works with Firefox, but behaves very strangely with IE
#  IE with this if one pre-clicks a tab aborts the page entirely and returns to the previous page
#  as this too has the effect of preventing mistakes from pre-clicking we'll leave it
print <<EOF;
    <script type='text/javascript'>
    // 'global' variable
    var tabslinksenabled = false;

    // slightly modify existing function
    var oldfunction = '' + select_tab + '';	// odd syntax forces this to be a "string" variable
    var revisedfunction = oldfunction.replace(/{/, '{ if (!tabslinksenabled) { return; } ');
    // strangeness with split 'tags' below is to avoid 
    //  having them interpreted too soon, leading to non-functionality and syntax errors
    document.write('<scr' + 'ipt type="text/javascript">' + revisedfunction + '</scr' + 'ipt>');

    // add another useful function of our own
    function onDelayedLoad()
    {
        tabslinksenabled = true;
        select_tab('', "$initialtab");
    }
    </script>
EOF

foreach my $tabref (@tabs) {
    ## all the setup work was done above and all the display is in a subroutine for which _all_ args are available, 
    ##  so we can just reel off the tabs

    ## show conf display
    &createatab($tabref);
}

## end of tabs ##

print &ui_tabs_end(1);

&webminfooterandexit();


###########################################################################
#
#    UTILITY SUBROUTINES
#
###########################################################################

{
# simulate "static" variable
our $haveseparator = 0;

################
sub addseparator
################
{
    # do it just once the first time, if called again just return without doing anything
    return if $haveseparator++;

    # add a "separator" tab (no contents, not selectable)
    push @tabs, [ -99, '', "", '', undef ];
}

}

##############
sub createatab
##############
{
    my ($tabinfoarrayref) = @_;

    ## show conf display
    my $groupnum = $$tabinfoarrayref[0];
    my $tabhandle = $groupnum;
    my $groupname = $$tabinfoarrayref[1];
    my $groupheading = $$tabinfoarrayref[3];
    my $contentshashref = $$tabinfoarrayref[4];

    print &ui_tabs_start_tab(undef, $tabhandle);
    &edit_options_formtable_start($tabinfoarrayref);

    ## Files for this tab (mostly a filter group)

    my $tabreturn = $return;
    $tabreturn .= '%3F' if ($tabreturn !~ m/%3[fF]/);
    $tabreturn .= '%26' if ($tabreturn !~ m/(?:%3[fF]|%26)$/);
    $tabreturn .= "initialtab%3D$tabhandle";
    foreach my $conf_file (sort bytype keys %$contentshashref) {
        &edit_file_row($conf_file, $groupnum, $conf_file, $tabreturn);
    }

    &edit_options_formtable_end(-1);	# (no buttons)
    print &ui_tabs_end_tab();
}

################
sub webminheader
################
{
    &ui_print_header($pagename, $text{'index_title'}, undef, 'editgroupslists', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, 'onLoad="setTimeout(\'onDelayedLoad()\', 750)"', "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}
