#!/usr/bin/perl

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

# Begin Webmin header stuff (also note footer at bottom of script)
require './dansguardian-lib.pl';
use POSIX;
&ReadParse();
&ui_print_header($text{'view_dglog'}, "", "");
%access = &get_module_acl();
$conffilepath = "$config{'conf_dir'}/dansguardian.conf";
$cfref = &read_file_lines($conffilepath);

# Check user acl
&checkmodauth(logs);

# Check dg config
&checkdgconf();
# End of Webmin header stuff


###########################################################################
#
# Change to point to your DansGuardian log directory
# NOTE: The trailing / IS REQUIRED!!
#
###########################################################################
$logdir = "$config{'log_path'}";


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
$logfile = 'access.log';


###########################################################################
#
# Log Format.  Change to indicate what format the log files are. This 
# should match what is in dansguardian.conf. Setting it to the wrong type
# will cause strange results.
#
# 1 = DansGuardian format     2 = CSV-style format
#
###########################################################################
$logformat = &readconfigoption('logfileformat');

###########################################################################
#
# If you need the perl modules below, download and untar them to a directory.
# Then cd to the directory and enter the commands:
#  perl Makefile.PL; make; make test; make install 
#
# If you need more instructions, 
#  go here: http://www.cpan.org/modules/INSTALL.html
#
# Get it here: http://www.cpan.org/authors/id/LDS/CGI.pm-2.81.tar.gz
#
###########################################################################
use CGI;

###########################################################################
#
# This is needed to do gzip'ed log files on the fly
# Get it here: http://www.cpan.org/authors/id/PMQS/Compress-Zlib-1.16.tar.gz
#
###########################################################################
use Compress::Zlib; 


###########################################################################
#
# This should determine where the program is called from automagically.
# If not, uncomment the first line, change to your server name/path and
# comment the second line.  You can use Apache restrictions to block 
# access to this file if desired. 
#
###########################################################################
#$cgipath = 'http://your.server.com/cgi-bin/dglog/dglog.pl';
$cgipath = $ENV{SCRIPT_NAME};



###########################################################################
#
#    SHOULDN'T HAVE TO MODIFY ANYTHING BELOW THIS LINE
#
###########################################################################

$q = new CGI;

