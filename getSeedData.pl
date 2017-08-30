#!/usr/bin/perl

use strict;
use warnings;
use DBConfig;
use LWP::Simple;
use DBI;
#use Data::Dumper;

$| = 1; # Do not buffer output
&run();

###########################################################

sub run {
    my $time = time();

    &printHead('Fetch SEED content');
    my $content = &fetchData(SEED_DATA_URL);
    &printFoot(\$time);

    if($content) {
	&printHead('Process SEED content');
	my $data = &processContent($content);
	&printFoot(\$time);
	
	&printHead('Parse SEED data');
	my $hash = &parseData($data);
	&printFoot(\$time);
	
	&printHead('Add data to Database');
	my $status = &addToDatabase($hash);
	&printFoot(\$time);
    }
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

sub fetchData {
    my $url = shift;
    my $content = get($url);
    print "ERROR/WARNING: Could not get: $url\n" unless(defined $content);
    return $content;

#     my $content;
#     my $count = 30000;
#     open(IN,"<ribo4.txt") or die "could not open test.txt: $! \n";
#     while(<IN>) {
# 	next unless($count-- > 0);
# 	$content .= $_;
	
#     }
#     close(IN);
#     return $content;
}

sub processContent {
    my $content = shift;
    my @data;
    my @lines = split(/[\r\n]+/,$content);
    foreach(@lines) {
	next if(/^\#/);
	my @values = split(/\t/,$_);
	push(@data,\@values) if(scalar(@values > 0));
    }
    return \@data;
}

sub parseData {
    my $data = shift;
    my %tmp;
    foreach my $values (@$data) {
	my ($id,$taxon,$orgn,$replace,$number,$contig,$start16S,$stop16S,$start23S,$stop23S,$length,$strand,$seq) = @$values;
	(my $taxonid = $id) =~ s/(\d+)\.\d+/$1/;
	my ($acc,$version) = split(/\./,$id);
	$tmp{$id} = {taxon => $taxon,
		     taxid => $taxonid,
		     accession => $id,
		     version => $version,
		     replace => $replace,
		     organism => $orgn} unless(exists $tmp{$id});
	$tmp{$id}->{contig}->{$contig}->{$number} = {strand => $strand,
						     start16S => $start16S,
						     stop16S => $stop16S,
						     start23S => $start23S,
						     stop23S => $stop23S,
						     sequence => $seq,
						     length => $length};
    }
    return \%tmp;
}

sub addToDatabase {
    my $datahash = shift;

    #connect to mysql database
    my $dsn = "DBI:mysql:database=".MYSQL_DB.";host=".MYSQL_HOST.";port=".MYSQL_PORT;
    my $dbh = DBI->connect($dsn,MYSQL_USER,'',
			   {
			       RaiseError => 1,
			       AutoCommit => 1
			   });
    my ($stm,$id,@where);

    #get source id
    $stm = 'SELECT id FROM source WHERE name=\'SEED\'';
    $id = $dbh->selectrow_arrayref($stm);
    my $source_id = $id->[0];

    #get all SEED accession numbers
    my @accessions;
    $stm = 'SELECT accession FROM entry WHERE source_id='.$source_id;
    $id = $dbh->selectcol_arrayref($stm);
    @accessions = @$id;

    #crosslink accessions and find acc to remove (not in DB anymore)
    my @remove;
    foreach(@accessions) {
	push(@remove,$_) unless(exists $datahash->{$_});
    }

    #remove deleted entries from ADAPTdb
    print "|\n| Remove ".(scalar(@remove) || 0)." entries from ADAPTdb that were deleted in SEED:".join(", ",@remove)."\n";
    if(@remove) {
	my $tmp_ids;
	$stm = 'SELECT id FROM entry WHERE '.join(" OR ",(map {'accession='.$_} @remove)).';';
	my $entry_ids = $dbh->selectall_hashref($stm,'id');

	#find organism entries to remove
	$stm = 'SELECT organism_id FROM entry WHERE '.join(" OR ",(map {'id='.$_} keys %$entry_ids)).';';
	my $organism_ids = $dbh->selectall_hashref($stm,'organism_id');
	$stm = 'SELECT organism_id,id FROM entry WHERE '.join(" OR ",(map {'organism_id='.$_} keys %$organism_ids)).';';
	$tmp_ids = $dbh->selectall_arrayref($stm);
	foreach(@$tmp_ids) {
	    delete $organism_ids->{$_->[0]} unless(exists $entry_ids->{$_->[1]});
	}

	#find taxon entries to remove
	$stm = 'SELECT taxon_id FROM organism WHERE '.join(" OR ",(map {'id='.$_} keys %$organism_ids)).';';
	my $taxon_ids = $dbh->selectall_hashref($stm,'taxon_id');
	$stm = 'SELECT taxon_id,id FROM organism WHERE '.join(" OR ",(map {'taxon_id='.$_} keys %$taxon_ids)).';';
	$tmp_ids = $dbh->selectall_arrayref($stm);
	foreach(@$tmp_ids) {
	    delete $taxon_ids->{$_->[0]} unless(exists $organism_ids->{$_->[1]});
	}

	#find region entries to remove
	$stm = 'SELECT region_id FROM region_entry WHERE '.join(" OR ",(map {'entry_id='.$_} keys %$entry_ids)).';';
	my $region_ids = $dbh->selectall_hashref($stm,'region_id');
	$stm = 'SELECT region_id,entry_id FROM region_entry WHERE '.join(" OR ",(map {'region_id='.$_} keys %$region_ids)).';';
	$tmp_ids = $dbh->selectall_arrayref($stm);
	foreach(@$tmp_ids) {
	    delete $region_ids->{$_->[0]} unless(exists $entry_ids->{$_->[1]});
	}

	#remove entries from database
	print "|   remove entry entries: ".join(", ",(sort {$a <=> $b} keys %$entry_ids))."\n";
	$dbh->do('DELETE FROM entry WHERE '.join(" OR ",(map {'id='.$_} keys %$entry_ids)));
	print "|   remove organism entries: ".join(", ",(sort {$a <=> $b} keys %$organism_ids))."\n";
	$dbh->do('DELETE FROM organism WHERE '.join(" OR ",(map {'id='.$_} keys %$organism_ids)));
	print "|   remove taxon entries: ".join(", ",(sort {$a <=> $b} keys %$taxon_ids))."\n";
	$dbh->do('DELETE FROM taxon WHERE '.join(" OR ",(map {'id='.$_} keys %$taxon_ids)));
	print "|   remove region entries: ".join(", ",(sort {$a <=> $b} keys %$region_ids))."\n";
	$dbh->do('DELETE FROM region WHERE '.join(" OR ",(map {'id='.$_} keys %$region_ids)));
    }

    #skip entries already in ADAPTdb
    my @skip;
    foreach my $id (@accessions) {
	if(exists $datahash->{$id}) {
	    push(@skip,$id);
	    delete $datahash->{$id};
	}
    }
    print "|\n| Skip ".scalar(@skip)." entries already in database: ".join(", ",@skip)."\n";

    #loop through hash and add new entries
    my $outoff = scalar(keys %$datahash);
    my $count = 1;
    print "|\n| Process ".$outoff." new entries:\n";
    foreach my $data (values %$datahash) {
	print "|\n|  Processing ".$count++."/$outoff: ".$data->{accession}."\n";

	#check if entry already exists
	my $acc = $data->{accession};
	my $ver = $data->{version};
	$stm = 'SELECT id FROM entry WHERE accession='.$dbh->quote($acc);
	$id = $dbh->selectrow_arrayref($stm);
	my ($entry_id);
	if($id) { #entry exists
	    $entry_id = $id->[0];
	    print "WARNING: found entry with same accession; something wrong here? [entry_id:".$entry_id."] --> do nothing\n";
	} else { #new entry
	    #input taxon
	    my $taxon = &getTaxonFromString($data->{taxon});
	    @where = map {$_.($taxon->{$_}eq'NULL'?' IS NULL':'='.$dbh->quote($taxon->{$_}))} keys %$taxon;
	    my @tmp = split(/\s/,$data->{organism});
	    push(@where,'genus='.$dbh->quote($tmp[0]));
	    push(@where,'species='.$dbh->quote($tmp[1]));
	    $stm = 'SELECT id FROM taxon WHERE '.join(" AND ",@where);
	    $id = $dbh->selectrow_arrayref($stm);
	    my $taxon_id;
	    if($id) {
		$taxon_id = $id->[0];
		print "|   taxon exists\n";
	    } else {
		my @values = map {$taxon->{$_}eq'NULL'?'NULL':$dbh->quote($taxon->{$_})} sort keys %$taxon;
		push(@values,$dbh->quote($tmp[0]));
		push(@values,$dbh->quote($tmp[1]));
		$dbh->do('INSERT INTO taxon ('.join(",",(sort keys %$taxon)).',genus,species) VALUES ('.join(",",@values).')');
		$taxon_id = $dbh->last_insert_id('%',MYSQL_DB,'taxon','id');
		print "|   added new taxon\n";
	    }
	    
	    #input trophic
	    my $phylum = $taxon->{'phylum'} || 'unknown';
	    my $kingdom = $taxon->{'kingdom'};
	    my $trophic = exists PHYLA->{$kingdom}->{$phylum} ? ABBREVS->{PHYLA->{$kingdom}->{$phylum}} : 'unknown';
	    $stm = 'SELECT id FROM trophic WHERE kind='.$dbh->quote($trophic);
	    $id = $dbh->selectrow_arrayref($stm);
	    my $trophic_id;
	    if($id) {
		$trophic_id = $id->[0];
	    } else {
		print "WARNING: unknown trophic_id - set trophic as \'unknown\'\n";
		$stm = 'SELECT id FROM trophic WHERE kind=\'unknown\'';
		$id = $dbh->selectrow_arrayref($stm);
		$trophic_id = $id->[0];
	    }
	    
	    #input organism
	    my $orgn = $data->{organism};
	    $stm = 'SELECT id FROM organism WHERE name='.$dbh->quote($orgn);
	    $id = $dbh->selectrow_arrayref($stm);
	    my $organism_id;
	    if($id) {
		$organism_id = $id->[0];
		print "|   organism exists\n";
	    } else {
		$stm = 'SELECT id FROM pathogenic WHERE kind=\'unknown\'';
		$id = $dbh->selectrow_arrayref($stm);
		my $pathogenic_id = $id->[0];
		my $taxid = $data->{taxid};
		$dbh->do('INSERT INTO organism (name,taxid,taxon_id,trophic_id,pathogenic_id) VALUES ('.$dbh->quote($orgn).','.$dbh->quote($taxid).','.$taxon_id.','.$trophic_id.','.$pathogenic_id.')');
		$organism_id = $dbh->last_insert_id('%',MYSQL_DB,'organism','id');
		print "|   added new organism\n";
	    }

	    #input entry
	    my $linkout = 'genome=fig|'.$acc;
	    $dbh->do('INSERT INTO entry (accession,version,linkout,source_id,organism_id) VALUES ('.$dbh->quote($acc).','.$ver.','.$dbh->quote($linkout).','.$source_id.','.$organism_id.')');
	    $entry_id = $dbh->last_insert_id('%',MYSQL_DB,'entry','id');
	    print "|   added new entry\n";
	    
	    my ($length,$sequence,$region_id,$contig,$strand,$start16S,$stop16S,$start23S,$stop23S);
	    foreach my $contig (keys %{$data->{contig}}) {
		#input region
		foreach my $region (values %{$data->{contig}->{$contig}}) {
		    $sequence = $region->{sequence};
		    $length   = $region->{length};
		
		    #add value to region table
		    $stm = 'SELECT id FROM region WHERE length='.$length.' AND sequence='.$dbh->quote($sequence);
		    $id = $dbh->selectrow_arrayref($stm);
		    if($id) {
			print "|   region exists\n";
			$region_id = $id->[0];
		    } else {
			$dbh->do('INSERT INTO region (sequence,length) VALUES ('.join(",",$dbh->quote($sequence),$length).')');
			print "|   added new region\n";
			$region_id = $dbh->last_insert_id('%',MYSQL_DB,'region','id');
		    }
		    
		    #add value to organism_region table
		    $stm = 'SELECT region_id FROM organism_region WHERE region_id='.$region_id.' AND organism_id='.$organism_id;
		    $id = $dbh->selectrow_arrayref($stm);
		    if($id) {
			print "|   organism_region exists\n";
		    } else {
			$dbh->do('INSERT INTO organism_region (region_id,organism_id) VALUES ('.join(",",$region_id,$organism_id).')');
			print "|   added new organism_region\n";
		    }
		
		    #add value to region_entry table
		    $start16S = $region->{start16S};
		    $stop16S  = $region->{stop16S};
		    $start23S = $region->{start23S};
		    $stop23S  = $region->{stop23S};
		    $strand =   $region->{strand};
		    $stm = 'SELECT entry_id FROM region_entry WHERE region_id='.$region_id.' AND entry_id='.$entry_id.' AND contig='.$dbh->quote($contig).' AND strand='.$strand.' AND start16S='.$start16S.' AND stop16S='.$stop16S.' AND start23S='.$start23S.' AND stop23S='.$stop23S;
		    $id = $dbh->selectrow_arrayref($stm);
		    if($id) {
			print "|   region_entry exists\n";
		    } else {
			$dbh->do('INSERT INTO region_entry (contig,strand,start16S,stop16S,start23S,stop23S,region_id,entry_id) VALUES ('.join(",",$dbh->quote($contig),$strand,$start16S,$stop16S,$start23S,$stop23S,$region_id,$entry_id).')');
			print "|   added new region_entry\n";
		    }
		}
	    }
	}
    }
    $dbh->disconnect();
    return 1;
}

sub getTaxonFromString {
    my $string = shift;
    my @columns = ('kingdom','phylum');
    my @values = split(/\;\s*/,$string);
    my %taxon;
    foreach(@columns) {
	$taxon{$_} = @values ? shift(@values) : 'NULL';
    }
    my $phylum = $taxon{'phylum'};
    my $kingdom = $taxon{'kingdom'};
    if(exists PHYLA->{$kingdom}) {
	unless(exists PHYLA->{$kingdom}->{$phylum}) {
	    print "WARNING: phylum $phylum does not exist in taxonomy\n";
	    $taxon{'phylum'} = 'unknown';
	}
    } else {
	print "WARNING: kingdom $kingdom does not exist in taxonomy\n";
	$taxon{'kingdom'} = 'unknown';
	$taxon{'phylum'} = 'unknown';
    }
    return \%taxon;
}
