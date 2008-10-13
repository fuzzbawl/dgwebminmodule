#!/usr/bin/perl
# groups.cgi

require './dansguardian-lib.pl';
use POSIX;
&ReadParse();
&ui_print_header($text{'index_groups'}, "", "");
%access = &get_module_acl();

# Check user acl
&checkmodauth(groups);

$groupnum = &readconfigoption(filtergroups);
$group = $in{"group"};

if ($group eq "") { $group = "f1"; }

my @configuration_files = ("bannedphraselist", "exceptionphraselist", "weightedphraselist", "bannedsitelist", "greysitelist", "exceptionsitelist", "bannedurllist", "greyurllist", "exceptionurllist", "bannedregexpurllist", "picsfile", "contentregexplist", "urlregexplist", "exceptionextensionlist", "exceptionmimetypelist", "bannedextensionlist", "bannedmimetypelist", "exceptionfilesitelist", "exceptionfileurllist", "logsitelist", "logurllist", "logregexpurllist", "headerregexplist", "bannedregexpheaderlist");

#print "$text{'index_dgversion'} $dg_version<br>\n";
#print "$text{'index_numberofgroups'}: $groupnum<br>\n";

## Make links to edit each group
my @groups;
for ($i = 1; $i <= $groupnum; $i++) {
  push(@groups,"f$i",);
#print "<a href=\"?group=f$i\">Group f$i</a> &nbsp;&nbsp;\n";
}

@groups = map { [ $_, $text{'index_group'}." ".$_, "groups.cgi?group=$_" ] } ( @groups );

print &ui_tabs_start(\@groups, "group", $in{'group'} || "f1", 1);

print &ui_form_start("savegroups.cgi", "post");
print &ui_table_start("$text{'index_groupsettings'} $group", undef, 2);
&gform_line("groupmode", 4, 4, "groupmode", $group);
&gform_line("groupname", 56, 128, "groupname", $group);
&gform_option("blockdownloads","blockdownloads", $group);
&gform_line("naughtynesslimit", 4, 4, "naughtynesslimit", $group);
&gform_line("categorydisplaythreshold", 4, 4, "categorydisplaythreshold", $group);
&gform_line("embeddedurlweight", 4, 4, "embeddedurlweight", $group);
&gform_option("enablepics", "enablepics", $group);
&gform_line("bypasstimelimit", 4, 4, "bypass", $group);
&gform_line("bypasskey", 56, 128, "bypasskey", $group);
&gform_line("infectionbypass", 4, 4, "infectionbypass", $group);
&gform_line("infectionbypasskey", 56, 128, "infectionbypasskey", $group);
&gform_option("infectionbypasserrorsonly", "infectionbypasserrorsonly", $group);
&gform_option("disablecontentscan", "disablecontentscan", $group);
&gform_option("deepurlanalysis", "deepurlanalysis", $group);
&gform_line("reportinglevel", 4, 4, "reportinglevel", $group);
&gform_line("accessdeniedaddress", 56, 128, "accessdeniedaddress", $group);
&gform_line("htmltemplate", 56, 128, "htmltemplate", $group);

print &ui_table_end();
print &ui_form_end([ [ undef, $text{'save'} ] ]);

print &ui_table_start("$text{'edit_dgfiles'}", "width=75%",2);

foreach $conf_file (@configuration_files) {
  my $fileref = &readgroupconf($group,$conf_file);
  if ($fileref) {
    print &ui_table_row($fileref,"<a href=\"./edit.cgi?file=$fileref\">$text{'index_edit'}</a>");
  } else {
    print &ui_table_row($conf_file.": ".$text{'error_filenotused'}, "");
  }
}

print &ui_table_end();
&ui_print_footer("index.cgi", $text{'index_return'});
exit;