($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
$mon = $mon + 1;  # mon starts at 0 
$year = $year + 1900;  # year needs 1900 added
$pagename = 'Log Analyzer for DansGuardian';

$a = $q->param('a');

if ($a eq 'i') { # Inquiry into logs

  # These are the values that can be sent by the user through the browser
  $sIP = "ALL";   # IP address 
  $sUN = "ALL";   # Username
  $sURL = "ALL"; # URL to show or trace a denied site - this is the URL to trace
  $sSD = "ALL";   # Complete start date
  $sSDY = "ALL";  # Start date year
  $sSDM = "ALL";  # Start date month
  $sSDD = "ALL";  # Start date day
  $sED = "ALL";   # Complete end date
  $sEDY = "ALL";  # End date year
  $sEDM = "ALL";  # End date month
  $sEDD = "ALL";  # End date day
  $sA = "ALL";    # Action
  $sSumCnt = "20";    # Number of summary sites to show
  $sSumDen = "off";    # Show denied summary? on/off
  $sSumAlw = "off";    # Show allowed summary? on/off
  $sSumOrd = "URL"; # Default to showing url for summary denied/allowed
  $sL = "off"; # Turn URL's into links? on/off
  $sZ = "off"; # Examine gziped files? on/off

  $sIP = &validateIP($q->param('sIP')) if $q->param('sIP') ne "";
  $sUN = $q->param('sUN') if $q->param('sUN') ne "";
  $sURL = $q->param('sURL') if $q->param('sURL') ne "";

  if ($q->param('sSDY') ne "" && $q->param('sSDY') ne 'ALL' &&
      $q->param('sSDM') ne "" && $q->param('sSDM') ne 'ALL' &&
      $q->param('sSDD') ne "" && $q->param('sSDD') ne 'ALL' &&
      $q->param('sEDY') ne "" && $q->param('sEDY') ne 'ALL' &&
      $q->param('sEDM') ne "" && $q->param('sEDM') ne 'ALL' &&
      $q->param('sEDD') ne "" && $q->param('sEDD') ne 'ALL') {

      $sSDY = $q->param('sSDY'); 
      $sSDM = $q->param('sSDM'); 
      $sSDD = $q->param('sSDD'); 
      $sEDY = $q->param('sEDY'); 
      $sEDM = $q->param('sEDM'); 
      $sEDD = $q->param('sEDD'); 

      $sSD = $sSDY.'.'.$sSDM.'.'.$sSDD;
      $sSD = convertDate($sSD);
      $sED = $sEDY.'.'.$sEDM.'.'.$sEDD;
      $sED = convertDate($sED);

      if ($sSD > $sED) {
        $msg = "End Date is greater than Start Date";
        &printMenu;
      }
  }

  $sA = &validateAction($q->param('sA')) if $q->param('sA') ne "";  # Action
 
  $sSumCnt = &validateSummary($q->param('sSumCnt')) 
             if $q->param('sSumCnt') ne "";
  $sSumDen = $q->param('sSumDen') if $q->param('sSumDen') eq 'on';
  $sSumAlw = $q->param('sSumAlw') if $q->param('sSumAlw') eq 'on';
  $sSumOrd = $q->param('sSumOrd') if $q->param('sSumOrd') ne '';

  $sL = $q->param('sL') if $q->param('sL') eq 'on';
  $sZ = $q->param('sZ') if $q->param('sZ') eq 'on';


  # Need a few global variables to keep from passing back and forth a bunch
  $linesRead, $allowTotal, $blockTotal, $grandTotal = 0;

  &searchLog;

}
elsif ($a eq 'h') {
  &displayHelp;
}
else {
  &printMenu;
}

#############
sub searchLog
#############
{
  my $first = 0;

  &printHeader;
  print "<font face=arial,helvetica,sans-serif size=2>";
  print "Report information for:<br>
   Start Date: <b>$sSD</b> | End Date: <b>$sED</b> |
   Username : <b>$sUN</b> | IP: <b>$sIP</b> |
   Action: <b>$sA</b> | URL: <b>$sURL</b><hr></font>\n";
  print "<font face=arial,helvetica,sans-serif size=1>";

  opendir(D, $logdir);
  @files = grep {/^$logfile/} readdir(D);
  @files = sort {$b cmp $a} @files;
  closedir(D);

  foreach $file (@files) {
    if ($file =~ /\.gz/) {
      if ($sZ eq 'off') {
        if ($first == 0) {
          print "Ignoring gzip logfile(s) in $logdir: ";
          $first = 1;
        }
        print "$file | ";
        next;
      }
      $gz = gzopen($logdir.$file,r);
      if (!$gz) {
        $msg = "Cannot open $logdir$file. Check Permissions.<p>Try setting
        directories chmod 755 and logfiles chmod 644.";
        &printMenu;
      }
      while ($gz->gzreadline($line)) {
        &checkLine($line);
      }
      $gz->gzclose;
    } 
    else {
      print "<p>";
      unless (open(F,$logdir.$file)) {
        $msg = "Cannot open $logdir$file. Check Permissions.<p>Try setting
        directories chmod 755 and logfiles chmod 644.";
        &printMenu;
      }
      while ($line = <F>) {
        &checkLine($line);
      }
      close(F);
    }
  }

  if ($sSumAlw eq "on" && $allowTotal != 0) {
    &showSummarySites($allowTotal,'ALLOWED',$sSumCnt,$sSumOrd,%topSites);
  }
  if ($sSumDen eq "on" && $blockTotal != 0) {
    &showSummarySites($blockTotal,'DENIED',$sSumCnt,$sSumOrd,%blockSites);
  }

  print "<center><hr noshade size=1 width=50%>
         <font size=2>Total matches: $grandTotal |
         Total ALL Requests: $linesRead</font>
         <hr noshade size=1 width=50%></font>";
  print "<center><a href=$cgipath>Return to Menu</a></center>";
}

#############
sub checkLine
#############
{
  my ($line) = @_;
  $linesRead++;

  # Print out a '.' every 1000 log file lines read. Keep browser connect alive
  if (($linesRead % 1000) == 0) {
    print " ";
  } 
  if ($logformat == 2) {
    # If CSV format, then convert to dg format.
    # $c1=date+time,$c5=action, $c6=method, $c7=size
    ($c1,$user,$ip,$url,$c5,$c6,$c7) = split(/","/,$line,7);
    ($date,$time) = split(/ /,$c1);
    # Clean up the extra quotes - this is dirty but does the trick. Also, by
    # doing the split above it would be possible for a line to be misread if 
    # a strange URL contained such a sequence...but it gets the job done in
    # most cases.
    $date =~ s/\"//; $c7 =~ s/\"//;
    $toeol = $c5 . ' ' . $c6. ' ' . $c7;
  }
  else {
    ($date,$time,$user,$ip,$url,$toeol) = split(/ /,$line,6);
  }
  # Rule out the easy matches first 
  return if ($sIP ne "ALL" && $sIP ne $ip);
  return if ($sUN ne "ALL" && $sUN ne $user);

  # Don't do a date comparison unless we are told to
  if ($sSD ne "ALL" || $sED ne "ALL") {
    $dgDate = &convertDate($date);
    return if (!($dgDate ge $sSD && $dgDate le $sED));
  }

  $url =~ /(\w+):\/\/([\w\.-]+)\/?(\S*)/;  
  $protocol = $1; # HTTP, FTP
  $baseurl = $2;  # domain part without http:// or ftp://
  return if ($sURL ne "ALL" && $sURL ne $baseurl);
  $toeol =~ /(\*.+\*)? ?(.+)? (\w+) (\d+)$/;
  $action = $1; # *DENIED# or *EXCEPTION* etc., if exists
  $reason = $2; # Reason for #1 if exists
  $method = $3; # method (GET POST)
  $size = $4;   # size
  if ($sA ne "ALL") { 
    return if ($sA eq "denAll" &&
      $action ne "*DENIED*");
    return if ($sA eq "excAll" &&
      $action ne "*EXCEPTION*");
    return if ($sA eq "denSite" && 
      !($reason =~ /^Banned site/));
    return if ($sA eq "denRegURL" && 
      !($reason =~ /^Banned Regular Expression URL/));
    return if ($sA eq "denPhrase" && 
      !($reason =~ /^Banned Phrase/));
    return if ($sA eq "denCombPhrase" && 
      !($reason =~ /^Banned combination phrase/));
    return if ($sA eq "denWeightPhrase" && 
      !($reason =~ /^Weighted phrase limit/));
    return if ($sA eq "denExt" && 
      !($reason =~ /^Banned extension/));
    return if ($sA eq "denMIME" && 
      !($reason =~ /^Banned MIME Type/));
    return if ($sA eq "denICRA" && 
      !($reason =~ /^ICRA/));
    return if ($sA eq "denBlanketIP" && 
      !($reason =~ /^Blanket IP Block/));
    return if ($sA eq "excSite" && 
      !($reason =~ /^Exception site/));
    return if ($sA eq "excPhrase" && 
      !($reason =~ /^Exception phrase/));
    return if ($sA eq "excCombPhrase" && 
      !($reason =~ /^Combination exception phrase/));
  }

  # Need to do a count for grandTotal if allowed OR denied summary selected 
  if ($sSumAlw eq "on" || $sSumDen eq "on") {
    if ($action ne '*DENIED*') {
      $allowTotal++;
      $grandTotal++;
      # Don't waste memory if didn't want this, but need to count for grandTotal
      $topSites{$baseurl}++ if ($sSumAlw eq "on" && $sSumOrd eq "URL");
      $topSites{$ip}++ if ($sSumAlw eq "on" && $sSumOrd eq "IP");
      $topSites{$user}++ if ($sSumAlw eq "on" && $sSumOrd eq "User");
    }
    else {
      $blockTotal++;
      $grandTotal++;
      # Don't waste memory if didn't want this, but need to count for grandTotal
      $blockSites{$baseurl}++ if ($sSumDen eq "on" && $sSumOrd eq "URL");
      $blockSites{$ip}++ if ($sSumDen eq "on" && $sSumOrd eq "IP");
      $blockSites{$user}++ if ($sSumDen eq "on" && $sSumOrd eq "User");
    }
  }
  else {
    print "$date &nbsp; $time &nbsp; ";
    print "<a href=$cgipath?a=i&sSDY=$sSDY&sSDM=$sSDM&sSDD=$sSDD&sEDY=$sEDY&sEDM=$sEDM&sEDD=$sEDD&sIP=$ip&sZ=$sZ&sL=$sL>$ip</a> 
      &nbsp; $user<br>";
    if ($sL eq 'on') {
      print "<a href=\"$url\" target=_blank>$url</a> $method $size<br>";
    } else {
      print "$url $method $size<br>";
    }
    if ($action ne "" && $reason ne "") {
      print "<font color=red>$action : $reason</font><p>";
    } else {
      print "<p>";
    }
    $grandTotal++;
  }
}

####################
sub showSummarySites {
####################
  my ($subTotal, $whatToShow, $topNum, $sumOrder, %sites) = @_;
  my $count = 1;

  print "<table border=0 cellpadding=2 cellspacing=2 align=center>
         <tr><th colspan=6>
         <b><center>
         <hr noshade width=50% size=1>
         Top $topNum $whatToShow Sites by $sumOrder</b></td></tr>
         <hr noshade width=50% size=1>
         <tr><td align=center>Rank</td>
             <td align=center>URL</td>
             <td align=center>Count</td>
             <td align=right>\% of<br>$whatToShow</td>
             <td align=right>\% of<br>Total</td>
             <td align=center>Investigate</td></tr>";

  foreach $key (sort {$sites{$b} <=> $sites{$a}} keys %sites) {
    if ($count <= $topNum) {
      print "<tr>
         <td align=right>$count.&nbsp;&nbsp;</td>";
      print "<td align=right>";
      if ($sL eq 'on' && $sumOrder eq 'URL') {
        print "<a href=http://$key target=_blank>$key</a>";
      } else {
        print "$key";
      }
      print "</td><td align=right>$sites{$key}</td><td align=right>";
      printf("&nbsp;&nbsp;&nbsp;%2.2f &nbsp;",($sites{$key}/$subTotal)*100);
      print "</td><td align=right>";
      printf("&nbsp;&nbsp;&nbsp;%2.2f",($sites{$key}/$grandTotal)*100);
      print "</td>";
      print "<td align=center>
             <a href=$cgipath?a=i&sSDY=$sSDY&sSDM=$sSDM&sSDD=$sSDD&sEDY=$sEDY&sEDM=$sEDM&sEDD=$sEDD&sUN=";
      if ($sumOrder eq 'User') { print "$key"; } else { print "$sUN"; }
      print "&sIP=";
      if ($sumOrder eq 'IP') { print "$key"; } else { print "$sIP"; }
      print "&sURL=";
      if ($sumOrder eq 'URL') { print "$key"; } else { print "$sURL"; }
      print "&sL=$sL&sZ=$sZ&sA=";
      if ($whatToShow eq "DENIED") { print "denAll"; } else { print ""; }
      print">Trace</a></td></tr>";
      $count++;
    }
    break;
  }
  print "<tr><td colspan=6 align=center>
         <hr noshade size=1 width=85% align=center>
         Total $whatToShow Requests (only top $topNum sites shown) : $subTotal
         <hr noshade size=1 width=85% align=center>
         </td></tr>";
  print "</table>
         <hr noshade width=100% size=1>";
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

##############
sub validateIP 
##############
{
  my ($checkIP) = @_;

  if ($checkIP eq 'ALL') {
    return('ALL');
  }
  elsif ($checkIP =~ /^((2([0-4]\d|5[0-5])|1?\d{1,2})(\.|$)){4}/) {
    return ($checkIP);
  }
  else {
    $msg = "Invalid IP address entered.";
    &printMenu;
  }
}

##################
sub validateAction {
##################
  my ($action) = @_;

  # Need to make the actions a hash and reference them that way
  # Make it easier to add/modify and can validate that way too
  # Maybe later.
  if ($action eq "none") { return ("ALL"); }

  return ($action);
}

###############
sub convertDate {
###############
  my ($workDate) = @_;
  ($year, $mon, $day) = split(/\./,$workDate);

  if (length($mon) == 1) { $mon = '0'.$mon; }
  if (length($day) == 1) { $day = '0'.$day; }
  if (($mon ge "01" && $mon le "12") && ($day ge "01" && $day le "31") &&
      ($year ge "2000" && $year le "2035")) {

      $goodDate = $year.$mon.$day;
      return ($goodDate);
  } else {
    $msg = "Invalid Date Detected - $workDate - 
    Be sure logformat is set to the correct format.";
    &printMenu;
  }
}

###############
sub buildSelect
###############
{
  my ($start, $end, $type) = @_;
  my $x = 0;
  
##  print "<option value=\"\">--$type--";
  print "<option value=\"\">--ALL--";
  for ($x = $start; $x <= $end; $x++) {
    if ($type eq 'Year' && $x == $year) {
      print "<option value=$x selected>$x";
    }
    elsif ($type eq 'Month' && $x == $mon) {
      print "<option value=$x selected>$x";
    }
    elsif ($type eq 'Day' && $x == $mday) {
      print "<option value=$x selected>$x";
    }
    else {
      print "<option value=$x>$x";
    }
  }
}

#############
sub printMenu
#############
{
  &printHeader;
  print "
    <table align=center bgcolor=ffffff border=1 cellpadding=3 cellspacing=1>\n";
  if ($msg ne "") {
    print "<tr><td colspan=3 bgcolor=c80000 align=center>
           <font face=arial,helvetica,sans-serif size=3><b>$msg</b>
           </font></tr>\n";
  }
  
  # Menu items header row
  print "
  <tr bgcolor=f0f0f0>
  <th width=40%>
    Parameter
  </th>
  <th width=40%>
    Value
  </th>
  <th width=20%>
    Description
  </th></tr>\n";

  # Menu item for entering date ranges
  print "
  <tr><td align=left>
    Enter date range:
    <form action=$cgipath><input type=hidden name=a value=i>
    <br>
  </td>
  <td align=left>
    Start Date<br>
    <select name=sSDY>";
  &buildSelect(2002,2010,"Year");
  print "</select><select name=sSDM>";
  &buildSelect(01,12,"Month");
  print "</select><select name=sSDD>";
  &buildSelect(01,31,"Day");
  print "</select><br>
    End Date<br>
    <select name=sEDY>";
  &buildSelect(2002,2010,"Year");
  print "</select><select name=sEDM>";
  &buildSelect(01,12,"Month");
  print "</select><select name=sEDD>";
  &buildSelect(01,31,"Day");
  print "</select>
  </td>
  <td align=center>
    A start and end must be specified.
  </td></tr>\n";

  # Menu item for IP viewing
  print "
  <tr><td align=left>
    Enter IP Address
  </td>
  <td align=left>
    <input name=sIP maxlength=15 size=20>
  </td>
  <td align=center>
    ex: 10.0.0.1<br>
  </td></tr>\n";

  # Menu item for username viewing
  print "
  <tr><td align=left>
    Enter a Username
  </td>
  <td align=left>
    <input name=sUN maxlength=15 size=20>
  </td>
  <td align=center>
    (proxy auth must be enabled)<br>
  </td></tr>\n";
  
  # Menu item for URL viewing
  print "
  <tr><td align=left>
    Enter a URL (domain part only)
  </td>
  <td align=left>
    <input name=sURL maxlength=30 size=20>
  </td>
  <td align=center>
    Enter the www.domain.com part of a URL only<br>
  </td></tr>\n";
  
  # Menu item for ACTION
  print "
  <tr><td align=left>
    View activity by ACTION
  </td>
  <td align=left>
    <select name=sA>
    <option value=none>Show ALL
    <option value=none>---------------
    <option value=denAll>Show ALL Denied
    <option value=none>---------------
    <option value=excAll>Show ALL Exception
    <option value=none>---------------
    <option value=denSite>Banned Site
    <option value=denPhrase>Banned Phrase
    <option value=denRegURL>Banned Regular Expression URL
    <option value=denCombPhrase>Banned Combination Phrase
    <option value=denWeightPhrase>Weighted Phrase Limit
    <option value=denExt>Banned Extension
    <option value=denMIME>Banned MIME Type
    <option value=denICRA>ICRA Exceeded
    <option value=denBlanketIP>Blanket IP Block
    <option value=none>---------------
    <option value=excSite>Exception Site
    <option value=excPhrase>Exception Phrase
    <option value=excCombPhrase>Combination Exception Phrase
    </select>
   
  </td>
  <td align=center>
    Can only do one at a time.
  </td></tr>\n";
  
  # Menu item for selecting summary statistics
  print "
  <tr><td colspan=2 align=left>
    Show summary information for the top  
    <input maxlength=3 size=5 name=sSumCnt value=20> 
    <input type=checkbox name=sSumDen>DENIED 
    <input type=checkbox name=sSumAlw>ALLOWED
    sites by <select name=sSumOrd>
    <option value=URL>URL
    <option value=IP>IP
    <option value=User>User
    </select>
  </td>
  <td align=center>
    Will summarize the top sites for the criteria specified.
  </td></tr>\n";

  print "
  <tr><td colspan=3 align=center>
   <table width=100% border=0 cellpadding=0 cellspacing=0 align=center>
    <tr><td>
     <input type=checkbox name=sL>Check to turn URL's in reports into links.<br>
     <input type=checkbox name=sZ>Check to <b>include</b> gzip log files.<br>
     <a href=$cgipath?a=h>View Usage Instructions</a><br>
    </td>
    <td align=center valign=middle>
     Click the \"Run Report\" Button to Start<p>
     <input type=submit value=\"Run Report\">&nbsp;&nbsp;&nbsp;
     <input type=reset value=\"Reset Values\"><br>
    </td></tr>
   </table>
  </td></tr>\n";

  print " </form> </td> </tr> </table> ";
  &printFooter;
  exit;
}

###############
sub printHeader
###############
{
 print $q->header;
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
 <hr noshade size=1 width=90%>
 $pagename 
 <hr noshade size=1 width=90%>
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

###############
sub displayHelp
###############
{
  &printHeader;
  print<<"(EOF)";
  <table width=75% border=1 cellpadding=2 cellspacing=0 align=center>
  <tr><th bgcolor=f0f0f0><font face=arial,helvetica,sans-serif size=4>
   Instructions
  </th></tr>
  <tr><td align=right><font face=arial,helvetica,sans-serif size=1>
  Written by Jimmy Myrick - see program file for contact information.
  </td></tr>
  <tr><td align=left><font face=arial,helvetica,sans-serif size=2>
  <b>Overview</b>
  <ul>
  This program will examine logs files created by DansGuardian filtering
  software (http://www.dansguardian.org).<p>
  Different search criteria can be specified.  The search criteria are
  cummulatvie (added together).  For example, specifying a date range
  and an IP address will only show entries that match BOTH criteria.  If
  you want to see all log entries, do not specify any criteria.
  <p>
  Presently, no sorting is done on the results.  This is to ensure a very
  fast search, use a small amount of memory, and "feed" the browser peridically with information
  so a timeout does not occur.  What this means is that your log files
  must be in chronological sequence on your system by name.  
  </ul>
  </td></tr>
  <tr><td align=left><font face=arial,helvetica,sans-serif size=2>
  <b>Dates</b>
  <ul>
Select the range of dates to match.  If dates are used, <b>both</b> a start and end date must be selected.  Selecting ALL in any of the date fields will cause ALL of the log records to be examined.  The dates will match greater than or equal to start date - less than or equal to end date. 
  </ul>
  </td></tr>
  <tr><td align=left><font face=arial,helvetica,sans-serif size=2>
  <b>IP Address</b>
  <ul>
  Enter a IPv4 address to match.  Example:  10.0.0.1
  </ul>
  </td></tr>
  <tr><td align=left><font face=arial,helvetica,sans-serif size=2>
  <b>Username</b>
  <ul>
  Enter a username to match.  Proxy auth must be enabled in DansGuardian for this to work.  If usernames are not shown when matching without any criteria, then proxy auth is most likely not enabled.  Refer to the appropriate instructions on how to do this.
  </ul>
  </td></tr>
  <tr><td align=left><font face=arial,helvetica,sans-serif size=2>
  <b>Action</b>
  <ul>
  Enter an action to match.  
  Use the drop-down list to select the ACTION to match.  The ACTIONs are the
  special case requests logged by DansGuardian.  To see ALL matches for
  DENIED and EXCEPTION, select "ALL DENIED" or "ALL EXCEPTIONS".  Only one
  ACTION can be viewed at a time and it shows most restrictive.  For example,
  if "Banned Site" is selected, then only DENIED requests that were DENIED because of a site being in a banned site list will be shown.  No other DENIED requests will be shown.
  </ul>
  </td></tr>
  <tr><td align=left><font face=arial,helvetica,sans-serif size=2>
  <b>Summary Information</b>
  <ul>
  Selecting these options will show a summary report for the number
  of sites entered.  The top 1 to 100 sites may be selected.
  <p>
  Once the summary screen appears, you may "investigate" why a site was
  denied/allowed and who/what machine was visiting the site.  Simply click
  on the "Trace" link under the "Investigate" column and the results will be
  shown.
  <p>
  Caution:  If you select to filter for only DENIED and check to show
  a summary for allowed, there will not be any results.  This is correct.
  If you don't see the results you expected, go back and check the
  criteria that was entered.
  <p>
  Turn URL's into links
  <ul>Checking this box will cause the URL's in the report to be clickable.
  </ul>
  </ul>
  </td></tr>
(EOF)
  print "<tr><td align=center><font face=arial,helvetica,sans=serif size=2>
  <a href=$cgipath>Return to $pagename</a></tr></td> 
  </table>\n";
}

# Webmin footer
&ui_print_footer("index.cgi", $text{'index_return'});
exit;
# End of Webmin footer
