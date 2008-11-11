#!/usr/bin/perl -w
# dansguardian-lib.pl

do '../web-lib.pl';
do '../ui-lib.pl';
&init_config();
%access = &get_module_acl();

# Get the DG version
$dg_version=&checkdgver();

# Read in the dansguardian.conf file
$cfref = &read_file_lines($config{'conf_dir'}."/dansguardian.conf");
$modulever = "0.7.0alpha2";

## checkdgconf();
## Check for existance of DG config file
sub checkdgconf {
  $conffilepath = "$config{'conf_dir'}/dansguardian.conf";
  if (!(-f $conffilepath)) {
    print "<p>";
    print &text('error_confnotfound', $conffilepath, "/config.cgi?$module_name"),"<p>\n";
    print "$text{'index_confloc'} $conffilepath.";
    print "<hr>\n";
    &ui_print_footer("/", $text{'index_return'});
#    exit;
  } else {
    return true;
  }
}

## checkdgbinary();
## Check for existance and executable state of DG binary
sub checkdgbinary {
  if (!(-x $config{'binary_file'})) {
    print "<p>";
    print &text('error_binnotfound', $config{'binary_file'}, "/config.cgi?$module_name"),"<p>\n";
    print "<hr>\n";
    &ui_print_footer("/", $text{'index_return'});
#    exit;
  } else {
    return true;
  }
}

## checkdgver();
## Check DG version for compatibility
sub checkdgver {
  my $ver = `$config{'binary_file'} -v 2>&1`;
  if (($ver =~ /(2\.9\.9\.\d+)/) || ($ver =~ /(2\.10\.?\d*.?\d*)/)) {
    return $1;
  } else {
    return false;
  }
}

## checkmodauth(ACLNAME);
## Check webmin ACL's for ACLNAME against username
sub checkmodauth {
  my $section = $_[0];
  if (!$access{$section}) {
    print "<p>$text{'index_notauth'}\n";
    &ui_print_footer("index.cgi", $text{'index_return'});
    exit;
  }
}

sub readconfigoption {
    my $option = $_[0];
    my $value;
    my $name;
    my $line;
    foreach $line (@$cfref) {
        ($name, $value) = split(/=/, $line);
        $name =~ s/ //g;
        if ($name eq $option) {
            $value =~ s/ //g;
            $value =~ s/^'//g;
            $value =~ s/'.*$//g;
            return $value;
        }
    }
}

## Read filter group config. This is so ugly
sub readgroupconf {
  my $group = $_[0];
  my $option = $_[1];
  my $value;
  my $name;
  my $line;
  my $cfrefgrp = &read_file_lines($config{'conf_dir'} . "/dansguardian" . $group . ".conf");
  foreach $line (@$cfrefgrp) {
    ($name, $value) = split(/=/, $line);
    $name =~ s/ //g;
    if ($name eq $option) {
      $value =~ s/ //g;
      $value =~ s/^'//g;
      $value =~ s/'.*$//g;
      return $value;
    }
  }
}

# form_line(<configfileoptionname>, <icon size>, <icon max len>, <editable file>)
sub form_line {
    my $option = $_[0];
    my $size = $_[1];
    my $maxlen = $_[2];
    my $helpfile = $_[3];
    my $editable = $_[4];
    my $group = $_[5];
    my $label = $text{"conf_".$option};
    my $value = &readconfigoption($option);
    if ($editable ne "") {
        my $editlink = " <A HREF=\"./edit.cgi?file=$value\">$editable</a>";
    }
    print &ui_table_row(&hlink("$label", "$helpfile"), "<input name=\"$option\" size=\"$size\" maxlength=\"$maxlen\" value=\"$value\" $editlink>");
}

# gform_line(<configfileoptionname>, <icon size>, <icon max len>, <editable file>)
sub gform_line {
    my $option = $_[0];
    my $size = $_[1];
    my $maxlen = $_[2];
    my $helpfile = $_[3];
    my $group = $_[4];
    my $label = $text{"conf_".$option};
    my $value = &readgroupconf($group,$option);
    print &ui_table_row(&hlink("$label", "$helpfile"), "<input name=\"$option\" size=\"$size\" maxlength=\"$maxlen\" value=\"$value\">");
}


# edit_line_file(<configfileoptionname>, <icon size>, <icon max len>, <editable file>)
sub edit_line_file {
    my $option = $_[0];
    my $helpfile = $_[1];
    my $label = $text{"conf_".$option};
    my $value = &readconfigoption($option);
    print &ui_columns_row( [ &hlink("$label", "$helpfile"), $value, "<A HREF=\"./edit.cgi?file=$value\">$text{'index_edit'}</a>" ] );
    # search the file for '.Include<...>' directives and list any files found
    $fileref = &read_file_lines($value);
    my $file_line;
    my $file_count = 0;
    my $output_string = "";

    foreach $file_line (@{$fileref}) {
        if ($file_line =~ /^\s*\.Include\<([^\>]+)\>.*$/) {
	    if ($file_count != 0) {
	        $output_string .= "<tr>";
	    }
            $output_string .= "<td>$1</td><td><A HREF=\"./edit.cgi?file=$1\">$text{'index_edit'}</A></td></tr>\n";
	    $file_count++;
	}
    }
    if ($output_string ne "") {
        print "<tr><td rowspan=\"$file_count\">&nbsp;</td>$output_string</tr>\n";
    }
}

