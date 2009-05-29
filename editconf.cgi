#!/usr/bin/perl
# editconf.cgi

# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
use POSIX;
require './dansguardian-lib.pl';
use warnings;
use strict qw(subs vars);
&passthroughautoreturn();

our %access = &get_module_acl();
our $return = &getcleanreturn();
our $pagename = "$text{'index_viewedit'} $text{'index_editconf'}";
our $conffilepath = &group2conffilepath(0);

our $readonly = ! &accessfile($conffilepath);

&webminheader();

# Make sure user has access to this file
&checkmodauth('editconf');

# Check if the right version
if (!(&checkdgver())) {
    print "<span style='color: brown'>$text{'error_version_notsupp'}<br>$text{'index_modulever'} $modulever $text{'index_moduleversupports'}<br>$text{'index_dgversion'} $dg_version<p>\n";
}

# Check if DansGuardian conf file is there
if (! &checkdgconf) {
    print "<span style='color: brown'>$text{'error_confnotfound'}<br>($text{'index_location'}: " . &group2conffilepath(0) . ")</span><p>\n";
}

# Load dynamic settings scripts
&loadeditjslib();

# list of tabs
our @tabs = qw( network process logging reporting content phrase updownload plugins );
push @tabs, '', 'allgroups' if &sharedoptionsavailable();

# lists of which options go on which tabs
# every option is listed exactly once
our @networktaboptions = qw( filterip filterport proxyip proxyport forwardedfor usexforwardedfor maxips );
our @processtaboptions = qw( maxchildren minchildren minsparechildren preforkchildren maxsparechildren maxagechildren ipcfilename urlipcfilename ipipcfilename pidfilename nodaemon daemonuser daemongroup softrestart createlistcachefiles languagedir language );
our @loggingtaboptions = qw( nologger logsyslog loglocation statlocation anonymizelogs maxlogitemlength logexceptionhits showweightedfound logconnectionhandlingerrors loglevel logfileformat logchildprocesshandling logclienthostnames logadblocks loguseragent logtimestamp );
our @reportingtaboptions = qw( reportinglevel htmltemplate accessdeniedaddress nonstandarddelimiter );
our @contenttaboptions = qw( filtergroups usecustombannedimage custombannedimagefile reverseclientiplookups maxcontentramcachescansize maxcontentfilecachescansize filecachedir contentscannertimeout contentscanexceptions reverseaddresslookups recheckreplacedurls );
our @phrasetaboptions = qw( weightedphrasemode scancleancache urlcachenumber urlcacheage maxcontentfiltersize phrasefiltermode preservecase hexdecodecontent forcequicksearch );
our @updownloadtaboptions = qw( maxuploadsize deletedownloadedtempfiles initialtrickledelay trickledelay );
our @pluginstaboptions = qw( authplugin downloadmanager contentscanner );
# this list of options is "special" - it may or may NOT be a tab
our @allgroupstaboptions =  qw( groupmode blockdownloads naughtynesslimit categorydisplaythreshold embeddedurlweight enablepics bypass bypasskey infectionbypass infectionbypasskey infectionbypasserrorsonly disablecontentscan deepurlanalysis );

# complete the definitions of each tab
# each tab is specified by an array [0->handle, 1->tablegend, 
#  2->destination (must be present, but not actually used), 3->displaytitle, 4->ref-to-array-of-options ]
# the first three (0, 1, 2) are used by Webmin, (3) is used by our subroutine, and (4) is only for here
@tabs = map { [ $_, $text{"edit_tab_$_"}, "saveconf.cgi", "$text{\"edit_tab_$_\"} $text{'edit_heading_options'}", \@{"${_}taboptions"} ] } @tabs;



################### find-tab-with-option section ################

# Init the hash that we'll use for our find-the-tab function
our %option2tab = ();

# first set up "allgroups" options
#  if they're on a tab, the same thing will be written again
#  if they're not on a tab, they won't be overwritten and will point at 'fg'
foreach my $option (@allgroupstaboptions) {
    $option2tab{$option} = 'fg';
}

# now spin through everything that will appear on any displayed tab
foreach my $tabref (@tabs) {
    next if ! defined $tabref;
    next if ! $$tabref[0];
    next if ! $$tabref[4];
    next if scalar @{$$tabref[4]} <= 0;
    foreach my $option (@{$$tabref[4]}) {
        $option2tab{$option} = $$tabref[0];
    }
}

