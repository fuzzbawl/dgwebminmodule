#!/usr/bin/perl -w
# dansguardian-edit-lib.pl


use warnings;

print DEBUGLOG "at very top of dansguardian-edit-lib.pl\n" if $debug;

############################################################################################
#
# shared utilities for editing configurations and/or files
#
#  (these are in a separate file rather than mainline dansguardian-lib.pl
#   so a] they're not parsed unless the calling .cgi really needs them,
#   and b] this keep dansguardian-lib.pl from getting quite so big)
#
############################################################################################

my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime;
$mon += 1;
$wday += 1;
$year += 1900;
# this sets up two GLOBALS that can be used by other subroutines and/or by the caller
our $marker = sprintf "%d.%d.%d-%02d:%02d", $year, $mon, $mday, $hour, $min;
our $filemarker = sprintf "%04d%02d%02d%02d%02d%02d", $year, $mon, $mday, $hour, $min, $sec;


############################################################################################
#
# subroutines for editing configurations and/or files
#
############################################################################################

{
# simulate "static" variable
our $fileeditingjsloaded = 0;

###############################
sub start_manually_editing_file
###############################
{
    my ($filepath) = @_;
    $filepath = &canonicalizefilepath($filepath);

    if (!$fileeditingjsloaded) {
	&loadtabintextjslib();
	$fileeditingjsloaded = 1;
    }
    my $fileref = &read_file_lines_just_once($filepath);
    print "<input type=hidden name=filepath value='$filepath'>\n";
    print "<textarea name='filecontents' id='id" . int(rand * 10000) . "' onKeydown='interceptTab(this, event)' rows=30 cols=80>";
    # although using &join might be more "Perlish", this way uses less memory by not needing an extra copy
    foreach my $line (@$fileref) {
        print &html_escape($line)."\n";
    }
    print "</textarea>";
    return $fileref;
}

################################
sub finish_manually_editing_file
################################
{
    my ($hashref, $showmessages) = @_;
    my $filepath = &canonicalizefilepath($$hashref{'filepath'});
    &makebackupcopy($filepath, $showmessages);
    my $fileref = &read_file_lines_just_once($filepath);
    # entirely replace the lines Webmin has with the new ones that were passed in
    @$fileref = split /[ \t\r]*\n\r*/s, $$hashref{'filecontents'};	# don't use \s*, it eats up blank lines
    &flush_file_lines_and_reset($filepath);
    # tell user what we've done
    print "<p>$text{'editfile_storefile'}: $filepath<br>\n" if $showmessages;

    return $filepath;
}

}

##############
sub createfile
##############
{
    my ($filename) = @_;

    # only act on truly new files, 
    #  if file already exists (or is undefined) 
    #  just do nothing at all and silently return
    return if !$filename;
    return if -e $filename;

    # (there must be a better way, perhaps via Webmin, perhaps via Perl)
    open NEWFILE, ">$filename";
    print NEWFILE "\n";
    close NEWFILE;
}

############
sub makecopy
############
{
    my ($oldfilepath, $newfilepath, $showmessages) = @_;

    if (! -e $oldfilepath) {
        print "<P>$text{'error_filenotfound'}: $oldfilepath<br>\n" if $showmessages;
        return 0;
    }
    if ($oldfilepath eq $newfilepath) {
        print "<P>$text{'error_samefile'}: $oldfilepath=$newfilepath<br>\n" if $showmessages;
        return 0;
    }

    open OLDFILE,"<$oldfilepath" or return 0;
    open NEWFILE,">$newfilepath" or return 0;
    print NEWFILE <OLDFILE>;
    close NEWFILE;
    close OLDFILE;
    print "<p>$text{'editfile_copyfile'}: $oldfilepath->$newfilepath<br>\n" if $showmessages;

    return 1;
}

##################
sub makebackupcopy
##################
{
    my ($conffilepath, $showmessages) = @_;
    $conffilepath = readlink $conffilepath if -l $conffilepath;

    my $backupfilepath = "$conffilepath.$filemarker";

    # if we're called more than once, bail except for the first time - never overwrite a previous backup
    return if -e $backupfilepath;

    open CURRENT,"<$conffilepath" or return 0;
    open BACKUP,">$backupfilepath" or return 0;
    print BACKUP <CURRENT>;
    close CURRENT;
    close BACKUP;
    print "<p>$text{'editfile_backupcopyfile'}: $backupfilepath<br>\n" if $showmessages;

    return 1;
}

