#!/usr/bin/perl

use strict;
use warnings;
use DBConfig;
#use Data::Dumper;
use LWP::Simple;
use DBI;

$| = 1; # Do not buffer output
&run($ARGV[0]);

###########################################################

sub run {
    my $reldate = shift;
    if($reldate || $reldate == 0) {
	die "ERROR: reldate value is not a number: $reldate\n"  unless($reldate =~ /^\d+$/);
    } else {
	$reldate = RELDATE;
    }
    my $time = time();

    &printHead('Run ESEARCH');
    my ($count,$queryKey,$webEnv) = &search(EUTILS,SEARCH_DB1,SEARCH_TERM,$reldate);
    print "| Search for files updated during the last ".$reldate." days\n";
    print "| Number of files to fetch: ".$count."\n";
    &printFoot(\$time);
    
#    &printHead('Run EFETCH');
#    my $filenames = &fetch(EUTILS,SEARCH_DB1,$count,$queryKey,$webEnv,NCBI_TOOLNAME,NCBI_SLEEP);
#    &printFoot(\$time);
    
#    &printHead('Process GBK files');
#    &processFiles($filenames);
#    &processFiles();
#    &printFoot(\$time);
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

sub search {
    my ($utils,$db,$term,$reldate) = @_;
    my $esearch = $utils.'esearch.fcgi?retmax=1&usehistory=y&datetype=mdat'.($reldate==0?'':'&reldate='.$reldate).'&db='.$db.'&term='.$term;
#    print "ESEARCH QUERY:\n".$esearch."\n";
    my $result = get($esearch);
    $result =~ m|<Count>(\d+)</Count>.*<QueryKey>(\d+)</QueryKey>.*<WebEnv>(\S+)</WebEnv>|s;
    return ($1,$2,$3); #count,querykey,webenv
}

sub fetch {
    my ($utils,$db,$count,$queryKey,$webEnv,$tool,$sleep) = @_;
    my @filenames = ();
    my $efetch = $utils.'efetch.fcgi?db='.$db.'&query_key='.$queryKey.'&WebEnv='.$webEnv.'&retmode=text&tool='.$tool;
    my $width  = length($count)*2+3;
    my $retmax = 1;
    for(my $retstart=0;$retstart<$count;$retstart+=$retmax) {
	sleep($sleep);
#	print "EFETCH QUERY:\n".$efetch.'&rettype=acc&retstart='.$retstart.'&retmax='.$retmax."\n";
	my $acc = get($efetch.'&rettype=acc&retstart='.$retstart.'&retmax='.$retmax);
	$acc =~ s/(.*)\..*/$1/g;
	$acc =~ s/[\r\n]//g;
	printf("| %*s".$acc."\n",$width,($retstart+1)."/".$count.": ");
	unless($acc =~ m/^NC\_/i) {
	    print "|"." "x$width." not a _N_ucleotide _C_hromosome file\n";
	    next;
	}
	my $file = GBK_GENOME.$acc.".gbk";
	push(@filenames,$file);
	if(-e "$file") {
	    #TODO: how to deal with existing files? make backup copy under different name and create new one und current name?
	    print "|"." "x$width." WARNING: gbk file already exists -> skip fetching\n";
	} else {
	    sleep($sleep);
#	    print "EFETCH QUERY:\n".$efetch.'&rettype=gbwithparts&retstart='.$retstart.'&retmax='.$retmax."\n";
	    my $gbk = get($efetch.'&rettype=gbwithparts&retstart='.$retstart.'&retmax='.$retmax);
	    open(GBK,">$file") or die "ERROR: could not create gbk file: $!";
	    print GBK $gbk;
	    close(GBK);
	    print "|"." "x$width." done\n";
	}
    }
    return \@filenames;
}


sub processFiles {
    my $filenames = shift;
    
#    my @files = <c:/gbk_files/genome/NC_*.gbk>;
#    $filenames = \@files;
#    $filenames = ['c:/gbk_files/NC_006958.gbk'];

    my $count = scalar(@$filenames);
    my $width  = length($count)*2+2;
    my $counter = 1;
    my @notfound;
    foreach my $file (@$filenames) {
	printf("|\n| [%*s \n",$width,($counter++)."/".$count."]");
	print "|  $file: ";
	my ($status,$data) = &parseGbkFile($file);
	(my $acc = $file) =~ s/^.*[\/](.*)\.gbk$/$1/;
	if($status) {
	    print "found 16S and 23S rRNA genes\n";
	    &addToDatabase($data) if($data);
	} else {
	    print "could not find 16S and 23S rRNA genes\n";
	    push(@notfound,$acc);
	}
#	sleep(0.1); #otherwise perl could produce error and die
    }
    print "|\n| nothing found for accession: ".join(", ",@notfound)."\n" if(@notfound);
}

sub convertGbkDate {
    my $gbkdate = shift;
    my %month = (JAN=>'01',
		 FEB=>'02',
		 MAR=>'03',
		 APR=>'04',
		 MAY=>'05',
		 JUN=>'06',
		 JUL=>'07',
		 AUG=>'08',
		 SEP=>'09',
		 OCT=>'10',
		 NOV=>'11',
		 DEC=>'12');
    my @date = split(/\-/,$gbkdate);
    $date[1] = $month{$date[1]};
    return join("-",reverse(@date));
}

sub parseGbkFile {
    my $file = shift;    
    open(GBK,"<$file") or die "could not open gbk file $file: $!";
    my @data = <GBK>;
    close(GBK);
    #looking for 16S and 23S rRNA
    if((grep(/16S[\s\w]*ribosomal RNA/gi,@data) && 
	 grep(/[^\-]23S[\s\w]*ribosomal RNA/gi,@data)) || 
	(grep(/16S\s{0,1}rRNA[^\-^\;^\/]/gi,@data) && 
	 grep(/[^\-^\/]23S\s{0,1}rRNA/gi,@data))) {
#    if(grep(/16S ribosomal RNA/gi,@data) && grep(/23S ribosomal RNA/gi,@data)) {
	my ($date,$acc,$gi,$orgn,$taxon,$ref,$rrna,$gene,@r16S,@r23S,$origin,$seq,$strain,$subsp,$taxonid);
	foreach(@data) {
	    if(/^LOCUS\s{7}.*(\d{2}\-\w{3}\-\d{4})[\n\r]+$/) {
		$date = &convertGbkDate($1);
	    } elsif(/^\s{21}\/strain\=\"(.*)\"[\n\r]+$/) {
		$strain = $1;
	    } elsif(/^\s{21}\/sub\_species\=\"(.*)\"[\n\r]+$/) {
		$subsp = $1;
	    } elsif(/^\s{21}\/db\_xref\=\"taxon\:(.*)\"[\n\r]+$/) {
		$taxonid = $1;
	    } elsif(/^ACCESSION\s{3}(\S*)[\s\n\r]/) {
		$acc = $1;
	    } elsif(/^VERSION\s{5}.*\s+GI\:(\d+)[\s\r\n]/) {
		$gi = $1;
	    } elsif(/^\s{2}ORGANISM\s{2}(.*)[\n\r]+$/) {
		$orgn = $1;
	    } elsif($orgn && !$ref && /^\s{12}(.*)[\n\r]+$/) {
		$taxon .= $1;
	    } elsif(/^REFERENCE\s{3}1\s+/) {
		$ref = 1;
		$taxon =~ s/\;\s/\;/g;
		$taxon =~ s/\.//g;
	    } elsif(/^\s{5}rRNA\s{12}(.*)[\n\r]+$/) {
		$rrna = $1;
		$rrna =~ s/[\<\>]//g;
		$gene = 0;
	    } elsif(/^\s{5}gene\s{12}.*[\n\r]+$/) {
		$gene = 1;
	    } elsif(!$gene && !/\s+and[\s\n]+/g && (/(\d{2})S.*ribosomal RNA/g || /(\d{2})S\s{0,1}rRNA/g || /ribosomal RNA\-(\d{2})S/g) && $rrna) {
		push(@r16S,$rrna) if($1 == 16);
		push(@r23S,$rrna) if($1 == 23);
		$rrna = undef;
#	    } elsif(!$gene && /16S ribosomal RNA/g && $rrna) {
#		push(@r16S,$rrna);
#		$rrna = undef;
#	    } elsif(!$gene && /23S ribosomal RNA/g && $rrna) {
#		push(@r23S,$rrna);
#		$rrna = undef;
	    } elsif(/^ORIGIN\s*[\n\r]$/) {
		$origin = 1;
	    } elsif($origin && /^\s+\d+\s(.*)[\n\r]+$/) {
		$seq .= $1;
	    }
	}
	$seq =~ s/\s//g;
	$orgn .= ($subsp?($subsp=~/\s/g?' ':' subsp. ').$subsp:'').(($strain && $orgn!~/$strain/g)?' '.$strain:'');
	#get ITS, 16S and 23S data
	my %data = (taxon => $taxon,
		    taxid => $taxonid,
		    accession => $acc,
		    organism => $orgn,
		    creation_date => $date,
		    gi => $gi);
	my $good = &checkSeqPairs(\@r16S,\@r23S);
	my $count = 1;
	foreach(@$good) {
	    my $strand   = $_->[0];
	    my $kind1    = $_->[1];
	    my $start1   = $_->[2];
	    my $stop1    = $_->[3];
	    my $kind2    = $_->[4];
	    my $start2   = $_->[5];
	    my $stop2    = $_->[6];
	    my $startITS = $stop1+1;
	    my $stopITS  = $start2-1;
	    my $sequence1   = substr($seq,$start1-1,$stop1-$start1+1);
	    my $sequence2   = substr($seq,$start2-1,$stop2-$start2+1);
	    my $sequenceITS = substr($seq,$startITS-1,$stopITS-$startITS+1);
	    $data{region}->{$count++} = {$kind1 => {strand => $strand,
						    startpos => ($strand?$start1:$stop1),
						    stoppos => ($strand?$stop1:$start1),
						    sequence => ($strand?$sequence1:&revcomp($sequence1)),
						    length => length($sequence1)},
					 $kind2 => {strand => $strand,
						    startpos => ($strand?$start2:$stop2),
						    stoppos => ($strand?$stop2:$start2),
						    sequence => ($strand?$sequence2:&revcomp($sequence2)),
						    length => length($sequence2)},
					 'ITS' => {strand => $strand,
						   startpos => ($strand?$startITS:$stopITS),
						   stoppos => ($strand?$stopITS:$startITS),
						   sequence => ($strand?$sequenceITS:&revcomp($sequenceITS)),
						   length => length($sequenceITS)}};
	}
	return (exists $data{region}?(1,\%data):0);
    } else {
	return 0;
    }
}

sub checkSeqPairs {
    my ($r16S,$r23S) = @_;
    my %pos;
    foreach(@$r16S) {
	my $strand = ($_ =~ /^complement/ ? 0 : 1);
	$_ =~ /(\d+)\.{2}(\d+)/;
	my $start = $1;
	my $stop  = $2;
	$pos{$strand}->{$start} = {kind => '16S',
				   stop => $stop};
    }
    foreach(@$r23S) {
	my $strand = ($_ =~ /^complement/ ? 0 : 1);
	$_ =~ /(\d+)\.{2}(\d+)/;
	my $start = $1;
	my $stop  = $2;
	$pos{$strand}->{$start} = {kind => '23S',
				   stop => $stop};
    }
    my @good;
    foreach my $strand (keys %pos) {
	my @sort = sort {$a<=>$b} keys %{$pos{$strand}};
	next unless(scalar(@sort)>1);
	for(0..(scalar(@sort)-2)) {
	    my $dist = $sort[$_+1]-$sort[$_];
	    push(@good,[$strand,
			$pos{$strand}->{$sort[$_]}->{kind},
			$sort[$_],
			$pos{$strand}->{$sort[$_]}->{stop},
			$pos{$strand}->{$sort[$_+1]}->{kind},
			$sort[$_+1],
			$pos{$strand}->{$sort[$_+1]}->{stop}]) 
		if($dist<MAX_LENGTH && 
		   $pos{$strand}->{$sort[$_]}->{kind} ne $pos{$strand}->{$sort[$_+1]}->{kind});
	}
    }
    return \@good;
}

sub revcomp {
    my $seq = shift;
    $seq = reverse($seq);
    $seq =~ tr/acgt/tgca/;
    return $seq;
}

sub addToDatabase {
    my $data = shift;
    my $dsn = "DBI:mysql:database=mysql;host=".MYSQL_HOST.";port=".MYSQL_PORT;
    my $dbh = DBI->connect($dsn,MYSQL_USER,MYSQL_PW,
			   {RaiseError => 1});
    $dbh->do('USE '.MYSQL_DB);
    my ($stm,$id,@where);
#    sleep(0.1); #perl winxp mysql issue

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
	$taxon_id = $dbh->last_insert_id('%','adapt','taxon','id');
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
	$organism_id = $dbh->last_insert_id('%','adapt','organism','id');
	print "|   added new organism\n";
    }

    #input entry
    my $acc = $data->{accession};
    my $gi = $data->{gi};
    my $date = $data->{creation_date};
    $stm = 'SELECT id FROM entry WHERE accession='.$dbh->quote($acc).' AND gi='.$dbh->quote($gi);
    $id = $dbh->selectrow_arrayref($stm);
    my $entry_id;
    if($id) {
	$entry_id = $id->[0];
	$stm = 'SELECT creation_date FROM entry WHERE id='.$dbh->quote($entry_id);
	my $creation_date = $dbh->selectrow_arrayref($stm);
	if($creation_date && !&compareDates($date,$creation_date->[0])) {
	    print "|   entry exists\n";
	} else {
	    $dbh->do('UPDATE entry SET creation_date='.$dbh->quote($date).'WHERE id='.$entry_id);
	    print "|   updated entry creation_date\n";
	}
    } else {
	$stm = 'SELECT id FROM source WHERE name=\'Entrez Genomes\'';
	$id = $dbh->selectrow_arrayref($stm);
	my $source_id = $id->[0];
	$dbh->do('INSERT INTO entry (accession,gi,creation_date,source_id,organism_id) VALUES ('.$dbh->quote($acc).','.$dbh->quote($gi).','.$dbh->quote($date).','.$source_id.','.$organism_id.')');
	$entry_id = $dbh->last_insert_id('%','adapt','entry','id');
	print "|   added new entry\n";
    }

    #input region
    my $region = $data->{region};
    foreach my $number (keys %$region) {
	while(my ($kind,$hash) = each(%{$region->{$number}})) {
	    @where = map {$_.'='.$dbh->quote($hash->{$_})} keys %$hash;
	    $stm = 'SELECT id FROM region WHERE '.join(" AND ",@where).' AND number='.$number.' AND kind='.$dbh->quote($kind).' AND entry_id='.$entry_id;
	    $id = $dbh->selectrow_arrayref($stm);
	    if($id) {
		print "|   $kind region exists\n";
	    } else {
		my @values = map {$hash->{$_}} sort keys %$hash;
		push(@values,($number,$kind,$entry_id));
		@values = map {$dbh->quote($_)} @values;
		$dbh->do('INSERT INTO region ('.join(",",((sort keys %$hash),'number','kind','entry_id')).') VALUES ('.join(",",@values).')');
		print "|   added new $kind region\n";
	    }	    
	}
    }
#    sleep(0.01);
    $dbh->disconnect();
    return 1;
}

sub getTaxonFromString {
    my $string = shift;
    my @columns = ('kingdom','phylum');
    my @values = split(/\;/,$string);
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

sub compareDates {
    my ($datenew,$dateold) = @_;
    return 0 if($datenew eq $dateold);
    $datenew =~ s/\-//g;
    $dateold =~ s/\-//g;
    return ($datenew>$dateold?1:0);
}
