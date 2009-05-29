#!/usr/bin/perl -w
# dansguardian-lib.pl

# Note: Every sub-command execution used to be protected by a sequence that restored the Environment
#  just in case the sub-command had screwed it up. But according to the Webmin documentation (?),
#  the protection didn't actually work right. So, since the protection attempt seemed to take
#  extra time and risked breaking something else (particularly with its errors?-) and seemed to be
#  an attempt to "fix something that wasn't broken", I just removed it (March 2009). If there's 
#  ever a problem with sub-commands polluting the Environment, restore the protection and make it 
#  work right.

# by declaring all the globals we'll reference from libraries
#  _before_ pulling in libraries, and by adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %config, %in, $module_name, $current_lang);
do '../web-lib.pl';
do '../ui-lib.pl';
use Time::HiRes qw( time alarm sleep );
use warnings;
use strict;
# All Webmin initialization is now done here for everybody just once the same way
#  rather than doing it in each .cgi file. (March 2009)
# Note we do NOT &clean_environment(), because we utilize some of the webserver environment
#  variables ourselves, which wouldn't work if they were gone. 
if ($ENV{'SCRIPT_FILENAME'} =~ 'dansguardian') {
    # things we can't do in case we're called from a foreign user, for example ACL processing
    &ReadParse();
}
&init_config();
our %access = &get_module_acl();

our $dg_version;

#################################################################
#
# global flag setting - 
#  change this line of source code to 1 during development
#  change it back to 0 for production
#
our $debug = 0;
#
#################################################################

open DEBUGLOG,">>/var/log/dansguardian/debuglog" if $debug;

print DEBUGLOG "at almost very top of dansguardian-lib.pl\n" if $debug;

# useful constants

# typically the same as the hash "key" - can use for backtracking if necessary
use constant DETAILSNAME => 0;

# usually either same as the name, or "undef"
#  "undef" will problably be interpreted as generic for all vars of same type
use constant DETAILSHELP => 1;

# kind of variable (roughly -but not exactly- corresponds to HTML GUI
#  constructs: type=checkbox, type=radio, type=text, type=textarea, nomatch.)
use constant DETAILSVAR => 2;
use constant VARNONE => 0;
use constant VARONOFF => 1;
use constant VARCHOICE => 2;
use constant VARTEXT => 3;
use constant VARPARA => 4;
use constant VARLINE => 5;

# GUI details for various variable types (reused)
# for type=radio (or <select>), subarray lists choices,
#  each subarray entry is a subsubarray of [ external name, internal value ]
use constant DETAILSCHOICE => 3;
# for type=text, numeric representation (1-9) of size class
use constant DETAILSTEXT => 3;

# has a compiled-in default
use constant DETAILSHASDEFAULT => 4;
use constant HASDEFAULTYES => 1;
use constant HASDEFAULTNO => 0;

# compiled-in default value (if known)
use constant DETAILSDEFAULTVAL => 5;

# number of repetitions allowed
#  (if reality doesn't match this, the  current configuration is erroneous)
#  can occur only once, or can occur multiple times,
#  or individual lines can be commented in or out (like 'authplugin')
use constant DETAILSREP => 6;
use constant REPSINGLE => 1;
# REPMULTI isn't fully implemented! We say it's okay for this input to be multi-valued,
#  but then we have no allowance for properly displaying it or for changing its value
#  (it is fully implemented for variable type LINE though)
use constant REPMULTI => 2;
use constant REPLINES => 3;

# where the option is allowed to occur (NOT where it actually typically occurs)
# a few options can occur only in filter group config files
# a few options can occur only in the main system-wide config file
# most options can occur both places
#  (if present the individual filter group setting will take precedence,
#   so the system-wide setting becomes a sort of "all groups" local default)
use constant DETAILSWHERE => 7;
use constant WHEREMAIN => 1;
use constant WHEREGROUP => 2;
use constant WHEREOVERRIDE => 3;
use constant WHERESHARED => 4;

# read-only and statics
# (use these freely, but don't write to them)
# Perl doesn't actually _enforce_ treating them as read-only

# this is internal data used by &read_file_lines_just_once (and &flush_file_lines)
#  it MUST not be corrupted
our %filesread = ();

# note these are hashes rather than arrays so we can test for membership very quickly with just "exists"
# (the downside is there's no "order", so uses require rather sophisticated sorts)
our %mainconfigurationlists = (
    filtergroupslist => 1,
    exceptioniplist => 1,
    bannediplist => 1,
    );

our %groupsconfigurationlists = (
    exceptionsitelist => 1,
    bannedsitelist => 1,
    greysitelist => 1,
    logsitelist => 1,
    exceptionurllist => 1,
    bannedurllist => 1,
    greyurllist => 1,
    logurllist => 1,
    bannedregexpurllist => 1,
    exceptionregexpurllist => 1,
    logregexpurllist => 1,
    weightedphraselist => 1,
    exceptionphraselist => 1,
    bannedphraselist => 1,
    bannedextensionlist => 1,
    bannedmimetypelist  => 1,
    picsfile => 1,
    exceptionextensionlist => 1,
    exceptionmimetypelist  => 1,
    exceptionfilesitelist => 1,
    exceptionfileurllist  => 1,
    contentregexplist => 1,
    urlregexplist  => 1,
    headerregexplist => 1,
    bannedregexpheaderlist  => 1,
    );

our %configurationlists = (%mainconfigurationlists, %groupsconfigurationlists);

# next two lists are constructed at run-time, as they vary from one environment to the next
our %sharedgroupsconfigurationlists = ();

our %notsharedgroupsconfigurationlists = ();

# fixed lists of a few lists which can ONLY be shared for each scheme
our %sharedonlynestedconfigurationlists = (
    logsitelist => 1,
    logurllist => 1,
    logregexpurllist => 1,
    picsfile => 1,
    urlregexplist => 1,
    contentregexplist => 1,
    headerregexplist => 1,
    );

our %sharedonlyseparateconfigurationlists = ();

our %sharedonlycommonconfigurationlists = ();

