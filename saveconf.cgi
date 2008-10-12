#!/usr/bin/perl
# saveconf.cgi

require './dansguardian-lib.pl';
use POSIX;
&ReadParse();

&ui_print_header($text{'saveconf_title'}, "", "saveconf");

# Make sure user is allowed to edit conf first
&checkmodauth(editconf);

# Check if DansGuardian conf file is there
&checkdgconf;

# Read in the dansguardian.conf file
$cfref = &read_file_lines($conffilepath);
$filename = $in{"conffilepath"};
$configsection = $in{"configsection"};
print "configsection: ".$configsection;
print "$text{'saveconf_configfile'} <b>$filename</b><p>\n";

@configoptions = ();

# This is checkbox options
@cbopts = ("reverseaddresslookups", "forwardedfor", "usexforwardedfor", "reverseclientiplookups", "nodaemon", "nologger", "softrestart", "logexceptionhits", "showweightedfound", "logconnectionhandlingerrors", "preservecase", "hexdecodecontent", "forcequicksearch", "nonstandarddelimiter", "createlistcachefiles", "virusscan");

# This is textbox options
@tbopts= ("accessdeniedaddress", "languagedir", "language", "ipcfilename", "urlipcfilename", "pidfilename", "daemonuser", "daemongroup", "filtergroupslist", "htmltemplate", "exceptionvirusmimetypelist", "exceptionvirusextensionlist", "banneduserlist", "bannediplist", "exceptionuserlist", "exceptioniplist", "contentregexplist", "languagefile", "bannedphraselist", "bannedextensionlist", "bannedmimetypelist", "bannedsitelist", "bannedurllist", "bannedregexpurllist", "exceptionphraselist", "exceptionurllist", "weightedphraselist", "picsfile");

# This sets the default config options for ALL DG versions
# Version specific ones are push-ed into the array
#

## Network
if ($configsection eq "network") {
  push(@configoptions, "filterip","filterport","proxyport","proxyip","reverseaddresslookups", "usernameidmethodproxyauth", "usernameidmethodident", "forwardedfor", "usexforwardedfor", "reverseclientiplookups");

## Process
} elsif ($configsection eq "process") {
  push(@configoptions, "maxchildren", "minchildren", "minsparechildren", "preforkchildren", "maxsparechildren", "maxagechildren", "ipcfilename", "urlipcfilename", "nodaemon", "nologger", "softrestart");

## Logging
} elsif ($configsection eq "logging") {
  push(@configoptions, "logexceptionhits", "showweightedfound", "reportinglevel", "logconnectionhandlingerrors", "loglevel", "logfileformat", "urlcachenumber", "urlcacheage", "maxcontentfiltersize");

## Content
} elsif ($configsection eq "content") {
  push(@configoptions, "banneduserlist", "bannediplist", "exceptionuserlist", "exceptioniplist", "maxuploadsize", "weightedphrasemode", "urlcachenumber", "urlcacheage", "maxcontentfiltersize", "phrasefiltermode", "preservecase", "hexdecodecontent", "forcequicksearch", "nonstandarddelimiter", "preemptivebanning", "filtergroups", "filtergroupsl
ist");

## Misc
} elsif ($configsection eq "misc") {
  push(@configoptions, "createlistcachefiles", "accessdeniedaddress", "languagedir", "language");

## End of Config sections
}

my $opt;
my $grep_count;
my $optchk;

# This disgusting hack checks the checkboxes.
# if the checkbox isn't checked, then set the value to off
foreach $optchk (@cbopts) {
  if ($in{$optchk} eq "") {
    $in{$optchk} = "off";
  }
}

foreach $optchk (@tbopts) {
  if ($in{$optchk}) {
    $in{$optchk} = "\'" . $in{$optchk} . "\'";
  }
}

# DEBUG
#print "cfref values before push<p>\n";
#foreach $cfrefopt (@configoptions) {
#  print "$cfrefopt \= $in{$cfrefopt}<br>\n";
#}

foreach $opt (@configoptions) {
  $grep_count = grep { s/^(\s*$opt\s*=\s*)([^#]*)(.*)$/$1$in{$opt}$3/ } @{$cfref};
  if ($grep_count eq "0") {
        push @{$cfref}, "$opt = $in{$opt}";
  }
}

# write out the modified version of the dansguardian.conf file
&flush_file_lines($conffilepath);

#print "<hr><b>$text{'saveconf_configdata'}</b><br>";
#print "<pre>\n";
#my $conf_line;
#foreach $conf_line (@{$cfref}) {
#  print "$conf_line\n";
#}
#print "</pre>\n";

if ($access{'autorestart'}) {
  printf "<b>%s</b> %s<p>\n", $text{'note'}, $text{'restart_title'};
  &dgprocess("restart");
} else {
  printf "<b>%s</b> %s<p>\n", $text{'note'}, $text{'forgetrestart'};
}

print "<hr>\n";
&ui_print_footer("index.cgi", $text{'index_return'}, "editconf.cgi", $text{'edit_dgconfig'});
