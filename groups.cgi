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

my @configuration_files = ("bannedphraselist", "exceptionphraselist", "weightedphraselist", "bannedsitelist", "greysitelist", "exceptionsitelist", "bannedurllist", "greyurllist", "exceptionurllist", "bannedregexpurllist", "bannedextensionlist", "bannedmimetypelist", "picsfile", "contentregexplist");

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

#print &ui_form_start("", "post");
print "<b>$text{'index_groupsettings'} $group</b><p>\n";
printf("%s: %s<br>\n", $text{'conf_naughtynesslimit'}, &readgroupconf($group,naughtynesslimit));
printf("%s: %s<br>\n", $text{'conf_bypasstimelimit'}, &readgroupconf($group,bypass));
printf("%s: %s<br>\n", $text{'conf_bypasskey'}, &readgroupconf($group,bypasskey));
print "<p>";

print &ui_table_start("$text{'edit_dgfiles'}", "width=75%",2);

foreach $conf_file (@configuration_files) {
  my $fileref = &readgroupconf($group,$conf_file);
  print &ui_table_row($fileref,"<a href=\"./edit.cgi?file=$fileref\">$text{'index_edit'}</a>");
}

print &ui_table_end();
&ui_print_footer("index.cgi", $text{'index_return'});
exit;
