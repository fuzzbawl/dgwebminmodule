#!/usr/bin/perl
# setupfiltergroups.cgi


# by declaring all the globals we'll reference (including some in our own
#  libraries)_before_ pulling in libraries and adding the 'use ...' _after_ 
#  pulling in libraries, we can 'use strict'  for our own code without 
#  generating any messages about the less-than-clean code in the very old 
#  Webmin libraries themselves
our (%text, %access, %config, %in, $module_name, $modulever, $moduleinfo);
our ($debug, $dg_version, $current_lang, $module_config_directory);
our (%groupsconfigurationlists, %sharedgroupsconfigurationlists, %notsharedgroupsconfigurationlists);
our (%sharedonlynestedconfigurationlists, %sharedonlyseparateconfigurationlists, %sharedonlycommonconfigurationlists);
our ($EFFECTIVE_USER_ID);
require './dansguardian-lib.pl';
use POSIX;
use warnings;
use strict qw(subs vars);
# effectively index of last filter group
our $filtergroups = $in{'filtergroups'};
our $filtergroupsschemelists = $in{'filtergroupsschemelists'};
our $filtergroupsdefaultnoweb = ($in{'filtergroupsdefaultnoweb'} =~ m/on/i) ? 1 : 0;
our $filtergroupshighestallweb = ($in{'filtergroupshighestallweb'} =~ m/on/i) ? 1 : 0;
# first "real" filter group (not including f1 if the default is just "no web access")
our $firstvariablegroup = $filtergroupsdefaultnoweb ? 2 : 1;
our $lastvariablegroup = $filtergroupshighestallweb ? ($filtergroups -1) : $filtergroups;
our @sharedlists = split ' ', $in{'sharedlists'};
our @uniquelists = split ' ', $in{'uniquelists'};


# type of heading - note well the first three of these apply to *both* 
#  i) the scheme (filtergroupsschemeslists) and ii) the kind of header desired
use constant NESTED => 1;
use constant SEPARATE => 2;
use constant COMMON => 3;
use constant UNUSED => -1;
use constant SHARED => -2;
use constant ISCOMMON => -3;
use constant LOCAL => -4;
# direction (sub-subtype of heading)
#  note these are defined in such a way that !DIRBANNED==DIREXCEPTION (and !DIREXCEPTION==DIRBANNED)
use constant DIRBANNED => 1;
use constant DIREXCEPTION => 0;


#set up some useful globals
our $listdir = &canonicalizefilepath("$config{'conf_dir'}/lists");
our $conffilepath = &group2conffilepath(0);
our $basefgconffilepath = &group2conffilepath(1);

our @newgroupnames = ( 'error' );
our $newgroupname;
if ($filtergroups <= 9) {
    # name specified for each filter group, copy from HTML whatever the user specified
    for (my $i=1; $i<=$filtergroups; ++$i) {
        $newgroupname = "groupnamef$i";
        $newgroupname = $in{"groupnamef$i"};
        $newgroupname =~ s/\s/_/g;
        # fallback (which should never be used) is to name the group simply fN
        $newgroupnames[$i] = ($newgroupname) ? $newgroupname : "f$i";
    }
} else {
    # too many groups, completely ignore inputs from HTML and instead generate "generic" group names
    for (my $i=1; $i<=$filtergroups; ++$i) {
        $newgroupnames[$i] = "f$i";
    }
    # maybe handle names of first and/or last filter groups specially
    $newgroupnames[1] = 'No_Web_Access' if ($filtergroupsdefaultnoweb);
    $newgroupnames[$filtergroups] = 'All_Web_Access' if ($filtergroupshighestallweb);
}
# stick in our own name for the lowest/default filter group if user didn't supply one
$newgroupnames[1] = 'default' if $newgroupnames[1] eq 'f1';

&bailifcallercancelled();


&webminheader();


# we do everything in reverse order because some of the files we want to change
#  get used for patterns (copied) in other steps (for example dansguardianf1.conf)