##################
sub renametobackup
##################
{
    my ($conffilepath, $showmessages) = @_;

    my $backupfilepath = "$conffilepath.$filemarker";

    rename $conffilepath, $backupfilepath;
    print "<p>$text{'editfile_backuprenamefile'}: $backupfilepath<br>\n" if $showmessages;

    return 1;
}

##############
sub revertfile
##############
{
    my ($revertfilepath, $showmessages) = @_;
    my ($basefilepath) = ($revertfilepath =~ m/^(.*)\.20\d+$/);

    if ((! $revertfilepath) || (! $basefilepath) || (! -e $revertfilepath)) {
        print "OOPS! - selected version for revision (revertfilepath=$revertfilepath, basefilepath=$basefilepath) does not seem to exist!\n" if $debug;
    }

    $revertfilepath = &canonicalizefilepath($revertfilepath);
    $basefilepath = &canonicalizefilepath($basefilepath);

    &makebackupcopy($basefilepath, $showmessages);
    my $fileref = &read_file_lines_just_once($basefilepath);
    # replace all lines with contents of reversion
    @$fileref = ();
    open REVERSION,"<$revertfilepath";
    while (<REVERSION>) {
        chomp ;
        push @$fileref, $_;
    }
    close REVERSION;
    &flush_file_lines_and_reset($basefilepath);

    print "<p>$text{'editfile_revertfile'}: $basefilepath<br>($text{'editfile_usedreversion'}: $revertfilepath)<br>\n" if $showmessages;
    return 1;
}

####################
sub explodefilepaths
####################
{
    my ($filepaths, $dontremovesymdests) = @_;
    # $dontremovesymdests:
    # 0 (default) remove DESTINATION, retain source (the symlink itself)
    #  (works right for many cases, especially search, although perhaps a bit counter-intuitive)
    # !0 do not remove anything

    my ($explodeditem, @explodeditems, $explodedfilepath, @explodedfilepaths);
    my ($symlinkdestination, @symlinkdestinations, $finalfilepaths, @finalfilepaths);
 
    foreach my $item (split ' ', $filepaths) {
        @explodeditems = glob $item;
        foreach $explodeditem (@explodeditems) {
            next if -d $explodeditem;	# skip over things that are directories rather than files
            next if $explodeditem =~ m/20\d\d/;
            next if $explodeditem =~ m/processed/;
            next if $explodeditem =~ m/SAV/;
            next if $explodeditem =~ m/save/;
            next if $explodeditem =~ m/previous/;
            push @explodedfilepaths, $explodeditem;
        }
    }

    if ($dontremovesymdests) {
        # don't remove anything
        @finalfilepaths = @explodedfilepaths;
    } else {
        # build up a list of symlink destinations
        for $explodedfilepath (@explodedfilepaths) {
            next if ! -l $explodedfilepath;
            $symlinkdestination = readlink $explodedfilepath;
            $symlinkdestinations{$symlinkdestination}++;
        }

        # remove the DESTINATIONS, leaving the symlinks
        for $explodedfilepath (@explodedfilepaths) {
            next if exists $symlinkdestinations{$explodedfilepath};
            push @finalfilepaths, $explodedfilepath;
        }
    }

    $finalfilepaths = join ' ', @finalfilepaths;

    return $finalfilepaths;
}
  
########################
sub update_list_filepath
########################
{
# pretty much just a wrapper - functionality pretty much the same as &update_list_lines,
#  but calling args specify a filepath rather than passing an array of lines
#  and this automatically makes a backup copy of the file

# usually calling sequence will be three args ($filepath, \@activatelines, \@deactivatelines)
# once in a while an optional fourth argument will be used as well
#  it allows deactivation of lines with only a _partial_ match, which is quite dangerous
    my ($filepath, $activatelinesref, $deactivatelinesref, $deactivatepartiallinesref) = @_;
    $filepath = &canonicalizefilepath($filepath);

    &makebackupcopy($filepath);
    my $linesarrayref = &read_file_lines_just_once($filepath);
    &update_list_lines($linesarrayref, $activatelinesref, $deactivatelinesref, $deactivatepartiallinesref);
    &flush_file_lines_and_reset($filepath);
}

