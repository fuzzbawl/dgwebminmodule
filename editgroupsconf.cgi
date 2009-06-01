#!/usr/bin/perl
# editgroupsconf.cgi

# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($dg_version, $current_lang, $module_config_directory);
use POSIX;
require './dansguardian-lib.pl';
use warnings;
use strict qw(subs vars);
&passthroughautoreturn();

our $return = &getcleanreturn();

our $pagename = "$text{'index_viewedit'} $text{'index_editgroupsconf'}";

&webminheader();

# Check user acl
&checkmodauth('editgroupsconf');

# Check if the right version
if (!(&checkdgver())) {
    print "<span style='color: brown'>$text{'error_version_notsupp'}<br>$text{'index_modulever'} $modulever $text{'index_moduleversupports'}<br>$text{'index_dgversion'} $dg_version<p>\n";
}

# Load dynamic settings scripts
&loadeditjslib();

our $howmany = &getconfigvalue('filtergroups', 0);

our @groups = ( 1 .. $howmany );
@groups = map { [ $_, &getgrouptitle($_), 'saveconf.cgi', &getgroupheading($_, 'options') ] } ( @groups );


our $initialtab = $in{'initialtab'};
$initialtab = $groups[0][0] if ! $initialtab;
# following line is the minimal that works, line below that is how it used to be
print &ui_tabs_start(\@groups, undef, $initialtab);


#####################################
foreach my $groupref (@groups) {

## show conf display
our $groupnum = $$groupref[0];
our $tabhandle = $groupnum;
our $groupname = $$groupref[1];
our $groupheading = $$groupref[3];
our $conffilepath = &group2conffilepath($groupnum); 

my $tabreturn = $return;
$tabreturn .= '%3F' if ($tabreturn !~ m/%3[fF]/);
$tabreturn .= '%26' if ($tabreturn !~ m/(?:%3[fF]|%26)$/);
$tabreturn .= "initialtab%3D$tabhandle";

our $readonly = ! &accessfile($conffilepath);


print &ui_tabs_start_tab(undef, $tabhandle);
&edit_options_formtable_start($groupref);

our @groupuppertaboptions = qw( groupname );

foreach my $option ( @groupuppertaboptions ) {
	&edit_options_data_row($option, $groupnum);
}

&edit_options_separator_row;
&edit_options_headings_row($groupnum, 0);

our @groupmiddletaboptions =  qw( groupmode blockdownloads naughtynesslimit categorydisplaythreshold embeddedurlweight enablepics bypass bypasskey infectionbypass infectionbypasskey infectionbypasserrorsonly disablecontentscan deepurlanalysis );

foreach my $option ( @groupmiddletaboptions ) {
	&edit_options_data_row($option, $groupnum);
}

&edit_options_separator_row;
&edit_options_headings_row($groupnum, 1);

our @grouplowertaboptions = qw( reportinglevel htmltemplate accessdeniedaddress );

foreach my $option ( @grouplowertaboptions ) {
	&edit_options_data_row($option, $groupnum);
}

print "<input type=hidden name='conffilepath' value='$conffilepath'>";
print "<input type=hidden name='group' value='$groupnum'>";
print "<input type=hidden name='return' value='$tabreturn'>";
&edit_options_formtable_end($readonly);


################### reversion section #################

if (! $readonly) {
    print "<hr><p><hr>\n";

    print "<p>$text{'editfile_whatrevert'}\n";

    our @availableversions = <$conffilepath.20*>;
    our $listlength = ($#availableversions > 20) ? 20 : ($#availableversions + 1);

    if ($listlength > 0) {
        print &ui_form_start('revertfile.cgi', 'post');

        print "<input type=hidden name='return' value='$return'>";

        print "<p>$text{'editfile_selectreversion'}<br><select name=revertfilepath>\n";
        print "<option value=''>--revert to ? (YYYYMMDDhhmmss)--</option>\n";
        foreach my $availableversion (@availableversions) {
            my ($label) = ($availableversion =~ m{/([^/]*)$});
            print "<option value='$availableversion'>$label</option>\n";
        }
        print "</select><br><br>\n";

        our @buttons = ( [ 'button', $text{'button_revert'} ], [ 'button', $text{'button_cancel'} ] );
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
our @buttons = ( [ 'button', $text{'button_edit'} ], [ 'button', $text{'button_cancel'} ] );
print &ui_form_end(\@buttons);

print "<hr>\n";

################### end #################

print &ui_tabs_end_tab();
}



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
    &ui_print_header($pagename, $text{'index_title'}, undef, 'editgroupsconf', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('index.cgi', $text{'index_return'});

    exit;
}