# note we should NOT use the globals @sharedgroupsconfigurationlists and @notsharegroupsconfigurationlists
#  because they reflect how things used to be in the past, but we're setting up the future
#  so we should only use our arguments @sharedlist and @uniquelists
#  (it's okay though to use @groupsconfigurationlists if necessary, because it never changes)

our ($fgconffilepath, $fglistdir, $uniquelist, $listfile, $uniquelistfile, $listfilepath, $fglistfilepath, $thisgroupname);

###################
##### setup subdirs

# create subdirs so we're sure they already exist when we need them
for (my $group=$lastvariablegroup; $group>=$firstvariablegroup; --$group) {
    $fglistdir = &canonicalizefilepath("$config{'conf_dir'}/lists/f$group");
    mkdir $fglistdir, 02775;
}
$fglistdir = &canonicalizefilepath("$config{'conf_dir'}/lists/local");
mkdir $fglistdir, 02775;

#################
##### setup lists
for (my $group=$lastvariablegroup; $group>=$firstvariablegroup; --$group) {
    # set up a few per-filtergroup variables which we can then use
    $fgconffilepath = &group2conffilepath($group);
    $fglistdir = &canonicalizefilepath("$listdir/f$group");
    foreach my $uniquelist (@uniquelists) {
        # set up more variables which we can then use
        $uniquelistfile = ($uniquelist ne 'picsfile') ? $uniquelist : 'pics';
        $listfilepath = &canonicalizefilepath("$listdir/$uniquelistfile");
        $fglistfilepath = &canonicalizefilepath("$fglistdir/${uniquelistfile}f$group");
        $thisgroupname = &groupnumber2newgroupname($group);
        # file shouldn't already exist, but if it does save the old copy out of the way
        &renametobackup($fglistfilepath, $debug) if (-e $fglistfilepath);
        # now figure out which "subroutine" to call to do the real work
        if ($filtergroupsschemelists == NESTED) {
            &setuponenestedlist($group, $uniquelist);
        } elsif ($filtergroupsschemelists == SEPARATE) {
            &setuponeseparatelist($group, $uniquelist);
        } elsif ($filtergroupsschemelists == COMMON) {
            &setuponecommonlist($group, $uniquelist);
        } else {
            print "OOPS!, unknown scheme filtergroupsschemelists=$filtergroupsschemelists requested in setupfiltergroups.cgi<br>\n" if $debug;
        }
    }
}

#####################################
##### set up per-filter group configs

for (my $group=$filtergroups; $group>=1; --$group) {
    # set up a few per-filtergroup variables which we (including "subroutines") can then use
    my $fgconffilepath = &group2conffilepath($group);
    my $fglistdir = &canonicalizefilepath("$config{'conf_dir'}/lists/f$group");

    # handle the config file
    if ($basefgconffilepath ne $fgconffilepath) {
        &renametobackup($fgconffilepath, $debug) if -e $fgconffilepath;
        &makecopy($basefgconffilepath, $fgconffilepath, $debug);
    } else {
        &makebackupcopy($fgconffilepath, $debug);
    }

    our %arguments = ();
    $arguments{'groupname'} = &groupnumber2newgroupname($group);
    $arguments{'groupname_set'} = 'on';
    $arguments{'groupmode'} = 1;	# default, for most filter groups
    if (($group == 1) && $filtergroupsdefaultnoweb) { $arguments{'groupmode'} = 0; }
    if (($group== $filtergroups) && $filtergroupshighestallweb) { $arguments{'groupmode'} = 2; }
    $arguments{'groupmode_set'} = 'on';

    foreach my $sharedlist (@sharedlists) {
        my $sharedlistfile = ($sharedlist ne 'picsfile') ? $sharedlist : 'pics';
        my $sharedlist_set = "${sharedlist}_set";
        if ((($group == 1) && $filtergroupsdefaultnoweb) || (($group == $filtergroups) && $filtergroupshighestallweb)) {
            $arguments{$sharedlist_set} = 'off';
        } else {
            $arguments{$sharedlist_set} = (! &sharedoptionsavailable) ? 'on' : 'off';
            $arguments{$sharedlist} = "$listdir/$sharedlistfile";
        }
    }

    foreach my $uniquelist (@uniquelists) {
        my $uniquelistfile = ($uniquelist ne 'picsfile') ? $uniquelist : 'pics';
        my $uniquelist_set = "${uniquelist}_set";
        if ((($group == 1) && $filtergroupsdefaultnoweb) || (($group == $filtergroups) && $filtergroupshighestallweb)) {
            $arguments{$uniquelist_set} = 'off';
        } else {
            $arguments{$uniquelist_set} = 'on';
            $arguments{$uniquelist} = "$fglistdir/${uniquelistfile}f$group";
        }
    }

    &update_config_filepath($fgconffilepath, \%arguments);

}

