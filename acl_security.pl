#!/usr/bin/perl -w
# dansguardian-lib.pl

require 'dansguardian-lib.pl';

###############################################################
# internal/utility sub-subroutines
###############################################################
sub showyesno
{
    my ($option) = @_;

    my $headingtitle;

    my $optionname = $option;
    if ($option =~ m/(conf|lists|messages|edit)/) {
        $headingtitle = "$text{'acl_canedit'} ";
    } elsif ($option =~ m/view/) {
        $headingtitle = "$text{'acl_canview'} ";
    } elsif ($option =~ m/auto/) {
        $headingtitle = "$text{'acl_canchooseauto'} ";
        $optionname =~ s/auto//;
    } else {
        $headingtitle = "$text{'acl_can'} "; 
    }
    $headingtitle .= $text{"index_$optionname"};

    if (($option eq 'start') || ($option eq 'stop')) {
        $interplay = "onChange='if((this.form.start[0].checked)&&(this.form.stop[0].checked)){this.form.autorestart[0].disabled=false;this.form.autorestart[1].disabled=false;}else{this.form.autorestart[0].checked=false;this.form.autorestart[1].checked=true;this.form.autorestart[0].disabled=true;this.form.autorestart[1].disabled=true;}'";
    } else {
        $interplay = '';
    }
    print "<tr><td colspan=2><b>$headingtitle</b></td>\n";
    print "<td><input type=radio name=$option value=1 " . ($$optionsref[0]->{$option} ? 'checked' : '') . " $interplay> $text{'yes'}\n";
    print "<td><input type=radio name=$option value=0 " . ($$optionsref[0]->{$option} ? '' : 'checked') . " $interplay> $text{'no'}\n";
    print "</td></tr>\n";
}

sub showlistsoptions
{
  print "<tr><td valign=bottom><b>$text{'acl_canedit'} $text{'index_editgroupsconfandlists'}</b></td>";
  print "<td align=right valign=middle>$text{'acl_groups'}</td>\n";
  print "<td colspan=2><select name=groups multiple size=6>\n";
  print "<option value=f0 " . ($$optionsref[0]->{'f0'} ? 'selected' : '') . ">shared/common/base</option>\n";
  print "<option value=local " . ($$optionsref[0]->{'local'} ? 'selected' : '') . ">local</option>\n";
  print "<option value='' disabled>&nbsp;----------&nbsp;</option>\n";
  for ($i=1; $i<=99; ++$i) {
    $groupname = "f$i";
    print "<option value='$groupname' " . ($$optionsref[0]->{$groupname} ? 'selected' : '') . ">&nbsp;&nbsp;$groupname&nbsp;&nbsp;</option>\n";
  }
  print "</select></td></tr>\n";


  # This array populates an html select list with the list names
  print "<tr><td>&nbsp;</td>";
  print "<td align=right valign=middle>$text{'acl_lists'}</td>\n";
  print "<td colspan=2><select name=lists multiple size=7>\n";
  foreach $s ('conf', '', 'blacklists', 'phraselists', '', sort bytype keys %groupsconfigurationlists) {
    if ($s) {
      print "<option value='$s' " . ($$optionsref[0]->{$s} ? 'selected' : '') . ">" . ($text{"conf_$s"}) . " ...</option>\n";
    } else {
      # separator
      print "<option value='' disabled>&nbsp;----------&nbsp;</option>\n";
    }
  }
  print "</select></td></tr>\n";

}

###############################################################
# external subroutines expected by Webmin
#  (effectively our API)
###############################################################
sub acl_security_form 
{
  # set up a global so we can call subroutines
  $optionsref = \@_;

  # This is for the main menu 
  $hralready = 0;
  $groupsalready = 0;
  foreach $s ('start', 'stop', 'reload', 'status', 'logs', 'search', 'editconf', 'editplugconf', 'editmessages', 'editlists', 'editfiltergroupassignments', 'setupfiltergroups', 'viewfiltergroups', 'editgroupsconf', 'editgroupslists', 'autorestart', 'autoreload' ) {
    if (($s eq 'editgroupslists') || ($s eq 'editgroupsconf')) {
        print "<tr><td colspan=4><hr></td></tr>" if ! $hralready;
        &showlistsoptions() if ! $groupsalready;
        print "<tr><td colspan=4><hr></td></tr>";
        $hralready = 1;
        $groupsalready = 1;
    } else {
        &showyesno($s);
	$hralready = 0;
    }
  }
}

sub acl_security_save {
  my ($access, $in) = @_;
  $access->{'start'} = $in->{'start'};
  $access->{'stop'} = $in->{'stop'};
  $access->{'restart'} = ($in->{'start'} && $in->{'stop'}) ? 1 : 0;
  $access->{'reload'} = $in->{'reload'};
  $access->{'status'} = $in->{'status'};
  $access->{'logs'} = $in->{'logs'};
  $access->{'search'} = $in->{'search'};
  $access->{'editconf'} = $in->{'editconf'};
  $access->{'editplugconf'} = $in->{'editplugconf'};
  $access->{'editlists'} = $in->{'editlists'};
  $access->{'editmessages'} = $in->{'editmessages'};
  $access->{'editfiltergroupassignments'} = $in->{'editfiltergroupassignments'};
  $access->{'editgroupsconf'} = $in->{'editgroupsconf'};
  $access->{'editgroupslists'} = $in->{'editgroupslists'};
  $access->{'setupfiltergroups'} = $in->{'setupfiltergroups'};
  $access->{'viewfiltergroups'} = $in->{'viewfiltergroups'};
  $access->{'autorestart'} = ($in->{'start'} && $in->{'stop'}) ? $in->{'autorestart'} : 0 ;
  $access->{'autoreload'} = $in->{'autoreload'};

  # parse HTML input into a form more convenient for Perl
  map { $groups{$_} = 1} split(/\0/, $in->{'groups'});
  map { $lists{$_} = 1 } split(/\0/, $in->{'lists'});

  # check all the filter groups, see if at least one
  #  ('f0' is a fake filter group which means the shared/common/base files)
  $somegroup = 0;
  for ($i=0; $i<=99; ++$i) {
      $groupname = "f$i";
      ++$somegroup if exists $groups{$groupname};
      $access->{$groupname} = $groups{$groupname};
  }
  ++$somegroup if exists $groups{'local'};
  $access->{'local'} = $groups{'local'};
  $somelist = 0;
  $someconf = 0;
  foreach $s ('conf', 'blacklists', 'phraselists', keys %groupsconfigurationlists) {
    $somelist = 1 if $lists{$s};
    $access->{$s} = $lists{$s};
  }
  $someconf = 1 if $lists{'conf'};
  if ($somegroup) {
    # at least one group, show choices if also a) 'conf' or b) at least one list
    $access->{'editgroupsconf'} = $someconf;
    $access->{'editgroupslists'} = $somelist;
  } else {
    # no groups, not allowed to edit anything at all, don't even show the choice
    $access->{'editgroupsconf'} = 0;
    $access->{'editgroupslists'} = 0;
  }
}
