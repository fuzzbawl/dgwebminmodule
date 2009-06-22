#!/usr/bin/perl
# logs.cgi

print DEBUGLOG "beginning processing logs.cgi\n" if $debug;
###########################################################################
#
# Program  : Log Analyzer for DansGuardian
# Author   : Jimmy Myrick (jmyrick@cherokeek12.org)
# Version  : 1.0
# Released : October 10, 2005
# 
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#
# If you like it and want to send me something, that's ok too.
# How about a gift certificate to amazon.com or a donation to DansGuardian
# on my behalf? 
#
###########################################################################

# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
##########################################################################
# declare global variables
##########################################################################
our ($parseactionsandreasonregexp, $parsetoeolregexp, $parsetoeolregexpjr);
######## settings
our ($sSD, $sED, $sSDY, $sSDM, $sSDD, $sEDY, $sEDM, $sEDD);
our ($sL, $sZ, $sD, $sR, $sG, $sP);
our ($sSumExc, $sSumDen, $sSumAlw, $sSumCnt);
our ($sA, $sA2, $sSN, $sSD);
our ($sRC, $sRM, $sRG);
our ($sCAT, $sMIME, $sGRP, $sIP, $sUN, $sWGHT, $sAGT);
our ($sWD, $sWN);
our ($sTITLE);	# <-- only on batch reports (in fact use "defined $sTITLE" as a switch)
######## "global" variables that are part of the UI
our ($msg);
our ($line);
########
our ($dgDate);
######## "global" variables used to pass information between large block subroutines
our ($linesRead, $allowedTotal, $deniedTotal, $exceptionTotal, $grandTotal);
our ($noaddr, $nouser, $userisaddr);
our (@files, $file);
######## all these are globally available resources  (they're in a subroutine only for coding clarity) #####
our (%order2title, %order2varname, %order2source, %what2subtitle, %what2varname, %what2option);
our (%reasons_number2text, %reasons_text2number);
our (%reasonMessageNumbers, %regexpreasonMessageNumbers);
our (%phrasereasonMessageNumbers, %blanketreasonMessageNumbers, %exceptionreasonMessageNumbers);
our (%regexpreasons_number2text, %regexpreasons_text2number);
our (%phrasereasons_number2text, %phrasereasons_text2number);
our (%blanketreasons_number2text, %blanketreasons_text2number);
our (%exceptionreasons_number2text, %exceptionreasons_text2number);
######## "global" variables freely used by large block subroutines
our ($hashname, $separator);
our ($order, $source, $varname);
our ($modpattern, $modurl);
our ($majormime, $prevmajormime);
our ($substring);
our ($number);
######## "global" variables used to pass around parts of log entries
our ($date, $time, $ip, $user);
our ($url, $baseurl, $queryurl, $protocol, $allbutprotocol, $urlpath, $sitename, $protocolandsitename);
our ($toeol, $cl1, $cl2, $method, $retcode, $size, $clientname); 
our ($category, @categoryeach, $weight, $filtergroup, $filtergroupnum, $mimetype, $browseragent);
our ($action, $otheractions, $reason, $reasonjr, $subreason, $subreasonjr, $privatereason);
######## counters
our (%filtergroups, $listchanged_filtergroups);
our (%mimetypes, $listchanged_mimetypes);
our (%categories, $listchanged_categories);
######## temps
our ($onecategory, $categorytemp);
######## initialized counters
our $formaterrcount = 0;
our $languageerrcount = 0;
our $formaterrcountthislogfile = 0;


# Begin Webmin header stuff (also note footer at bottom of script)
require './dansguardian-lib.pl';
use POSIX;
use warnings;
use strict qw(subs vars);
our $pagename = $text{'index_logs'};

# finish transferring anything set by the calling URL from %in to our vars
while (my ($name, $value) = each %in) {
	$$name = $value;
}

&webminheader();


# give checkboxes a definite value if coming from menu
# (oddity of HTML, checkboxes are just plain absent if off)
&setCheckboxes();
# give a default value to anything that's not set yet
&setDefaults();
# standardize variables
&canonicalizeVars();

# Check user acl
&checkmodauth('logs');

# End of Webmin header stuff


###########################################################################
#
# Change to point to your DansGuardian log directory
#
###########################################################################

# modified to use a setting from our module-config
our $logdir = &canonicalizefilepath($config{'log_path'});


###########################################################################
#
# Log filename.  Change this to match the prefix of your log files
# This defaults to access.log and should not have to be modified.
#
# Any logfiles in $logdir that match the prefix $logfile and are gzip'ed
# with a .gz extension will also be read.  The results will be printed in
# reverse chronological filename order.
#
# Example:
#  If you have the files:  access.log access.log.0.gz access.log.1.gz
#  where they are newest to oldest, then any matches in
#  access.log.1.gz will be printed first, followed by access.log.0.gz
#  and then access.log
#
# No sorting is done by the program and the results are displayed in logfile
# order.  If your results are out of sequence, check the filename/dates
# to be sure they are compressed and rotated properly.  If you use 
# the FreeBSD newsyslog.conf to rotate your logs, this will not be a
# problem.
#
###########################################################################

# essentially hard-coded, as there is no provision for changing this
our $logfile = 'access.log';


###########################################################################
#
# If you need the perl modules below, download and untar them to a directory.
# Then cd to the directory and enter the commands:
#  perl Makefile.PL; make; make test; make install 
#
# This is needed to do gzip'ed log files on the fly
#
# If you need more instructions, 
#  go here: http://www.cpan.org/modules/INSTALL.html
#
# Get it here: http://www.cpan.org/authors/id/PMQS/Compress-Zlib-1.16.tar.gz
#
###########################################################################

# essentially hard-coded, as there is no provision for changing this
use Compress::Zlib; 


###########################################################################
#
# This should determine where the program is called from automagically.
# If not, uncomment the first line, change to your server name/path and
# comment the second line.  You can use Apache restrictions to block 
# access to this file if desired. 
#
###########################################################################

# changed to work properly for log analysis embedded in Webmin rather than standalone
#$cgipath = 'http://your.server.com/cgi-bin/dglog/dglog.pl';
our $cgipath = $ENV{SCRIPT_NAME};
(our $modulenameself = $cgipath) =~ s{^.*/([^/]*)$}{$1};



###########################################################################
#
#    SHOULDN'T HAVE TO MODIFY ANYTHING BELOW THIS LINE
#
###########################################################################

if (&cputoobusy()) {
    print "<p><span style='color: brown'>$text{'error_verybusy'}</span><br>\n";
}

###########################################################################
# check prerequisites and complain about any that aren't found
###########################################################################
if (($config{'messages_path'} =~ m/follow/i) || ($config{'log_format'} =~ m/follow/i)) {
  if (! &checkdgconf) {
    print "<span style='color: brown'>$text{'error_confnotfound'}<br>$text{'index_location'}: " . &group2conffilepath(0) . "</span><p>\n";
  }
}

our $logfileformat;
our $whereisit = $config{'log_format'};
if ((! defined $whereisit) || ($whereisit eq '') || ($whereisit =~ m/follow/i)) {
    $logfileformat = &getconfigvalue('logfileformat');
} else {
    $logfileformat = $whereisit;
}
if (! (($logfileformat == 1) || ($logfileformat == 2) || ($logfileformat == 4))) {
    print "<span style='color: brown'>$text{'error_logfileformat_notsupp'}<br>$text{'view_logfileformat'}: $logfileformat</span><p>\n";
    &webminfooterandexit();
}


##########################################################################
# begin processing request
##########################################################################
# set up housekeeping
&initVars();
# get our persistent data that drives our configuration
&unPersistData(); 
# define "constants"
&initConstants();


# define 'today'
my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
$mon = $mon + 1;  # mon starts at 0 
$year = $year + 1900;  # year needs 1900 added

if ($a eq 'i') { # Inquiry into logs

  # check some input variables for validity
  # if anything invalid is found, reprint the menu (but with current values) then exit
  &validateVars();

  # Need a few global variables to keep from passing back and forth a bunch
  $linesRead = 0;
  $allowedTotal = 0;
  $deniedTotal = 0;
  $exceptionTotal = 0;
  $grandTotal = 0;
  # and need some global counters
  $noaddr = 0;
  $nouser = 0;
  $userisaddr = 0;

  # do the work
  &searchLog();

} elsif ($a eq 'd') {
  # alternate inquiry into logs, settings from %in (batch or detail) rather than menu
  # typically used for "details" (hence the acronym)

  # do not validateVars(), as we couldn't get here if anything was invalid
  # do the work it would do though
  &dateParts2wholeDates;

  # Need a few global variables to keep from passing back and forth a bunch
  $linesRead = 0;
  $grandTotal = 0;
  # and need some global counters
  $noaddr = 0;
  $nouser = 0;
  $userisaddr = 0;

  # do the work
  &searchLog();

}
else {
  # maybe a='m', or maybe a='', or maybe a is not set
  &printMenu();
}

# save our persistent information that drives our configuration
&persistData();

# Webmin footer
&webminfooterandexit();

# all done!


###########################################################################
#
#    SUBROUTINES FOR MAJOR PORTIONS OF PROCESSING
#
###########################################################################