############################
##### set up main config file
our %addlists = ();
foreach my $sharedlist (@sharedlists) {
    my $sharedlist_set = "${sharedlist}_set";
    $addlists{$sharedlist_set} = 'on';
    my $sharedlistfile = ($sharedlist ne 'picsfile') ? $sharedlist : 'pics';
    $addlists{$sharedlist} = "$listdir/$sharedlistfile";
}
foreach my $uniquelist (@uniquelists) {
    my $uniquelist_set = "${uniquelist}_set";
    $addlists{$uniquelist_set} = 'off';
}

our %arguments = (%in, %addlists);
&update_config_filepath($conffilepath, \%arguments);

#############################
########### mark shared lists
### and create local sublists
my @newheaderlines = &getnewheaderlines(SHARED, undef, undef);
my @newlocalheaderlines = &getnewheaderlines(LOCAL, undef, undef);
foreach my $list (@sharedlists) {
    my $listfile = ($list ne 'picsfile') ? $list : 'pics';
    my $listfilepath = "$listdir/$listfile";
    my $locallistfilepath = "$listdir/local/$listfile";
    my $newlistref = &read_file_lines_just_once($listfilepath);
    # add heading to top of list file
    unshift @$newlistref, @newheaderlines;
    # also add an .Include for "local" list file
    push @$newlistref, "", ".Include<$locallistfilepath>", ""; 
    &flush_file_lines_and_reset($listfilepath);
    # create new "local" file
    &createfile($locallistfilepath);
    # now that file exists, use regular mechanisms to add some comments to its top
    my $newlocallistref = &read_file_lines_just_once($locallistfilepath);
    unshift @$newlocallistref, "", "#listcategory '$list local'", "", "";
    unshift @$newlocallistref, @newlocalheaderlines;
    &flush_file_lines_and_reset($locallistfilepath);
}

#############################
########### mark unique lists
### and create local sublists
# next line rather pithily maps which scheme we're setting up to the use of the 'unique' files
our $usewhich = ( 'error', undef, UNUSED, ISCOMMON )[$filtergroupsschemelists];
my @newheaderlines = &getnewheaderlines($usewhich, undef, undef);
my @newlocalheaderlines = &getnewheaderlines(LOCAL, undef, undef);
foreach my $list (@uniquelists) {
    my $listfile = ($list ne 'picsfile') ? $list : 'pics';
    my $listfilepath = "$listdir/$listfile";
    my $locallistfilepath = "$listdir/local/$listfile";
    my $newlistref = &read_file_lines_just_once($listfilepath);
    # if we have a heading, add it to top of list file
    unshift @$newlistref, @newheaderlines if ((defined @newheaderlines) && (defined $newheaderlines[0]));
    # also add an .Include for "local" list file
    push @$newlistref, "", ".Include<$locallistfilepath>", ""; 
    &flush_file_lines_and_reset($listfilepath);
    # create new "local" file
    &createfile($locallistfilepath);
    # now that file exists, use regular mechanisms to add some comments to its top
    my $newlocallistref = &read_file_lines_just_once($locallistfilepath);
    unshift @$newlocallistref, "", "#listcategory '$list local'", "", "";
    unshift @$newlocallistref, @newlocalheaderlines;
    &flush_file_lines_and_reset($locallistfilepath);
}

