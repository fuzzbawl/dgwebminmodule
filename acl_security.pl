do 'dansguardian-lib.pl';

sub acl_security_form {
  # This is for the main menu 
  foreach $s ('start', 'stop', 'restart', 'regroup', 'status', 'logs', 'editconf', 'editfiles', 'groups', 'autorestart') {
    printf "<tr><td><b>%s</b></td>\n", $text{"index_${s}"};
    printf "<td><input type=radio name=%s value=1 %s> %s\n", $s, $_[0]->{$s} ? 'checked' : '', $text{'yes'};
    printf "<td><input type=radio name=%s value=0 %s> %s</td></tr>\n", $s, $_[0]->{$s} ? '' : 'checked', $text{'no'};
  }

  # This array populates an html select list with the file names
  print "<tr><td><b>$text{'acl_editfiles'}</b></td>\n";
  print "<td><select name=files multiple size=6>\n";
  foreach $s ('exceptionurllist', 'bannedurllist', 'exceptionuserlist', 'banneduserlist', 'exceptionphraselist', 'bannedphraselist', 'exceptionsitelist', 'bannedsitelist', 'exceptioniplist', 'bannediplist', 'weightedphraselist', 'bannedextensionlist', 'bannedmimetypelist', 'bannedregexpurllist', 'pics', 'contentregexplist', 'messages') {
    printf "<option value=%s %s>%s\n", $s, $_[0]->{$s} ? 'selected' : '', $text{"conf_${s}"};
  }

}

sub acl_security_save {
  $_[0]->{'start'} = $in{'start'};
  $_[0]->{'stop'} = $in{'stop'};
  $_[0]->{'restart'} = $in{'restart'};
  $_[0]->{'regroup'} = $in{'regroup'};
  $_[0]->{'status'} = $in{'status'};
  $_[0]->{'logs'} = $in{'logs'};
  $_[0]->{'editconf'} = $in{'editconf'};
  $_[0]->{'editfiles'} = $in{'editfiles'};
  $_[0]->{'groups'} = $in{'groups'};
  $_[0]->{'autorestart'} = $in{'autorestart'};

  map { $files{$_} = 1 } split(/\0/, $in{'files'});
  foreach $s ('exceptionurllist', 'bannedurllist', 'exceptionuserlist', 'banneduserlist', 'exceptionphraselist', 'bannedphraselist', 'exceptionsitelist', 'bannedsitelist', 'exceptioniplist', 'bannediplist', 'weightedphraselist', 'bannedextensionlist', 'bannedmimetypelist', 'bannedregexpurllist', 'pics', 'contentregexplist', 'messages') {
    $_[0]->{$s} = $files{$s};
  }
}
