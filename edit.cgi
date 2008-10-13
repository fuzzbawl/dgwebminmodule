#!/usr/bin/perl
# edit.cgi

require './dansguardian-lib.pl';
use POSIX;
&ReadParse();

%access = &get_module_acl();

&ui_print_header($text{'edit_title'}, "", "edit");

my $filename = $in{"file"};

# Make sure dg config is there
&checkdgconf;

# Check to see if the file we are editing is in the DG config dir
if (( -e $filename ) && (&is_under_directory($config{'conf_path'}, $filename))) {
#  $cfref = read_file_lines($conffilepath);
  print "<H3>$filename</H3>";
  print &ui_form_start("savefile.cgi", "post");
  print "<input type=hidden name=\"file\" value=\"$filename\">\n";
  &form_file($filename);
  print &ui_form_end([ [ undef, "submit" ] ]);

# If file is not within DG config dir, tell user
} elsif ( -e $filename) {
  print "$text{'error_filenotfound'}";
} else {
  print "$text{'index_notauth'}";
}
&ui_print_footer("index.cgi", $text{'index_return'}, "editfiles.cgi", $text{'edit_dgfiles'});
