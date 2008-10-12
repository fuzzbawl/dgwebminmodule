#!/usr/bin/perl

require './dansguardian-lib.pl';
&ReadParse();
&init_config();
&clean_environment();

# Run and display output
my $conffilepath = $config{'conf_path'};
my $cmd = "grep -irH \"$in{'search'}\" $conffilepath/phraselists/";
my $temp = &tempname();
&system_logged("$cmd >$temp 2>&1 </dev/null");
my $out = &read_file_lines($temp);
unlink($temp);
&reset_environment();
&ui_print_header($text{'search_title'}, "", "search");
print "<center><font size=+2>$cmd</font></center>\n";
print "<hr>\n";
print "<p>",&text('run_out', "<tt><pre>".$displaystr."</pre></tt>"),"\n";
print "<pre>";
my $name;
my $value;
foreach $line (@$out) {
    ($name, $value) = split(/:/, $line);
    print "<font size=3><A HREF=\"./edit.cgi?file=$name\"></font>";
    $line =~ s/>/&gt;/g;
    $line =~ s/</&lt;/g;
    print "<font size=3>$text{'index_edit'}</a> $line</font>\n";
}
print "</pre>\n";
print "<hr>\n";
&ui_print_footer("index.cgi", $text{'index_return'}, "editfiles.cgi", $text{'edit_dgfiles'});