# form_option(<configfileoptionname>)
sub form_option {
    my $option = $_[0];
    my $helpfile = $_[1];
    my $label = $text{"conf_".$option};
    my $value = &readconfigoption($option);
    if ($value eq 'on') {
        my $checked = 'checked=CHECKED';
    }
    print &ui_table_row(&hlink("$label", "$helpfile"), "<input type=\"checkbox\" name=\"$option\" value=\"on\" $checked>");
}

# gform_option(<configfileoptionname>)
sub gform_option {
    my $option = $_[0];
    my $helpfile = $_[1];
    my $group = $_[3];
    my $label = $text{"conf_".$option};
    my $value = &readgroupconf($group,$option);
    if ($value eq 'on') {
        my $checked = 'checked=CHECKED';
    }
    print &ui_table_row(&hlink("$label", "$helpfile"), "<input type=\"checkbox\" name=\"$option\" value=\"on\" $checked>");
}

# form_radio(<configfileoptionname>, <onchangefunction>, <option 1>, <option 2>, ...)
sub form_radio {
    my @options = @_;
    my $option = $options[0];
    my $onchangefunction = $options[1];
    my $optionradio = "conf_".$option."_radio_";
    my $label = $text{"conf_".$option};
    my $helpfile = $options[0];
    my $value = &readconfigoption($option);
    my $radio = "blah";
    my $radioname;
    my $i = 1;
    my $i = 2;
    print "<tr><td>", &hlink("$label", "$helpfile"), "</td><td>";
    while($radio ne "") {
        $radio = $options[$i];
        if (length($radio) > 0) {
            print "<INPUT TYPE=RADIO NAME=\"$option\" VALUE=\"$radio\" ONCHANGE=\"$onchangefunction\"";
            if ($radio eq $value) {
                print " checked=\"checked\"";
            }
            $radioname = $optionradio . "$i";
            print "> $radio = $text{$radioname}<BR>";
#            print &ui_table_row(&hlink("$label", "$helpfile"), "<input type=\"radio\" name=\"$option\" value=\"$radio\" onchange=\"$onchangefunction\" $checked> $radio = $text{$radioname}");
        }
        $i++;
    }
    print "</td></tr>\n";
}

sub form_file {
    my $option = $_[0];
    my $fileref = &read_file_lines($option);
    my $line;
    print "<INPUT TYPE=HIDDEN NAME=\"filename\" VALUE=\"$option\">";
    print "<TEXTAREA NAME=\"filecontents\" ROWS=30 COLS=80>";
    foreach $line (@$fileref) {
        print &html_escape($line)."\n";
    }
    print "</TEXTAREA>";
}

# restart_button()
# Returns HTML for a link to put in the top-right corner
# I stole this from the apache module
sub restart_button {
#  my $pidfile = "$config{'pid_file'}";
  if ($access{'start'}) {
    if (&check_pid_file($config{'pid_file'})) {
        $rv = "<a href=\"status.cgi?action=restart\">$text{'header_restartdg'}</a><br>\n";
        $rv .= "<a href=\"status.cgi?action=regroup\">$text{'header_regroup'}</a><br>\n";
        $rv .= "<a href=\"status.cgi?action=stop\">$text{'header_stopdg'}</a><br>\n";
    } else {
        $rv = "<a href=\"status.cgi?action=start\">$text{'header_startdg'}</a><br>\n";
    }
    return $rv;
  }
}

sub dgprocess {
  my $action = $_[0];
  if ($access{$action}) {
  # You are authorized to perform the action
    if ($action eq "start") {
      if ($config{'start_cmd'}) {;
        $cmd = "$config{'start_cmd'}";
      } else {
        $cmd = "$config{'binary_file'}";
      }
    } elsif ($action eq "stop") {
      if ($config{'stop_cmd'}) {
        $cmd = "$config{'stop_cmd'}";
      } else {
        $cmd = "pkill dansguardian";
      }
    } elsif ($action eq "restart") {
      if ($config{'restart_cmd'}) {
        $cmd = "$config{'restart_cmd'}";
      } elsif ($config{'restart_type'} eq "1") {
          $cmd = "$config{'binary_file'} -r";
      } else {
          $cmd = "pkill dansguardian\; sleep 3\; $config{'binary_file'}";
      }
    } elsif ($action eq "regroup") {
      $cmd = "$config{'binary_file'} -g";
    } elsif ($action eq "status") {
      $cmd = "$config{'binary_file'} -s";
    }
  } else {
  # You are not authorized to perform the action
    print "<p>$text{'index_notauth'}\n";
    &ui_print_footer("index.cgi", $text{'index_return'});
    exit;
  }
  # Now we run the command, and display output
  $temp = &tempname();
  $rv = &system_logged("$cmd >$temp 2>&1 </dev/null");
  $out = `cat $temp`;
  unlink($temp);
  &reset_environment();
  print &ui_table_start($cmd, undef, 1);
  if ($out) { print &ui_table_row($out); } else { print &ui_table_row($text{'index_done'}) };
  if ($action eq "status") {
    print &ui_table_row($text{'index_childproc'}.": ".&find_byname(dansguardian));
    foreach (&find_byname(dansguardian)) {
      $childprocs .= " ".$_;
    }
    print &ui_table_row($text{'index_childproclist'}.": ".$childprocs);
  }
  print &ui_table_end();
}

sub loadwebjslib {
  print "<script type=text/javascript>\n";
  open(JS,"dgweblib.js");
  while ($line = <JS>) {
    print $line;
  }
  close(JS);
  print "</script>\n";
}