our $textindex = "conf_filtergroupslistsscheme_radio_${filtergroupsschemelists}";
print "<p>&nbsp;<p><span style='color: magenta'>$text{'setup_done'} $text{$textindex}</span><br>\n";


########
#### end


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

#####################
sub getnewheaderlines
#####################
{
    my ($whichheader, $group, $direction) = @_;
    $group = &canonicalizegroupnumber($group);

    return undef if !$whichheader;
      
    my @result = ( '############################################################################', '#' );

    if ($whichheader == ISCOMMON) {
        push @result, "# This list is the common base upon which all filter groups elaborate.", "# Any changes to it will affect all filter groups.";
    } elsif ($whichheader == SHARED) {
        push @result, "# This list is shared by all filter groups.", "# Any changes to it will affect all filter groups.";
    } elsif ($whichheader == UNUSED) {
        push @result, "# This list is not currently used by any filter group.", "# Changes to it won't have any effect at all.";
    } elsif ($whichheader == NESTED) {
        if ($direction == DIRBANNED) {
            if ($group >= $lastvariablegroup) {
                push @result, "# This list applies to filter group '$newgroupnames[$group]'", "#  as well as all other filter groups.";
            } else {
                push @result, "# This list is the difference between '$newgroupnames[$group]' (and lower filter groups)", "#  and '$newgroupnames[$group+1]' (and higher filter groups)."; 
            }
        } elsif ($direction == DIREXCEPTION) {
            if ($group <= $firstvariablegroup) {
                push @result, "# This list applies to filter group '$newgroupnames[$group]'", "#  as well as all other filter groups.";
            } else {
                push @result, "# This list is the difference between '$newgroupnames[$group]' (and higher filter groups)", "#  and '$newgroupnames[$group-1]' (and lower filter groups)."; 
            }
        } else {
            print "OOPS! unknown direction argument $direction in subroutine getnewheaderlines in module setupfiltergroups.cgi\n" if $debug;
        }
	push @result, '#', '# This list affects filter groups:';
	for (my $i=$group; ($i>=$firstvariablegroup)&&($i<=$lastvariablegroup); ($direction)?--$i:++$i) {
	    push @result, "#\t'$newgroupnames[$i]'";
	}
    } elsif ($whichheader == SEPARATE) {
       push @result, "# This list is just for filter group '$newgroupnames[$group]'.", "# Changing it will have no effect on any other filter group";
    } elsif ($whichheader == COMMON) {
       push @result, "# This list is the elaboration on a common base for filter group '$newgroupnames[$group]'", "# Changing it will have no effect on any other filter group.";
    } elsif ($whichheader == LOCAL) {
       push @result, "# This list contains only settings only for this system", "#  in a master-slaves configuration. All other settings are elsewhere.", "# Unlike other config files", "#  master-slaves updating won't overwrite this file.", "#", "# This list is shared by all filter groups."; 
    } else {
        print "OOPS! unknown whichheader argument $whichheader to subroutine getnewheaderlines in module setupfiltergroups.cgi\n" if $debug;
    }

    push @result, '#', '############################################################################', '';

    return @result;
}

