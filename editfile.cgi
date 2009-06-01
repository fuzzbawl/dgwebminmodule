#!/usr/bin/perl
# editfile.cgi

# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
our (%mainconfigurationlists, %groupsconfigurationlists);
our (%sharedgroupsconfigurationlists, %notsharedgroupsconfigurationlists);
our (%sharedonlynestedconfigurationlists, %sharedonlyseparateconfigurationlists, %sharedonlycommonconfigurationlists);
our ($EFFECTIVE_USER_ID);
require './dansguardian-lib.pl';
use POSIX;
use warnings;
use strict qw(subs vars);
our $filepath = &canonicalizefilepath($in{'file'});
our $returnto = $in{'return'};


&bailifcallercancelled();


&webminheader();


# check error conditions
if (! (-e $filepath)) {
    print "<span style='color: red'>$text{'error_filenotfound'}</span><br>\n";
    &showackandret();
    &webminfooterandexit();
}
if (! &is_under_directory($config{'conf_path'}, $filepath)) {
    print "<span style='color: red'>$text{'error_filenotindir'}</span><br>\n";
    &showackandret();
    &webminfooterandexit();
}
if ($filepath =~ m/blacklist/) {
    print "<span style='color: brown'>$text{'error_blacklist'}</span><br>\n";
}
if ($filepath =~ m{/phraselist}) {
    print "<span style='color: brown'>$text{'error_fixedlist'}</span><br>\n";
}
if ((-s $filepath) > 999999) {
    print "<span style='color: red'>$text{'error_toobig'}</span><br>\n";
    &showackandret();
    &webminfooterandexit();
}
our $readonly = 0;
if (! &accessfile($filepath)) {
    print "<p><span style='color: brown'>$text{'error_notauthfile'} - $text{'error_viewonly'}<br>$text{'index_location'}: $filepath</span><p>\n";
    $readonly = 1;
}



# proceed with the file edit 
print &ui_form_start("savefile.cgi", "post");
print "<input type=hidden name=return value='$returnto'>\n";
&start_manually_editing_file($filepath);
if (! $readonly) {
    print &ui_form_end([ [ 'button', $text{'button_update'} ], [ 'button', $text{'button_cancelchange'} ] ]);
} else {
    print &ui_form_end([ [ 'button', $text{'button_ok'} ] ]);
}

################### reversion section #################

if (! $readonly) {
    print "<hr><p><hr>\n";

    print "<p>$text{'editfile_whatrevert'}\n";

    our @availableversions = <$filepath.20*>;
    our $listlength = ($#availableversions > 20) ? 20 : ($#availableversions + 1);

    if ($listlength > 0) {
        print &ui_form_start('revertfile.cgi', 'post');

        print "<input type=hidden name='return' value='$returnto'>";

        print "<p>$text{'editfile_selectreversion'}<br><select name=revertfilepath>\n";
        print "<option value=''>--revert to ? (YYYYMMDDhhmmss)--</option>\n";
        foreach my $availableversion (@availableversions) {
            our ($label) = ($availableversion =~ m{/([^/]*)$});
            print "<option value='$availableversion'>$label</option>\n";
        }
        print "</select><br><br>\n";

        our @buttons = ( [ 'button', $text{'button_revert'} ], [ 'button', $text{'button_cancel'} ] );
        print &ui_form_end(\@buttons);
    } else {
        print "<p align=center>* $text{'editfile_noversionsavailable'} *\n";
    }

    print "<hr>\n";
}

################# end #####################

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
    &ui_print_header("$text{'index_viewedit'} $filepath", $text{'index_title'}, undef, undef, 0, 1, 1, undef, undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer();	# entirely omit/suppress the return arrow

    exit;
}
