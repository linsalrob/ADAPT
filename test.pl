#!/usr/bin/perl

use strict;
use warnings;
use DBConfig;
use ADAPTConfig;
#use Time::localtime;
use MIME::Lite::TT::HTML;
use Data::Dumper;

$| = 1; # Do not buffer output

&runScripts();

######################################################################

sub runScripts {
    my $cmd;

    #update with Entrez data from genome database
    $cmd = PERL_PATH."perl -e \'print STDERR \"test0rn\n\";\'"; #use 7 for last 7 days
    &addToLogFile('"'.$cmd."\" (update database with Entrez Genomes data)");
#    &systemCall($cmd);

    #backup MySQL database "adapt"
    my $day_of_year = (localtime(time()))[7];
    my $week_of_year = int($day_of_year / 7);
    #backup into same file every two weeks, to keep a two week update
    my $dump = '/var/backup/adaptdump'.($week_of_year % 2 ? '_1' : '_2').'.sql';
    $cmd = '/usr/bin/mysqldump --opt --flush-logs --user=adaptuser adapt > '.$dump.'; /usr/bin/gzip -f '.$dump;
    &addToLogFile('"'.$cmd.'" (backup MySQL database adapt before updating)');
#    &systemCall($cmd);

    #send email of update status
    my %tparams; 
    $tparams{time} = sprintf("%02d/%02d/%04d %02d:%02d:%02d",sub {($_[4]+1,$_[3],$_[5]+1900,$_[2],$_[1],$_[0])}->(localtime));
    $tparams{status}  = 'ok';
    my %options; 
    $options{INCLUDE_PATH} = TT_FILES; 
    my $msg = MIME::Lite::TT::HTML->new(
	TimeZone    => 'America/Los_Angeles',
	From        => 'ADAPTdb@update.done',
	To          => MAILTO,
#	Cc          => undef,
	Subject     => '[ADAPTdb] Automatic update status report', 
	Template    => {
	    text    =>  'update.txt.tt',
	    html    =>  'update.html.tt',
	},
	TmplOptions =>  \%options, 
	TmplParams  =>  \%tparams, 
	); 
    &addToLogFile('Send email with update report');
    $msg->send(); 
}


sub addToLogFile {
    my $string = shift;
    my $log = UPDATEDB_LOG;
    &checkLogFile($log);
    my $time = sprintf("[%02d/%02d/%04d %02d:%02d:%02d]",sub {($_[4]+1,$_[3],$_[5]+1900,$_[2],$_[1],$_[0])}->(localtime));
    open(LOG,">>$log") or die "ERROR: could not open file $log: $!\n";
    print LOG $time." run command: ".$string."\n";
    close(LOG);
}

sub systemCall {
    my $cmd = shift;
    my $log = UPDATEDB_LOG;
    &checkLogFile($log);
    my $time = time();
    system($cmd." 0<".DEV_NULL." >>$log 2>&1") == 0 or die "ERROR: system call failed: $?";
    &addToLogFile("...done ".&formatTime(time()-$time));
}

sub checkLogFile {
    my $errorlog = shift;
    if(defined $errorlog) {
	unless(-e "$errorlog") {
	    open(LOG,">$errorlog") or die "ERROR: could not create file $errorlog: $!\n";
	    close(LOG);
	}
    }
}

sub formatTime {
    my $secs = shift;
    my $hours = int($secs/3600);
    my $minutes = int(($secs-$hours*3600)/60);
    my $seconds = $secs-$hours*3600-$minutes*60;
    return "[".$hours."h ".$minutes."min ".$seconds."sec]";
}
