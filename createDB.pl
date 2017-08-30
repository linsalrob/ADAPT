#!/usr/bin/perl

use strict;
use warnings;
use DBConfig;
#use Data::Dumper;

$| = 1; # Do not buffer output

&runScripts();

######################################################################

sub runScripts {
    #create new mysql database
    my $cmd = PERL_PATH."perl createMysqlDB.pl";
    &addToLogFile($cmd." (create new mysql database)");
    &systemCall($cmd);

    #fill with Entrez data from genomes database
    $cmd = PERL_PATH."perl getNcbiGenomesData.pl 0"; #use 0 for all days
    &addToLogFile('"'.$cmd."\" (fill database with NCBI Genomes data of Bacteria and Archaea)");
    &systemCall($cmd);
   
    #fill with data from SEED database
    $cmd = PERL_PATH."perl getSeedData.pl"; #use 0 for all days
    &addToLogFile('"'.$cmd."\" (fill database with SEED data of Bacteria and Archaea)");
    &systemCall($cmd);

    #fill with NCBI data from lproks file
    $cmd = PERL_PATH."perl getLprokData.pl";
    &addToLogFile('"'.$cmd."\" (fill database with Lproks data)");
    &systemCall($cmd);

    #fill with data from RISSC
#    $cmd = PERL_PATH."perl getRisscData.pl";
#    &addToLogFile('"'.$cmd."\" (fill database with RISSC data)");
#    &systemCall($cmd);
}

sub addToLogFile {
    my $string = shift;
    my $log = CREATEDB_LOG;
    &checkLogFile($log);
    my $time = sprintf("[%02d/%02d/%04d %02d:%02d:%02d]",sub {($_[4]+1,$_[3],$_[5]+1900,$_[2],$_[1],$_[0])}->(localtime));
    open(LOG,">>$log") or die "ERROR: could not open file $log: $!\n";
    print LOG $time." run command: ".$string."\n";
    close(LOG);
}

sub systemCall {
    my $cmd = shift;
    my $log = CREATEDB_LOG;
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