#################################################################
#
# this program is almost entirely DATA-DRIVEN
#
# to fix a variable or add a new variable (or delete a variable),
# just change the follow table
#
# there will very seldom be any need to change the code
#
# for example to delete a variable just change its type to 
# VARNONE - it will be handled correctly and appropriate
# warning messages will be generated if it appears
#
# (implementation note: as a side effect of implementing this
#  as a Perl 'hash', the one thing it canNOT do is specify an
#  order - that's why separate arrays of option names [generally
#  in other modules] exist)
#
# (implementation note: this should be a "read-only" variable -
#  however Perl does not enforce this so you can accidentally
#  change this - doing so will almost certainly screw things up)
#
#################################################################
our %options2details = (
	loglevel => [ 'loglevel', 'loglevel', VARCHOICE, [ [ 0, 'conf_loglevel_radio_1' ], [ 1, 'conf_loglevel_radio_2' ], [ 2, 'conf_loglevel_radio_3' ], [ 3, 'conf_loglevel_radio_4' ] ], HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
	logfileformat => [ 'logfileformat', 'logfileformat', VARCHOICE, [ [ 1, 'conf_logfileformat_radio_1' ], [ 2, 'conf_logfileformat_radio_2' ], [ 3, 'conf_logfileformat_radio_3' ], [ 4, 'conf_logfileformat_radio_4' ] ], HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ], 
	logclienthostnames => [ 'logclienthostnames', 'logclienthostnames', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
	logconnectionhandlingerrors => [ 'logconnectionhandlingerrors', 'logconnectionhandlingerrors', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ], 
	languagedir => [ 'languagedir', 'filepaths', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ], 
	language => [ 'language', 'language', VARTEXT, 6, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
	groupname => [ 'groupname', 'groupname', VARTEXT, 6, HASDEFAULTYES, '', REPSINGLE, WHEREGROUP ],
        # next option exists in the code but isn't reference ANYwhere, so effectively it doesn't exist
        groupnamelist => [ 'groupnamelist', 'groupnamelist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
	naughtynesslimit => [ 'naughtynesslimit', 'naughtynesslimit', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        daemonuser => [ 'daemonuser', 'daemonid', VARTEXT, 6, HASDEFAULTYES, 'PROXYUSER', REPSINGLE, WHEREMAIN ],
        daemongroup => [ 'daemongroup', 'daemonid', VARTEXT, 6, HASDEFAULTYES, 'PROXYGROUP', REPSINGLE, WHEREMAIN ], 
        # note REPMULTI (used in following) is unfortunately NOT fully implemented so it won't work in some cases
        filterip => [ 'filterip', 'filterip', VARTEXT,  6, HASDEFAULTNO, undef, REPMULTI, WHEREMAIN ],
        filterport => [ 'filterport', 'filterport', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        proxyip => [ 'proxyip', 'proxyip', VARTEXT, 6, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        proxyport => [ 'proxyport', 'proxyport', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        maxchildren => [ 'maxchildren', 'children', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        minchildren => [ 'minchildren', 'children', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        minsparechildren => [ 'minsparechildren', 'children', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        preforkchildren => [ 'preforkchildren', 'children', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        maxsparechildren => [ 'maxsparechildren', 'children', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        maxagechildren => [ 'maxagechildren', 'children', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        maxips => [ 'maxips', 'maxips', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        reverseaddresslookups => [ 'reverseaddresslookups', 'reverseaddresslookups', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        reverseclientiplookups => [ 'reverseclientiplookups', 'reverseclientiplookups', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        forwardedfor => [ 'forwardedfor', 'forwardedfor', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        usexforwardedfor => [ 'usexforwardedfor', 'usexforwardedfor', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        ipcfilename => [ 'ipcfilename', 'ipc', VARTEXT, 7, HASDEFAULTYES, '/tmp/.dguardianipc', REPSINGLE, WHEREMAIN ],
        urlipcfilename => [ 'urlipcfilename', 'ipc', VARTEXT, 7, HASDEFAULTYES, '/tmp/.dguardianurlipc', REPSINGLE, WHEREMAIN ],
        ipipcfilename => [ 'ipipcfilename', 'ipc', VARTEXT, 7, HASDEFAULTYES, '/tmp/.dguardianipipc', REPSINGLE, WHEREMAIN ],
	pidfilename => [ 'pidfilename', 'pidfilename', VARTEXT, 7, HASDEFAULTYES, 'PREFIX/var/run/dansguardian.pid', REPSINGLE, WHEREMAIN ], 
        nodaemon => [ 'nodaemon', 'nodaemon', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        nologger => [ 'nologger', 'nologger', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        softrestart => [ 'softrestart', 'softrestart', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        authplugin => [ 'authplugin', 'authplugin', VARLINE, undef, HASDEFAULTNO, undef, REPMULTI, WHEREMAIN ],
        downloadmanager => [ 'downloadmanager', 'downloadmanager', VARLINE, undef, HASDEFAULTNO, undef, REPMULTI, WHEREMAIN ],
        contentscanner => [ 'contentscanner', 'contentscanner', VARLINE, undef, HASDEFAULTNO, undef, REPMULTI, WHEREMAIN ],
        maxlogitemlength => [ 'maxlogitemlength', 'maxlogitemlength', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        anonymizelogs => [ 'anonymizelogs', 'anonymizelogs', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        # next option exists in the code but isn't reference ANYwhere, so effectively it doesn't exist
        logtimestamp => [ 'logtimestamp', 'logtimestamp', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        logsyslog => [ 'logsyslog', 'logsyslog', VARONOFF, undef, HASDEFAULTYES, 'on', REPSINGLE, WHEREMAIN ],
        loglocation => [ 'loglocation', 'filepaths', VARTEXT, 8, HASDEFAULTYES, 'PREFIX/var/log/dansguardian/access.log', REPSINGLE, WHEREMAIN ],
        statlocation => [ 'statlocation', 'filepaths', VARTEXT, 8, HASDEFAULTYES, 'PREFIX/var/log/dansguardian/stats', REPSINGLE, WHEREMAIN ],
        logexceptionhits => [ 'logexceptionhits', 'logexceptionhits', VARCHOICE, [ [ 0, 'conf_logexceptionhits_radio_1' ], [ 1, 'conf_logexceptionhits_radio_2' ], [ 2, 'conf_logexceptionhits_radio_3' ] ], HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ], 
       showweightedfound => [ 'showweightedfound', 'showweightedfound', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        weightedphrasemode => [ 'weightedphrasemode', 'weightedphrasemode', VARCHOICE, [ [ 0, 'conf_weightedphrasemode_radio_1' ], [ 1, 'conf_weightedphrasemode_radio_2' ], [ 2, 'conf_weightedphrasemode_radio_3' ] ], HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        reportinglevel => [ 'reportinglevel', 'reporterrors', VARCHOICE, [ [ -1, 'conf_reportinglevel_radio_1' ], [ 0, 'conf_reportinglevel_radio_2' ], [ 1, 'conf_reportinglevel_radio_3' ], [ 2, 'conf_reportinglevel_radio_4' ], [ 3, 'conf_reportinglevel_radio_5' ] ], HASDEFAULTNO, undef, REPSINGLE, WHEREOVERRIDE ],
        accessdeniedaddress => [ 'accessdeniedaddress', 'reporterrors', VARTEXT, 7, HASDEFAULTNO, undef, REPSINGLE, WHEREOVERRIDE ],
        htmltemplate => [ 'htmltemplate', 'reporterrors', VARTEXT, 8, HASDEFAULTYES, 'LANGUAGEDIR/LANGUAGE/template.html', REPSINGLE, WHEREOVERRIDE ], 
        logchildprocesshandling => [ 'logchildprocesshandling', 'logchildprocesshandling', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        logadblocks => [ 'logadblocks', 'logadblocks', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],

        loguseragent => [ 'loguseragent', 'loguseragent', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        bannediplist => [ 'bannediplist', 'iplists', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        exceptioniplist => [ 'exceptioniplist', 'iplists', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        maxuploadsize => [ 'maxuploadsize', 'maxuploadsize', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        urlcachenumber => [ 'urlcachenumber', 'urlcachenumber', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        urlcacheage => [ 'urlcacheage', 'urlcacheage', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        maxcontentfiltersize => [ 'maxcontentfiltersize', 'maxcontentfiltersize', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        maxcontentramcachescansize => [ 'maxcontentramcachescansize', 'maxcontentramcachescansize', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        maxcontentfilecachescansize => [ 'maxcontentfilecachescansize', 'maxcontentfilecachescansize', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        filecachedir => [ 'filecachedir', 'filecachedir', VARTEXT, 7, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        deletedownloadedtempfiles => [ 'deletedownloadedtempfiles', 'deletedownloadedtempfiles', VARONOFF, undef, HASDEFAULTYES, 'on', REPSINGLE, WHEREMAIN ],
        initialtrickledelay => [ 'initialtrickledelay', 'initialtrickledelay', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        trickledelay => [ 'trickledelay', 'trickledelay', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        phrasefiltermode => [ 'phrasefiltermode', 'phrasefiltermode', VARCHOICE, [ [ 0, 'conf_phrasefiltermode_radio_1' ], [ 1, 'conf_phrasefiltermode_radio_2' ], [ 2, 'conf_phrasefiltermode_radio_3' ], [ 3, 'conf_phrasefiltermode_radio_4' ] ], HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        preservecase => [ 'preservecase', 'preservecase', VARCHOICE, [ [ 0, 'conf_preservecase_radio_1' ], [ 1, 'conf_preservecase_radio_2' ], [ 2, 'conf_preservecase_radio_3' ] ], HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        hexdecodecontent => [ 'hexdecodecontent', 'hexdecodecontent', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ], 
        forcequicksearch => [ 'forcequicksearch', 'forcequicksearch', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        nonstandarddelimiter => [ 'nonstandarddelimiter', 'nonstandarddelimiter', VARONOFF, undef, HASDEFAULTYES, 'on', REPSINGLE, WHEREMAIN ],
        filtergroups => [ 'filtergroups', 'filtergroups', VARTEXT, 2, HASDEFAULTYES, 1, REPSINGLE, WHEREMAIN ],
        filtergroupslist => [ 'filtergroupslist', 'filtergroupslist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        usecustombannedimage => [ 'usecustombannedimage', 'usecustombannedimage', VARONOFF, undef, HASDEFAULTYES, 'on', REPSINGLE, WHEREMAIN ],
        custombannedimagefile => [ 'custombannedimagefile', 'custombannedimagefile', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        scancleancache => [ 'scancleancache', 'scancleancache', VARONOFF, undef, HASDEFAULTYES, 'on', REPSINGLE, WHEREMAIN ],
        createlistcachefiles => [ 'createlistcachefiles', 'createlistcachefiles', VARONOFF, undef, HASDEFAULTYES, 'on', REPSINGLE, WHEREMAIN ],
        contentscannertimeout => [ 'contentscannertimeout', 'contentscannertimeout', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
        contentscanexceptions => [ 'contentscanexceptions', 'contentscanexceptions', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
        recheckreplacedurls => [ 'recheckreplacedurls', 'recheckreplacedurls', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHEREMAIN ],
       groupmode => [ 'groupmode', 'groupmode', VARCHOICE, [ [ 0, 'conf_groupmode_radio_1' ], [ 1, 'conf_groupmode_radio_2' ], [ 2, 'conf_groupmode_radio_3' ] ], HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        blockdownloads => [ 'blockdownloads', 'blockdownloads', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHERESHARED ],
        categorydisplaythreshold => [ 'categorydisplaythreshold', 'categorydisplaythreshold', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        embeddedurlweight => [ 'embeddedurlweight', 'embeddedurlweight', VARTEXT, 3, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        enablepics => [ 'enablepics', 'enablepics', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHERESHARED ],
        bypass => [ 'bypass', 'bypass', VARTEXT, 3, HASDEFAULTYES, 0, REPSINGLE, WHERESHARED ],
        bypasskey => [ 'bypasskey', 'bypasskey', VARTEXT, 6, HASDEFAULTYES, '', REPSINGLE, WHERESHARED ],
        infectionbypass => [ 'infectionbypass', 'bypass', VARTEXT, 3, HASDEFAULTYES, 0, REPSINGLE, WHERESHARED ],
        infectionbypasskey => [ 'infectionbypasskey', 'bypasskey', VARTEXT, 6, HASDEFAULTYES, '', REPSINGLE, WHERESHARED ],
        infectionbypasserrorsonly => [ 'infectionbypasserrorsonly', 'infectionbypasserrorsonly', VARONOFF, undef, HASDEFAULTYES, 'on', REPSINGLE, WHERESHARED ],
        disablecontentscan => [ 'disablecontentscan', 'disablecontentscan', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHERESHARED ],
        deepurlanalysis => [ 'deepurlanalysis', 'deepurlanalysis', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHERESHARED ],
        filtergroupsschemelists => [ 'filtergroupsschemelists' , 'filtergroupsschemelists', VARCHOICE, [ [ 1, 'conf_filtergroupsschemelists_radio_1' ], [ 2, 'conf_filtergroupsschemelists_radio_2' ], [ 3, 'conf_filtergroupsschemelists_radio_3' ] ], HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ], # this is _Webmin's_ variable, although stored in dansguardian.conf it means _nothing_ to DansGuardian itself
        filtergroupsdefaultnoweb => [ 'filtergroupsdefaultnoweb' , 'filtergroupsdefaultnoweb', VARONOFF, undef, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ], # this is _Webmin's_ variable, although stored in dansguardian.conf it means _nothing_ to DansGuardian itself
        filtergroupshighestallweb => [ 'filtergroupshighestallweb' , 'filtergroupshighestallweb', VARONOFF, undef, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ], # this is _Webmin's_ variable, although stored in dansguardian.conf it means _nothing_ to DansGuardian itself
        exceptionsitelist => [ 'exceptionsitelist', 'exceptionsitelist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        bannedsitelist => [ 'bannedsitelist', 'bannedsitelist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        greysitelist => [ 'greysitelist', 'greysitelist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        logsitelist => [ 'logsitelist', 'logsitelist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        exceptionurllist => [ 'exceptionurllist', 'exceptionurllist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        bannedurllist => [ 'bannedurllist', 'bannedurllist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        greyurllist => [ 'greyurllist', 'greyurllist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        logurllist => [ 'logurllist', 'logurllist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        exceptionregexpurllist => [ 'exceptionregexpurllist', 'exceptionregexpurllist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        bannedregexpurllist => [ 'bannedregexpurllist', 'bannedregexpurllist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        logregexpurllist => [ 'logregexpurllist', 'logregexpurllist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        weightedphraselist => [ 'weightedphraselist', 'weightedphraselist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        bannedphraselist => [ 'bannedphraselist', 'bannedphraselist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        exceptionphraselist => [ 'exceptionphraselist', 'exceptionphraselist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        picsfile => [ 'picsfile', 'picsfile', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        bannedextensionlist => [ 'bannedextensionlist', 'bannedextensionlist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        bannedmimetypelist => [ 'bannedmimetypelist', 'bannedmimetypelist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        exceptionextensionlist => [ 'exceptionextensionlist', 'exceptionextensionlist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        exceptionmimetypelist => [ 'exceptionmimetypelist', 'exceptionmimetypelist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        exceptionfilesitelist => [ 'exceptionfilesitelist', 'exceptionfilesitelist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        exceptionfileurllist => [ 'exceptionfileurllist', 'exceptionfileurllist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        contentregexplist => [ 'contentregexplist', 'contentregexplist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        urlregexplist => [ 'urlregexplist', 'urlregexplist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        headerregexplist => [ 'headerregexplist', 'headerregexplist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        bannedregexpheaderlist => [ 'bannedregexpheaderlist', 'bannedregexpheaderlist', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        mailer => [ 'mailer', 'emailnotify', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHEREMAIN ],
	# all the rest of the email-notify options are group-only
        usesmtp => [ 'usesmtp', 'emailnotify', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHERESHARED ],
        mailfrom => [ 'mailfrom', 'emailnotify', VARTEXT, 7, HASDEFAULTYES, '', REPSINGLE, WHERESHARED ],
        avadmin => [ 'avadmin', 'emailnotify', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        contentadmin => [ 'contentadmin', 'emailnotify', VARTEXT, 8, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        avsubject => [ 'avsubject', 'emailnotify', VARTEXT, 7, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        contentsubject => [ 'contentsubject', 'emailnotify', VARTEXT, 7, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        notifyav => [ 'notifyav', 'emailnotify', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHERESHARED ],
        notifycontent => [ 'notifycontent', 'emailnotify', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHERESHARED ],
        thresholdbyuser => [ 'thresholdbyuser', 'emailnotify', VARONOFF, undef, HASDEFAULTYES, 'off', REPSINGLE, WHERESHARED ],
        violations => [ 'violations', 'emailnotify', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
        threshold => [ 'threshold', 'emailnotify', VARTEXT, 4, HASDEFAULTNO, undef, REPSINGLE, WHERESHARED ],
	# there are a whole bunch of per-filter-group options that set the score levels for various PICS categories,
	#  however they are only mentioned in the source code, the config files avoid them as though they didn't exist
	#  we don't list them here
	);


# these are FIXED data which may be reference various places
#  do _not_ change them (note that Perl does _not_ enforce the read-only restriction; you must be nice)
our @varnum2vartext = ( 'obsolete', 'checkbox', 'radio', 'text', 'textarea', 'line' );

# input is a "size class", outputs are HTML-specific size= and maxsize= 
our %sizeclass2specifics = (
    1 => [ 1, 1 ],
    2 => [ 2, 2 ],
    3 => [ 3, 3 ],
    4 => [ 6, 6 ],
    5 => [ 12, 12 ],
    6 => [ 20, 20 ],
    7 => [ 20, 56 ],
    8 => [ 40, 128 ],
    9 => [ 56, 200 ],
);

###################
sub validateoptions
###################
{
    return if ! $debug;

    print DEBUGLOG "beginning validating options table\n" if $debug;
    while ( my ($optionname, $entryref) = each %options2details) {
        print DEBUGLOG "OOPS? dangling help pointer help/$$entryref[DETAILSHELP].html (for option $optionname)\n" if ((! -e "help/$$entryref[DETAILSHELP].html") && $debug);
        die "OOPS! - wrong size of array describing option (@$entryref)\n" if scalar @$entryref != 8;
	# following will always fail because we have one use of REPMULTI despite its not being implemented
	#die "OOPS! - REPMULTI not fully implemented yet specified (@$entryref)\n" if (($$entryref[DETAILSREP] == REPMULTI) && ($$entryref[DETAILSVAR] != VARLINE));
        die "OOPS! - out of range variable type (@$entryref)\n" if (($$entryref[DETAILSVAR] < 1) || ($$entryref[DETAILSVAR] > 5));
        die "OOPS! - option (@$entryref) supposedly has default yet no value is specified\n" if (($$entryref[DETAILSHASDEFAULT] == HASDEFAULTYES) && (! defined $$entryref[DETAILSDEFAULTVAL]));
        die "OOPS! - option (@$entryref) default value yet it will never be used\n" if ((defined $$entryref[DETAILSDEFAULTVAL]) && ($$entryref[DETAILSHASDEFAULT] != HASDEFAULTYES));
        die "OOPS! - option (@$entryref) detailsname is not same as key\n" if $optionname ne $$entryref[DETAILSNAME];
    }
}

# Get the DG version
&checkdgver(\$dg_version);

&validateoptions();
&adjustdefaultpaths();
&adjustvariablelocations();
&constructsharedgroupsconfigurationlists();


our $cfref;
if ($ENV{'SCRIPT_FILENAME'} =~ 'dansguardian') {
    # these things don't make sense except if we're invoked on behalf of one of the DG .cgi's

    # Read in the dansguardian.conf file
    $cfref = &read_file_lines_just_once(&group2conffilepath(0));

    # get our own version (we're given the global $module_name)
    our %moduleinfo = &get_module_info($module_name);
    our $modulever = $moduleinfo{'version'};
}


############################################################################################
#
# subroutines only for local use
#
############################################################################################

######################
sub adjustdefaultpaths
######################
{
    my $executable = $config{'binary_file'};
    # exit silently if we can't continue, 
    #  as we have no way to display an error message yet
    #  and callers are not expecting any failure at this point
    return if ! $executable;
    return if (! -e $executable);
    my $output = `$executable -v`;
    my $prefix = '/usr/local';
    if ($output =~ m/--prefix=([^']*)'/) { $prefix = $1; }
    my $proxyuser = 'anonymous';
    if ($output =~ m/--with-proxyuser=([^']*)'/) { $proxyuser = $1; }
    my $proxygroup = 'anonymous';
    if ($output =~ m/--with-proxygroup=([^']*)'/) { $proxygroup = $1; }

    my $languagedir = &getconfigvalue('languagedir');
    my $language = &getconfigvalue('language');

    foreach my $entryref (values %options2details) {
	next if !($$entryref[DETAILSDEFAULTVAL]);
        $$entryref[DETAILSDEFAULTVAL] =~ s/PREFIX/$prefix/;
        $$entryref[DETAILSDEFAULTVAL] = &canonicalizefilepath($$entryref[DETAILSDEFAULTVAL]);
        $$entryref[DETAILSDEFAULTVAL] =~ s/PROXYUSER/$proxyuser/;
        $$entryref[DETAILSDEFAULTVAL] =~ s/PROXYGROUP/$proxygroup/;
        $$entryref[DETAILSDEFAULTVAL] =~ s/LANGUAGEDIR/$languagedir/;
        $$entryref[DETAILSDEFAULTVAL] =~ s/LANGUAGE/$language/;
    }
}

###########################
sub adjustvariablelocations
###########################
{
    # if "shared" variables supported, nothing to adjust in option descriptions
    return if &sharedoptionsavailable();

    # no "shared" variables in earlier versions, so adjust option descriptions
    foreach my $entryref (values %options2details) {
	$$entryref[DETAILSWHERE] = WHEREGROUP if $$entryref[DETAILSWHERE] == WHERESHARED;
    }
}

##########################################
sub constructsharedgroupsconfigurationlists
##########################################
{
    my @values;
    foreach my $list (keys %groupsconfigurationlists) {
        my $currentvalue = &readconfigoptionlimited($list);
        if ($currentvalue) {
            $sharedgroupsconfigurationlists{$list} = 1;
        } else {
            $notsharedgroupsconfigurationlists{$list} = 1;
        }
    }
}

############################################################################################
#
# subroutines for callers (and also this module) to use
#
############################################################################################

###############
sub checkwbconf
###############
{
## checkwbconf();
## Check for existence of Webmin-DG config file

# (admittedly this is quite paranoid [yet easily fooled] and may not be necessary..
#  but it doesn't hurt anything)
    if ((scalar keys %config) <= 0) {
        return 0;
    } else {
        return 1;
    }
}

###############
sub checkdgconf
###############
{
## checkdgconf();
## Check for existence of DG config file
    my $conffilepath = &group2conffilepath(0);
    if (!(-f $conffilepath)) {
        return 0;
    } else {
        return 1;
    }
}

#################
sub checkdgbinary
#################
{
## checkdgbinary();
## Check for existence and executable state of DG binary
    if (!(-x $config{'binary_file'})) {
        return 0;
    } else {
        return 1;
    }
}

##########################
sub sharedoptionsavailable
##########################
{
    &checkdgver(\$dg_version) if (! $dg_version);

    #################################################################################
    #
    # literal in following line is VERY IMPORTANT
    #
    # change it to be the first version in which "shared" (one setting
    # in dansguardian.conf for all groups) options were supported
    #
    my $firstsharedversionstring = '99.99.99.99';	
    #########$firstsharedversionstring = '2.9.8.5';
    #  (current setting of '99.99.99.99' means "we don't know, we're assuming NONE")
    #
    #################################################################################
    my $currentversionnum = &versionstring2versionnum($dg_version);
    my $firstsharedversionnum = &versionstring2versionnum($firstsharedversionstring);

    return ($currentversionnum >= $firstsharedversionnum) ? 1 : 0;
}

############################
sub versionstring2versionnum
############################
{
    my ($stringversion) = @_;
    my ($major, $minor, $sub, $subsub) = ($stringversion =~ m/^\D*(\d+)\D+(\d+)(?:\D+(\d+)(?:\D+(\d+))?)?\D*$/);
    $major = 0 if !$major;
    $minor = 0 if !$minor;
    $sub = 0 if !$sub;
    $subsub = 0 if !$subsub;

    my $numericversion = $subsub + (100 * ($sub + (100 * ($minor  + (100 * $major)))));

    return $numericversion;
}

##############
sub checkdgver
##############
{
## checkdgver();
## Check DG version for compatibility

# optional argument is where to return actual version
#    ($retver is a dummy for $retverrref to point at if argument NOT passed)
    my ($ver, $retver, $retverref);
    if ($#_ >= 0) { ($retverref) = @_; } else { $retverref = \$retver; }

    if (&checkdgbinary) {
        $ver = `$config{'binary_file'} -v 2>&1`;
        '' =~ /()/;
        $ver =~ m/\b(\d+\.\d+(?:\.\d+(?:\.\d+)?)?)\b/;
        $ver = $1;
    } else {
        $ver = '?';
    }
    $$retverref = $ver;
    return(($ver =~ m/^2\.(?:9|10)/) ? $ver : "");
}

################
sub checkmodauth
################
{
## checkmodauth(ACLNAME);
## Check webmin ACL's for ACLNAME against username
    my ($section) = @_;
    if (!$access{$section}) {
        print "<p><span style='color: red'>$text{'index_notauth'}</span><br>\n";
        &ui_print_footer("index.cgi", $text{'index_return'});
        exit;
    }
}

################################################################
#
# there are several different variations 
#  on routines to read configuration variables
#
# (note that -unlike in the past- main-vs.-group is NOT 
# one of the the variations - group number is an argument
# to all routines, and in all cases group=0 means the 
# main group
#
# available routines are:
#
# 1) readconfigoptionlimited(optionname, groupnumber)
#     returns a single naked value that's the first value
#     found in the specified config file
#     -defaults and overrides are NOT accounted for
#     -this is very simple if you just want to know whether
#     a particular option is defined in a particular file
#     -very similar to getconfigvalue, the difference is 
#     one accounts for overrides and defaults while
#     the other doesn't
# 2) getconfigvalue(optionname, groupnumber)
#     returns only a single naked value
#     -DOES account for overrides and defaults,
#     so will sometimes return a value even if that
#     option is not explicitly set in the specified file
#     -this is useful to get the option value that's
#     actually in effect
#     -very similar to readconfigoptionlimited, the
#     difference is one accounts for overrides and defaults
#     while the other doesn't
# 3) readconfigoptiondetails(optionname, groupnumber)
#     returns a complicated structure that includes lots of
#     information and can be used directly for editing
#     -not convenient for some uses though, as the caller
#     has to watch out for 'undef' at various levels and
#     for multiple values
#     -if you're not sure what you want, and you're willing
#     to pick through the complicated returned structure,
#     this is the most complete option
#     -the complicated return structure isn't as arbitrary
#     as it may look, as it can be used DIRECTLY to set up
#     display and editing of config options
# 4) readconfiglinedetails(optionname)
#     this finds whole lines associated with the option,
#     even if they are currently commented out
#     (for example 'authplugin')
#     -group is not an implemented option because such
#     options only occur legitimately in the main config
#     -useful mainly for a few plugin options 
#     -this is a special purpose routine that's probably
#     not useful for anything else
#
################################################################

###########################
sub readconfigoptionlimited
###########################
{
## Read a name=value ONLY from the specified DansGuardian config

## #1 of 4 variants, see earlier comments in this file about ALL config reading routines

## also, only return the first value found no matter what
##  (not even a suggestion of an indication there are multiple values)

# you can think of this as just a thin wrapper around &readconfigoptiondetails_inner
#  so the functionality is easily available to callers even though it can't be called directly
    my ($option, $group) = @_;
    $option = lc $option;
    $group = &canonicalizegroupnumber($group);

    my ($valueslocalref, $valuesallgroupsref, $valuesdefaultref);
    $cfref = &read_file_lines_just_once(&group2conffilepath($group));
    $valueslocalref = &readconfigoptiondetails_inner($option, $cfref);
    return $$valueslocalref[0];
}

##################
sub getconfigvalue
##################
{
## #2 of 4 variants, see earlier comments in this file about ALL config reading routines

    # this is a wrapper for &readconfigoptiondetails that gets the one currently active value,
    #  even if it's a shared setting or a default
    #  (rather than just an explicit setting in the outermost config file)
    my ($option, $group) = @_;
    $group = &canonicalizegroupnumber($group);

    my ($valueslocalref, $valuesallgroupsref, $valuesdefaultref) = &readconfigoptiondetails($option, $group);

    return $$valueslocalref[0] if defined $valueslocalref;
    return $$valuesallgroupsref[0] if ((defined $valuesallgroupsref) && (($options2details{$option}[DETAILSWHERE] == WHERESHARED) || ($options2details{$option}[DETAILSWHERE] == WHEREOVERRIDE)));
    return $$valuesdefaultref[0] if defined $valuesdefaultref;
}

###########################
sub readconfigoptiondetails
###########################
{
## Read a name=value from DansGuardian configs

## #3 of 4 variants, see earlier comments in this file about ALL config reading routines

# this is the guts of much of the "read current setting ..." functionality

# note although we (sorta) handle the case of multiple occurrences, i.e.        foo=bar1
#                                                                       	foo=bar2
#                                                                               foo=bar3
# we do NOT handle (not hardly at all) the alternate syntax of multiple values on one line, i.e.
#                                                                               foo=bar1 bar2 bar3
# also note though that even the bits of functionality that do already exist have 
#  NOT been tested, and may very well not entirely work correctly. 
    my ($option, $group) = @_;
    $option = lc $option;
    $group = &canonicalizegroupnumber($group);

    return [ undef, undef, undef ] if $group < 0;

    my ($valueslocalref, $valuesallgroupsref, $valuesdefaultref);
    my (@result);

    $cfref = &read_file_lines_just_once(&group2conffilepath($group));
    $valueslocalref = &readconfigoptiondetails_inner($option, $cfref);
our $foo = $valueslocalref ? "[ @$valueslocalref ]" : 'undef';
    $result[0] = $valueslocalref;
    if ($group != 0) {
        $cfref = &read_file_lines_just_once(&group2conffilepath(0));
        $valuesallgroupsref = &readconfigoptiondetails_inner($option, $cfref);
        $result[1] = $valuesallgroupsref;
    } else {
        $result[1] = undef;
    }
    my $detailsref = $options2details{$option};
    if ($$detailsref[DETAILSHASDEFAULT] == HASDEFAULTYES) {
        my $defaultval = $$detailsref[DETAILSDEFAULTVAL];
        $result[2] = [ $defaultval ];
    } else {
        $result[2] = undef;
    }
    return @result;
}

#--------------------------------
sub readconfigoptiondetails_inner
#--------------------------------
{
# Only called internally, never to be called directly by a user
# (if you want this functionality, call &readconfigoptionlimited,
#  which is available to users and is a thin wrapper around this functionality)

# this subroutine is defined at file scope rather than inside another subroutine
# for a couple reasons - first, we don't want a "closure" - second, this
# is called by more than one subroutine so it wouldn't work to have it inside any one of them

# note this assumes ONE value per line and _probably_won't_work_correctly_
#  with lines of the form foo=bar1 bar2 bar3

# this at bottom provides much of the functionality exposed by &readconfigoptiondetails,
# and also by &readconfigoptionlimited
    my ($option, $cfref) = @_;
    my ($line, $name, $value, $valuealt);
    my @result = ();
    my $valuesfound = 0;
    CONFIGLINE: foreach my $protoline (@$cfref) {
	next if $protoline =~ m/^\s*$/;	# skip blank lines
        next if $protoline =~ m/^\s*#+\s*[^!][^!]/;	# skip comment-only lines (except !! warnings)
	#($line) = ($protoline =~ m/^\s*((?:#[#\s]*)?[^#]*[^#\s])/);	# copy data part but not partial comment part
	# used above line to get rid of display of inactivated config files, but this also screwed up conf display
	# so reimplemented it in a higher subroutine (edit_file_row) so it wouldn't have such drastic effects all over
	($line = $protoline) =~ s/\s*#(?!!!).*$//;	# trim off partial comment part (except !! warnings)
        next if $line !~ m/=/;	# skip anything without an equals sign in the part we kept
        ($valuealt, $name, $value) = ($line =~ m/^\s*(?:#(?>[\s#]*)(.*?(?<=\S)))?\s*\b(\w+)\s*=\s*(\S.*(?<=\S))?\s*$/);
	$valuealt = '' if ! defined $valuealt;	# can happen if parse failure
	$name = '' if ! defined $name;		# can happen if parse failure
	$value = '' if ! defined $value;	# can happen if parse failure

	$name = lc $name;
        if ($name eq $option) {
            if ($options2details{$option}[DETAILSVAR] == VARONOFF) {
                $value = ($value =~ m/on|t[r\b]|y[e\b]|[1-9]/i) ? 'on' : 'off';
            }
            $value = $valuealt if $valuealt =~ m/!!/;
            # no need to trim leading/trailing white space because regexp above already did it!
            $value =~ s/^(['"])([^\1]*)\1.*$/$2/;	# strip quotes (also strip any second value on same line)
            ++$valuesfound;
            push @result, $value;
            next CONFIGLINE;
        }
    }
    my $resultref = ($valuesfound > 0) ? \@result : undef;
    return $resultref;
}

#########################
sub readconfiglinedetails
#########################
{
## Read a name=value from DansGuardian config even if commented out and/or multivalued

## #4 of 4 variants, see earlier comments in this file about ALL config reading routines

# use this only for things like "authplugin" and other things that may be "commented out"
# mostly use &readconfigoptiondetails
    my ($option) = @_;
    $option = lc $option;
    my @result = ();
    my ($name, $value, $comment, $line);
    CONFIGLINE: foreach my $protoline (@$cfref) {
	next if $protoline =~ m/^\s*$/;	# skip blank lines
	($line) = ($protoline =~ m/^\s*((?:#[#\s]*)?[^#]*[^#\s])/);	# copy data part but not partial comment part
        next if $line !~ m/=/;	# skip anything without an equals sign in the non-comment part
        $line =~ s/^\s*//;	# trim white space from line
	$line =~ s/\s*$//;
        ($name, $value) = split /\s*=\s*/, $line;
        ($value, $comment) = split /\s*#\s*/, $value;
        $name = lc $name;
        if ($name =~ m/\b$option$/) {
            # no need to trim leading/trailing white space because already done above!
            $value =~ s/^(['"])([^\1]*)\1$/$2/;	# strip quotes
            push @result, [ $name, $value ];
            next CONFIGLINE;
        }
    }
our $foo0 = $result[0] ? "[ @{$result[0]} ]" : 'undef';
our $foo1 = $result[1] ? "[ @{$result[1]} ]" : 'undef';
our $foo2 = $result[2] ? "[ @{$result[2]} ]" : 'undef';
our $foo3 = $result[3] ? "[ @{$result[3]} ]" : 'undef';
our $foo4 = $result[4] ? "[ @{$result[4]} ]" : 'undef';
our $foo5 = $result[5] ? "[ @{$result[5]} ]" : 'undef';
our $foo6 = $result[6] ? "[ @{$result[6]} ]" : 'undef';
    return @result;
}

###################
sub getbesthelpfile
###################
{
    my ($option, $helpfile) = @_;
    my $result = $helpfile;

    $result = $option if ! defined $helpfile;
    if ((! -e "./help/$result.html") && (! -e "./help/$result.$current_lang.html")) {
        # no such helpfile exists, so try to select an appropriate generic one
        if ($option =~ m/(path|dir|filename)/) {
            $result = 'filepaths';
        } elsif (($option =~ m/list[s\s]*$/ ) || ($option =~ m/pics/)) {
           $result = 'lists';
        } else {
           my $detailsref = $options2details{$option};
           $result = "helpvar$varnum2vartext[($$detailsref[DETAILSVAR])]";
        }
    }
    return $result;
}

{
# variable shared between outer and inner routines
our %filepathslisted;
our $showdupsflag;

#################
sub edit_file_row
#################
{
# edit_file_row(<configfileoptionname>, <groupnumber>, <helpfile>, <wheretoreturnto>)
# third argument defaults more intelligently than in previous version
# second and fourth arguments are new
    my ($option, $group, $helpfile, $return, $showdupsflagarg) = @_;
    $showdupsflag = $showdupsflagarg;
    $group = &canonicalizegroupnumber($group);
    $helpfile = &getbesthelpfile($option, $helpfile);

    my $label = $text{"conf_$option"};
    $label = $option if ! $label;
    my ($valuesref, $valuesmainref, $defaultsref) = &readconfigoptiondetails($option, $group);
    # ignore any settings found in the main config file if they can't have any effect
    $valuesmainref = undef if ! &sharedoptionsavailable();
    # (note the following only works if &readconfigoptiondetails returns 'undef' [rather than ( )]
    #  for missing sets of values - as the assumption is indeed true, this works, 
    #  but changing style of &readconfigoptiondetails to be more "standard Perl" would probably break this)
    my @values = (defined $valuesref) ? @$valuesref : ((defined $valuesmainref) ? @$valuesmainref : ((defined $defaultsref) ? @$defaultsref : () ));
    if (($#values < 0) && ($option =~ m/(list|pics)/)) {
        # if no value at all was found, create a reasonable (filepath) value and use that
        $values[0] = &canonicalizefilepath("$config{'conf_dir'}/lists/$option"); 
    }
    foreach  my $value (@values) {
        # readconfigoptiondetails may return a value like "!! Not Compiled!!"
        # just skip any such lines
        next if $value =~ m/!!/;
        $value = '&nbsp;' if ! $value;	# avoid displaying line with screwy background colors (even if data error)

        %filepathslisted = ();	# (re)set to nothing

        # actually do the work (and anything below it too)
        &edit_file_row_inner($option, $value, $helpfile, 0, $return);
    }

#-----------------------
sub edit_file_row_inner
#-----------------------
{
    my ($name, $filepath, $helpfile, $level, $return) = @_;

    # list a file only once even if there are multiple .Includes for it in either same/different files
    return if ((exists $filepathslisted{$filepath}) && (!$showdupsflag));
    ++$filepathslisted{$filepath};

    my ($formatlink, $formatnolink, $recurse);
    my ($label, $sublabel, $newlevel, $globalname);
    my ($fileref, $file_path, $file_name, $file_line, $proto_file_line);
    $filepath = &canonicalizefilepath($filepath);
    my $filepath2 = readlink $filepath;
    $label = $text{"conf_$name"}; 
    $newlevel = $level + 1;
    
    if (($filepath =~ m/\b(blacklists|phraselists)/) || ($filepath2 =~ m/\b(blacklists|phraselists)/)) {
        # lists from outside mechanisms (treat as read-only)
        # display them as follows (or just return to not display them)
        return if ! $config{'show_fixedlists'};
        $recurse = 0;
        $formatnolink = "style='font-size: 90%; font-variant: small-caps; color: #808080'";
        $formatlink = $formatnolink;
        ($label, $sublabel) = ($filepath =~ m{/([^/]+)/(?:[^/_]*|[^/]*_([^/]*))$});
        $label = "$label/$sublabel" if $sublabel;
    } elsif ((($filepath =~ m{lists/[^/]*$}) || ($filepath =~ m{lists/local}))
        || (($filepath2 =~ m{lists/[^/]*$}) || ($filepath2 =~ m{lists/local}))) {
    #($label in @sharedgroupsconfigurationlists)# MIGHT need to code subroutine to test this explicitly, unlikely
        # shared lists (only edit carefully, widespread effects)
        $formatnolink = "style='font-size: 85%; font-style: italic; color: #707070'";
        $formatlink = "style='font-size: 90%; font-style: italic; color: #50507c'";
        $recurse = 1;
    } elsif ($level > 0) {
        # an included list, probably for a different filter group
        $formatnolink = "'style='font-size: 85%; color: #404040'";
        $formatlink = "style='font-size: 90%; color: #404070'";
        ($globalname) = ($name =~ m/^(.*)f\d+/);
        $label = $text{"conf_$globalname"} if ! $label;
        $recurse = 1;
    } else {
        # un-special top-level list
        $formatnolink = '';
        $formatlink = '';
        ($globalname) = ($name =~ m/^(.*)f\d+/);
        $label = $text{"conf_$globalname"} if ! $label;
        $recurse = 1;
    }

    $label = $name if ! $label;
    $label = (($level > 0) ? '&nbsp;' : '') . ('+ ' x $level) . $label;

    my $helplink = $helpfile ? &hlink("<span $formatlink>[$text{'button_help'}]</span>", $helpfile) : '';

    print &ui_columns_row( [ "<span $formatnolink>$label</span>", "<a href='./editfile.cgi?file=$filepath&return=$return'><span $formatlink>$filepath</span></a>", $helplink ] );

    if ($recurse) {
        # search the file for '.Include<...>'-like directives
        #  and list any files found

        # (except do NOT scan through blacklist/phraselist files,
        #  as it will take a very large amount of CPU time and will never find anything useful)
        $fileref = &read_file_lines_just_once($filepath);
        foreach $proto_file_line (@$fileref) {
            next if $proto_file_line =~ m/^#/;	# m/^\s*#/ smarter, but doesn't perform as well
            next if $proto_file_line =~ m/^$/;	# m/^\s*$/ smarter, but doesn't perform as well
            ($file_line = $proto_file_line) =~ s/#.*$//;	# dumb stripping of partial line comment,
								#  but we're very concerned with performance
            next if $file_line =~ m/^\s*(#|$)/;	# finish ignoring uninteresting lines, 
						#  but only later so we don't impact performance so much
            my ($subname, $subvalue) = '';
            if (($file_line =~ m/^\s*(\S*include\S*)\s*<(.*)>\s*$/i) || ($file_line =~ m/^\s*(\S+)\s*=\s*(\S.*\S)\s*$/)) {
                # note regexps not only isolate values but also trim them
                $subname = $1;
                $subvalue = $2;
            } else {
                # we now know for sure this is not a line of interest
                next;
            }
            # conditions (_reversed_ in 'if') on $subname that say definitely include this line
            if ($subname !~ m/include/i) {
                # not certain yet, so see if $subvalue looks like a filenamepath
                next if $subvalue !~ m{['"<]?/};
                next if $subvalue !~ m{/.*/.*/};
            }
            # we now know this line is definitely to be processed, so strip quotes
            ($file_path = $subvalue) =~ s/^(['"])(.*)\1$/$2/;
            if ($subname eq '.Include') { ($file_name = $file_path) =~ s{^.*/}{}; } else { $file_name = $subname; }
            # recursive calls
            &edit_file_row_inner($file_name, $file_path, undef, $newlevel, $return);
        }
    }
}

}

}

our $errorsonform;	# "global" because referenced by several different subroutines,
			#  but not intended to be referenced by callers

################################
sub edit_options_formtable_start
################################
{
    my ($tabref) = @_;

    my $dest = $$tabref[2];

    print &ui_form_start($dest, 'post');
    print "<table border=0 bgcolor=#d8d8d8 cellpadding=2 cellspacing=3><tr bgcolor=#6080ff><td align=center><span style='color: white; font-size: larger; font-weight: 800'>&nbsp;&nbsp;$$tabref[3]&nbsp;&nbsp;</span></td></tr><tr bgcolor=#e8e8e8><td><table cellpadding=4 cellspacing=0 border=0>\n";
    $errorsonform = 0;
}

##############################
sub edit_options_formtable_end
##############################
{
    my ($buttonsflag) = @_;
    # 0 for normal, 1 for only "ok", -1 for no buttons at all


    print "</table></td></tr><tr><td align=center style='padding: 10px'>";
    my @buttons = ( [ 'button', $text{'button_update'} ], [ 'button', $text{'button_cancelchange'} ] );
    if (($errorsonform != 0)  || ($buttonsflag == 1)) {
        @buttons = ( [ 'button', $text{'button_ok'} ] );
        print "<input type=hidden name=invoke value=cancelreturn>\n";
    }
    if ($buttonsflag >= 0) {
        print &ui_form_end(\@buttons);
    } else {
        print &ui_form_end(undef);
    }
    print "</td></tr></table>\n";
}

#############################
sub edit_options_headings_row
#############################
{
# first argument is filter group number (0 == "main")
# second argument >0 means show 'All Groups' no matter what,
# == 0 show 'All Groups' IF shared options are available in the current release
# <0 means do _not_ show 'All Groups' no matter what
    my ($group, $forcegroupheadingonoroff) = @_;
    $group = &canonicalizegroupnumber($group);

    my $leftvaluetitle = ($group == 0) ? $text{'edit_columns_system'} : $text{'edit_columns_group'};
    $leftvaluetitle .= " $text{'edit_columns_value'}";
    # net effect (intentional but not obvious) is that if first argument is group==0 (main group), 
    #  second argument acts like it was -1 (never show a middle title) even if not specified explicitly
    my $middlevaluetitle = '';
    $middlevaluetitle = $text{'edit_columns_allgroups'} if (($forcegroupheadingonoroff > 0) || (($forcegroupheadingonoroff == 0) && &sharedoptionsavailable));

    print "<tr><td align=left style='font-size: larger; font-weight: 600'>$text{'edit_columns_name'}</td><td align=center style='font-size: larger; font-weight: 600'>$leftvaluetitle</td><td align=right style='font-size: larger; font-weight: 600'>$text{'edit_columns_set'}</td><td align=center style='font-size: larger; font-weight: 600'>$middlevaluetitle</td><td align=center style='font-size: larger; font-weight: 600'>$text{'edit_columns_default'}</td></tr>\n";
}

##############################
sub edit_options_separator_row
##############################
{
    print "<tr><td colspan=5><hr></td></tr>\n";
}

#########################
sub edit_options_data_row
#########################
{
# this is the guts of all the configuration editing functionality
# to do this, it's a very long complicated subroutine

    my ($option, $group) = @_;
    $group = &canonicalizegroupnumber($group);

    if (! exists $options2details{$option}) {
        print "OOPS! internal error, no details available for option $option<br>\n" if $debug;
        return;	# we can't do anything useful, so just skip this one
    }
    my $detailsref = $options2details{$option};
    my $detailsname = $$detailsref[DETAILSNAME];
    my $detailshelp = $$detailsref[DETAILSHELP];
    my $detailsvar = $$detailsref[DETAILSVAR];
    my $detailschoiceref = $$detailsref[DETAILSCHOICE];
    my $detailstextindex = $$detailsref[DETAILSTEXT];
    my $detailsdefault = $$detailsref[DETAILSDEFAULTVAL];
    my $detailsrep = $$detailsref[DETAILSREP];
    my $detailswhere = $$detailsref[DETAILSWHERE];

    print "internal error choice type var but choice parameters not defined (@$detailsref)<br>\n" if (($detailsvar == VARCHOICE) && (! defined $detailschoiceref) && $debug);
    print "internal error text type var but text parameters not defined (@$detailsref)<br>\n" if (($detailsvar == VARTEXT) && (! defined $detailstextindex) && $debug);

    # silently discard requests for variables that can only go in the other conf
    if (($detailswhere == WHEREMAIN) && ($group != 0)) {
        print "OOPS! internal error, main-only option ($option) called for group<br>\n" if $debug;
        return;
    }
    if (($detailswhere == WHEREGROUP) && ($group == 0)) {
        print "OOPS! internal error, group-only option ($option) called for main<br>\n" if $debug;
        return;
    }

    my $legend = $text{"conf_$detailsname"};
    $legend = $text{"conf_$option"} if ! $legend;
    $legend = $detailsname if ! $legend;
    $legend = $option if ! $legend;
    my $helpfile = &getbesthelpfile($detailsname, $detailshelp);

    my @currentsetting = &readconfigoptiondetails($option, $group);

    my $localavail = (defined $currentsetting[0]) ? 1 : 0;
    my $allgroupsavail = (defined $currentsetting[1]) ? 1 : 0;
    # if not &sharedoptionsavailable
    #  (which we can determine as WHERESHARED has _already_ been "adjusted" to WHEREGROUP),
    #  make the middle option not available no matter what the conf file says)
    #  (probably the conf file does not have any such setting so it will work,
    #  but there's always the possibility of a stray setting)
    $allgroupsavail = 0 if (($detailswhere != WHEREOVERRIDE) && ($detailswhere != WHERESHARED));
    my $defaultavail = (defined $currentsetting[2]) ? 1 : 0;
    my $localcolor = 'transparent';
    my $pointatlocal = '';
    my $localset = 0;
    my $localdisabled = 'disabled';
    my $allgroupscolor = 'transparent';
    my $defaultcolor = 'transparent';
    if ($localavail) {
        $localcolor = '#26f';
        $pointatlocal = 'checked';
        $localset = 1;
        $localdisabled = '';
    } elsif ($allgroupsavail) {
        $allgroupscolor = '#26f';
        $pointatlocal = '';
    } elsif ($defaultavail) {
        $defaultcolor = '#26f';
        $pointatlocal = '';
    }
    my $previousvalue = ($localset) ? $currentsetting[0][0] : 'not_set';

    print "<tr><th align=left>".&hlink("$legend<small><br>($option)</small>", $helpfile)."</th>";

    if (($detailsvar != VARLINE) && $currentsetting[0] && (scalar @{$currentsetting[0]} > 1)) {
        print "<td colspan=4 align=center><span style='color: red'>$text{'error_morethanonce'}</span></td></tr>";
        ++$errorsonform;
        return;
    }
    if (($detailsvar != VARLINE) && ($currentsetting[0][0] =~ m/!!/)) {
        print "<td colspan=4 align=center><span style='color: blue'>$text{'error_warning'} $currentsetting[0][0]</span></td></tr>\n";
        return;
    }

    goto qw(VARNONE VARONOFF VARCHOICE VARTEXT VARPARA VARLINE)[$detailsvar];
    print "OOPS! internal error, detailsvar=$detailsvar not understood ($detailsname)\n" if $debug;
    return;

    my ($legendkey, $availabletag, $color, $valueonoff);

    VARNONE: {
        print "<td colspan=4 align=center><span style='color: magenta'>$text{'error_obsolete'}</td>" if $localset;
        print "</tr>\n";
        return;
    }
    VARONOFF: {
        my $localchecked = ($currentsetting[0][0] eq 'on') ? 'checked' : '';
        my $allgroupschecked = ($currentsetting[1][0] eq 'on') ? 'checked' : '';
        my $defaultchecked = ($currentsetting[2][0] eq 'on') ? 'checked' : '';

        print "<td align=right style='border: 5px ridge $localcolor' title=$localavail><input type=checkbox name=$detailsname value=on $localchecked $localdisabled><input type=hidden name=${detailsname}_previous value='$previousvalue'></td><td>&lArr<input name=${detailsname}_set type=checkbox $pointatlocal onClick='highlightactive(this.parentNode.parentNode,this.checked)'></td><td align=left style='border: 5px ridge $allgroupscolor' title=$allgroupsavail>";
        if ($allgroupsavail) {
            print "<img src='images/transparent1x1.gif' width=20><input name=x type=checkbox $allgroupschecked disabled>";
        }
        print "</td><td align=left style='border: 5px ridge $defaultcolor' title=$defaultavail>";
        if (defined $detailsdefault) {
            print "<img src='images/transparent1x1.gif' width=20><input name=x type=checkbox $defaultchecked disabled>";
        }
        print "</td></tr>\n";
        goto ENDCASE;
    }
    VARCHOICE: {
        # must give "all groups" and "default" fields a full name for radio buttons,
        #  as just an 'x' results in 'checked' not working
        my $localvalue = $currentsetting[0][0];
        my $allgroupsvalue = $currentsetting[1][0];
        my $defaultvalue = $currentsetting[2][0];

        print "<td align=right style='border: 5px ridge $localcolor' title=$localavail>";
        my ($value, $checked, $legendindex, $legendname, $legend);
        foreach my $valueref (@$detailschoiceref) {
            $value = $$valueref[0];
            $legendkey = $$valueref[1];
	    $checked = ($localvalue eq $value) ? 'checked' : '';
            $legend = (exists $text{$legendkey}) ? $text{$legendkey} : $value;
            print "$legend<input type=radio name=$detailsname value=$value $checked $localdisabled><br>";
        }
        print "<input type=hidden name=${detailsname}_previous value='$previousvalue'>";
        print "</td><td>&lArr<input name=${detailsname}_set type=checkbox $pointatlocal onClick='highlightactive(this.parentNode.parentNode,this.checked)'></td><td align=left style='border: 5px ridge $allgroupscolor' title=$allgroupsavail>";
        if ($allgroupsavail) {
            foreach my $valueref (@$detailschoiceref) {
                $value = $$valueref[0];
                $legendkey = $$valueref[1];
                $checked = ($allgroupsvalue eq $value) ? 'checked' : '';
                print "<img src=images/transparent1x1.gif width=20><input name='X$detailsname' type=radio $checked disabled><br>";
            }
	}
        print "</td><td align=left style='border: 5px ridge $defaultcolor' title=$defaultavail>";
        if (defined $detailsdefault) {
            foreach my $valueref (@$detailschoiceref) {
                $value = $$valueref[0];
                $legendkey = $$valueref[1];
	        $checked = ($defaultvalue eq $value) ? 'checked' : '';
                print "<img src=images/transparent1x1.gif width=20><input name='XX$detailsname' type=radio $checked disabled><br>";
            }
        }
        print "</td></tr>\n";
        goto ENDCASE;
    }
    VARTEXT: {
        my $localvalue = $currentsetting[0][0];
        my $allgroupsvalue = $currentsetting[1][0];
        my $defaultvalue = $currentsetting[2][0];

	my $sizeref = $sizeclass2specifics{$detailstextindex};
        my $boxsize = $$sizeref[0];
        my $boxmaxlength = $$sizeref[1];

        print "<td align=right style='border: 5px ridge $localcolor' title=$localavail><input type=text name=$detailsname value='$localvalue' size=$boxsize maxlength=$boxmaxlength $localdisabled><input type=hidden name=${detailsname}_previous value='$previousvalue'></td><td>&lArr<input name=${detailsname}_set type=checkbox $pointatlocal onClick='highlightactive(this.parentNode.parentNode,this.checked)'></td><td align=left style='border: 5px ridge $allgroupscolor' title=$allgroupsavail>";
        if ($allgroupsavail) {
            print "<input name=x type=text value='$allgroupsvalue' size=$boxsize maxlength=$boxmaxlength disabled>";
        }
        print "</td><td align=left style='border: 5px ridge $defaultcolor' title=$defaultavail>";
        if (defined $detailsdefault) {
            print "<input name=x type=text value='$defaultvalue' size=$boxsize maxlength=$boxmaxlength disabled>";
        }
        print "</td></tr>\n";
        goto ENDCASE;
    }
    VARPARA: {
        print "<tr><td>VARPARA not yet</td></tr>\n";
        goto ENDCASE;
    }
    VARLINE: {
        print "<tr>\n";
        my @values = &readconfiglinedetails($option);
        my ($name, $value, $subname, $setting, $available, $checked, $disabled);
        foreach my $namevalueref (@values) {
            $name = $$namevalueref[0];
            $value = $$namevalueref[1];
            ($subname) = $value =~ m{^[^#]*/([^/.#]+)\.};
            $name = "# !! unavail-use icap !!  $option" if $subname =~ m/kavd/;
    	    $setting = $name !~ m/^\s*#/;
            ($availabletag) = ($name =~ m/^[#\s]*(.*\S)\s*$option/);
            $available = $availabletag !~ m/!!/;
            $checked = $setting ? 'checked' : '';
            $valueonoff = $setting ? 'on' : 'off';
            $disabled = $available ? '' : 'disabled';
            $color = $available ? '#26f' : 'transparent';
            $legend = $available ? $subname : "$availabletag - $subname";
            $legend = "(clamdscan preferred) $legend" if $subname =~ m/clamav/;
            print "<tr><td align=right>$legend</td><td style='border: 5px ridge $color'>&nbsp;&nbsp;&nbsp;<input type=checkbox name='$option;$subname' value=on $checked $disabled>&nbsp;&nbsp;<input type=hidden name='$option;${subname}_previous' value=$valueonoff></td></tr>\n";
        }
        print "<tr><td></td></tr>\n";	# a little space at the end before next
        goto ENDCASE;
    }

    ENDCASE:
        return;

}

##################
sub restart_button
##################
{
    my ($forceflag) = @_;
    $forceflag = 0 if !$forceflag;	# provide default value
    # > 0 means output as if running no matter what
    # == 0 means check and respond to the actual current situation
    # > 0 means output as if not running no matter what

# restart_button()
# Returns HTML for a link to put in the top-right corner
# I stole this from the apache module
    my $rv = '<small>';
    if (($forceflag > 0) || (($forceflag == 0) && &dgisrunning())) {
        if ($access{start}) {
            $rv .= "<a href='status.cgi?action=restart'>$text{'index_restart'}</a><br>\n";
        }
        if ($access{stop}) {
            $rv .= "<a href='status.cgi?action=stop'>$text{'index_stop'}</a><br>\n";
        }
        if ($access{reload}) {
            $rv .= "<a href='status.cgi?action=reload'>$text{'index_reload'}</a><br>\n";
        }
    } else {
        if ($access{start}) {
            $rv .= "<a href='status.cgi?action=start'>$text{'index_start'}</a><br>\n";
        }
    }
    $rv .= '</small>';

    return $rv;
}

#############
sub dgprocess
#############
{
# do the actual process manipulation (this does the guts of status.cgi)
#                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    my ($action) = @_;
    (my $checkaccessaction = $action) =~ s/^restart$/start/;
    my ($cmd, @allpids, $childprocs, $numchildren, $temp);
    my $typeofwait = 0;
    if ($access{$checkaccessaction}) {
    # You are authorized to perform the action
        if ($action eq 'start') {
            if ($config{'start_cmd'}) {
                $cmd = $config{'start_cmd'};
            } else {
                $cmd = $config{'binary_file'};
            }
            $typeofwait = 1;
        } elsif ($action eq 'stop') {
            if ($config{'stop_cmd'}) {
                $cmd = $config{'stop_cmd'};
            } else {
                $cmd = "$config{'binary_file'} -q";
            }
            $typeofwait = 2;
        } elsif ($action eq 'restart') {
            if ($config{'restart_cmd'}) {
                $cmd = $config{'restart_cmd'};
            } else {
                $cmd = "$config{'binary_file'} -r";
            }
            $typeofwait = 1;
        } elsif ($action eq 'reload') {
            $cmd = "$config{'binary_file'} -g";
            $typeofwait = 3;
        } elsif ($action eq 'status') {
            $cmd = "$config{'binary_file'} -s";
            $typeofwait = 0;
        }
    } else {
    # You are not authorized to perform the action
        print "<p>$text{'index_notauth'}\n";
        return;
    }
    # Now we run the command, and display output
    $temp = &tempname();
    my $rv = &system_logged("$cmd >$temp 2>&1 </dev/null");
    my $outlinesref = &read_file_lines_just_once($temp);
    unlink($temp);

    # if it was a start command and failed, try to get more details
    if ((($cmd eq $config{'start_cmd'}) && ($cmd =~ m/ start/i) && ($$outlinesref[0] =~ m/fail/i))
	|| (($cmd eq $config{'restart_cmd'}) && ($cmd =~ m/ restart/i) && ($$outlinesref[1] =~ m/fail/i))) {
        my $temp2 = &tempname();
        my $cmd2 = "$config{'binary_file'} -v";
        my $rv2 = &system_logged("$cmd2 >$temp2 2>&1 </dev/null");
        my $cmd3 = $config{'binary_file'};
        my $rv3 = &system_logged("$cmd3 >>$temp2 2>&1 </dev/null");
        my $outlinesref2 = &read_file_lines_just_once($temp2);
        unlink ($temp2);
        # append details so they appear to be part of output of original command
        push @$outlinesref, '', '', @$outlinesref2;
    }

foreach my $line (@$outlinesref) {
}
    print &ui_table_start($cmd, undef, 1);
    my ($parentpid) = ($$outlinesref[0] =~ m/:\D*(\d+)/);
    if ($#$outlinesref >= 0) {
        for my $outline (@$outlinesref) {
            $outline =~ s/\e\[\d+(?:;\d+)?\w//sg;	# remove escape sequences
					#    (such as service-init scripts setting a color)
            $outline =~ s/:(?=\S)/: /;	# insert a space after the colon if there isn't already one
            print &ui_table_row($outline);
        }
    } else {
        print &ui_table_row($text{'index_done'});
    }
    if ($action eq "status") {
        print "<tr><td><hr></td></tr>\n";
        @allpids = &find_byname('dansguardian');
        shift @allpids if $allpids[0] == $parentpid;	# remove parent pid if we can
        $numchildren = scalar @allpids;
        print &ui_table_row("$text{'index_childproc'}: $numchildren");
        $childprocs = join ' ', @allpids;
        print &ui_table_row("$text{'index_childproclist'}: $childprocs");
    }
    print &ui_table_end();

    # provide a little "settling time" for the operation we just did to really complete
    #  (we attempt to be intelligent about this, not waiting longer than necessary,
    #   but we are NOT determinate - we'll stop waiting and return no matter what
    #   happens [or doesn't happen] after only a very short time - even in the worst
    #   case of a whole loop completing, it's not long, we never get "stuck" in any loop)
    my $pidfile = $config{'pid_file'};
    my $i;
    if ($typeofwait == 1) {
        # start, probably won't return here until complete, but be cautious anyway
	for ($i=0; $i<2; ++$i) {
	    last if -e $pidfile;
            Time::HiRes::sleep 0.1;
        }
        Time::HiRes::sleep 0.2;
    } elsif ($typeofwait == 2) { 
        # stop, asynchronous, don't be fooled 
        #  just because pid file has gone doesn't mean `ps` won't still show processes
        for ($i=0; $i<8; ++$i) {
            last if ! -e $pidfile;
            Time::HiRes::sleep 0.1;
        }
        Time::HiRes::sleep 1.2;
    } elsif ($typeofwait == 3) {
        # gentle reload/restart, should be very fast
        Time::HiRes::sleep 0.25;
    }
        
}

###############
sub dgisrunning
###############
{
    # run the command that finds out 
    #  (checking for the presence of /var/run/dansguardian.pid isn't totally reliable)
    my $cmd = "$config{'binary_file'} -s";
    my $temp = &tempname();
    my $rv = &system_logged("$cmd >$temp 2>&1 </dev/null");
    my $outlinesref = &read_file_lines_just_once($temp);
    unlink($temp);

    return 1 if ($$outlinesref[0] =~ m/arent.*pid/);
    return 0;
}

####################
sub checkdgisrunning
####################
{
# call only internally to library, don't "print" on behalf of caller in most cases
    print "<p><span style='color: red'>$text{'error_notrunning'}</span><p>\n" if ! &dgisrunning;
}

####################
sub getcpupercentage
####################
{
    # Run search command and collect output
    my $cmd = "vmstat 1 3";
    my $temp = &tempname();
    &system_logged("$cmd >$temp 2>&1 </dev/null");
    my $outlinesref = &read_file_lines_just_once($temp);
    my ($idlepercentage1) = ($$outlinesref[2] =~ m/\b(\d+)\s+\d+\s*$/);
    return -1 if $idlepercentage1 !~ m/^\d+$/;
    my ($idlepercentage2) = ($$outlinesref[3] =~ m/\b(\d+)\s+\d+\s*$/);
    return -1 if $idlepercentage2 !~ m/^\d+$/;
    my ($idlepercentage3) = ($$outlinesref[4] =~ m/\b(\d+)\s+\d+\s*$/);
    return -1 if $idlepercentage3 !~ m/^\d+$/;
    my $idlepercentage = ($idlepercentage1 > $idlepercentage2) ? (($idlepercentage1 > $idlepercentage3) ? $idlepercentage1 : $idlepercentage3) : (($idlepercentage2 > $idlepercentage3) ? $idlepercentage2 : $idlepercentage3);	# could also be an average of 1+2+3 (or could take more than 3 samples)

    my $cpupercentage = 100 - $idlepercentage;
    $cpupercentage = 100 if $cpupercentage > 100;
    $cpupercentage = 0 if $cpupercentage < 0;

    return $cpupercentage;
}

##############
sub cputoobusy
##############
{
    my $cpupercentage = &getcpupercentage();

    return '' if $cpupercentage < 0;	# on internal error don't trip caller error, just feign success 
    return '' if $cpupercentage < 75;	# our threshold

    return 1;	# oops, return 'true'
}

# data used by &accessfile to handle non-regular lists (filename => permissionsname)
our %basefilepermissions = (
    messages => 'editmessages',
    filtergroupslist => 'editfiltergroupassignments',
    ipgroups => 'editfiltergroupassignments',
    bannediplist => 'editlists',
    exceptioniplist => 'editlists',
    authplugins => 'editplugconf',
    downloadmanagers => 'editplugconf',
    contentscanners => 'editplugconf',
    );

##############
sub accessfile
##############
{
# does the user have permission to modify this file?
    my ($filepath) = @_;
    ($filepath =~ m{\b([^/.]+?)(f\d+)?\.(conf|20\d+)$}) || ($filepath =~ m{\b([^/.]+?)(f\d+)?$});
    my $listname = $1;
    my $group = $2;
    $group = 'local' if ($filepath =~ m/\blocal\b/);
    $group = 'f0' if ! $group;

    (my $branch) = ($filepath =~ m/\b(blacklists|phraselists|authplugins|contentscanners|downloadmanagers)/);
    return 0 if ((! $branch) && (! $listname) && (! $group));	# parse failure, wha??? return failure
    $listname = 'conf' if $listname eq 'dansguardian';
    $listname = $branch if ($branch && (! exists($basefilepermissions{$listname})));
    $listname = 'picsfile' if $listname eq 'pics';
    $listname =~ s/list.*$/list/ if $listname ne $branch;	# truncate filenames only, not directory names

    if (exists $basefilepermissions{$listname}) {
        return 1 if $access{$basefilepermissions{$listname}};
    } else {
        return 1 if ($access{$listname} && $access{$group}); 
    }
    return 0;
}

#################
sub loadeditjslib
#################
{
    print "<script type=text/javascript>\n";
    open JS, "<dgeditlib.js";
    # &copydata seems even simpler BUT it doesn't seem to work right for unknown reasons
    print <JS>;
    close JS;
    print "</script>\n";
    return;
}

###################
sub loadschemejslib
###################
{
    print "<script type=text/javascript>\n";
    open JS, "<dgschemelib.js";
    print <JS>;
    close JS;
    print "</script>\n";
    return;
}

# it seems this is _no_longer_used_ (February 2009),
#  but since the file still exists we leave the routine here too
################
sub loadwebjslib
################
{
    print "<script type=text/javascript>\n";
    open(JS,"dgweblib.js");
    # &copydata seems even simpler BUT it doesn't seem to work right for unknown reasons
    print <JS>;
    close(JS);
    print "</script>\n";
}

######################
sub loadtabintextjslib
######################
{
    print "<script type=text/javascript>\n";
    open JS, "<dgtabintextlib.js";
    print <JS>;
    close JS;
    print "</script>\n";
    return;
}

######################
sub group2conffilepath
######################
{
# if groupnum is unset (or 0 or ''), main config file will be returned
    my ($group) = @_;
    my $groupname = ($group) ? (($group =~ m/^f/) ? $group : "f$group") : '';
    my $conffilepath = &canonicalizefilepath("$config{'conf_dir'}/dansguardian$groupname.conf");

    return $conffilepath;
}

#############################
sub read_file_lines_just_once
#############################
{
# thin wrapper around Webmin function read_file_lines
#  almost all error checking now done here, so Webmin-detected errors will never appear
#  dispenses with Webmin functionality for read-only files, alternate line endings, etc.
#  most importantly, makes the existing array reference available to the caller after a second call

# note dependence on the "static" variable %filesread, which is allocated above
#  (callers MUST not manipulate that variable even though it's in their name space)
    my ($filepath) = @_;
    $filepath = &canonicalizefilepath($filepath);
    $filepath = &canonicalizefilepath($filepath);
    if (exists $filesread{$filepath}) {
        return $filesread{$filepath};
    } else {
        my $fileref = &read_file_lines($filepath);
        $filesread{$filepath} = $fileref;
        return $fileref;
    }
}

##############################
sub flush_file_lines_and_reset
##############################
{
# wrapper around Webmin function flush_file_lines
#  almost all error checking now done here, so Webmin-detected errors will never appear
#  enforces only the one-specific-file-only kind of call
#   (never the all-files-that-have-been-read kind of call)
#  dispenses with Webmin functionality for read-only files, alternate line endings, etc.

    my ($filepath) = @_;
    $filepath = &canonicalizefilepath($filepath);
    $filepath = &canonicalizefilepath($filepath);
    if (exists $filesread{$filepath}) {
        &makebackupcopy($filepath, $debug);
        &flush_file_lines($filepath);
        delete $filesread{$filepath};
    } else {
        print "OOPS! attempt to flush out from memory to disk a file ($filepath) that hasn't been read in\n" if $debug;
    }

    return undef;
}

#################
sub handlerefresh
#################
{
    my ($filepath) = @_;

    $filepath = &group2conffilepath(0) if ! $filepath;
    (my $filename = $filepath) =~ s{^.*/}{};
    if ((($filepath =~ m/\b(?:authplugins|contentscanners|downloadmanagers)/) && ($filepath !~ m/\blists/)) || (($filename eq 'dansguardian.conf') || ($filename eq 'bannediplist') || ($filename eq 'exceptioniplist'))) {
        # we need to handle a major reset
        if (&dgisrunning()) {
            # if DG is running, issue messages (if not, nothing to do)

            # perform auto-actions and/or tell the user what we've done
            if ($access{'restart'}) {
                if ($access{'autorestart'} && $config{'autorestart'}) {
                    print "<p><span style='color: darkmagenta'>$text{'restart_change'} $text{'restart_title'}</span><p>\n";
                    &dgprocess('restart');
                    &checkdgisrunning();
                } else {
                    print "<p><span style='color: magenta'><b>$text{'error_note'}</b> $text{'restart_forget'}</span></p>\n";
                }
            } else {
                print "<p><span style='color: magenta'><b>$text{'error_note'}</b> $text{'restart_needed'}</span></p>\n";
            }
        }  
    } else {
        # we only need to handle a minor reload
        if (&dgisrunning()) {
            # if DG is running, issue messages (if not, nothing to do)

            # perform auto-actions and/or tell the user what we've done
            if ($access{'reload'}) {
                if ($access{'autoreload'} && $config{'autoreload'}) {
                    print "<p><span style='color: darkmagenta'>$text{'reload_change'} $text{'reload_title'}</span><p>\n";
                    &dgprocess('reload');
                    &checkdgisrunning();
                } else {
                    print "<p><span style='color: magenta'><b>$text{'error_note'}</b> $text{'reload_forget'}</span></p>\n";
                }
            } else {
                print "<p><span style='color: magenta'><b>$text{'error_note'}</b> $text{'reload_needed'}</span></p>\n";
            }
        }  
    }
}

################
sub getgroupname
################
{
    my ($group) = @_;
    $group = &canonicalizegroupnumber($group);

    my $answer = '';

    $answer = &readconfigoptionlimited('groupname', $group);
    $answer = "$text{'index_group'} f$group" if ! $answer;

    return $answer;
}

#################
sub getgrouptitle
#################
{
    my ($group) = @_;
    $group = &canonicalizegroupnumber($group);

    my $groupid = "f$group";

    my $answer = &getgroupname($group);

    $answer .= " ($groupid)" if $answer !~ m/\b$groupid\b/;

    return $answer;
}

###################
sub getgroupheading
###################
{
    my ($group, $extension) = @_;
    $group = &canonicalizegroupnumber($group);

    my $groupname = &getgroupname($group);
    my $groupmode = &readconfigoptionlimited('groupmode', $group);

    my $extensiontextname = "edit_heading_$extension";

    my $label = ($text{'conf_groupmode_radio_1'}, $text{$extensiontextname}, $text{'conf_groupmode_radio_3'})[$groupmode];

    my $answer = "$groupname $label";

    return $answer;
}

#########################
sub getgrouplists_hashref
#########################
{
    my ($group) = @_;
    $group = &canonicalizegroupnumber($group);

    my $groupmode = &readconfigoptionlimited('groupmode', $group);

    my $answer_ref = ( { }, \%groupsconfigurationlists, { } ) [$groupmode];

    return $answer_ref; 
}

################
sub getgroupmode
################
{
    my ($group) = @_;
    $group = &canonicalizegroupnumber($group);

    my $answer = &readconfigoptionlimited('groupmode', $group);

    return $answer;
}

##########
sub bytype
##########
{
# this is a kind of sort, do not use it for anything else
# if you "call" it normally, it will probably fail, 
# like any other "sort" extension it "magically" gets $a an $b as arguments
    my $discriminator = qr/^(?:banned|exception|grey|log|weighted|content|url|header)?(.*)$/;
    my $asupertype = (($a =~ m/list$/) || ($a =~ m/^pics/)) ? 'list' : 'any';
    my $bsupertype = (($b =~ m/list$/) || ($b =~ m/^pics/)) ? 'list' : 'any';
    my ($atype) = ($a =~ $discriminator);
    $atype = "yyy$atype" if $atype =~ m/^(?:extension|mimetype)/;
    $atype = 'zzz' if $atype =~ m/^(?:file)/;
    my ($btype) = ($b =~ $discriminator);
    $btype = "yyy$btype" if $btype =~ m/^(?:extension|mimetype)/;
    $btype = 'zzz' if $btype =~ m/^(?:file)/;
    my $result = "$asupertype $atype $a" cmp "$bsupertype $btype $b";
    return $result;
}

##################
sub partialnumeric
##################
{
# this is a kind of sort, do not use it for anything else
# if you "call" it normally, it will probably fail, 
# like any other "sort" extension it "magically" gets $a an $b as arguments

# ' ' used because it's the lowest-sorting alpha character
    my $aprime = " ${a} 0 ";	# "extend" so RE parse will _always_ work
    my ($atext1, $anum, $atext2) = ($aprime =~ m/^(\D+)(\d+)(.*)$/);
    my $bprime = " ${b} 0 ";	# "extend" so RE parse will _always_ work
    my ($btext1, $bnum, $btext2) = ($bprime =~ m/^(\D+)(\d+)(.*)$/);
    my $result = $atext1 cmp $btext1;
    if (!$result) {
        $result = $anum <=> $bnum;
        if (!$result) {
            $result = $atext1 cmp $atext2;
        }
    }

    return $result;
}

##############
sub ignorecase
##############
{
# this is a kind of sort, do not use it for anything else
# if you "call" it normally, it will probably fail, 
# line any other "sort" extension it "magically" gets $a an $b as arguments
	return ((lc $a) cmp (lc $b));
}

#################
sub existsinarray
#################
{
    my ($needle, $ignorecaseflag, @haystack) = @_;
    my $caseflag = $ignorecaseflag ? '(?i:' : '(?:';
    for my $hay (@haystack) {
        return 1 if $needle =~ m/$caseflag$hay)/;
    }
    return 0;
}

########################
sub canonicalizefilepath
########################
{
    my ($filepath) = @_;
    return '' if !$filepath;

    $filepath =~ s/^\s*(['"])([^\1]*)\1\s*$/$2/;	# strip regular quotes
    $filepath =~ s/^\s*<[^>]*>\s*$/$1/;		# strip filepath quotes

    $filepath =~ s{^\./+}{};	# strip off any leading relative junk
    $filepath =~ s{/+$}{};	# strip off any trailing slashes

    $filepath =~ s{/\.?/}{/}g;	# compress out any irrelevant double slashes or "current directory"
    $filepath =~ s{/\.?/}{/}g;	# do it again, just to be absolutely sure (paranoid, but...)

    return $filepath;
}

###########################
sub canonicalizegroupnumber
###########################
{
    my ($group) = @_;

    return 0 if !$group;		# any completely missing value becomes 0
    return 0 if ($group =~ m/-\d/);	# any negative number becomes 0
    return 0 if ($group =~ m/^\D*$/);	# any missing/meaningless string becomes 0

    my ($result) = ($group =~ m/(\d+)/);	# extract the number
    $result = 0 if ! $result;			# explicit 0 rather than undefined or '' or ...
    return $result;
}

#########################
sub passthroughautoreturn
#########################
{
# if we're just being returned to, pass it through to our parent and get out of the way
     my $invoke = $in{'invoke'};
    if ($invoke =~ m/autoreturn/) {
        redirect('index.cgi');
        exit;
    }
}

#########################
sub bailifcallercancelled
#########################
{
    my $return = $in{'return'};
    my $invoke = $in{'invoke'};
    my $button = $in{'button'};

    my ($label1, undef) = split ' ', $text{'button_cancelchange'};
    my ($label2, undef) = split ' ', $text{'button_ok'};
    if (($button =~ m/^(:?$label1|$label2)/i) or ($invoke  =~ 'cancel')) {
	my $rawreturn = &un_urlize($return);
        $rawreturn =~ s/(invoke|button|autoreturn|autocancel)=[^\b]*(?:&)?//g;
	$rawreturn .= ($rawreturn =~ m/\?/) ? '&' : '?';
	$rawreturn .= 'invoke=cancelreturn';
	&redirect($rawreturn);
	exit;
    }
}

#################
sub showackandret
#################
{
    my $return = $in{'return'};
    $return = 'index.cgi' if ! $return;
    my $rawreturn = &un_urlize($return);
    my ($pathstring, $querystring) = split /\?/, $rawreturn, 2;
    print "<form action='$pathstring' method=GET>\n";
    my @pairs = split /&/, $querystring;
    my %uniquepairs = ();
    foreach my $pair (@pairs) {
        my ($queryname, $queryvalue) = split '=', $pair;
        next if $queryname =~ m/\b(?:invoke|button|auto)/;	# ignore some name=value pairs
        $uniquepairs{$queryname} = $queryvalue;
    }
    $uniquepairs{'invoke'} = 'return';	# add (even override) a name=value pair noting what we've done
    foreach my $querykey (keys %uniquepairs) {
        print "<input type=hidden name='$querykey' value='$uniquepairs{$querykey}'>\n";
    }
    print "<br><br><img src=image/transparent1x1.gif height=1 width=40 border=0>\n";
    print "<input type=submit name=button value='$text{'button_ok'}'>\n";
    print "\n";
}

##################
sub getcleanreturn
##################
{
    my $return = ($ENV{'REQUEST_URI'});
    # generally net effect is to strip away ALL the query part
    #  (in fact we're not even sure it works right if some remain)
    $return =~ s/&?invoke=[^&]*//g;
    $return =~ s/&?initialtab=[^&]*//g;
    $return =~ s/&?button=[^&]*//g;
    $return =~ s/&?auto[^=]*=[^&]*//g;

    $return =~ s/\?[?&]*$//;
    $return = &urlize($return);

    return $return;
}

print DEBUGLOG "finished including dansguardian-lib.pl\n" if $debug;

require 'dansguardian-edit-lib.pl';	# separate file to keep this from being so large

1;
