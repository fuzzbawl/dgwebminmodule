#!/usr/bin/perl

require './dansguardian-lib.pl';
&ReadParse();
&init_config();
&clean_environment();
%access = &get_module_acl();

if ($in{"action"} eq "") {
  $in{"action"} = "status";
}

&ui_print_header($text{$in{"action"}.'_title'}, "", "");

&dgprocess($in{"action"});

&ui_print_footer("index.cgi", $text{'index_return'});