######################
sub setuponenestedlist
######################
{
    my ($group, $list) = @_;

    my (@newheaderlines, $newlistref, $includedgroup, $includedfilepath);

    $listfile = ($list ne 'picfile') ? $list : 'pics';
    if (($list =~ m/^exception/) || ($list =~ m/grey/)) {
        # include next lower
        @newheaderlines = &getnewheaderlines(NESTED, $group, DIREXCEPTION);
        $includedgroup = $group - 1;
        $includedfilepath = &canonicalizefilepath("$listdir/f$includedgroup/${listfile}f$includedgroup");
        # we need something to start with
        if ($group == $firstvariablegroup) {
            # create a symlink to the existing file
            symlink $listfilepath, $fglistfilepath;
        } else {
            # create a new minimal file to start with
            &createfile($fglistfilepath);
        }
	$newlistref = &read_file_lines_just_once($fglistfilepath);
        if ($group != $firstvariablegroup) {
            # construct a "delta" list
            unshift @$newlistref, "", ".Include<$includedfilepath>", "";
        }
	unshift @$newlistref, "", "#listcategory 'f$group $list '", "", "";
        # add our new heading
        unshift @$newlistref, @newheaderlines, '';
    } else {
        # include next higher
        @newheaderlines = &getnewheaderlines(NESTED, $group, DIRBANNED);
        $includedgroup = $group + 1;
        $includedfilepath = &canonicalizefilepath("$listdir/f$includedgroup/${listfile}f$includedgroup");
        if ($group == $lastvariablegroup) {
            # create a symlink to the existing file
            symlink $listfilepath, $fglistfilepath;
        } else {
            # create a new minimal file to start with
            &createfile($fglistfilepath);
        }
	$newlistref = &read_file_lines_just_once($fglistfilepath);
        if ($group != $lastvariablegroup) {
            # construct a "delta" list
            unshift @$newlistref, "", ".Include<$includedfilepath>", "";
        }
	unshift @$newlistref, "", "#listcategory 'f$group $list '", "", "";
        # add our new heading
        unshift @$newlistref, @newheaderlines, '';
    }
    # persist the file back to disk (we're all done with it)
    &flush_file_lines_and_reset($fglistfilepath);
}

########################
sub setuponeseparatelist
########################
{
    my ($group, $list) = @_;

    $listfile = ($list ne 'picfile') ? $list : 'pics';
    # start with a copy of an existing file
    &makecopy($listfilepath, $fglistfilepath);
    my $newlistref = &read_file_lines_just_once($fglistfilepath);
    # no .Includes (this file is "separate" after all)
    # add our new heading
    my @newheaderlines = &getnewheaderlines(SEPARATE, $group, undef);
    unshift @$newlistref, @newheaderlines, '';
    # persist the file back to disk (we're all done with it)
    &flush_file_lines_and_reset($fglistfilepath);
}

######################
sub setuponecommonlist
######################
{
    my ($group, $list) = @_;

    $listfile = ($list ne 'picfile') ? $list : 'pics';
    # create a new minimal file to start with
    &createfile($fglistfilepath);
    my $newlistref = &read_file_lines_just_once($fglistfilepath);
    # construct lines that will make this a "common" list
    unshift @$newlistref, "", ".Include<$listdir/${listfile}>", "";
    unshift @$newlistref, "", "#listcategory: 'f$group $list", "", "";
    # add our new heading
    my @newheaderlines = &getnewheaderlines(COMMON, $group, undef);
    unshift @$newlistref, @newheaderlines, '';
    # persist the file back to disk (we're all done with it)
    &flush_file_lines_and_reset($fglistfilepath);
}

###########################################################################
#
#    UTILITY SUBROUTINES
#
###########################################################################

############
sub isinlist
############
{
    my ($listref, $item) = @_;
    for my $trythis (@$listref) {
        return 1 if $trythis eq $item;
    }
    return 0;
}

############################
sub groupnumber2newgroupname
############################
{
    my ($group) = @_;
    $group = &canonicalizegroupnumber($group);

    return 'error' if $group < 1;
    return 'error' if $group > $filtergroups;

    return $newgroupnames[$group];
}

################
sub webminheader
################
{
    &ui_print_header($text{'index_setupfiltergroups'}, $text{'index_title'}, undef, undef, 0, 1, 1, '', undef, undef, "$text{'index_version'} $dg_version <small>($text{'index_modulever'} $modulever)</small>");
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
        &ui_print_footer('index.cgi', $text{'index_return'}, 'editconf.cgi', "$text{'index_viewedit'} $text{'index_editconf'}", 'editplugconf.cgi', "$text{'index_viewedit'} $text{'index_editplugconf'}", 'setupfiltergroupsinput.cgi', $text{'index_setupfiltergroups'});
    }

    exit;
}