#############
sub searchLog
#############
{
  my $first = 1;

  #&printHeader(); # standalone, but don't do this when embedded in Webmin

  opendir(D, $logdir);
  @files = grep {/^$logfile/} readdir(D);
  # the sort below puts the files in a consistent (and hopefully chronological) order
  @files = reverse sort partialnumeric @files;
  closedir(D);

  print "<small>\n";


  # list all the files we're going to analyze (possibly including compressed ones)
  $first = 1;
  foreach $file (@files) {
    next if (($file =~ m/\.gz$/) && ($sZ eq 'off'));
    if ($first) {
      print "<span style='color: darkred; font-size: smaller'>$text{'view_whichlogfiles'} $logdir:  $file";
      $first = 0;
    } else {
      print ", $file";
    }
  }
  print "</span><br>\n" if !$first;

  # go through all files and list compressed ones if we're not going to analyze them
  $first = 1;
  foreach $file (@files) {
    if ($file =~ m/\.gz$/) {
      if ($sZ eq 'off') {
        if ($first) {
          print "<span style='color: brown; font-size: smaller'>$text{'error_lognotcompressed'} $logdir:  $file";
          $first = 0;
        } else {
          print ", $file";
	}
        next;
      }
    }
  }
  print "</span><br>\n" if !$first;

  # print the standard filter-settings heading
  print "<br>\n";
  &printFilter();

  # go through contents of all files and print detail and/or count for summary
  if ($sD eq "on") {

    print "<hr style='height: 3'><small><i>\n";
    print "$text{'view_detailcaption1'}<br>\n";
    print "$text{'view_detailcaption2'}<br>\n" if $sG eq 'on'; 
    print "<a href='#'>" if $sL eq 'on';
    print "$text{'view_detailcaption3'}";
    print "</a>" if $sL eq 'on';
    print "<br>\n";
    print "<span style='color: #686828'>$text{'view_detailcaption4a'}</span><br>\n" if $sR eq 'on';
    print "<span style='color: #686828'>$text{'view_detailcaption4b'}</span><br>\n" if $sP eq 'on';
    print "<span style='color: red'>$text{'view_detailcaption5'}</span><br>\n";
    print "</i></small>\n";

  }
  foreach $file (@files) {
    $formaterrcountthislogfile = 0;
    our $logdirfile = "$logdir/$file";
    if ($file =~ m/\.gz$/) {
      if ($sZ eq 'on') {
        my $gz = gzopen($logdirfile,'r');
        if (!$gz) {
          $msg = "$text{'view_err_cannotopen'} ($logdirfile)<p>$text{'view_err_fixperms'}";
          &printMenu();	# try again
          &webminfooterandexit();
        }
        while ($gz->gzreadline($line)) {
          &checkLine($line);
        }
        $gz->gzclose;
      }
    } 
    else {
      unless (open(F,$logdirfile)) {
        $msg = "$text{'view_err_cannotopen'} ($logdirfile)<p>$text{'view_err_fixperms'}";
        &printMenu();	# try again
        &webminfooterandexit();
      }
      while ($line = <F>) {
        &checkLine($line);
      }
      close(F);
    }
  }

  our $messages = 0;
  if (($formaterrcount > ($linesRead * 0.001)) && ($linesRead > 3)) {
    print "<br><span style='color: brown'>$text{'error_warning'} $text{'view_err_notparse'}: $formaterrcount - $text{'view_err_logformat'}</span>\n";
    ++$messages;
  }
  if (($languageerrcount > ($linesRead * 0.001)) && ($linesRead > 3)) {
    print "<br><span style='color: brown'>$text{'error_warning'} $text{'view_err_notunderstood'}: $languageerrcount - $text{'view_err_language'}</span>\n";
    ++$messages;
  }
  if ((($noaddr - $formaterrcount) > ($linesRead * 0.35)) && ($linesRead > 3)) {
    print "<br><span style='color: brown'>$text{'error_noaddr'}</span>\n"; 
    ++$messages;
  }
  if ((($nouser - $formaterrcount) > ($linesRead * 0.35)) && ($linesRead > 3))  {
    print "<br><span style='color: brown'>$text{'error_nouser'}</span>\n";
    ++$messages;
  } 
  if ((($userisaddr - $formaterrcount) > ($linesRead * 0.35)) && ($linesRead > 3))  {
    print "<br><span style='color: brown'>$text{'error_userisaddr'}</span>\n";
    ++$messages;
  } 
  print "<br><br>\n" if $messages;

  if ($grandTotal > 0) {
    if ($sD eq 'on') {
      print "<hr style='height: 3'>\n";
      if (($sSumExc eq 'on') || ($sSumDen eq 'on') || ($sSumAlw eq 'on')) { print "<br><br>\n"; }
    }
    print "<div style='max-width: 1600px'><!-- begin summary tables, not off right edge of screen -->\n";
    my $first = 1;
    if ($sSumExc eq "on") {
      if ($first) { $first = 0; } else { print "<br><br>\n"; }
      print "<center><span style='padding: 1ex; border: 1px greenyellow solid; font-size: larger; font-weight: 800'>" . uc($text{'view_exception'}) . ' ' . ucfirst($text{'view_summaries'}) . "</span></center><br><br>\n";
      if ($exceptionTotal != 0) {
        foreach my $order (keys %order2source) {
          $hashname = "exception$order";
          &showSummary($exceptionTotal,'exception',$sSumCnt,$order,%$hashname);
        }
      }
      print "<br><hr style='height: 3'>\n";
    }
    if ($sSumDen eq "on") {
      if ($first) { $first = 0; } else { print "<br><br>\n"; }
      print "<center><span style='padding: 1ex; border: 1px greenyellow solid; font-size: larger; font-weight: 800'>" . uc($text{'view_denied'}) . ' ' . ucfirst($text{'view_summaries'}) . "</span></center><br><br>\n";
      if ($deniedTotal != 0) {
        foreach my $order (keys %order2source) {
          $hashname = "denied$order";
          &showSummary($deniedTotal,'denied',$sSumCnt,$order,%$hashname);
        }
      }
      print "<br><hr style='height: 3'>\n";
    }
    if ($sSumAlw eq "on") {
      if ($first) { $first = 0; } else { print "<br><br>\n"; }
      print "<center><span style='padding: 1ex; border: 1px greenyellow solid; font-size: larger; font-weight: 800'>" . uc($text{'view_allowed'}) . ' ' . ucfirst($text{'view_summaries'}) . "</span></center><br><br>\n";
      if ($allowedTotal != 0) {
        foreach my $order (keys %order2source) {
          $hashname = "allowed$order";
          &showSummary($allowedTotal,'allowed',$sSumCnt,$order,%$hashname);
        }
      }
      print "<br><hr style='height: 3'>\n";
    }
    print "</div><!-- end summary tables -->\n";

    print "</small>\n";

  } else {

    print "</small>\n";
    print "<br><center><span style='padding: 1ex; border: 1px orange solid; font-weight: 600'>$text{'view_no'}</span></center><br>\n";

  }

  &printTotals();

}

#################
sub initConstants
#################
{
# without some sort of "terminator" on the subreason, can get into doing an awful lot of
#  backtracking with attendant horrid performance - performance problem is very noticeable

# test for "terminator" has to be a little careful though, stopping before GET and POST and
#  CONNECT, but _not_ SSL - which can legitimately be in the middle of the subreason field

$parseactionsandreasonregexp = '(?:((?:\*(?!(?:DENIED|EXCEPTION))[A-Z]{6,}\* ?)*) )?(?:(\*(?:DENIED|EXCEPTION)\*) )?(?:([^.:* ][^.:]*)\.?(?::+ +((?:(?! [A-R][A-R][A-Z]).)+))? +)?';
$parsetoeolregexp = '^ *' . $parseactionsandreasonregexp . '([A-Z]{3,8}) (\d+) (?:(-?\d+) )?(?:((?:(?!\d\d? )[^ ]+ )*(?!\d\d? )[^ ]+) )?(?:([1-9]\d?) )?(?:(\d\d\d) )?(?:(-|[-\w]+\/[-_.\w]+) )?(?:(\w[-_\w]*(?:\.[-_\w]+)+) )?(?:([a-zA-Z][^ ]*) )?(?:([a-zA-Z][^ ]*\d.+ .*[^ ]) )? *$';
($parsetoeolregexpjr = $parsetoeolregexp) =~ s/\((?:[^()]*|[^()]*\([^()]*\)[^()]*|[^()]*\([^()]*\([^()]*\)[^()]*\)[^()]*)\)[^()]*$/()/;
}

#########################
sub clearRequestVariables
#########################
{
    $cl1 = '';
    $date = '';
    $time = '';
    $user = '';
    $ip = '';
    $url = '';
    $protocol = '';
    $allbutprotocol = '';
    $baseurl = '';
    $queryurl = '';
    $sitename = '';
    $protocolandsitename = '';
    $urlpath = '';
    $cl2 = '';
    $otheractions = '';	# URLMOD, CONTENTMOD, SCANNED, INFECTED, etc.
    $action = '';	# DENIED or EXCEPTION etc., if exists
    $reason = '';	# Reason for 1 if exists
    $reasonjr = '';	# Same except with trailing number deleted for standardized comparisons
    $subreason = '';	# Detail supporting reason (maybe Regular Expression, maybe Phrases, maybe...)
    $subreasonjr = '';	# Same except with leading number (score) deleted for better appearance
    $method = '';	# method (GET or POST  ...or maybe CONNECT)
    $size = '';		# Size of webpage/document in bytes
    $weight = '';	# Calculated weight/score
    $category = '';	# Principal #listcategory's contributing to disposition of request
    @categoryeach = ();	# Individual #listcategory's
    $filtergroupnum = '';	# 1-based number of filter group request was actually assigned to
    $retcode = '';	# HTTP return code
    $mimetype = '';	# MIME type of requested webpage/document according to remote server
    $clientname = '';	# Client host name (reversed from IP above)
    $filtergroup = '';	# Filter group name (assume no whitespace) (same as fg# above but more convenient)
    $browseragent = '';	# browser Agent string (hard to parse because so variable)
}

######################
sub canonicalizereason
######################
{
	my $reasonout = $_[0];
	return '' if !$reasonout;
	# probable future change: delete leading and trailing numbers too as they're always variable
	$reasonout =~ s/^\s+//;
	$reasonout =~ s/[\s:;.,!?]+$//;
	return $reasonout;
}

