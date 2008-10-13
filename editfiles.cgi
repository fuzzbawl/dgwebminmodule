#!/usr/bin/perl
# editfiles.cgi

require './dansguardian-lib.pl';

use POSIX;
&ReadParse();
&ui_print_header($text{'edit_dgfiles'}, "", "");
%access = &get_module_acl();

# Check user acl
&checkmodauth(editfiles);

# Check if DansGuardian conf file is there
&checkdgconf;

print "$text{'index_dgversion'} $dg_version<br>\n";
print "<p align=left>$text{'index_clickhelp'}</p>";
print "\&nbsp;\n";
print "<p align=left>$text{'index_search_title'}";
print &ui_form_start("search.cgi", "post");
print &ui_textbox("search", "$text{'index_search'}", "20");
print &ui_form_end([ [ undef, $text{'index_search'} ] ]);

@filecolumns = ("Help Link","File Location","");
print &ui_columns_start(\@filecolumns);

## Files for all versions
my @configuration_files = ("filtergroupslist", "bannediplist", "exceptioniplist");

%help_files = ("filtergroupslist" => "filepaths", "bannediplist" => "filepaths", "exceptioniplist" => "filepaths");

my $conf_file;

foreach $conf_file (@configuration_files) {
  if ($access{$conf_file}) {
    &edit_line_file("$conf_file", $help_files{$conf_file});
  }
}

print &ui_columns_end();
&ui_print_footer("index.cgi", $text{'index_return'});
exit;
