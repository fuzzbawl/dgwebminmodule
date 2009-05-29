#!/usr/bin/perl

# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
require './dansguardian-lib.pl';
use warnings;
use strict qw(subs vars);
our $search=$in{'search'};
our $interpret=$in{'interpret'};

&webminheader();

# if there's nothing, bail immediately
if (! $search) {
    print "<p><span style='color:red'>$text{'search_none'}</span><br><br>\n";
    &showackandret();
    &webminfooterandexit();
}

# set up some useful globals
our $confdir = &canonicalizefilepath($config{'conf_dir'});
our $listdir = "$confdir/lists";
our $conffilepath = &group2conffilepath(0);

our $filtergroups = &readconfigoptionlimited('filtergroups', 0);
our @groupnames = ( 'error' );
our @groupmodes = ( 'error' );
our %conffilepath2group = ();

for (my $i=1; $i<=$filtergroups; ++$i) {
    $groupnames[$i] = &getgroupname($i);
    $groupmodes[$i] = &getgroupmode($i);
    our $fgconffilepath = &group2conffilepath($i);
    $conffilepath2group{$fgconffilepath} = $i;
}

our $includesearchfiles = "$confdir/dan*.conf $listdir/*list* $listdir/pics* $listdir/f*/*list* $listdir/f*/pics*";
our $explodedincludesearchfiles = &explodefilepaths($includesearchfiles);

# display warning messages, both dynamic and fixed
print "<p><span style='color: brown'>$text{'error_nopath'}</span><p>\n";

