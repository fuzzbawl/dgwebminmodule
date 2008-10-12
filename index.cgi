#!/usr/bin/perl
# index.cgi

# Load module functions
require './dansguardian-lib.pl';

# Are the following two needed?
#use POSIX;
# This reads in form POSTS and ? variables into the %in array
#ReadParse();

# Read webmin module ACL
%access = &get_module_acl();

if (&checkdgver() eq "false") {
     &ui_print_header($text{'index_title'}, "", undef, 1, 1);
      print "<p>$text{'index_notsupported'}<p>";
      print "$text{'index_dgversion'} $dg_version<br>\n";
      &ui_print_footer("/", $text{'index_return'});
      exit;
## Binary or conf file does not exist or is not executable, warn the user
} elsif (!(&checkdgconf) && (&checkdgbinary)) {
  &ui_print_header($text{'index_title'}, "", undef, 1, 1);
  if (!(&checkdgconf)) {
    print "$text{'error_confnotfound'}<br>\n";
    print "$text{'index_location'} $config{'conf_file'}<p>\n";
  }
  if (!(&checkdgbinary)) {
    print "$text{'error_binnotfound'}<br>\n";
    print "$text{'index_location'} $config{'binary_file'}<p>\n";
  }
  print "$text{'error_modconfig'}<p>\n";
  exit 0;
}

## Print the Header
&header($text{'index_title'}, "", "index", 1, 1, undef, &restart_button."<br>".&help_search_link("dansguardian", "man"), undef, undef, &text('index_version')." ".$dg_version);
  
print "$text{'index_modulever'} $modulever<br>\n";

# Set the arrays for the links, titles, and icons of each option
# NOTE: The .cgi file names MUST be the same as the title and icon for the 
# button! Or if you put the word edit infront of the filename, i.e. editconf.cgi
# then all will be ok as the edit is stripped later.
# Otherwise problems will occur.
#
@olinks = ( "status.cgi", "logs.cgi", "editconf.cgi", "editfiles.cgi", "groups.cgi" );
@otitles = map { $t=$_; $t=~s/.cgi//; "$t" } @olinks;
for($i=0; $i<@otitles; $i++) {
  if (!$access{$otitles[$i]}) {
    splice(@otitles, $i, 1);
    splice(@olinks, $i, 1);
    $i--;
  }
  else {
    $otitles[$i] = $text{'index_'.$otitles[$i]};
  }
}
@oicons =  map { $t=$_; $t=~s/cgi/gif/; $t=~s/edit//; "images/$t" } @olinks;
&icons_table(\@olinks, \@otitles, \@oicons);

&ui_print_footer("/", $text{'index'});
exit;
