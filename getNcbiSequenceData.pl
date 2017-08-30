#!/usr/bin/perl

use strict;
use warnings;
use DBConfig;
use LWP::Simple;
use DBI;

use Data::Dumper;

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
    
    if($count > 0) {
	&printHead('Run EFETCH');
	my $filenames = &fetch(EUTILS,SEARCH_DB1,$count,$queryKey,$webEnv,NCBI_TOOLNAME,NCBI_SLEEP);
	&printFoot(\$time);
	
	&printHead('Process GBK files');
	&processFiles($filenames);
#       &processFiles();
	&printFoot(\$time);
    } else {
	print ">> NOTE: No new files to fetch and add.\n\n";
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

sub search {
    my ($utils,$db,$term,$reldate) = @_;
    my $esearch = $utils.'esearch.fcgi?retmax=0&usehistory=y&datetype=mdat'.($reldate==0?'':'&reldate='.$reldate).'&db='.$db.'&term='.$term;
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
	    open(GBK,">$file") or die "ERROR: could not create gbk file $file: $!";
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
    return join("",reverse(@date));
}

sub parseGbkFile {
    my $file = shift;    
    open(GBK,"<$file") or die "could not open gbk file $file: $!";
    my @data = <GBK>;
    close(GBK);
    my ($rrnas,$keep);
    #looking for 16S and 23S rRNA
    if((grep(/16S[\s\w]*ribosomal RNA/gi,@data) && 
	 grep(/[^\-]23S[\s\w]*ribosomal RNA/gi,@data)) || 
	(grep(/16S\s{0,1}rRNA[^\-^\;^\/]/gi,@data) && 
	 grep(/[^\-^\/]23S\s{0,1}rRNA/gi,@data))) {
#    if(grep(/16S ribosomal RNA/gi,@data) && grep(/23S ribosomal RNA/gi,@data)) {
	my ($date,$acc,$gi,$orgn,$taxon,$ref,$rrna,$gene,@r16S,@r23S,$origin,$seq,$strain,$subsp,$taxonid,$tmp);
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
		$tmp = $1;
		if($tmp =~ /\;/g) {
		    $taxon .= $tmp;
		} elsif(!$taxon) {
		    $orgn .= $tmp;
		}
	    } elsif(/^REFERENCE\s{3}1\s+/) {
		$ref = 1;
		$taxon =~ s/\;\s/\;/g;
		$taxon =~ s/\.//g;
	    } elsif(/^\s{5}rRNA\s{12}(.*)[\n\r]+$/i) {
		$rrna = $1;
		$rrna =~ s/[\<\>]//g;
		$gene = 0;
	    } elsif(/^\s{5}gene\s{12}.*[\n\r]+$/i) {
		$gene = 1;
	    } elsif(!$gene && !/\s+and[\s\n]+/g && (/(\d{2})S.*ribosomal RNA/ig || /(\d{2})S\s{0,1}rRNA/ig || /ribosomal RNA\-(\d{2})S/ig) && $rrna) {
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
	$orgn .= ($subsp ? ($subsp =~ /\s/g ? ' ' : ' subsp. ').$subsp : '').(($strain && $orgn !~ /$strain/g) ? ' '.$strain : '') if($orgn =~ /^\S+\s\S+$/);
	#get ITS, 16S and 23S data
	my %data = (taxon => $taxon,
		    taxid => $taxonid,
		    accession => $acc,
		    organism => $orgn,
		    creation_date => $date,
		    gi => $gi);
	$rrnas = &reformatData(\@r16S,\@r23S);
	$keep = &checkRegionPairs(&checkForOverlaps($rrnas)); #values: number,kind,start,stop,length,strand
	if($keep) {
	    foreach(@$keep) {
		#get seq (rest from keep array)
		my $regionseq = substr($seq,($_->[2]-1),$_->[4]);
		$regionseq = &revcomp($regionseq) unless($_->[5]);
		$data{region}->{$_->[0]}->{$_->[1]} = {strand => $_->[5],
						       startpos => $_->[2],
						       stoppos => $_->[3],
						       sequence => $regionseq,
						       length => $_->[4]};
	    }
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
	my $strand = ($_ =~ /^complement/ ? 0 : 1);  #forward 1 - reverse 0
	$_ =~ /(\d+)\.{2}(\d+)/;
	my $start = $1;
	my $stop  = $2;
	$pos{$strand}->{$start} = {kind => '16S',
				   stop => $stop};
    }
    foreach(@$r23S) {
	my $strand = ($_ =~ /^complement/ ? 0 : 1);  #forward 1 - reverse 0
	$_ =~ /(\d+)\.{2}(\d+)/;
	my $start = $1;
	my $stop  = $2;
	$pos{$strand}->{$start} = {kind => '23S',
				   stop => $stop};
    }
    my (@good,$kind1,$kind2,$dist);
    foreach my $strand (keys %pos) {
	if(scalar(keys %{$pos{$strand}})>1) {
	    my @sort = sort {$a<=>$b} keys %{$pos{$strand}};
	    for(0..(scalar(@sort)-2)) {
		$kind1 = $pos{$strand}->{$sort[$_]}->{kind};
		$kind2 = $pos{$strand}->{$sort[$_+1]}->{kind};
		next unless(($strand && ($kind1 eq '16S' && $kind2 eq '23S')) || (!$strand && ($kind1 eq '23S' && $kind2 eq '16S')));
		$dist = $sort[$_+1]-$sort[$_]+1;
		next unless($dist <= MAX_LENGTH);
		push(@good,[$strand,
			    $kind1,
			    $sort[$_],
			    $pos{$strand}->{$sort[$_]}->{stop},
			    $kind2,
			    $sort[$_+1],
			    $pos{$strand}->{$sort[$_+1]}->{stop}]);
	    }
	}
    }
    return \@good;
}

sub reformatData {
    my ($r16S,$r23S) = @_;
    my %rrnas;
    foreach(@$r16S) {
	my $strand = ($_ =~ /^complement/ ? 0 : 1);  #forward 1 - reverse 0
	$_ =~ /(\d+)\.{2}(\d+)/;
	push(@{$rrnas{'16S'}},($strand ? [$1,$2] : [$2,$1]));
    }
    foreach(@$r23S) {
	my $strand = ($_ =~ /^complement/ ? 0 : 1);  #forward 1 - reverse 0
	$_ =~ /(\d+)\.{2}(\d+)/;
	push(@{$rrnas{'23S'}},($strand ? [$1,$2] : [$2,$1]));
    }
    return \%rrnas;
}

#discard overlapping regions on same strand and contig (16S with 16S, 23S with 23S, 16S with 23S)
#remove all overlapping regions bc we do not know which one is correct one
sub checkForOverlaps {
    my $rrnas = shift;
    my (%pos,$strand,$check);
    #separate regions by strand
    while(my ($kind,$array) = each(%$rrnas)) {
	foreach my $rrna (@$array) {
	    my ($start,$stop) = @$rrna;
	    $strand = ($start < $stop ? 1 : 0);
	    push(@{$pos{$strand}},[$start,$stop,$kind]);
	}
    }
    #find overlapping regions and remove them
    while(my ($strand,$array) = each(%pos)) {
	my (%overlapindex,$n,$c16S,$c23S,@sort);
	$n = scalar(@$array)-1;
	if($n) { #more than one region
	    #sort array by start position
	    @sort = sort {$a->[0] <=> $b->[0]} @$array;
	    foreach my $i (0..($n-1)) {
		foreach my $j (($i+1)..$n) {
		    #check if start_i <= start_j and start_j <= stop_i on forward strand -> overlap of rrna_i and rrna_j
		    #same for reverse strand, just change start and stop
		    $overlapindex{$i} = $overlapindex{$j} = 1 if($sort[$i]->[abs($strand-1)] <= $sort[$j]->[abs($strand-1)] && $sort[$j]->[abs($strand-1)] <= $sort[$i]->[$strand]);
		}
	    }
	    #remove overlapping regions
	    splice(@sort,$_,1) foreach(reverse sort {$a <=> $b} keys %overlapindex);
	}
	$check = 1 if(scalar(keys %overlapindex));
	#remove strand entries without at least one 16S and 23S region on same strand
	($_->[2] eq '16S' ? $c16S = 1 : $c23S = 1) foreach(@sort);
	if($c16S && $c23S) { #found 16S and 23S regions
	    $pos{$strand} = \@sort;
	} else {
	    delete $pos{$strand};
	}
    }
    print "[Warning: found overlapping rRNAs] " if($check);
    return \%pos;
}

#check for each 16S region in contig: 
# - 16S region before 23S on forward strand
# - 16S region behind 23S on on reverse strand
# - region between 16S and 23S region is less than 5000bp long
sub checkRegionPairs {
    my $hash = shift;
    my (@keep,$start,$stop);
    my $number = 1;
    return 0 unless($hash && scalar(keys %$hash)); #empty hash from previous function
    while(my ($strand,$array) = each(%$hash)) {
	my $n = scalar(@$array);
	foreach(0..($n-2)) {
	    next unless($array->[$_]->[2] eq ($strand ? '16S' : '23S') && #check for 16S/23S region
			$array->[$_+1]->[2] eq ($strand ? '23S' : '16S') && #check for following 16S/23S region
			$array->[$_]->[$strand] - $array->[$_+1]->[abs($strand-1)] < MAX_LENGTH); #check for distance between 16S/23S
	    #values: number,fig,contig,kind,start,stop,length,strand
	    $start = $array->[$_]->[abs($strand-1)];
	    $stop = $array->[$_]->[$strand];
	    push(@keep,[$number,$array->[$_]->[2],$start,$stop,($stop-$start+1),$strand]);
	    $start = $array->[$_+1]->[abs($strand-1)];
	    $stop = $array->[$_+1]->[$strand];
	    push(@keep,[$number,$array->[$_+1]->[2],$start,$stop,($stop-$start+1),$strand]);
	    $start = $array->[$_]->[$strand]+1;
	    $stop = $array->[$_+1]->[abs($strand-1)]-1;
	    push(@keep,[$number,'ITS',$start,$stop,($stop-$start+1),$strand]);
	    $number++;
	}
    }
    return \@keep;
}




sub revcomp {
    my $seq = shift;
    $seq = reverse($seq);
    $seq =~ tr/GATCgatc/CTAGctag/;
    return $seq;
}

sub addToDatabase {
    my $data = shift;
    #connect to mysql database
    my $dsn = "DBI:mysql:database=".MYSQL_DB.";host=".MYSQL_HOST.";port=".MYSQL_PORT;
    my $dbh = DBI->connect($dsn,MYSQL_USER,'',
			   {
#			       RaiseError => 1,
			       AutoCommit => 1
			   });
    my ($stm,$id,@where);
#    sleep(0.1); #perl winxp mysql issue

    #get source id
    $stm = 'SELECT id FROM source WHERE name=\'NCBI\'';
    $id = $dbh->selectrow_arrayref($stm);
    my $source_id = $id->[0];

    #check if entry already exists
    my $acc = $data->{accession};
    my $date = $data->{creation_date};
    $stm = 'SELECT id FROM entry WHERE accession='.$dbh->quote($acc);
    $id = $dbh->selectrow_arrayref($stm);
    my ($entry_id,$version);
    if($id) { #entry exists
	$entry_id = $id->[0];
	$stm = 'SELECT version FROM entry WHERE id='.$dbh->quote($entry_id);
	$version = $dbh->selectrow_arrayref($stm)->[0];
	if($version && $date == $version) {
	    print "|   entry exists\n";
	} else {
	    print "WARNING: found entry with different version (old version: ".$version->[0].", new version: ".$date.") --> do nothing\n" if($version && $date > $version->[0]);
	}
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
	my $linkout;
	my $esearch = EUTILS.'esearch.fcgi?db=genome&retmax=0&term='.$acc;
#       print "ESEARCH QUERY:\n".$esearch."\n";
	my $result = get($esearch);
	$result =~ m|<IdList>.*<Id>(\d+)</Id>.*</IdList>|s;
	$linkout = $1.'&db=genome';
	$dbh->do('INSERT INTO entry (accession,version,linkout,source_id,organism_id) VALUES ('.$dbh->quote($acc).','.$date.','.$dbh->quote($linkout).','.$source_id.','.$organism_id.')');
	$entry_id = $dbh->last_insert_id('%',MYSQL_DB,'entry','id');
	print "|   added new entry\n";
	
	#input region
	my $region = $data->{region};
	my ($length,$sequence,$region_id,$contig,$strand,$startpos,$stoppos);
	foreach my $number (keys %$region) {
	    while(my ($kind,$hash) = each(%{$region->{$number}})) {
		$length = $hash->{length};
		$sequence = $hash->{sequence};

		#add value to region table
		$stm = 'SELECT id FROM region WHERE kind='.$dbh->quote($kind).' AND length='.$length.' AND sequence='.$dbh->quote($sequence);
		$id = $dbh->selectrow_arrayref($stm);
		if($id) {
		    print "|   $kind region exists\n";
		    $region_id = $id->[0];
		} else {
		    $dbh->do('INSERT INTO region (kind,length,sequence) VALUES ('.join(",",$dbh->quote($kind),$length,$dbh->quote($sequence)).')');
		    print "|   added new $kind region\n";
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
		$contig = $acc;
		$strand = $hash->{strand};
		$startpos = $hash->{startpos};
		$stoppos = $hash->{stoppos};
		$stm = 'SELECT entry_id FROM region_entry WHERE region_id='.$region_id.' AND entry_id='.$entry_id.' AND contig='.$dbh->quote($contig).' AND strand='.$strand.' AND startpos='.$startpos.' AND stoppos='.$stoppos;
		$id = $dbh->selectrow_arrayref($stm);
		if($id) {
		    print "|   region_entry exists\n";
		} else {
		    $dbh->do('INSERT INTO region_entry (contig,strand,startpos,stoppos,region_id,entry_id) VALUES ('.join(",",$dbh->quote($contig),$strand,$startpos,$stoppos,$region_id,$entry_id).')');
		    print "|   added new region_entry\n";
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
    $string =~ s/[\'\"]//g;
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


