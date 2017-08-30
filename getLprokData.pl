#!/usr/bin/perl

use strict;
use warnings;
use DBConfig;
use LWP::Simple;
use DBI;
use Data::Dumper;

$| = 1; # Do not buffer output
&run();

#######################################################

sub run {
    my $time = time();

    &printHead('Get lproks file');
    my $content = &getFile(LPROKS);
    &printFoot(\$time);

    &printHead('Parse lproks file');
    my $data = &parseContent($content);
    &printFoot(\$time);

    &printHead('Add data to database');
    &addToDatabase($data);
    &printFoot(\$time);
}

sub printHead {
    my $string = shift;
    print "+".("-"x(WIDTH_PRINT-1))."\n\| ".$string."...\n+".("-"x(WIDTH_PRINT-1))."\n";
}

sub printFoot {
    my $time = shift;
    print "|\n| ...done. ".&formatTime(time()-$$time)."\n" if($time);
    print "+".("-"x(WIDTH_PRINT-1))."\n\n";
    $$time = time();
}

sub formatTime {
    my $secs = shift;
    my $hours = int($secs/3600);
    my $minutes = int(($secs-$hours*3600)/60);
    my $seconds = $secs-$hours*3600-$minutes*60;
    return "[".$hours."h ".$minutes."min ".$seconds."sec]";
}

sub getFile {
    my $url = shift;
    my $content = get($url);
    print "ERROR: Could not get: $url --> try to use local file\n" unless(defined $content);
    unless(defined $content) {
	open(IN,"<lproks.txt") or print "ERROR: Could not open local lproks.txt file: $! \n";
	my @tmp = <IN>;
	$content = join("",@tmp);
	close(IN);
    }
    return $content;
}

sub parseContent {
    my $content = shift;
    my @data;
    my @lines = split(/[\r\n]+/,$content);
    foreach(@lines) {
	next if(/^\#/);
	my @values = split(/\t/,$_);
	push(@data,[$values[2],$values[18],$values[14]]) if($values[18] && $values[18] ne ''); #[name,pathogenic,oxygen req.]
    }
    return \@data;    
}

sub addToDatabase {
    my $data = shift;
    my $dsn = "DBI:mysql:database=".MYSQL_DB.";host=".MYSQL_HOST.";port=".MYSQL_PORT;
    my $dbh = DBI->connect($dsn,MYSQL_USER,'',
			   {
#			       RaiseError => 1,
			       AutoCommit => 1
			   });
    my ($stm,$id,@where);
    
    #add pathogenicity to organisms in database
    foreach(@$data) {
	my $name = $_->[0];
	my $pathogenic = $_->[1];
	$stm = 'SELECT id,pathogenic_id FROM organism WHERE name='.$dbh->quote($name);
	$id = $dbh->selectrow_arrayref($stm);
	my ($organism_id,$pathogenic_id);
	if($id) {
	    $organism_id = $id->[0];
	    $pathogenic_id = $id->[1];
	    $stm = 'SELECT kind FROM pathogenic WHERE id='.$pathogenic_id;
	    my $patho = $dbh->selectrow_arrayref($stm);
	    my $checktargets = 0;
	    if($pathogenic && $patho->[0] ne 'unknown') {
		print "| pathogenicity exists (old:".$patho->[0]." new:$pathogenic)\n";
		$checktargets = 1 if($patho->[0] eq 'pathogenic');
	    } elsif($pathogenic eq 'No') {
		$stm = 'SELECT id FROM pathogenic WHERE kind=\'nonpathogenic\'';
		my $pathoid = $dbh->selectrow_arrayref($stm);
		$dbh->do('UPDATE organism SET pathogenic_id='.$pathoid->[0].' WHERE id='.$organism_id);
		print "| updated pathogenicity\n";
	    } else {
		$stm = 'SELECT id FROM pathogenic WHERE kind=\'pathogenic\'';
		my $pathoid = $dbh->selectrow_arrayref($stm);
		$dbh->do('UPDATE organism SET pathogenic_id='.$pathoid->[0].' WHERE id='.$organism_id);
		print "| updated pathogenicity\n";
		$checktargets = 1;
	    }
	    if($checktargets) {
		my @targets = split(/\,\s/,$pathogenic);
		my @ids;
		foreach my $target (@targets) {
		    #check target table
		    $stm = 'SELECT id FROM target WHERE name='.$dbh->quote($target);
		    my $target_id = $dbh->selectrow_arrayref($stm);
		    if($target_id) {
			push(@ids,$target_id->[0]);
			print "| target exists\n";
		    } else { #add if not exist yet
			$dbh->do('INSERT INTO target (name) VALUES ('.$dbh->quote($target).')');
			$target_id = $dbh->last_insert_id('%','adapt','target','id');
			push(@ids,$target_id);
			print "| added new target\n";
		    }
		}
		#insert into organism_target table
		foreach my $target_id (@ids) {
                    #check organism_target table
		    $stm = 'SELECT organism_id FROM organism_target WHERE organism_id='.$organism_id.' AND target_id='.$target_id;
		    my $organism_target_id = $dbh->selectrow_arrayref($stm);
		    if($organism_target_id) {
			print "| organism_target exists\n";
		    } else { #add if not exist yet
			$dbh->do('INSERT INTO organism_target (organism_id,target_id) VALUES ('.$organism_id.','.$target_id.')');
			print "| added new organism_target\n";
		    }
		}
	    }
	} else {
#	    print "| organism not found\n";
	}
    }
    
    $dbh->disconnect();
}