# all the data is now fully prepared, so do the display
# (also set up the bit of javascript we need,
#  it's separate because putting it inline involves too many quoting problems)
print <<"EOF";
<script type=text/javascript>
function findoption(name, value)
{
    if (value == '') {
        // just return, effectively igore the selection
    } else if (value == 'fg') {
        // a per-filter-group option, either on 'allgroups' tab if shared variables available, or not here at all
        alert(name + " $text{'edit_fgoption'}");
    } else {
        // the normal situation
        select_tab('', value);
    }

    return false;
}
</script>
EOF

print "<div style='margin-left: 60px'><p>$text{'edit_whichtab'}<br>\n";
print "<img border=0 src=images/transparent1x1.gif height=1 width=40><select onChange=\"findoption(this.options[this.selectedIndex].text, this.options[this.selectedIndex].value);\">\n";
print "<option value=''>&nbsp;- select option -</option>\n";
foreach my $findoption (sort keys %option2tab) {
    my $description = $text{"conf_$findoption"};
    print "<option value='$option2tab{$findoption}'>$findoption ($description)</option>\n";
}
print "</select></div><p>\n";


## the tabs
# message at top
print "<p align=left>($text{'index_clickhelp'})</p>";

our $initialtab = $in{'initialtab'};
$initialtab = $tabs[0][0] if ! $initialtab;
## following line is the minimal that works, line below that is how it used to be
print &ui_tabs_start(\@tabs, undef, $initialtab);

## fill in content for each tab
foreach my $tabref (@tabs) {
    next if ! defined $tabref;
    next if ! $$tabref[0];
    next if ! $$tabref[4];
    next if scalar @{$$tabref[4]} <= 0;

    print &ui_tabs_start_tab(undef, $$tabref[0]);
    &edit_options_formtable_start($tabref);

    &edit_options_headings_row(0, -1);

    foreach my $option (@{$$tabref[4]}) {
        &edit_options_data_row($option);
    }

    my $tabreturn = $return;
    $tabreturn .= '%3F' if ($tabreturn !~ m/%3[fF]/);
    $tabreturn .= '%26' if ($tabreturn !~ m/(?:%3[fF]|%26)$/);
    $tabreturn .= "initialtab%3D$$tabref[0]";

    print "<input type=hidden name='conffilepath' value='$conffilepath'>";
    print "<input type=hidden name='configsection' value='$$tabref[0]'>";
    print "<input type=hidden name='group' value='0'>";
    print "<input type=hidden name='return' value='$tabreturn'>";
    &edit_options_formtable_end($readonly);
    print &ui_tabs_end_tab();
}

## End of tabs

print &ui_tabs_end(1);


################### reversion section #################

our (@availableversions,  $availableversion, $listlength, $label, @buttons);

if (! $readonly) {
    print "<hr><p><hr>\n";

    print "<p>$text{'editfile_whatrevert'}\n";

    @availableversions = <$conffilepath.20*>;
    $listlength = ($#availableversions > 20) ? 20 : ($#availableversions + 1);

    if ($listlength > 0) {
        print &ui_form_start('revertfile.cgi', 'post');

        print "<input type=hidden name='return' value='$return'>";

        print "<p>$text{'editfile_selectreversion'}<br><select name=revertfilepath>\n";
        print "<option value=''>--revert to ? (YYYYMMDDhhmmss)--</option>\n";
        foreach $availableversion (@availableversions) {
            ($label) = ($availableversion =~ m{/([^/]*)$});
            print "<option value='$availableversion'>$label</option>\n";
        }
        print "</select><br><br>\n";

        @buttons = ( [ 'button', $text{'button_revert'} ], [ 'button', $text{'button_cancel'} ] );
        print &ui_form_end(\@buttons);
    } else {
        print "<p align=center>* $text{'editfile_noversionsavailable'} *\n";
    }
}

################### manual edit section #################

print "<hr><p><hr>\n";

print "<p>$text{'editfile_whatmanual'}\n";

print &ui_form_start('editfile.cgi', 'get');
print "<input type=hidden name=file value='$conffilepath'><input type=hidden name=return value='$return'>\n";
@buttons = ( [ 'button', $text{'button_edit'} ], [ 'button', $text{'button_cancel'} ] );
print &ui_form_end(\@buttons);

print "<hr>\n";

################### end #################

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
    &ui_print_header($pagename, $text{'index_title'}, undef, 'editconf', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}
