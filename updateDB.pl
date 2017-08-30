#!/usr/bin/perl

use strict;
use warnings;
use DBConfig;
use ADAPTConfig;
use MIME::Lite::TT::HTML;
#use Data::Dumper;

$| = 1; # Do not buffer output

&runScripts();

######################################################################

sub runScripts {
    my ($cmd,@warn,$warnings);

    #clean/empty log file
    &cleanLogFile(UPDATEDB_LOG);

    #backup MySQL database "adapt"                                                                                                  
    my $day_of_year = (localtime(time()))[7];
    my $week_of_year = int($day_of_year / 7);
    #backup into same file every two weeks, to keep a two week update                                                               
    my $dump = '/var/backup/adaptdump'.($week_of_year % 2 ? '_1' : '_2').'.sql';
    $cmd = '/usr/bin/mysqldump --opt --flush-logs --user=adaptuser adapt > '.$dump.'; /usr/bin/gzip -f '.$dump;
    &addToLogFile('"'.$cmd.'" (backup MySQL database adapt before updating)');
    &systemCall($cmd);         
    
    #update with Entrez data from NCBI Genomes database
    $cmd = PERL_PATH."perl getNcbiGenomesData.pl 8"; #e.g. use 7 for last 7 days
    &addToLogFile('"'.$cmd."\" (update database with NCBI data using Entrez Genomes queries)");
    &systemCall($cmd);

    #update with data from SEED database
    $cmd = PERL_PATH."perl getSeedData.pl";
    &addToLogFile('"'.$cmd."\" (update database with SEED data from ".SEED_DATA_URL.")");
    &systemCall($cmd);

    #update with NCBI data from lproks file
    $cmd = PERL_PATH."perl getLprokData.pl";
    &addToLogFile('"'.$cmd."\" (update database with Lproks data)");
    &systemCall($cmd);

    #copy update logfile
    my $newlog = 'log/updateDB_'.time().'.log';
    system('cp '.UPDATEDB_LOG.' '.$newlog) == 0 or die "ERROR: system call failed: $?";
    @warn = `grep '^WARNING' $newlog`;
    $warnings = (scalar(@warn) == 0 ? 'none' : join("\n",@warn));
    
    #send email of update status                                                                                                    
    my %tparams;
    $tparams{time} = sprintf("%02d/%02d/%04d %02d:%02d:%02d",sub {($_[4]+1,$_[3],$_[5]+1900,$_[2],$_[1],$_[0])}->(localtime));
    $tparams{status}  = 'OK';
    $tparams{logfile} = $newlog;
    $tparams{version} = ADAPT;
    $tparams{warnings} = $warnings;
    my %options;
    $options{INCLUDE_PATH} = TT_FILES;
    my $msg = MIME::Lite::TT::HTML->new(
        TimeZone    => 'America/Los_Angeles',
        From        => 'ADAPTdb@update.done',
        To          => MAILTO,
#       Cc          => undef,                                                                                                       
        Subject     => '[ADAPTdb] Automatic update status report',
        Template    => {
            text    =>  'update.txt.tt',
            html    =>  'update.html.tt',
        },
        TmplOptions =>  \%options,
        TmplParams  =>  \%tparams,
        );
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

sub cleanLogFile {
    my $errorlog = shift;
    if(defined $errorlog) {
	open(LOG,">$errorlog") or die "ERROR: could not clean file $errorlog: $!\n";
	print LOG '';
	close(LOG);
    }
}

sub formatTime {
    my $secs = shift;
    my $hours = int($secs/3600);
    my $minutes = int(($secs-$hours*3600)/60);
    my $seconds = $secs-$hours*3600-$minutes*60;
    return "[".$hours."h ".$minutes."min ".$seconds."sec]";
}