#####################
sub update_list_lines
#####################
{
# usually calling sequence will be three args (\@filelines, \@activatelines, \@deactivatelines)
# once in a while an optional fourth argument will be used as well
#  it allows deactivation of lines with only a _partial_ match, which is quite dangerous
    my ($linesarrayref, $activatelinesref, $deactivatelinesref, $deactivatepartiallinesref) = @_;

    my ($item, $value, $done);

    # each of these skips over any lines that appear to be nothing more than full comment lines

    foreach $item (@$activatelinesref) {
        ($value = $item) =~ s/^[\s#]*(\S.*\S)\s*(?:#.*)?$/$1/;
        $done = grep {(! m/^\s*#[\s#]*[^#]*$/) && s/^[\s#]*($value)\s*(?:#\s*(.*\S))?\s*$/$1\t# $marker $2/} @$linesarrayref;
        push(@$linesarrayref, "$value\t# $marker") if ! $done;	# line not found, must add it at end
    }

    foreach $item (@$deactivatelinesref) {
        ($value = $item) =~ s/^[\s#]*(\S.*\S)\s*(?:#.*)?$/$1/;
        grep {(! m/^\s*#[\s#]*[^#]*$/) && s/^[\s#]*($value)\s*(?:#\s*(.*\S))?\s*$/# $1\t# $marker $2/} @$linesarrayref;
    }

    foreach $item (@$deactivatepartiallinesref) {
        ($value = $item) =~ s/^[\s#]*(\S.*\S)\s*(?:#.*)?$/$1/;
        grep {(! m/^\s*#[\s#]*[^#]*$/) && s/^[\s#]*(.*$value.*)\s*(?:#\s*(.*\S))?\s*$/# $1\t# $marker $2/} @$linesarrayref;
    }
}

##########################
sub update_config_filepath
##########################
{
# this allows the program to make unattended changes to config files

    # specify changes by making entries in the passed in hash as follows (in this example, option is 'foobar')
    #  (note there is _no_support_ through this interface for commenting/uncommenting lines
    #   for that use the &update_config_lines interface)

    # to add or change an option
    #   $arghash{'foobar_set'} = on
    #   $arghash{'foobar'} = <newvalue (unqouted)>
    # to delete an opton
    #   $arghash{'foobar_set'} = off

    my ($filepath, $changeshashref) = @_;

    my %internalchangeshash = ();
    my ($option, $rawoption, $oldvalue);
    my @oldvaluelines;

    &makebackupcopy($filepath);

    my $filelinesref = &read_file_lines_just_once($filepath);

    foreach $rawoption (keys %$changeshashref) {
        next if (! (($option) = ($rawoption =~ m/^(.*)_set$/)));
        $internalchangeshash{"${option}_set"} = $$changeshashref{"${option}_set"}; 
        $internalchangeshash{$option} = $$changeshashref{$option} if exists $$changeshashref{$option}; 
        @oldvaluelines = grep { m/^\s*$option\s*=/ } @$filelinesref;
        if ($#oldvaluelines >= 0) {
            ($oldvalue) = ($oldvaluelines[0] =~ m/^=\s*([^#]*[^#\s])/);
            $oldvalue =~ s/^(['"])([^\1]*)\1.*$/$2/;	# strip quotes (also strip any second value on same line)
            $internalchangeshash{"${option}_previous"} = $oldvalue;
        } else {
            $internalchangeshash{"${option}_previous"} = 'not_set';
        }
    }

    &update_config_lines(\%internalchangeshash, $filelinesref);

    &flush_file_lines_and_reset($filepath);
}

# this extra block allows variable sharing with our internal subroutines
# there are several variables which are "shared" but are not passed as arguments
# ($_ is also an implicit shared variable, but it's not listed here because Perl does it)

{

    my ($okaymatchopen, $bettermatchopen, $bestmatchopen, $okaylineafter, $betterlineafter, $bestlineafter, $lineafter);
    my ($lineindex, $state);

#######################
sub update_config_lines
#######################
{
# this very long subroutine completely performs a rather complex process:
#  it figures out from rather incomplete information in its instructionshash (usually %in)
#   what changes are needed, then makes those changes to the given list of lines
#  the net effect is this can single-handedly update (rather intelligently) a config file

# most likely trying to either break this into a bunch of smaller routines
#  or change it will just break things
    my ($instructionshashref, $linesarrayref) = @_;

    # intermediate used during construction of final hashes of what to do
    my %newvalues = ();

    # final hashes of what to do - 
    #  when we're done these should be very complete,
    #  there should be no more need to reference %instructionshashref or %newvalues
    my %changevalue = ();
    my %addoption = ();
    my %deleteoption = ();
    my %commentline = ();
    my %uncommentline = ();

    my ($key, $option, $optionbase, $newvalue);
    my ($set, $previousset, $previousvalue);

    foreach $key (keys %$instructionshashref) {
        next if $key !~ m/_previous/;
        ($option) = ($key =~ m/^([^_]+)/);
        ($optionbase) = ($option =~ m/^([^;]+)/);
        $newvalue = (exists $$instructionshashref{$option}) ? $$instructionshashref{$option} : ((($options2details{$optionbase}[DETAILSVAR] == VARONOFF) || (($options2details{$optionbase}[DETAILSVAR] == VARLINE))) ? 'off' : '');
        if ($newvalue =~ m/\0/) {
            print "YIKES! internal error, multiple values for option $option ($newvalue)<br>\n" if $debug;
            next;	# we don't know what to do, so just punt
        }
        $newvalues{$option} = $newvalue;
    }

    while (my ($option, $newvalue) = each %newvalues) {
        $set = ($$instructionshashref{"${option}_set"} eq 'on') ? 1 : 0;
        $previousvalue = $$instructionshashref{"${option}_previous"};
        $previousset = ($$instructionshashref{"${option}_previous"} eq 'not_set') ? 0 : 1;
        if ($option =~ m/;/) {
            if (($newvalue eq 'on') && ($previousvalue eq 'off')) {
                $uncommentline{$option} = 1;
                next;
            }
            if (($newvalue eq 'off') && ($previousvalue eq 'on')) {
                $commentline{$option} = 1;
                next;
            }
            next;
        }
        if ($set && (! $previousset)) {
            $addoption{$option} = $newvalue;
            next;
        }
        if ((! $set) && $previousset) {
            $deleteoption{$option} = 1;
            next;
        }
        if ($set && $previousset) {
            if ($previousvalue ne $newvalue) {
                $changevalue{$option} = $newvalue;
            }
            next;
        }
        if ((! $set) && (! $previousset)) {
            next;
        }
    }


    my $lineschanged = 0;

    # next, using the various hashes constructed above, change the config file as specified

    while (my ($name, $value) = each %changevalue) {
        my ($oldname, $oldvaluearea, $oldcomment);
        my ($quotednewvalue);
        $lineschanged += grep &changeavalue($name, $value), @$linesarrayref;
    }

    # impose an order on the entries in this hash 
    #  so if the entries are appended at the end, they will always be in the same order
    my $previousname = '';	# first time do not match
    my ($previousprefix, $prefix);
    my ($name, $value);
    for $name (sort bytype keys %addoption) {
        $value = $addoption{$name};
        $okaymatchopen = 0;
        $bettermatchopen = 0;
        $bestmatchopen = 0;
        $okaylineafter = -1;
        $betterlineafter = -1;
        $bestlineafter = -1;
        $lineindex = -1;
        $state = 1;

        # scan through file to find best insertion point
        grep &addanoption($name, $value), @$linesarrayref;

        my @linestoadd = ();
        if ($bestlineafter >= 0) {
            $lineafter = $bestlineafter;
        } elsif ($betterlineafter >= 0) {
            $lineafter = $betterlineafter;
        } elsif ($okaylineafter >= 0) {
            $lineafter = $okaylineafter;
        } else {
    	# no other reasonable place of any sort found, so add it at the end
            $lineafter = $lineindex + 1;
            # and add a blank line before it too (unless we're in the middle of a block of ...list options
            ($previousprefix) = ($previousname =~ m/^(.{1,4})/);
            ($prefix) = ($name =~ m/^(.{1,4})/);
            push @linestoadd, '' if (((($previousname !~ m/list$/) && ($previousname ne 'pics')) || (($name !~ m/list$/) && ($name ne 'pics'))) && ($previousprefix ne $prefix));
        }
        my $quotedvalue = &quotevalue($value);
        push @linestoadd, "$name = $quotedvalue\t# $marker";
        $lineschanged += scalar @linestoadd;
        splice(@$linesarrayref, $lineafter, 0, @linestoadd);
        $previousname = $name;
    }

    my ($namex, $subnamex, $valuex, $lineid, $commentline);
 
    while (($namex, $valuex) = each %deleteoption) {
        # find the line to delete and comment it out
        $lineschanged += grep &deleteanoption($namex, $valuex), @$linesarrayref;
    }

    foreach $lineid (keys %commentline) {
        $lineindex = -1;

        ($namex, $subnamex) = split /\s*;\s*/, $lineid;
        $lineschanged += grep &commentaline($namex, $subnamex), @$linesarrayref;
    }

    foreach $lineid (keys %uncommentline) {
        $lineindex = -1;

        ($namex, $subnamex) = split /\s*;\s*/, $lineid;
        $lineschanged += grep &uncommentaline($namex, $subnamex), @$linesarrayref;
    }

    return $lineschanged;

}

###########################################################################
#
#    LOCAL SUBROUTINES USED BY CALLS TO 'GREP' IN CONFIG CHANGE ABOVE
#
# some of these actually perform the change themselves,
#
# others set variables for an outer routine that implements the change
#  (a subset of these use '$state', which is defined as follows:
#   1 -searching for anything in comments
#   2 -searching for end of comments [while still watching for matches])
#
###########################################################################

#-----------------
sub uncommentaline
#-----------------
{
    my ($name, $subname) = @_;
    if (m/\b$name\b.*$subname/) {
        s/^(?:[#\s]*)?([^#]*\S)\s*(?:#\s*(.*))?$/$1\t# $marker $2/;
        return 1;
    } else {
        return 0;
    }
}

#---------------
sub commentaline
#---------------
{
    my ($name, $subname) = @_;
    if (m/\b$name\b.*$subname/) {
        # newline on replacement only for test harness
        s/^(?:[#\s]*)?([^#]*\S)\s*(?:#\s*(.*))?$/#$1\t# $marker $2/;
        return 1;
    } else {
        return 0;
    }
}

#-----------------
sub deleteanoption
#-----------------
{
    my ($option) = @_;

    if (m/^\s*$option\s*=/) {
        s/^([^#]*\S)\s*(?:#\s*(.*)?)?$/#$1\t# $marker $2/;
        return 1;
    } else {
        return 0;
    }
}

#--------------
sub addanoption
#--------------
{
    my ($option, $newvalue) = @_;

    ++$lineindex;

    my $newstate;

    if ($state == 1) {
        return 0 if ! m/^\s*#/;
    }
    if (m/^[\s#]*#\s?$option[^#]*=/) {
        $bestmatchopen = 1;
        $newstate = 2;
    }
    if (m/^[\s#]*\s+$option[^#]*=/) {
        $bettermatchopen = 1;
        $newstate = 2;
    }
    if (m/^[\s#]*\s+(?:\S+\s+){0,2}$option/) {
        $okaymatchopen = 1;
        $newstate = 2;
    }
    if (($state == 2) && m/^[^#]*$/) {
        $lineafter = $lineindex;
        $bestlineafter = $lineafter if $bestmatchopen;
        $betterlineafter = $lineafter if $bettermatchopen;
        $okaylineafter = $lineafter if $okaymatchopen;
        $bestmatchopen = 0;
        $bettermatchopen = 0;
        $okaymatchopen = 0;
        $newstate = 1;
    }
    $state = $newstate if $newstate;
}

#---------------
sub changeavalue
#---------------
{
    my ($option, $newvalue) = @_;

    return 0 if m/^\s*#/;
    return 0 if m/^\s*$/;

    my ($oldname, $oldvaluearea, $oldcomment) = m/^\s*(\w+)\s*=\s*(.*?(?=\s*(?:#|$)))\s*(?:#\s*(.*\S))?\s*$/;
    return 0 if ! $oldname;
    return 0 if $oldname ne $option;
    $oldcomment = '' if ! $oldcomment;
    chomp $oldcomment;
    my $quotednewvalue = &quotevalue($newvalue);
    s/^([^#]*=\s*).*$/$1$quotednewvalue\t# $marker $oldcomment/;
    return 1;
}

}

#############################
sub significantconfigfilepath
#############################
{
    # try to ignore variable parts (different PREFIXes)
    #  and determine only the "significant" part of a filepath into the configs
    my ($configfilepath) = @_;

    $configfilepath =~ s{^\s*(['<]?).*(/etc/dansguardian)}{$1$2};

    return $configfilepath;
}

###########################################################################
#
#    UTILITY SUBROUTINES
#    these are probably only of use internally
#
###########################################################################

##############
sub quotevalue
##############
{
# surround argument with quotes if they're needed
#  (needed if: argument is empty, argument contains embedded white space, argument is "long" ...)
    my ($value) = @_;

    my $quotedvalue = ((! defined $value) || ((length $value) < 1) || ($value =~ m/^\s*$/) || ($value =~ m/^\s+/) || ($value =~ m/^\s+$/) || (($value !~ m/^\d+$/) && ((length $value) > 5))) ? "'$value'" : $value;
    return $quotedvalue;
}

print DEBUGLOG "finished incorporating dansguardian-edit-lib.pl\n" if $debug;

return 1;	# signal we've loaded successfully
