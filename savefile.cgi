#!/usr/bin/perl
# savefile.cgi


# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
our (%mainconfigurationlists, %groupsconfigurationlists);
our (%sharedgroupsconfigurationlists, %notsharedgroupsconfigurationlists);
our (%sharedonlynestedconfigurationlists, %sharedonlyseparateconfigurationlists, %sharedonlycommonconfigurationlists);
our ($EFFECTIVE_USER_ID);
require './dansguardian-lib.pl';
use POSIX;
use warnings;
use strict qw(subs vars);
our $filepath = $in{'filepath'};


&bailifcallercancelled();


&webminheader();

# error checks
if (! &accessfile($filepath)) {
    print "<p><span style='color: magenta'>$text{'error_notauthfile'}<br>$text{'index_location'}: $filepath</span><p>\n";
    &showackandret();
    &webminfooterandexit();
}

# Check to see if the file we are editing is in the DG config dir
if (!(&is_under_directory($config{'conf_path'}, $filepath))) {
  print "$text{'error_filenotindir'}";
}

&finish_manually_editing_file(\%in, 'showmessages');

&touchwholechain($filepath);

&handlerefresh($filepath);

&showackandret();

&webminfooterandexit();

{
# "shared"/"global" variables for all the following subroutines - yucky/ugly, but...
our $confdir;
our $listdir;
our $includesearchfiles;
our $explodedincludesearchfiles;
our %upperfilepaths = ();
our $filtergroups = 0;

###########################################################################
#
#    Largeish subroutines for tracking and touching a whole .Include chain
#
#    These subroutines all work together. Rather than totally isolating
#    their varible namespace with "my", they rely on a bunch of "shared"
#    global varilables as above.
#
###########################################################################

###################
sub touchwholechain
###################
{
    my ($changedfilepath) = @_;

    return if $changedfilepath !~ m/phrase/;

    # record information about date changed from file we changed
    #  (get latest time even if this was a symlink of some sort)
    my (undef, undef, undef, undef, undef, undef, undef, undef, $atime, $mtime,undef, undef, undef) = stat($changedfilepath);
    $changedfilepath = readlink $changedfilepath if -l $changedfilepath;	# get real file
    my (undef, undef, undef, undef, undef, undef, undef, undef, $atime2, $mtime2,undef, undef, undef) = stat($changedfilepath);
    $atime = $atime2 if $atime2 > $atime;
    $mtime = $mtime2 if $mtime2 > $mtime;

    $filtergroups = &readconfigoptionlimited('filtergroups');

    (my $changedfilename = $changedfilepath) =~ s{^.*/}{};
    (my $basechangedfilename) = ($changedfilename =~ m/^(.*list).*$/);

    $confdir = &canonicalizefilepath($config{'conf_dir'});
    $listdir = "$confdir/lists";
    # following could probably use "$basechangedfilename*" rather than "*phrase*"
    # this searches a lot more files than really necessary, but doing so may be prudent
    $includesearchfiles = "$listdir/*phrase*";
    for (my $i=1; $i<=$filtergroups; ++$i) {
        $includesearchfiles .= " $listdir/f$i/*phrase*";
    }
    $explodedincludesearchfiles = &explodefilepaths($includesearchfiles, 'dontremovesymdests');

    # see if we can find any other names for (i.e. symlinks that point at) this file
    our @changedfilepaths = ($changedfilepath);
    our @suspectfilepaths = split ' ', $explodedincludesearchfiles;
    for my $suspectfilepath (@suspectfilepaths) { 
        push(@changedfilepaths, $suspectfilepath) if (&significantconfigfilepath(readlink $suspectfilepath)) eq &significantconfigfilepath($changedfilepath);
    }

    for $changedfilepath (@changedfilepaths) {
        # back up as necessary, result is filled in %upperfilepaths
        &trackchainback(1, $changedfilepath);

        # repeat the information into all files higher in the chain
        foreach my $upperfilepath (keys %upperfilepaths) {
            next if ! $upperfilepath;	# skip over empty entries
	# skip over ourselves if we're in the list
            next if &significantconfigfilepath($upperfilepath) eq &significantconfigfilepath($changedfilepath);
            utime $atime, $mtime, $upperfilepath;
        }
    }
}
    
##################
sub trackchainback
##################
{
    # this level uses a lot of RECURSION
    my ($level, @filepaths) = @_;

    return undef if $#filepaths < 0;	# stop recursion at full depth (nothing more to do)
    return undef if $level > ($debug ? 10 : 100);	# protection against recursion loop

    my @oneback = @filepaths;

    my $newlevel = $level + 1;

    foreach my $filepath (@filepaths) {
        if (($filepath =~ m/^\s*$/) || (! $filepath)) {
	    # empty search, not sure how we got here, but just ignore it and go on
            next;
        } elsif ($filepath =~ m/conf$/) {
            # search produced an irrelevant file, not sure how we got here, but just ignore it and go on
            next;
        } else {
            push @oneback, &trackchainback($newlevel, &backuponelevel($filepath));
        }
    }

    foreach my $filepath (@oneback) {
        next if ! $filepath;
        # canonicalize everything, (this is probably over-cautious)
        #  be absolutely certain  typos in files can't pollute what we're doing
        $filepath = &canonicalizefilepath($filepath);
        # this has the (desirable) side effect of listing each file only once
        # the count is only interesting for debugging, it's not actually used for anything
        $upperfilepaths{$filepath} += 1;
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

    foreach my $line (@$outlinesref) {
        # we didn't skip over comment lines above because a straight search is faster
        #  so now we have to throw out any that snuck in
        next if $line =~ m/^\s*(?:^[^:]*:\s*#|$)/;
        ($file, $value) = split(/\s*:\s*/, $line, 2);
        # we can get extra hits because of a partial name match
        #  we didn't skip when searching for performance, so we re-check and skip now
        # we omit &canonicalizefilepath for performance on the assumption that grep NEVER produces funky results
        next if $value !~ m/$filepath\b/;
        $file = &canonicalizefilepath($file);
	# try to avoid loops if file refers to itself
        next if &significantconfigfilepath($file) eq &significantconfigfilepath($filepath);
        # normal condition
        push @results, $file;
    }

    return @results;
}

}	# end block that contains "global" vars


###########################################################################
#
#    UTILITY SUBROUTINES
#
###########################################################################

################
sub webminheader
################
{
    &ui_print_header($text{'savefile_title'}, $text{'index_title'}, undef, undef, 0, 1, 1, &restart_button, undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
}

#######################
sub webminfooterandexit
#######################
{
    if (exists $in{'return'}) {
        # we have a specific return, issue a message then don't display any manual returns
        &ui_print_footer();	# entirely omit/suppress the return arrow
    } else {
        # no particular return specified, so supply user with lots of manual choices
        &ui_print_footer('index.cgi', $text{'index_return'}, 'editplugconf.cgi', "$text{'index_viewedit'} $text{'index_editplugconf'}", 'editlists.cgi', "$text{'index_viewedit'} $text{'index_editlists'}", 'editgroupslists.cgi', "$text{'index_viewedit'} $text{'index_editgroupslists'}" );
    }

    exit;
}

