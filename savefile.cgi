#!/usr/bin/perl
# savefile.cgi

require './dansguardian-lib.pl';
use POSIX;
&ReadParse();

&ui_print_header($text{'savefile_title'}, "", "savefile");
%access = &get_module_acl();
my $filename = $in{"file"};

# Check to see if the file we are editing is in the DG config dir
if (&is_under_directory($config{'conf_path'}, $filename)) {

print "<h3>$filename<h3>\n";

&lock_file("$filename");
open(OUTFILE, ">$filename");
print OUTFILE $in{"filecontents"};
close(OUTFILE);
&unlock_file("$filename");

if ($access{'autorestart'}) {
  printf "<b>%s</b> %s<p>\n", $text{'note'}, $text{'restart_title'};
  &dgprocess("restart");
} else {
  printf "<b>%s</b> %s<p>\n", $text{'note'}, $text{'forgetrestart'};
}

# If file is not within DG config dir, tell user
} else {
  print "$text{'index_notauth'}";
}
&ui_print_footer("index.cgi", $text{'index_return'}, "editfiles.cgi", $text{'edit_dgfiles'}, "groups.cgi", $text{'index_groups'});
