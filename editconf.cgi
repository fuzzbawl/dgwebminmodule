#!/usr/bin/perl
# editconf.cgi

require './dansguardian-lib.pl';
use POSIX;
&ReadParse();
&ui_print_header($text{'edit_dgconfig'}, "", "");
%access = &get_module_acl();

# Make sure user has access to this file
&checkmodauth(editconf);

# Check if DansGuardian conf file is there
&checkdgconf;

# Load dynamic settings script
&loadwebjslib;

#my $virus_engine;
@tabs = map { [ $_, $text{'edit_tab_'.$_}, "editconf.cgi?mode=$_" ] }
  (
    "network",
    "process",
    "logging",
    "content",
    "misc", 
    $access{'editavconf'} ? ( "dgav" ) : ( )
  );

$cfref = &read_file_lines($conffilepath);

$configsection = $in{"mode"};

print "$text{'index_dgversion'} $dg_version<br>\n";
print "<p align=left>$text{'index_clickhelp'}</p>";

## Network tab
print &ui_tabs_start(\@tabs, "mode", $in{'mode'} || "network", 1);
print &ui_tabs_start_tab("mode", "network");
print &ui_form_start("saveconf.cgi", "post");
print &ui_table_start("Network settings", undef, 2);

&form_line("filterip", 15, 15, "filterip");
&form_line("filterport", 4, 5, "filterport");
&form_line("proxyip", 15, 15, "proxyip");
&form_line("proxyport", 4, 5, "proxyport");
&form_option("reverseaddresslookups", "reverseaddresslookups");
&form_option("usernameidmethodproxyauth", "usernameauth");
&form_option("usernameidmethodident", "usernameauth");
&form_option("forwardedfor", "forwardedfor");
&form_option("usexforwardedfor", "usexforwardedfor");
&form_option("reverseclientiplookups", "reverseclientiplookups");

print &ui_table_end();
print "<input type=hidden name=\"conffilepath\" value=\"$conffilepath\">";
print "<input type=hidden name=\"configsection\" value=\"network\">";
print &ui_form_end([ [ undef, $text{'save'} ] ]);
print &ui_tabs_end_tab();

## Process tab
print &ui_tabs_start_tab("mode", "process");
print &ui_form_start("saveconf.cgi", "post");
print &ui_table_start("Process settings", undef, 2);

&form_line("maxchildren", 3, 4, "maxchildren");
&form_line("minchildren", 3, 3, "minchildren");
&form_line("minsparechildren", 3, 3, "minsparechildren");
&form_line("preforkchildren", 3, 3, "preforkchildren");
&form_line("maxsparechildren", 3, 3, "maxsparechildren");
&form_line("maxagechildren", 6, 6, "maxagechildren");
&form_line("ipcfilename", 56, 128, "ipcfilename");
&form_line("urlipcfilename", 56, 128, "urlipcfilename");
&form_line("pidfilename", 56, 128, "pidfilename");
&form_option("nodaemon", "nodaemon");
&form_option("nologger", "nologger");
&form_line("daemonuser", 20, 128, "daemonuser");
&form_line("daemongroup", 20, 128, "daemongroup");
&form_option("softrestart", "softrestart");

print &ui_table_end();
print "<input type=hidden name=\"conffilepath\" value=\"$conffilepath\">";
print "<input type=hidden name=\"configsection\" value=\"process\">";
print &ui_form_end([ [ undef, $text{'save'} ] ]);
print &ui_tabs_end_tab();

## Logging tab
print &ui_tabs_start_tab("mode", "logging");
print &ui_form_start("saveconf.cgi", "post");
print &ui_table_start("Log settings", undef, 2);

&form_option("logexceptionhits", "logexception");
&form_option("showweightedfound", "showweighted");
&form_radio("reportinglevel","-1","0","1","2","3");
&form_option("logconnectionhandlingerrors", "logconnecterr");
&form_radio("loglevel","0","1","2","3");
&form_radio("logfileformat","1","2","3","4");

print &ui_table_end();
print "<input type=hidden name=\"conffilepath\" value=\"$conffilepath\">";
print "<input type=hidden name=\"configsection\" value=\"logging\">";
print &ui_form_end([ [ undef, $text{'save'} ] ]);
print &ui_tabs_end_tab();

## Begin content filter tab
print &ui_tabs_start_tab("mode", "content");
print &ui_form_start("saveconf.cgi", "post");
print &ui_table_start("Content filter settings", undef, 2);

my @filepaths = ('bannediplist', 'exceptioniplist');
foreach (@filepaths) {
  &form_line("$_", 56, 128, "filepaths");
}
&form_line("maxuploadsize", 4, 6, "post");
&form_radio("weightedphrasemode","0","1","2");
&form_line("urlcachenumber", 4, 4, "urlcachenumber");
&form_line("urlcacheage", 4, 4, "urlcacheage");
&form_line("maxcontentfiltersize", 6, 6, "maxcontentfiltersize");
&form_radio("phrasefiltermode","0","1","2");
&form_option("preservecase", "preservecase");
&form_option("hexdecodecontent", "hexdecodecontent");
&form_option("forcequicksearch", "forcequicksearch");
&form_option("nonstandarddelimiter", "nonstandarddelimiter");
&form_line("filtergroups", 3, 3, "filtergroups");
&form_line("filtergroupslist", 56, 128, "filtergroupslist");

print &ui_table_end();
print "<input type=hidden name=\"conffilepath\" value=\"$conffilepath\">";
print "<input type=hidden name=\"configsection\" value=\"content\">";
print &ui_form_end([ [ undef, $text{'save'} ] ]);
print &ui_tabs_end_tab();

## Begin misc tab
print &ui_tabs_start_tab("mode", "misc");
print &ui_form_start("saveconf.cgi", "post");
print &ui_table_start("Miscelaneous settings", undef, 2);

&form_option("createlistcachefiles", "createlistcache");
&form_line("accessdeniedaddress", 56, 128, "accessdeniedaddress");
&form_line("languagedir", 56, 128, "languagedir");
&form_line("language", 25, 50, "language");

print &ui_table_end();
print "<input type=hidden name=\"conffilepath\" value=\"$conffilepath\">";
print "<input type=hidden name=\"configsection\" value=\"misc\">";
print &ui_form_end([ [ undef, $text{'save'} ] ]);
print &ui_tabs_end_tab();

## End of tabs

print &ui_tabs_end(1);
&ui_print_footer("index.cgi", $text{'index_return'});
exit;