#############
sub checkLine
#############
{
  my ($line) = @_;
  chomp $line;

  $linesRead++;

  # Print out a single character every bunch of log file lines read. 
  # Doing this keeps the browser connection alive and prevents browser timeouts
  #  (it also reassures the interactive human user that we're still doing something)
  if (($linesRead % 2000) == 0) {
    print defined $sTITLE ? ' ' : '.';	# use non-blank to reassure user if interactive
						# (if batch use blank to avoid defacing report)
    # (the performance is definitely not great, as we re-evaluate interactive/batch every
    #  time we print a character rather than doing it just once  ...but who cares?)
  } 

  &clearRequestVariables();	# this is probably unnecessary paranoia, but do it anyway
				# it prevents errors with weird input, and it guarantees
				#  correct operation of some of the sub-parsing

  goto qw(UNK NATIVE DELIM NOTSUPP DELIM)[$logfileformat];
  UNK: {
    $msg = "$text{'error_logfileformat_range'} ($logfileformat)";
    &printMenu();	# try again
    &webminfooterandexit();
  }
  NOTSUPP: {
    print "<span style='color: brown'>$text{'error_logfileformat_notsupp'}<br>$text{'view_logfileformat'}: $logfileformat</span><p>\n";
    &webminfooterandexit();
  }
  DELIM: {
    $separator = ( qr//, qr//, qr/"\s*,\s*"/, qr//, qr/\t/ )[$logfileformat];
    ($cl1, $user, $ip, $url, $cl2, $method, $size, $weight, $category, $filtergroupnum, $retcode, $mimetype, $clientname, $filtergroup, $browseragent) = split $separator, $line, 15; 
    ($date,$time) = ($cl1 =~ m/^\s*"?([^"\s]\S+)\s+(\S+[^"\s])"?\s*$/);
    $cl2 =~ s/\s*$/ /;	# add trailing space to be sure actions&reason regexp works right
    ($otheractions, $action, $reason, $subreason) = ($cl2 =~ m/^\s*$parseactionsandreasonregexp\s*$/);
    $browseragent =~ s/\s+$//;	# clean up by trimming right in case unclean parse
    goto ENDCASE;
  }
  NATIVE: {
  ($date,$time,$user,$ip,$url,$toeol) = split(/ /,$line,6);
  "" =~ /()()()()()()()()()()()()()()/;	# preset all match vars to nothing just in case this doesn't pars
  $toeol =~ s/\s*$/ /;	# be sure there's a space tacked onto the end, makes our regexps much simpler
  $toeol =~ s/\s{2,}/ /g;	# reduce all multiple whitespace sequences to a single space each
			#  (arguably this loses a bit of information, but it makes our regexps _much_ simpler)
  ($otheractions, $action, $reason, $subreason, $method, $size, $weight, $category, $filtergroupnum, $retcode, $mimetype, $clientname, $filtergroup, $browseragent) = ($toeol =~ m/$parsetoeolregexp/);
  # if parse failure, try again without "agent string" & end anchor ($browseragentstring will be blank)
  ($otheractions, $action, $reason, $subreason, $method, $size, $weight, $category, $filtergroupnum, $retcode, $mimetype, $clientname, $filtergroup, $browseragent) = ($toeol =~ m/$parsetoeolregexpjr/) if (!$otheractions && !$action && !$reason && !$subreason && !$method);
  goto ENDCASE;
  }

  # different parsing options all come back together here - we're back to common code
  ENDCASE: 
  # finish subsplitting a few more things
  if ($url) {
    # (note assumption variables are initially empty strings)
    ($protocol, $allbutprotocol) = ($url =~ m{(\w+)://+(.*)$});
    $protocol = '' if !$protocol;
    $allbutprotocol = '' if !$allbutprotocol;
    ($baseurl, $queryurl) = split /\?/, $allbutprotocol, 2;
    $baseurl = '' if !$baseurl;
    $queryurl = '' if !$queryurl;
    ($sitename, $urlpath) = ($baseurl =~ m{^(?:([^/:]+)(?::\d+)?|\w)(?:/+(.*))?$});
    $sitename = '' if !$sitename;
    $urlpath = '' if !$urlpath;
    $protocolandsitename = "$protocol://$sitename";
    # protocol part of url (HTTP, FTP, etc.)
    # baseurl is part without http:// or ftp:// and without the query part
    # sitename is just the part of the baseurl before the first '/'
    # urlpath is the part after the first '/' and before the '?'
  }
  @categoryeach = split(/\s*,\s*/, $category) if $category;
  # (note assumption that @categoryeach is initially empty)
  map s/^\((.*)\)$/$1/, @categoryeach;

  # do some modifications to make the data more friendly for us even if logged weirdly
  if (!$action && exists $exceptionreasons_text2number{&canonicalizereason($reason)}) {
    # may not be flagged if logexceptionhits=1 in dansguardian.conf, make it seem as though logexceptionhits=2
    $action = '*EXCEPTION*';
  }
  #
  if (exists $blanketreasons_text2number{&canonicalizereason($subreason)}) {
    # "promote" canonicalized blanket reasons to full reason
    $subreasonjr = &canonicalizereason($subreason);
    $reasonjr = $subreasonjr;
  } else {
    # calculate modified versions of a couple variables to make our comparisons easier
    # (note these assume reasonjr and subreasonjr are initially empty strings '')
    ($reasonjr = $reason) =~ s/\s+\d+\s*$// if $reason;	# canonicalize for comparisons (remove 'naughtynesslimit')
    ($subreasonjr = $subreason) =~ s/^\s*\d+\s+// if $subreason;	# remove score repeat to improve display
  }

#following line useful for debugging, would delete it except too much detailed typing
#print DEBUGLOG "line: [$line] (toeol: [$toeol]) --parsed to: date=$date, time=$time, user=$user, ip=$ip, url=$url(protocol=$protocol, allbutprotocol=$allbutprotocol, protocolandsitename=$protocolandsitename, baseurl=$baseurl, sitename=$sitename, urlpath=$urlpath, queryurl=$queryurl), otheractions=$otheractions, action=$action, reason=$reason (reasonjr=$reasonjr), subreason=$subreason (subreasonjr=$subreasonjr), method=$method, size=$size, weight=$weight, category=$category (categoryeach=@categoryeach), filtergroupnum=$filtergroupnum, retcode=$retcode, mimetype=$mimetype, clientname=$clientname, filtergroup=$filtergroup, browseragent=$browseragent ;; sA=$sA, sA2=$sA2<br>\n";

  # try to "canonicalize" the data
  # (don't mess with IP, USER, or URL(Domain) for now,
  #  as doing so before there's _full_ support
  #  screws up the "click for details" functionality)
  @categoryeach = ( '-' ) if ! $category;
  $category = '-' if ! $category;
  $retcode = '???' if ! $retcode;
  $mimetype = '-' if ! $mimetype;
  $filtergroup = '-' if ! $filtergroup;
  $browseragent = '-' if ! $browseragent;
  $ip = '-' if !$ip;
  $user = '-' if !$user;

  # don't swap in local names for IPs where known for now, 
  #  as it's not _fully_ supported yet 
  # the shortcut below at first appears to work, 
  #  but in fact causes problems with the "click for details" functionality
  ##$ip = $clientname if length $clientname > 1;

  # issue an error message (a few times) if we have a problem
  my $parseokcount = 0;
  ++$parseokcount if $ip;
  ++$parseokcount if $sitename;
  ++$parseokcount if $urlpath;
  ++$parseokcount if $action;
  ++$parseokcount if $reason;
  ++$parseokcount if $method;
  ++$parseokcount if $retcode;
  if ($parseokcount < 4) {
    print DEBUGLOG "in Log Analysis determined parse was screwed up so blanking everything\n" if $debug;
#print DEBUGLOG "just before blank because of misparse: line: [$line] (toeol: [$toeol]) --parsed to: date=$date, time=$time, user=$user, ip=$ip, url=$url(protocol=$protocol, allbutprotocol=$allbutprotocol, protocolandsitename=$protocolandsitename, baseurl=$baseurl, sitename=$sitename, urlpath=$urlpath, queryurl=$queryurl), otheractions=$otheractions, action=$action, reason=$reason (reasonjr=$reasonjr), subreason=$subreason (subreasonjr=$subreasonjr), method=$method, size=$size, weight=$weight, category=$category (categoryeach=@categoryeach), filtergroupnum=$filtergroupnum, retcode=$retcode, mimetype=$mimetype, clientname=$clientname, filtergroup=$filtergroup, browseragent=$browseragent ;; sA=$sA, sA2=$sA2<br>\n";
    print "<p align=center><span style='color: red; font-weight: bold;'>$text{'error_warning'}  $text{'view_err_notparse'} - $text{'view_err_logformat'}</span><br><i>example ($file):</i> $line<p>\n" if (($formaterrcountthislogfile < 1) && !$sTITLE);
    ++$formaterrcount;
    ++$formaterrcountthislogfile;
    # since we've determined the parse was screwed up, 
    #  completely blank ALL fields to make it very clear this is a failure
    #  and so (hopefully) not pollute the reports
    &clearRequestVariables();
  }

  # keep count of items we could not understand, probably because they were in a different language
  if (($reasonjr !~ m/^[-_+=.,:;\s]*$/) && (! exists $reasons_text2number{&canonicalizereason($reasonjr)})) {
    ++$languageerrcount;
  }

  # keep counts to figure out what kind of data we were given
  ++$noaddr if ((length($ip) <= 3) || ($ip =~ m/^\s*0+\./));
  if (length($user) <= 3) {
    ++$nouser;
  } else {
    ++$userisaddr if $user !~ m/^\D{4,}$/;
  }

  # keep choice lists complete
  map $categories{lc $_}=1, @categoryeach;
  $listchanged_categories = 1;
  $mimetypes{lc $mimetype} = 1;
  $listchanged_mimetypes = 1;
  $filtergroups{lc $filtergroup} = 1;
  $listchanged_filtergroups = 1;

  # no further processing on records that don't match filter
  # Rule out the easy matches first 
  if ($sIP ne 'ALL') {
    my ($addrpart, $cidrpart) = split qr(\s*[-\\/:]\s*), $sIP, 2;
    $addrpart = $sIP if ! defined $addrpart;
    $cidrpart = 32 if ! $cidrpart;
    my $numericaddrpart = &octets2numeric($addrpart);
    my $numericactual = &octets2numeric($ip);
    my $binmask = &cidr2binmask($cidrpart);
    return if (($numericactual & $binmask) != ($numericaddrpart & $binmask));
  }
  return if (($sUN ne 'ALL') && ($sUN !~ m/^$user$/i));

  # Rule out further matches
  return if (($sCAT ne 'ALL') && (!existsinarray($sCAT, 'ignorecase', @categoryeach)));
  return if (($sMIME ne 'ALL') && ($mimetype !~ m/^\s*$sMIME/i));
  return if (($sGRP ne 'ALL') && ($sGRP !~ m/^$filtergroup$/i));
  return if (($sAGT ne 'ALL') && ($browseragent !~ m/$sAGT/i));
  return if (($sSN ne 'ALL') && ($protocolandsitename !~ m/$sSN$/i)); 

  # don't do a date comparison unless we are told to
  if ($sSD ne 'ALL' || $sED ne 'ALL') {
    $dgDate = &convertDate($date);
    return if (($sSD ne 'ALL') && ($dgDate lt $sSD));
    return if (($sED ne 'ALL') && ($dgDate gt $sED));
  }

  # filter action/reason
  if ($sA ne 'ALL') {
    return if (($sA eq 'exceptionALL') &&
      ($action ne '*EXCEPTION*'));
    return if (($sA eq 'deniedALL') &&
      ($action ne '*DENIED*'));
    return if (($sA eq 'allowALL') &&
      ($action eq '*DENIED*'));
    $privatereason = &canonicalizereason($reasonjr);
    foreach my $number (keys %reasons_number2text) {
      # find the one matching reason, process it, and exit this loop
      next if $number != $sA;
      my $reasontext = &canonicalizereason($reasons_number2text{$number});
      return if $privatereason ne $reasontext;
      last;
    }
  }
  # filter action again against second criteria if following hyperlink
  if ($sA2 ne 'ALL') {
    return if (($sA2 eq 'exceptionALL') &&
      ($action ne '*EXCEPTION*'));
    return if (($sA2 eq 'deniedALL') &&
      ($action ne '*DENIED*'));
    return if (($sA2 eq 'allowALL') &&
      ($action eq '*DENIED*'));
  }


  # filter by weight(score) if specified 
  if ($sWGHT ne 'ALL') {
    return if (! eval "$weight $sWGHT");
  }

#print "next record summary counts, action=$action, sSumExc=$sSumExc, sSumDen=$sSumDen, sSumAlw=$sSumAlw<br>\n";

  # Anything that gets this far has "passed the filter", so count it
  $grandTotal++;
#print DEBUGLOG "matched filter: line: [$line] (toeol: [$toeol]) --parsed to: date=$date, time=$time, user=$user, ip=$ip, url=$url(protocol=$protocol, allbutprotocol=$allbutprotocol, protocolandsitename=$protocolandsitename, baseurl=$baseurl, sitename=$sitename, urlpath=$urlpath, queryurl=$queryurl), otheractions=$otheractions, action=$action, reason=$reason (reasonjr=$reasonjr), subreason=$subreason (subreasonjr=$subreasonjr), method=$method, size=$size, weight=$weight, category=$category (categoryeach=@categoryeach), filtergroupnum=$filtergroupnum, retcode=$retcode, mimetype=$mimetype, clientname=$clientname, filtergroup=$filtergroup, browseragent=$browseragent ;; sA=$sA, sA2=$sA2<br>\n";

  # Do summary processing if ANY summary selected
  if ($sSumAlw eq "on" || $sSumDen eq "on" || $sSumExc eq "on") {
    if (($action eq '*EXCEPTION*') && ($sSumExc eq 'on')) {
      $exceptionTotal++;
      # Don't waste memory if didn't want this
      while (($order, $source) = each %order2source) {
        $hashname = "exception$order";
        $$hashname{$$source} ++;
      }
    }
    if (($action eq '*DENIED*') && ($sSumDen eq 'on')) {
      $deniedTotal++;
      # Don't waste memory if didn't want this
      while (($order, $source) = each %order2source) {
        $hashname = "denied$order";
	$$hashname{$$source} ++;
      }
    }
    if (($action ne '*DENIED*') && ($sSumAlw eq 'on')) {
      $allowedTotal++;
      # Don't waste memory if didn't want this
      while (($order, $source) = each %order2source) {
        $hashname = "allowed$order";
	$$hashname{$$source} ++;
      }
    }
  }
  if (($sD eq 'on') && ($date ne '')) {
    my $displayip = $clientname ? "$ip($clientname)" : $ip;
    print "<br>$date &nbsp; $time &nbsp; $displayip &nbsp; $user &nbsp; $filtergroup &nbsp; $method &nbsp; $size &nbsp; $mimetype &nbsp; $category &nbsp; $weight<br>\n";
    print "$browseragent<br>\n" if (($sG eq 'on') && ($browseragent !~ m/^[-_+=.,:;\s]*$/));
    if ($sL eq 'on') {
      print "<a href='$url' target=_blank>$url</a><br>\n";
    } else {
      print "$url<br>\n";
    }
    if ($sR eq 'on') {
        # former hack ($reason =~ m/reg[uo]|compr/i) replaced with real working totally language-independent test
        if (exists $regexpreasons_text2number{$reason}) {
	($modpattern = $subreason) =~ s/\(\?:/\(/g;
	($modurl = $allbutprotocol) =~ s!$modpattern!<span style='color: #686828; text-decoration: underline'>$&</span>!i;
            my $escapedsubreason = &html_escape($subreason);
	print "<span style='color: #686828'>$escapedsubreason</span>&nbsp;$text{'view_matched'}=>&nbsp;$protocol://$modurl<br>\n";
	my %completedranges = ();
	my $first = 1;
	SUBSTRING: for my $i (1..$#-) {
	        $substring = $$i;
		next if !$substring;
	        #print "$i: $-[$i] - $+[$i] = $$i<br>\n";
	        if (($substring =~ m/^\W?\w{3,}\W?/) || ($substring =~ m/^\W{0,2}\w{4,}\W{0,2}$/) || ($substring =~ m/^\W{0,3}\w{5,}\W{0,3}$/) || ($substring =~ m/\w{6,}/)) {
		while (my ($left, $right) = each %completedranges) {
		        if (($-[$i] >= $left) && ($+[$i] <= $right)) {
			# this "word" was already included in a larger "word" that was already processed
			#print "superceded by completedranges $left $right<br>\n";
			next SUBSTRING; 
		        }
		}
		$completedranges{$-[$i]} = $+[$i]; 
		if ($first) {
		        print "$text{'view_matchterms'}: <span style='color: #686828'>";
		        $first = 0;
		} else {
		        print "</span>, <span style='color: #686828'>";
		}
                $substring =~ s/^\W+//;	# trim away things that are obviously not part of a word
                $substring =~ s/\W+$//;	# trim away things that are obviously not part of a word
		print "$substring";
	        }
	}
	print "</span><br>\n" if ! $first;
        }
    }
    if ($sP eq 'on') {
        if (exists $phrasereasons_text2number{$reasonjr}) {
            print "<span style='color: #686828'>$subreasonjr</span><br>\n";
        }
    }
    if ($action ne '' && $reason ne '') {
      print "<span style='color: red'>$action : $reason";
      print ": $reasonjr" if $reason !~ m/$reasonjr/;
      print "</span><br>\n";
    }
  }
}

#############
sub printMenu
#############
{
  #&printHeader(); # standalone, but don't do this when embedded in Webmin

  print "
    <form action=$cgipath name=mainmenu><input type=hidden name=a value='i'>
    <table align=center bgcolor=ffffff border=1 cellpadding=7 cellspacing=1>\n";
  if ($msg ne "") {
    print "<tr><td colspan=3 bgcolor=c80000 align=center>
           <font face=arial,helvetica,sans-serif size=3><b>$msg</b>
           </font></tr>\n";
  }
  
  # "Filter" section title
  print "
  <tr bgcolor=#e0e0e0>
  <th colspan=3>" .
    uc($text{'view_requestfilters'}) . "<br>($text{'view_anded'})
  </th>
  </tr>\n";

  # Filter items column headings
  print "
  <tr bgcolor=#f0f0f0>
  <th>
    $text{'view_parameter'}
  </th>
  <th>
    $text{'view_value'}
  </th>
  <th width=30%>
    $text{'view_description'}
  </th></tr>\n";

  # Menu item for entering date ranges
  print "<script type=text/javascript>
  function setALLStartDates(myself)
  {
    if (myself.selectedIndex > 1) return;

    myself.form.sSDY.selectedIndex = 0;
    myself.form.sSDM.selectedIndex = 0;
    myself.form.sSDD.selectedIndex = 0;
  }
  function setALLEndDates(myself)
  {
    if (myself.selectedIndex > 1) return;

    myself.form.sEDY.selectedIndex = 0;
    myself.form.sEDM.selectedIndex = 0;
    myself.form.sEDD.selectedIndex = 0;
  }
  function setNewStartDates(myself)
  {
    var field;
    field = myself.form.sSDY;
    if (field.selectedIndex == 0) { field.selectedIndex = 2; } 
    field = myself.form.sSDM;
    if (field.selectedIndex == 0) { field.selectedIndex = 2; } 
    field = myself.form.sSDD;
    if (field.selectedIndex == 0) { field.selectedIndex = 2; } 
  }
  function setNewEndDates(myself)
  {
    var field;
    field = myself.form.sEDY;
    if (field.selectedIndex == 0) { field.selectedIndex = 2; } 
    field = myself.form.sEDM;
    if (field.selectedIndex == 0) { field.selectedIndex = 2; } 
    field = myself.form.sEDD;
    if (field.selectedIndex == 0) { field.selectedIndex = 2; } 
  }
  </script>\n";
  print "
  <tr><td align=left>
    Enter $text{'field_daterange'}
    <br>
  </td>
  <td align=left>
    $text{'field_startdate'}<br>
    <select name=sSDY onChange='setNewStartDates(this);setALLStartDates(this);'>";
  &buildSelect(2002,2020,$year,$sSDY);
  print "</select><select name=sSDM onChange='setNewStartDates(this);setALLStartDates(this);'>";
  &buildSelect(01,12,$mon,$sSDM);
  print "</select><select name=sSDD onChange='setNewStartDates(this);setALLStartDates(this);'>";
  &buildSelect(01,31,$mday,$sSDD);
  print "</select><br>
    $text{'field_enddate'}<br>
    <select name=sEDY onChange='setNewEndDates(this);setALLEndDates(this);'>";
  &buildSelect(2002,2020,$year,$sEDY);
  print "</select><select name=sEDM onChange='setNewEndDates(this);setALLEndDates(this);'>";
  &buildSelect(01,12,$mon,$sEDM);
  print "</select><select name=sEDD onChange='setNewEndDates(this);setALLEndDates(this);'>";
  &buildSelect(01,31,$mday,$sEDD);
  print "</select>
  </td>
  <td align=center>
    Either specify a start date and end date,
    or set <i>any</i> field to '--ALL--'
    to include all the request records
    available in the logs directory
    regardless of their date.
  </td></tr>\n";

  # Menu item for IP viewing
  print "
  <tr><td align=left>
    Enter $text{'field_ipaddress'}
  </td>
  <td align=left>
    <input name=sIP maxlength=35 size=20 value='$sIP'>
  </td>
  <td align=center>
    examples:<br>
    for a single system 172.16.34.45,<br>
    for a whole subnet 172.16.0.0/12<br>(or equivalently 172.16.0.0/255.240.0.0)
  </td></tr>
  <script>
    if (document.mainmenu.sIP.value == 'ALL') document.mainmenu.sIP.value = '';
  </script>\n";

  # Menu item for username viewing
  print "
  <tr><td align=left>
    Enter a $text{'field_username'}
  </td>
  <td align=left>
    <input name=sUN maxlength=35 size=20 value='$sUN'>
  </td>
  <td align=center>
    authplugin(s) should be enabled and functioning<br>
  </td></tr>
  <script>
    if (document.mainmenu.sUN.value == 'ALL') document.mainmenu.sUN.value = '';
  </script>\n";
  
  # Menu item for sitename (domain) viewing
  print "
  <tr><td align=left>
    Enter a Site (domain) Name
  </td>
  <td align=left>
    <input name=sSN maxlength=50 size=20 value='$sSN'>
  </td>
  <td align=center>
    Enter the www.domain.com part of a URL only<br>
    (just 'domain' without 'www' or 'com' or dots is okay)
  </td></tr>
  <script>
    if (document.mainmenu.sSN.value == 'ALL') document.mainmenu.sSN.value = '';
  </script>\n";
  
  # menu item for (browser) agent
  print "
  <tr><td align=left>
    Enter any section of an $text{'field_agent'} string
  </td>
  <td align=left>
    <input name=sAGT maxlength=50 size=20 value='$sAGT'>
  </td>
  <td align=center>
    Enter any part of an agent string<br>
    to for example identify<br>
    a browser type or a browser version<br>
    or a platform or an operating system
  </td></tr>
  <script>
    if (document.mainmenu.sAGT.value == 'ALL') document.mainmenu.sAGT.value = '';
  </script>\n";
  
  # menu item for weight(score)
  print "
  <tr>
    <td align=left>
      Choose a $text{'field_weight'}
    </td>
    <td align=left>
      <select name=sWD onChange='if (this.selectedIndex <= 1) { this.selectedIndex=0; this.form.sWN.value=\"\";}'>
        <option value='' disabled></option>
        <option value='ALL'>--ALL--</option>
        <option value='&lt;='"; print " selected" if ($sWD eq '<'); print ">&lt;=</option>
        <option value='&gt;='"; print " selected" if ($sWD eq '>'); print ">&gt;=</option>
      </select>
      <input name=sWN maxlength=3 size=3 value='$sWN' onBlur='if (this.value == \"\") this.form.sWD.selectedIndex = 0;'>
    </td>
    <td align=center>
      Specify either 'less than or equal' or 'greater than or equal' and a number (the $text{'field_weight'}).
      <br>(Unscanned requested files are treated as having $text{'field_weight'} 0.)
    </td>
  </tr>
  <script>
    if (document.mainmenu.sWD.selectedIndex <= 1) document.mainmenu.sWD.selectedIndex = 0;
    if (document.mainmenu.sWN.value == 'ALL') document.mainmenu.sWN.value = '';
  </script>\n";

  # Menu item for categories
  print "
  <tr>
    <td align=left>
      Choose a $text{'field_category'}
    </td>
    <td align=left>
      <input name=sCAT maxlength=35 size=20 value='$sCAT'>
      <select name=sCATdrop onChange='this.form.sCAT.value=this.options[this.selectedIndex].value;this.selectedIndex=0'><option value='' disabled></option><option value='' selected>--ALL--</option>\n";
      foreach $category (sort ignorecase keys %categories) {
        print "<option value='$category'>$category</option>\n";
      } 
  print "
      </select>
    </td>
    <td align=center>
      Use whatever $text{'field_category'} names you have defined in your #listcategory statements.
    </td>
  </tr>
  <script>
    if (document.mainmenu.sCATdrop.selectedIndex <= 1) document.mainmenu.sCATdrop.selectedIndex = 0;
    if (document.mainmenu.sCAT.value == 'ALL') document.mainmenu.sCAT.value = '';
  </script>\n";

  # Menu item for mimetype
  print "
  <tr>
    <td align=left>
      Choose a $text{'field_mimetype'}
    </td>
    <td align=left>
      <input name=sMIME maxlength=30 size=20 value='$sMIME'>
      <select name=sMIMEdrop onChange='this.form.sMIME.value=this.options[this.selectedIndex].value;this.selectedIndex=0'><option value='' disabled></option><option value='' selected>--ALL--</option>\n";
      $prevmajormime = '';
      foreach $mimetype (sort ignorecase keys %mimetypes) {
        ($majormime = $mimetype) =~ s{/[^/]*$}{/}; 
        if (($majormime ne $prevmajormime) && ($majormime =~ m{/})) {
          print "<option value='$majormime'>${majormime}ALL</option>\n";
          $prevmajormime = $majormime;
        }
        print "<option value='$mimetype'>$mimetype</option>\n";
      } 
  print "
      </select>
    </td>
    <td align=center>
      Use any $text{'field_mimetype'}  names.
    </td>
  </tr>
  <script>
    if (document.mainmenu.sMIMEdrop.selectedIndex <= 1) document.mainmenu.sMIMEdrop.selectedIndex = 0;
    if (document.mainmenu.sMIME.value == 'ALL') document.mainmenu.sMIME.value = '';
  </script>\n";

  # Menu item for filtergroup
  print "
  <tr>
    <td align=left>
      Choose a $text{'field_filtergroup'}
    </td>
    <td align=left>
      <input name=sGRP maxlength=35 size=20 value='$sGRP'>
      <select name=sGRPdrop onChange='this.form.sGRP.value=this.options[this.selectedIndex].value;this.selectedIndex=0'><option value='' disabled></option><option value='' selected>--ALL--</option>\n";
      foreach $filtergroup (sort ignorecase keys %filtergroups) {
        print "<option value='$filtergroup'>$filtergroup</option>\n";
      } 
  print "
      </select>
    </td>
    <td align=center>
      Use the $text{'field_filtergroup'} names you have defined in your dansguardianfN.conf files with 'groupname = ...'.
    </td>
  </tr>
  <script>
    if (document.mainmenu.sGRPdrop.selectedIndex <= 1) document.mainmenu.sGRPdrop.selectedIndex = 0;
    if (document.mainmenu.sGRP.value == 'ALL') document.mainmenu.sGRP.value = '';
  </script>\n";

  # Menu item for action/reason
  print "
  <tr><td align=left>
    Choose a $text{'field_reason'}
  </td>
  <td align=left>
    <select name=sA onChange='if (this.selectedIndex <= 1) this.selectedIndex = 0;'>
    <option value='ALL' disabled></option>
    <option value='ALL'>Show ALL</option>
    <option value='' disabled>---------------</option>
    <option value='exceptionALL'"; print " selected" if ($sA eq 'exceptionALL'); print ">Show ALL " . uc($text{'view_exception'}) . "</option>
    <option value='deniedALL'"; print " selected" if ($sA eq 'deniedALL'); print ">Show ALL " . uc($text{'view_denied'}) . "</option>
    <option value='allowALL'"; print " selected" if ($sA eq 'allowALL'); print ">Show ALL " . uc($text{'view_allowed'}) . " ($text{'view_not'} " . ucfirst($text{'view_denied'}) . ")</option>
    <option value='' disabled>===============</option>\n";
    my $verytop = 1;
    my $prevfirstword = '';
    foreach my $reasontext (sort ignorecase keys %reasons_text2number) {
      $number = $reasons_text2number{$reasontext};
      my ($firstword, $remainder) = split ' ', $reasontext, 2;
      $firstword = lc $firstword;
      if (($firstword ne $prevfirstword) && (! $verytop)) {
        print "<option value='' disabled>---------------</option>";
      }
      $prevfirstword = $firstword;
      $verytop = 0;
      print "<option value='$number'"; print " selected" if ($number eq $sA); print ">$reasontext</option>\n";
    }
  print "
    </select>
   
  </td>
  <td align=center>
    Must do only one at a time.
  </td></tr>
  <script>
    if (document.mainmenu.sA.selectedIndex <= 1) document.mainmenu.sA.selectedIndex = 0;
  </script>\n";
  
  # "Options" section title
  print "
  <tr bgcolor=#e0e0e0>
  <th colspan=3>" .
    uc($text{'view_reportoptions'})
  . "</th>
  </tr>\n";

  # Menu item for selecting summary statistics
  print "
  <tr><td colspan=2 align=left>
    Show $text{'view_summaries'} information for the $text{'view_top'}  
    <input maxlength=3 size=5 name=sSumCnt value='$sSumCnt'>\n";
    foreach my $choice (values %what2varname) {
      print "<input type=hidden name=$choice value='$$choice'>\n";
    }
  print "
  #  </select>
  </td>
  <td align=center>
    Will summarize the top sites for the criteria specified.
  </td></tr>\n";

  # Menu items for checkboxes that modify report 
  print "
  <tr>
    <td align=left colspan=2>
     <input type=checkbox name=sD"; print (($sD eq 'on') ? " checked" : ""); print " onChange='if(this.checked){this.form.sR.checked=true;this.form.sG.checked=true;this.form.sP.checked=true;}else{this.form.sR.checked=false;this.form.sG.checked=false;this.form.sP.checked=false;}'>Check to also display details of individual (line-by-line) $text{'view_requests'}.<br>
     &nbsp;&nbsp;<input type=checkbox name=sR"; print (($sR eq 'on') ? " checked" : ""); print " onChange='this.form.sD.checked=true;'>Check to also display regular expression match information.<br>
     &nbsp;&nbsp;<input type=checkbox name=sP"; print (($sP eq 'on') ? " checked" : ""); print " onChange='this.form.sD.checked=true;'>Check to also display phrase match information.<br>
     &nbsp;&nbsp;<input type=checkbox name=sG"; print (($sG eq 'on') ? " checked" : ""); print " onChange='this.form.sD.checked=true;'>Check to also display agent string information.<br>
     <input type=checkbox name=sZ"; print (($sZ eq 'on') ? " checked" : ""); print ">Check to <i>include</i> compressed (gzip'ed) log files.<br>
     <input type=checkbox name=sL"; print (($sL eq 'on') ? " checked" : ""); print ">Check to make data displayed in detail lists be clickable links.<br>
    </td>
    <td align=center>
	Each option will modify the displayed report.
    </td>
  </tr>\n";

  # "Future" section title
  print "
  <tr bgcolor=#e0e0e0>
  <th colspan=3>" .
    uc($text{'view_futureoptions'})
  . "</th>
  </tr>\n";

  # Menu items for checkboxes that modify report 
  print "
  <tr>
    <td align=left colspan=2>
     <input type=checkbox name=sRC"; print (($sRC eq 'on') ? " checked" : ""); print ">Check to reset list of $text{'field_category'} before the next report is specified.<br>
     <input type=checkbox name=sRM"; print (($sRM eq 'on') ? " checked" : ""); print ">Check to reset list of $text{'field_mimetype'} before the next report is specified.<br>
     <input type=checkbox name=sRG"; print (($sRG eq 'on') ? " checked" : ""); print ">Check to reset list of $text{'field_filtergroup'} before the next report is specified.<br>
    </td>
    <td align=center>
	Each option will clear a list of choices available when specifying the next report.
    </td>
  </tr>\n";

  # End of form
  print "</table> ";

  print "<br>
     <center>
     Click the [$text{'button_run'}] Button Below to Start<p>
     <img src=images/transparent1x1.gif border=0 height=1 width=30>
     <input type=submit value='$text{'button_run'}'>
     <img src=images/transparent1x1.gif border=0 height=1 width=50>
     <input type=reset value='$text{'button_reset'}'>
     </center>\n";

  print "</form>\n";

  # section presenting batch report scaffolding file
  # (download, view, etc.)
  print "<p>&nbsp;<p><hr><p><hr><center><div style='margin-left: 80px; margin-right: 80px; margin-top: 15px; margin-bottom: 15px; font-size: 85%; color: #998'>";
  print "<p>$text{'view_batchfile_title'}\n";
  print "<p>To download the file through your browser, ";
  print "right-click on the link and select 'save link as...' from the menu.\n";
  print "<br><span style='font-size: 90%'>(If you want to 'view' the file rather than download it, ";
  print "start by left-clicking on the link, ";
  print "view the file, then click your browser's 'back' button when you're done.)</span>\n";
  print "<p><a href='scaffold/batchreport.scaffold'>$text{'view_batchfile_link'}</a>";
  print "<p>After obtaining the example file, make a copy of it and edit as necessary.\n";
  print "<br>For security, create a new Webmin user just to produce batch reports, ";
  print "<br>and remove all Webmin permissions except DansGuardian 'Can Analyze Log Files'.\n";
  print "<p></div></center><hr>";

  #&printFooter();	# standalone, but don't do this when embedded in Webmin
}

################
sub validateVars
################
{
  my $newsIP = &validateIP($sIP);
  if ($newsIP == -1) {
    $msg = "$text{'view_err_entryinvalid'} - $text{'field_ipaddress'}";
    &printMenu();	# try again
    &webminfooterandexit();
  } else {
    $sIP = $newsIP;
  }

  &dateParts2wholeDates();
  if (($sSD ne 'ALL') && ($sED ne 'ALL') && ($sSD > $sED)) {
      $msg = "$text{'field_startdate'} $text{'view_err_greaterthan'} $text{'field_enddate'}";
      &printMenu();	# try again
      &webminfooterandexit();
  }
  $sA = &validateAction($sA); # Action
  $sSumCnt = &validateSummary($sSumCnt);
  &validateWeight($sWD, $sWN);

  my $newsSN = &validateDomain($sSN);
  if ($newsSN == -1) {
    $msg = "$text{'view_err_entryinvalid'} - $text{'field_domain'}";
    &printMenu();	# try again
    &webminfooterandexit();
  } else {
    $sSN = $newsSN;
  }

  &canonicalizeVars();	# if we mangled anything, mangle it back
			#  (should never be needed, but it's good insurance)
}

###############
sub showSummary
###############
{
  my ($subTotal, $whatToShow, $topNum, $sumOrder, %activities) = @_;
  my $count = 1;

  print "
	 <table border=0 cellpadding=2 cellspacing=5 align=center>
         <tr><th colspan=6>
         <b><center>
         <small>($text{'view_matching'})</small> $text{'view_top'} $topNum " . uc($text{"view_$whatToShow"}) . "$what2subtitle{$whatToShow} $order2title{$sumOrder}</b></td></tr>
         <tr><td align=center>Rank</td>
             <td align=center>$sumOrder</td>
             <td align=right>Count</td>
             <td align=right>\% of<br>" . ucfirst($text{"view_$whatToShow"}) . "<br>Matches</td>
             <td align=right>\% of<br>Total<br>Matches</td>
             </tr>\n";

  foreach my $key (sort {$activities{$b} <=> $activities{$a}} keys %activities) {
    if ($count <= $topNum) {
      print "<tr>
         <td align=right>$count.&nbsp;&nbsp;</td>";
      print "<td align=right>";
      if ($sL eq 'on') {
        print "<a href='$cgipath?a=d&sSDY=$sSDY&sSDM=$sSDM&sSDD=$sSDD&sEDY=$sEDY&sEDM=$sEDM&sEDD=$sEDD";
        while (($order, $varname) = each %order2varname) {
          print "&$varname=";
          if ($sumOrder eq $order) {
            print &html_escape($key); 
          } else { 
            print &html_escape($$varname); 
          }
        }
        print "&sWD=" . &html_escape($sWD) . "&sWN=$sWN&sCAT=" . &html_escape($sCAT) . "&sMIME=$sMIME&sGRP=" . &html_escape($sGRP) . "&sAGT=" . &html_escape($sAGT) . "&sL=$sL&sZ=$sZ&sD=on&sG=on&sR=on&sP=on&sSumExc=off&sSumDen=off&sSumAlw=off&sA=$sA&sA2=$what2option{$whatToShow}'>$key</a>";
      } else {
        print "$key";
      }
      if ($sumOrder eq 'Domain') {
        # note key may already be a full URL including protocol, in which case we don't need to add a protocol here
        my $destination = ($key =~ m/^htt/i) ? $key : "http://$key";
        print " <a href='$destination' target=_blank>[$text{'button_visit'}]</a>";
      }
      my $displayableSubTotalPercentage = sprintf "%3.1f", (($activities{$key} * 100) / $subTotal);
      my $displayableGrandTotalPercentage = sprintf "%3.1f", (($activities{$key} * 100) / $grandTotal);
      print "</td><td align=right>$activities{$key}</td><td align=right>";
      print "&nbsp;&nbsp;&nbsp;$displayableSubTotalPercentage&nbsp;&nbsp;";
      print "</td><td align=right>";
      print "&nbsp;&nbsp;&nbsp;$displayableGrandTotalPercentage";
      print "</td></tr>\n";
      $count++;
    } else {
      # we're down past the "top ---", so exit the outer loop, no point in doing any more
      last;
    }
  }
  my $displayableGrandTotalPercentage = sprintf "%3.1f", (($subTotal * 100) / $grandTotal);
  print "<tr><td colspan=6 align=center>
	 <hr style='height: 2'>
         Total " . uc($text{"view_$whatToShow"}) . " $text{'view_requests'} (all, not just $text{'view_top'}) : $subTotal ($displayableGrandTotalPercentage% of Filter Matches)
         </td></tr>
	 </table>\n";
}


###########################################################################
#
#    UTILITY SUBROUTINES
#
###########################################################################

################
sub webminheader
################
{
    if (! defined $sTITLE) {
        # interactive
        &ui_print_header($pagename, $text{'index_title'}, undef, 'logs', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, 'onLoad="if(document.mainmenu){document.mainmenu.sSDY.focus();};"', "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
    } else {
        # batch
        &ui_print_header('', "$sTITLE<br><small>(" . localtime .")</small><br><br>", undef, undef, 0, 1, 1, '', undef, undef, '');
    }
}

#######################
sub webminfooterandexit
#######################
{
    if (! defined $sTITLE) {
        # interactive
	if ($a eq 'd') {
	    # detail display
            &ui_print_footer('javascript:window.back()', $text{'view_subreturn'}, $modulenameself, $text{'view_return'}, 'index.cgi', $text{'index_return'});
	} else {
	    # summary display
            &ui_print_footer($modulenameself, $text{'view_return'}, 'index.cgi', $text{'index_return'});
	}
    } else {
	# batch
	&ui_print_footer();
    }
    exit;
}

############
sub initVars
############
{
    %order2title = (
	'Domain' => 'Websites',
	'IP' => 'Source Computers',
	'User' => 'Individuals',
	);

    %order2varname = (
	'Domain' => 'sSN',
	'IP' => 'sIP',
	'User' => 'sUN',
	);

    %order2source = (
	'Domain' => 'protocolandsitename',
	'IP' => 'ip', 
	'User' => 'user',
	);

    %what2subtitle = (
	'exception' => '',
	'denied' => '',
	'allowed' => "($text{'view_not'} $text{'view_denied'})",
	);

    %what2varname = (
	'exception' => 'sSumExc',
	'denied' => 'sSumDen',
	'allowed' => 'sSumAlw',
	);

    %what2option = (
	'exception' => 'exceptionALL',
	'denied' => 'deniedALL',
	'allowed' => 'allowALL',
	);

    # these are "reasons" for an action that may appear in the log
    # these specifically do _not_ include operational and "access denied" page messages
    #  that do not also appear in the log, as including them too would not serve any
    #  purpose but would have the undesirable side effect of a large misleading menu
    %reasonMessageNumbers = (
	100 => 1,
	102 => 1,
	300 => 1,
	400 => 1,
	402 => 1,
	500 => 1,
	501 => 1,
	502 => 1,
	503 => 1,
	505 => 1,
	506 => 1,
	507 => 1,
	508 => 1,
	600 => 1,
	601 => 1,
	602 => 1,
	603 => 1,
	604 => 1,
	605 => 1,
	606 => 1,
	607 => 1,
	609 => 1,
	700 => 1,
	701 => 1,
	750 => 1,
	751 => 1,
	800 => 1,
	900 => 1,
	1000 => 1,
    );

    # these are "reasons" that involve a regular expression
    # (which appears as the literal subreason)
    %regexpreasonMessageNumbers = (
	503 => 1,
	504 => 1,
	609 => 1,
    );

    # these are "reasons" that involve a banned/weighted phrase list
    #  (which appears as the literal subreason)
    %phrasereasonMessageNumbers = (
	300 => 1,
	301 => 1,
	400 => 1,
	401 => 1,
	402 => 1,
	403 => 1,
    );

    # these are "reasons" to us, but they are "subreasons" of 'banned site:' to the log
    # so we must allow for them, as naively they'd not be in the field we checkd
    %blanketreasonMessageNumbers = (
	502 => 1,
	505 => 1,
	506 => 1,
	507 => 1,
    );

    %exceptionreasonMessageNumbers = (
	600 => 1,
	601 => 1,
	602 => 1,
	603 => 1,
	604 => 1,
	605 => 1,
	606 => 1,
	607 => 1,
	608 => 1,
	609 => 1,
    );

    &initReasonText();	# (note this assumes previous variable already set)
}

##################
sub initReasonText
##################
{
  my ($whereisit, $messagesfilepath);

  $whereisit = $config{'messages_path'};
  if (($whereisit =~ m/follow/i) || (! $whereisit)) {
    my $conf_languagedir = &getconfigvalue('languagedir');
    my $conf_language = &getconfigvalue('language');
    $messagesfilepath = &canonicalizefilepath("$conf_languagedir/$conf_language/messages");
  } else {
    $messagesfilepath = &canonicalizefilepath($whereisit);
  }
  my $messagesref = read_file_lines_just_once($messagesfilepath);
  # process lines in _reverse_ order, so any duplicate text will be assigned the lower number
  foreach my $line (reverse @$messagesref) {
    if ($line =~ m/^\s*"(\d+)"\s*,\s*"([^"]+)"/) {
      my $number = $1;
      my $text = &canonicalizereason($2);
      # $1 is (usually 3-digit) message number, $2 is corresponding message text
      if (exists $reasonMessageNumbers{$number}) {
        $reasons_number2text{$number} = $text;
        $reasons_text2number{$text} = $number;
      }
      if (exists $regexpreasonMessageNumbers{$number}) {
        $regexpreasons_number2text{$number} = $text;
        $regexpreasons_text2number{$text} = $number;
      }
      if (exists $phrasereasonMessageNumbers{$number}) {
        $phrasereasons_number2text{$number} = $text;
        $phrasereasons_text2number{$text} = $number;
      }
      if (exists $blanketreasonMessageNumbers{$number}) {
        $blanketreasons_number2text{$number} = $text;
        $blanketreasons_text2number{$text} = $number;
      }
      if (exists $exceptionreasonMessageNumbers{$number}) {
        $exceptionreasons_number2text{$number} = $text;
        $exceptionreasons_text2number{$text} = $number;
      }
    } else {
    }
  }
}

#################
sub unPersistData
#################
{
  my ($filepath);

  if (!	defined %categories) {
    # should always be true...
    #  but just in case it somehow already exists, don't overwrite it
    %categories = ();
    $filepath = "$module_config_directory/categories";
    $listchanged_categories = 0;
    read_file($filepath, \%categories);
  }

  if (!	defined %mimetypes) {
    # should always be true...
    #  but just in case it somehow already exists, don't overwrite it
    %mimetypes = ();
    $filepath = "$module_config_directory/mimetypes";
    $listchanged_mimetypes = 0;
    read_file($filepath, \%mimetypes);
  }

  if (!	defined %filtergroups) {
    # should always be true...
    #  but just in case it somehow already exists, don't overwrite it
    %filtergroups = ();
    $filepath = "$module_config_directory/filtergroups";
    $listchanged_filtergroups = 0;
    read_file($filepath, \%filtergroups);
  }

}

###############
sub persistData
###############
{
  my ($filepath);

  if ($sRC eq 'on') {
    %categories = ();
    $listchanged_categories = 1;
    print "<span style='font-size: smaller; color: green'>List of choices of $text{'field_category'} has been reset. List of choices will be empty when the report menu is next displayed.</span><p>\n";
  }
  if ($listchanged_categories) {
    $filepath = "$module_config_directory/categories";
    write_file($filepath, \%categories);
  }

  if ($sRM eq 'on') {
    %mimetypes = ();
    $listchanged_mimetypes = 1;
    print "<span style='font-size: smaller; color: green'>List of choices of $text{'field_mimetype'} has been reset. List of choices will be empty when the report menu is next displayed.</span><p>\n";
  }
  if ($listchanged_mimetypes) {
    $filepath = "$module_config_directory/mimetypes";
    write_file($filepath, \%mimetypes);
  }

  if ($sRG eq 'on') {
    %filtergroups = ();
    $listchanged_filtergroups = 1;
    print "<span style='font-size: smaller; color: green'>List of choices of $text{'field_filtergroup'} has been reset. List of choices will be empty when the report menu is next displayed.</span><p>\n";
  }
  if ($listchanged_filtergroups) {
    $filepath = "$module_config_directory/filtergroups";
    write_file($filepath, \%filtergroups);
  }
}

#################
sub setCheckboxes
#################
{
  # only do this if coming from GUI, otherwise return immediately (do _not_ override "defaults")
  return if (! exists $in{'a'});

  $sD = 'off' if ! defined $sD;
  $sZ = 'off' if ! defined $sZ;
  $sL = 'off' if ! defined $sL;
  $sR = 'off' if ! defined $sR;
  $sG = 'off' if ! defined $sG;
  $sP = 'off' if ! defined $sP;
  $sRC = 'off' if ! defined $sRC;
  $sRM = 'off' if ! defined $sRM;
  $sRG = 'off' if ! defined $sRG;
}

###############
sub setDefaults
###############
{
  # In answer to the question 'what are all the parameters' which are part of the URL
  #  in the example/scaffold for running a batch report, SEE THE COMMENTS IN THIS SUBROUTINE below
  #  for a complete list of parameters, their meanings, and their default values if not specified
  # (when used in a URL, parameters do not have the leading dollar sign that's used within 
  #  Perl code, otherwise we've arranged that the parameter spellings and meanings are identical)

  # These are the values that can be set by the user through the browser
  # set them if they aren't already set (for example by the query part of a URL)
  $sIP = 'ALL' if !defined $sIP;	# IP address 
  $sUN = 'ALL' if !defined $sUN;	# Username
  $sSN = 'ALL' if !defined $sSN;	# SiteName (part of URL)
  $sSDY = 'ALL' if !defined $sSDY;	# Start date year
  $sSDM = 'ALL' if !defined $sSDM;	# Start date month
  $sSDD = 'ALL' if !defined $sSDD;	# Start date day
  $sEDY = 'ALL' if !defined $sEDY;	# End date year
  $sEDM = 'ALL' if !defined $sEDM;	# End date month
  $sEDD = 'ALL' if !defined $sEDD;	# End date day
  &dateParts2wholeDates;
  $sA = 'ALL' if !defined $sA;		# Action
  $sA2 = 'ALL' if !defined $sA2;	# Action following hyperlink
  $sWD = 'ALL' if !defined $sWD;	# Weight Direction
  $sWN = 'ALL' if !defined $sWN;	# Weight Number
  &weightParts2wholeWeight;
  $sCAT = 'ALL' if !defined $sCAT;	# (list)Category
  $sMIME = 'ALL' if !defined $sMIME;	# Mimetype
  $sGRP = 'ALL' if !defined $sGRP;	# Filter Group Name
  $sAGT = 'ALL' if !defined $sAGT;	# Browser Agent	
  # all of above are our "filter"; their values are printed at the top of every report
  #
  # the options below control the appearance and behavior of the report, many are 
  #  forced one way for "summary" reports and a different way for "detail" reports
  # (most of the on/off options correspond to checkboxes on the menu)
  $sSumCnt = 20 if !defined $sSumCnt;	# Number of summary sites to show
  $sSumExc = 'on' if !defined $sSumExc;	# Show excepted summary? on/off
  $sSumDen = 'on' if !defined $sSumDen;	# Show denied summary? on/off
  $sSumAlw = 'on' if !defined $sSumAlw;	# Show allowed(!denied) summary? on/off
  $sL = 'on' if !defined $sL;		# Turn URL's into links? on/off
  $sZ = 'off' if !defined $sZ;		# Examine gziped files? on/off
  $sD = 'off' if !defined $sD;		# Display individual requests (details)
  # following defaults can be misleading - if above $sD is turned on, following three come on also
  $sG = 'off' if !defined $sG;		# Display browser agent string
  $sR = 'off' if !defined $sR;		# Display regular expression matches
  $sP = 'off' if !defined $sP;		# Display matching phrases(words)
  $sRC = 'off' if !defined $sRC;	# Reset list of categories? on/off
  $sRM = 'off' if !defined $sRM;	# Reset list of mimetypes? on/off
  $sRG = 'off' if !defined $sRG;	# Reset list of filtergroups? on/off
  $a = 'm' if !defined $a;		# Display menu
}

####################
sub canonicalizeVars
####################
{
  # These are the values that can be set by the user through the browser
  # the menu may set them to a default value we don't understand
  #  so set them back to the values we're familiar with
  $sIP = 'ALL' if $sIP eq '';		# IP address 
  $sUN = 'ALL' if $sUN eq '';		# Username
  $sSN = 'ALL' if $sSN eq '';		# SiteName (part of URL)
  $sSDY = 'ALL' if $sSDY eq '';		# Start date year
  $sSDM = 'ALL' if $sSDM eq '';		# Start date month
  $sSDD = 'ALL' if $sSDD eq '';		# Start date day
  $sEDY = 'ALL' if $sEDY eq '';		# End date year
  $sEDM = 'ALL' if $sEDM eq '';		# End date month
  $sEDD = 'ALL' if $sEDD eq '';		# End date day
  &dateParts2wholeDates;
  $sA = 'ALL' if $sA eq '';		# Action
  $sA2 = 'ALL' if $sA2 eq '';		# Action following hyperlink
  $sWD = '>=' if $sWD =~ m/&gt;/;	# our own funky/special purpose/not exactly right html_unescape
  $sWD = '<=' if $sWD =~ m/&lt;/;	# our own funky/special purpose/not exactly right html_unescape
  $sWD = 'ALL' if $sWD eq '';		# Weight Direction
  $sWN = 'ALL' if $sWN eq '';		# Weight Number
  &weightParts2wholeWeight;
  $sCAT = 'ALL' if $sCAT eq '';		# (list)Category
  $sMIME = 'ALL' if $sMIME eq '';	# Mimetype
  $sGRP = 'ALL' if $sGRP eq '';		# Filter Group Name
  $sAGT = 'ALL' if $sAGT eq '';		# Browser Agent	
  $sSumCnt = 0 if $sSumCnt eq '';	# Number of summary sites to show
  $sSumExc = 'off' if $sSumExc eq '';	# Show excepted summary? on/off
  $sSumDen = 'off' if $sSumDen eq '';	# Show denied summary? on/off
  $sSumAlw = 'off' if $sSumAlw eq '';	# Show allowed(!denied) summary? on/off
  $sL = 'off' if $sL eq '';		# Turn URL's into links? on/off
  $sZ = 'off' if $sZ eq '';		# Examine gziped files? on/off
  $sD = 'off' if $sD eq '';		# Display individual requests (details)
  $sG = 'off' if $sG eq '';		# Display browser agent string 
  $sR = 'off' if $sR eq '';		# Display regular expression matches
  $sP = 'off' if $sP eq '';		# Display matching phrases(words)
  $sRC = 'off' if $sRC eq '';		# Reset list of categories? on/off
  $sRM = 'off' if $sRM eq '';		# Reset list of mimetypes? on/off
  $sRG = 'off' if $sRG eq '';		# Reset list of filtergroups? on/off
  $a = 'm' if $a eq '';			# switch to type of operation
}

###############
sub convertDate
###############
{
  my ($workDate) = @_;
  $workDate =~ s/^['"\s]+//;
  $workDate =~ s/['"\s]+$//;

  my ($year, $mon, $day) = split(/\s*\.\s*/,$workDate);

  if (($year eq 'ALL') || ($year eq '') || ($mon eq 'ALL') || ($mon eq '') || ($day eq 'ALL') || ($day eq '')) {
      return ('ALL');
  }
  if (($mon >= 1 && $mon <= 12) && ($day >= 1 && $day <= 31) &&
      ($year >= 2000 && $year <= 2035)) {
      my $goodDate = sprintf '%04d%02d%02d', $year, $mon, $day;
      return $goodDate;
  } else {
    $msg = "$text{'view_err_dateinvalid'} - $workDate<p>$text{'view_err_logformat'}";
    &printMenu();	# try again
    &webminfooterandexit();
  }
}

########################
sub dateParts2wholeDates
########################
{
  $sSD = convertDate(join '.', $sSDY, $sSDM, $sSDD);
  $sED = convertDate(join '.', $sEDY, $sEDM, $sEDD);
}

###########################
sub weightParts2wholeWeight
###########################
{
  # check for either part explicitly being 'ALL'
  # and also for either part being clearly invalid
  my $direction = $sWD;
  $direction = '<=' if $direction =~ m/&lt;/;
  $direction = '>=' if $direction =~ m/&gt;/;
  if ((($direction =~ m/^\s*ALL\s*$/i) || ($sWN =~ m/^\s*ALL\s*$/i))
    || ((length($direction) != 2) || ($sWN !~ m/^-?\d+/))) {
      $sWGHT = 'ALL';
  } else {
      $sWGHT = "$sWD $sWN";
  }
}

###############
sub printFilter
###############
{ 
   my $sAtext = (exists $reasons_number2text{$sA}) ? $reasons_number2text{$sA} : $sA;
   $sAtext .= ' ';
   (my $reason = $sAtext) =~ s/^\s*((?:\S+\s+){1,5}).*$/$1/;
   if ($reason ne $sAtext) { $reason .= '...'; }
  print "<I><U>$text{'view_filter_postheading'}:</U></I><br>\n
   $text{'field_startdate'}: <b>$sSD</b> - $text{'field_enddate'}: <b>$sED</b> <br>\n
   $text{'field_username'} : <b>$sUN</b> | $text{'field_ipaddress'}: <b>$sIP</b> <br>\n
   $text{'field_weight'}: <b>" . &html_escape($sWGHT) . "</b> | $text{'field_category'}: <b>$sCAT</b> <br>\n
   $text{'field_mimetype'}: <b>$sMIME</b> | $text{'field_filtergroup'}: <b>$sGRP</b> <br>\n
   $text{'field_reason'}: <b>$reason"; print "($sA2)" if (($sA2 ne 'ALL') && ($sA2 ne $sA)); print"</b> | $text{'field_domain'}: <b>$sSN</b> <br>\n
   $text{'field_agent'}: <b>$sAGT</b> <br>\n";
}

###############
sub printTotals
###############
{
    # if float (%f) Perl handles rounding, but if int (%d) must do intelligent rounding ourselves
    my $percentage = (($grandTotal * 100) / $linesRead);
    # paranoia, almost certainly never used, but just in case of error make display seem correct anyway
    $percentage = 100.0 if $percentage > 100;
    $percentage = 0.0 if $percentage < 0;
    $percentage = sprintf '%3.1f', $percentage;

    print "<center>
      $text{'view_match'}: $grandTotal ($percentage% of $text{'view_all'}: $linesRead)\n
      <hr style='height: 3'></center>\n";
}

###################
sub validateSummary 
###################
{
  my ($count) = @_;
  if ($count < 0 || $count > 100) {
    $count = 20;
  }
  return($count);
}

#############
sub mask2cidr
#############
{
    my ($mask) = @_;
    return -1 if ($mask !~ m/^(\d+)\.(\d+)\.(\d+)\.(\d+)$/);
    my $m1 = $1; my $m2 = $2; my $m3 = $3; my $m4 = $4;
    my $numericmask = ((((((256 * $m1) + $m2) * 256) + $m3) * 256) + $m4);
    my $bits = 32;
    while ((($numericmask & 0x00000001) == 0) && ($bits > 0)) {
        $numericmask >>= 1;
        --$bits;
    }
    for (my $i=$bits; $i>=1; --$i) {
        return -1 if (($numericmask & 0x00000001) != 1);
        $numericmask >>= 1;
    }
    return $bits;
}

################
sub cidr2binmask
################
{
    my ($bits) = @_;
    return 0 if !$bits;
    return 0 if $bits == 0;
    return -1 if $bits < 0;
    return -1 if $bits > 32;
    my $binmask = 0;
    for (my $i=1; $i<=$bits; ++$i) {
        $binmask >>= 1;
        $binmask |= 0x80000000;
    }
    return $binmask;
}

##################
sub octets2numeric
##################
{
    my ($IPaddr) = @_;
    return -1 if $IPaddr !~ m/^(\d+)\.(\d+)\.(\d+)\.(\d+)$/;
    my $p1 = $1; my $p2 = $2; my $p3 = $3; my $p4 = $4;
    my $numeric = (((((($p1 << 8) | $p2) << 8) | $p3) << 8) | $p4);
    return $numeric;
}

##############
sub validateIP 
##############
{
  my ($checkIP) = @_;

  if ($checkIP eq 'ALL') {
    return('ALL');
  }
  $checkIP =~ s/^\s+//;
  $checkIP =~ s/\s+$//;
  my ($addrpart, $maskpart) = split qr(\s*[-/\\:]\s*), $checkIP, 2; 
  return -1 if ((! $addrpart) && (! $maskpart));
  $maskpart = 32 if ! $maskpart;
  $maskpart = &mask2cidr($maskpart) if $maskpart !~ m/^\d+$/;
  my $binmask = &cidr2binmask($maskpart);
  return -1 if $binmask == -1;
  my $numericaddrpart = &octets2numeric($addrpart);
  return -1 if $numericaddrpart == -1;
  if (($numericaddrpart == 0) && ($maskpart == 0)) {
    return ('ALL');
  } elsif ((($numericaddrpart & $binmask) >= 1) && ($binmask != 0)) {
    $numericaddrpart &= $binmask;
    my $x4 = $numericaddrpart & 0xFF;
    $numericaddrpart >>= 8;
    my $x3 = $numericaddrpart & 0xFF;
    $numericaddrpart >>= 8;
    my $x2 = $numericaddrpart & 0xFF;
    $numericaddrpart >>= 8;
    my $x1 = $numericaddrpart & 0xFF;
    return "$x1.$x2.$x3.$x4/$maskpart";
  } else {
    return -1;
  }
}

##################
sub validateDomain
##################
{
  my ($site) = @_;

  $site =~ s/^\s+//;
  $site =~ s/\s+$//;

  return 'ALL' if $site eq 'ALL';
  return '' if $site eq '';

  my ($protocol, $domainname) = ($site =~ m{^(?:(http|https|ftp|file)://+)?(.*)$});


  return 'ALL' if $domainname eq 'ALL';
  return '' if $domainname eq '';

  return -1 if $domainname !~ m/\./;
  return -1 if $domainname =~ m{/};
  return -1 if $domainname =~ m/\s/;
  return -1 if $domainname =~ m/\.[^.]{5,}$/;

  return $site;
}

##################
sub validateWeight
##################
{
  my ($direction, $number) = @_;

  return 1 if (($direction =~ m/^\s*ALL\s*$/i) || ($number =~ m/^\s*ALL\s*$/i));
  return 1 if ((! $direction) || (! $number));

  return 1 if (($direction =~ m/^(?:<|>)=$/) && ($number =~ m/-?\d+/));

  $msg = "$text{'view_err_entryinvalid'} - $text{'field_weight'}";
  &printMenu();	# try again
  &webminfooterandexit();
}

##################
sub validateAction
##################
{
  my ($action) = @_;

  # Need to make the actions a hash and reference them that way
  # Make it easier to add/modify and can validate that way too
  # Maybe later.
  if ((! $action) || ($action =~ m/^\s*no/i) || ($action =~ m/^\s*all\s*$/i)) { return ("ALL"); }

  return ($action);
}

###############
sub buildSelect
###############
{
  # emit all the "option" statements for a numeric select
  # third arg is value to start with initially
  # fourth arg is continued value to use
  my ($start, $end, $newvalue, $prevvalue) = @_;
  my $selected = (($prevvalue ne '') && ($prevvalue ne 'ALL')) ? $prevvalue : $newvalue;
  my $x = 0;
  
  print "\n<option value='ALL' disabled></option>\n<option value='ALL'>--ALL--</option>\n";
  for ($x = $start; $x <= $end; $x++) {
      print "<option value='$x'";
      print " selected" if ($x eq $selected);
      print ">$x</option>\n";
  }
}


###########################################################################
#
#    ***UNUSED*** SUBROUTINES
#     retained for possible reference by future development
#
###########################################################################

###############
sub printHeader
###############
{
 #print $q->header;	# remnant of an earlier coding style which has been deleted
 print <<"(EOT)";
 <HTML><HEAD>
 <META HTTP-EQUIV="Pragma" CONTENT="no-cache">
 <META HTTP-EQUIV="Cache-Control" CONTENT="no-cache">
 <META HTTP-EQUIV="Expires" CONTENT="-1">
 <TITLE>$pagename</TITLE>
 <STYLE>
 <!--
    TABLE       {margin-top: 0; padding-top: 0}
    TD  	{font-family: Serif; font-size: 10pt }
    TH  	{font-family: Serif; font-size: 12pt }
 -->
 </STYLE>
 </HEAD>
 <body bgcolor="#ffffff" text="#000000" link="#0000ff" vlink="#0000ff"
 alink="#0000ff">
 <center>
 <table width="600" border="0" cellspacing="0" cellpadding="0">
 <tr><th width=600 align=center>
 <font size="4" color="#000000" face="arial">
 <hr align=center noshade size=1 width=90%>
 $pagename 
 <hr align=center noshade size=1 width=90%>
 </th></tr>
 </table>
 </center>

(EOT)
}

###############
sub printFooter
###############
{
  print <<"(EOT)";
  </BODY>
  </HTML>
(EOT)
}

print DEBUGLOG "finished processing logs.cgi\n" if $debug;