# start processing input
if ($interpret eq 'detect') {
    if ($search =~ m/[][()+*\\]/) {
        $interpret = 'regexp';
        # note 'modify' will never be detected, it will always be masked by 'regexp'
    } elsif ($search =~ m{/}) {
        $interpret = 'url'; 
    } elsif ($search =~ m/\./) {
        $interpret = 'domain';
    } elsif (($search =~ m/['"]/) || ($search =~ m/\s\s/) || ($search =~ m/\S\s+\S.*\s+\S.*\s+/g)) {
        $interpret = 'phrase';
    } else {
        $interpret = 'permute';
    }
}

# strip quotes if any
$search =~ s/^\s*(['"])([^\1]*)\1\s*$/$2/;

# if there's nothing left, bail
if (! $search) {
    print "<p><span style='color:red'>$text{'search_none'}</span><br><br>\n";
    &showackandret();
    &webminfooterandexit();
}

our ($searchfiles);
if ($interpret eq 'url') {
    $searchfiles = "$listdir/bannedurllist* $listdir/greyurllist* $listdir/exceptionurllist* $listdir/logurllist* $listdir/{f*,local}/bannedurllist* $listdir/{f*,local}/greyurllist* $listdir/{f*,local}/exceptionurllist* $listdir/{f*,local}/logurllist* $listdir/blacklists*/*/urls";
} elsif ($interpret eq 'domain') {
    $searchfiles = "$listdir/bannedsitelist* $listdir/greysitelist* $listdir/exceptionsitelist* $listdir/logsitelist* $listdir/{f*,local}/bannedsitelist* $listdir/{f*,local}/greysitelist* $listdir/{f*,local}/exceptionsitelist* $listdir/{f*,local}/logsitelist* $listdir/blacklists*/*/domains";
} elsif ($interpret eq 'regexp') {
    $searchfiles = "$listdir/bannedregexpurllist* $listdir/exceptionregexpurllist* $listdir/logregexpurllist* $listdir/{f*,local}/bannedregexpurllist* $listdir/{f*,local}/exceptionregexpurllist* $listdir/{f*,local}/logregexpurllist* $listdir/blacklists*/*/expressions";
} elsif ($interpret eq 'modify') {
    $searchfiles = "$listdir/urlregexplist* $listdir/contentregexplist* $listdir/headerregexplist* $listdir/{f*,local}/urlregexplist* $listdir/{f*,local}/contentregexplist* $listdir/{f*,local}/headerregexplist*";
} elsif ($interpret eq 'permute') {
    $searchfiles = "$listdir/weightedphraselist* $listdir/bannedphraselist* $listdir/exceptionphraselist* $listdir/{f*,local}/weightedphraselist* $listdir/{f*,local}/bannedphraselist* $listdir/{f*,local}/exceptionphraselist* $listdir/phraselists/*/*";
} elsif ($interpret eq 'phrase') {
    $searchfiles = "$listdir/weightedphraselist* $listdir/bannedphraselist* $listdir/exceptionphraselist* $listdir/{f*,local}/weightedphraselist* $listdir/{f*,local}/bannedphraselist* $listdir/{f*,local}/exceptionphraselist* $listdir/phraselists/*/*";
} else {
    print "<br>OOPS! unknown interpret $interpret<br>\n" if $debug;
}

our $explodedsearchfiles = &explodefilepaths($searchfiles);

our (@searchwords, $numberofwords);
if ($interpret eq 'permute') {
    @searchwords = split ' ', $search;
    $numberofwords = $#searchwords + 1;
    print "<p><span style='color: brown'>$text{'search_toomany'}</span><br><br>\n" if $numberofwords > 3;
    splice(@searchwords, 3);	# throw away all but first 3 words
    $searchwords[0] = quotemeta $searchwords[0];
    $searchwords[1] = quotemeta $searchwords[1];
    $searchwords[2] = quotemeta $searchwords[2];
    if ($numberofwords == 1) {
        $search = $searchwords[0];
    } elsif ($numberofwords == 2) {
        $searchwords[0] = quotemeta $searchwords[0];
        $searchwords[1] = quotemeta $searchwords[1];
        $search = "$searchwords[0].*$searchwords[1]|$searchwords[1].*$searchwords[0]";
    } else {
        $search = "$searchwords[0].*$searchwords[1].*$searchwords[2]|$searchwords[0].*$searchwords[2].*$searchwords[1]|$searchwords[1].*$searchwords[0].*$searchwords[2]|$searchwords[1].*$searchwords[2].*$searchwords[0]|$searchwords[2].*$searchwords[0].*$searchwords[1]|$searchwords[2].*$searchwords[1].*$searchwords[0]";
    }
} else {
$search = quotemeta $search;
}

# Run search command and collect output
our $cmd = "grep -EiH '$search' $explodedsearchfiles";
our $temp = &tempname();
&system_logged("$cmd >$temp 2>&1 </dev/null");
our $outlinesref = &read_file_lines_just_once($temp);
our $findcount = scalar @$outlinesref;
unlink($temp);
&reset_environment();

# Display heading saying what we did and how many we found
our $interprettext = $text{"search_$interpret"};
print "<u>$text{'button_search'}  for</u> '$search` <u>as</u> $interprettext <u>in $text{'edit_heading_lists'}:</u> $searchfiles<br><br>\n";
if ($findcount) {
   print "<p align=center>$text{'search_found'}: $findcount<p>\n";
} else {
   print "<p align=center>$text{'search_notfound'}<p>\n";
}

# Display detailed results of command
our $firsttime = 1;	# implement a "half" loop
our $previousfile = '';
our @founditems = ();
print "<table border=0 cellpadding=0 cellspacing=0>\n";
foreach my $line (@$outlinesref, '') {
    my ($file, $value) = split(/\s*:\s*/, $line, 2);
    if ($file ne $previousfile) {
        if (! $firsttime) {
            print "<tr><td><img src=images/transparent1x1.gif width=32 height=1></td><td align=left valign=top width=200><i><u>$text{'search_heading_filtergroup'}</u>:</i><br>";
            &showfiltergroupsstatus($previousfile);
            print "</td><td><img src=images/transparent1x1.gif width=75 height=1></td><td align=left valign=top><i><u>$text{'search_heading_match'}</u>:</i><br>";
            print join '<br>', @founditems;
            print "</td></tr>\n";
            @founditems = ();
        }
        print "<tr><td align=left colspan=4><br><i><u>$text{'search_heading_file'}</u>:</i> $file</td></tr>\n" if $file;
        $firsttime = 0;
        $previousfile = $file;
    }
    push @founditems, &html_escape($value);
}
print "</table>\n";

&showackandret();

&webminfooterandexit();

###########################################################################
#
#    LARGE BLOCKS OF FUNCTIONALITY ENCAPSULATED AS SUBROUTINES
#
#    Note some of these rely greatly on accessing shared variables
#    from a common namespace. They are "subroutines" to reduce
#    the sheer size a block of code and to avoid over-indenting.
#    They do NOT do a good job of isolating all their arguments
#    like traditional subroutines usually do, using "my" for 
#    everything and limiting themselves to using only the variables 
#    passed in as arguments.
#
###########################################################################

##########################
sub showfiltergroupsstatus
##########################
{
    my ($filepath) = @_;

    my ($filtergroupsflag, $filtergroupsformat);
    my %grouphits = ();
    &getgroupincludehits($filepath, \%grouphits);

    for (my $i=1; $i<=$filtergroups; ++$i) {
        if ($groupmodes[$i] == 1) {
            if ($grouphits{$i} > 0) {
                $filtergroupsflag = '&radic;';
                $filtergroupsformat = '';
            } else {
                $filtergroupsflag = '&not;';
                $filtergroupsformat = "style='color: #777'";
            }
        } else {
            $filtergroupsflag = '&ensp;';
            $filtergroupsformat = "style='color: #AAA'";
        }

        print "$filtergroupsflag&nbsp;<span $filtergroupsformat>$groupnames[$i]&nbsp;(f$i)</span><br>"; 
    }
}

#######################
sub getgroupincludehits
#######################
{
    # outermost level produces a hash of which groups are "enabled" via include
    my ($filepath, $grouphitshashref) = @_;

    my @hitconfs = &trackback(1, $filepath);

    foreach my $hitconf (@hitconfs) {
        my $group = $conffilepath2group{$hitconf};
        $$grouphitshashref{$group} += 1;
    }
}

#############
sub trackback
#############
{
    # middle level, called by getgroupincludehits to do the work
    # this level uses a lot of RECURSION
    # (there is protection though against getting caught in a recursion loop)
    my ($level, @filepaths) = @_;

    return undef if $#filepaths < 0;	# stop recursion at full depth (nothing more to do)
    return undef if $level > ($debug ? 10 : 100);	# protection against recursion loop

    my @oneback = ();

    my $newlevel = $level + 1;

    foreach my $filepath (@filepaths) {
        if (($filepath =~ m/^\s*$/) || (! $filepath)) {
            push @oneback, undef;
        } elsif ($filepath =~ m/conf$/) {
            push @oneback, $filepath;
        } else {
            push @oneback, &trackback($newlevel, &backuponelevel($filepath));
        }
    }

    return (@oneback);
}

##################
sub backuponelevel
##################
{
    # lowest level, does one bit of work for caller who's in charge
    my ($filepath) = @_;

    my ($line, $file, $value, $outlinesref);

    # strip quotes and remove other junk
    $filepath = &canonicalizefilepath($filepath);

    return () if ! $filepath;

    my @results = ();

    # run search command and collect output
    my $cmd = "grep -FiH '$filepath' $explodedincludesearchfiles";
    my $temp = &tempname();
    &system_logged("$cmd >$temp 2>&1 </dev/null");
    my $outlinesref = &read_file_lines_just_once($temp);
    my $findcount = scalar @$outlinesref;
    unlink($temp);
    &reset_environment();

    foreach my $line (@$outlinesref) {
        # we didn't skip over comment lines above because a straight search is faster
        #  so now we have to throw out any that snuck in
        next if $line =~ m/^\s*(?:^[^:]*:\s*#|$)/;
        ($file, $value) = split(/\s*:\s*/, $line, 2);
        # we can get extra hits because of a partial name match
        #  we didn't skip when searching for performance, so we re-check and skip now
        next if $value !~ m/$filepath\b/;
        $file = &canonicalizefilepath($file);
	# try to avoid loops if file refers to itself
        next if &significantconfigfilepath($file) eq &significantconfigfilepath($filepath);
        if (($file =~ m/dansguardian.conf$/) && &sharedoptionsavailable) {
            # special condition, we need to handle it
            my ($name, $datum) = split /\s*=\s*/, $value, 2;
            $name =~ s/^\s+//;
            for (my $fg=1; $fg<=$filtergroups; ++$fg) {
                my $anything = &readconfigoptionlimited($name, $fg);
                # if not masked by locally set value, report groupconfname
                push @results, &group2conffilepath($fg) if ! $anything;
            }
        } else {
            # normal condition
            push @results, $file;
        }
    }

    return @results;
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
    &ui_print_header($text{'search_title'}, $text{'index_title'}, undef, 'search', 1, 0, 0, &restart_button.'<br>'.&help_search_link("dansguardian", "man"), undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    &ui_print_footer('searchinput.cgi', $text{'search_return'}, 'index.cgi', $text{'index_return'});

    exit;
}

