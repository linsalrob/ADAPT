#!/usr/bin/perl

use strict;
use warnings;
use CGI;
#use CGI::Pretty;
use CGI::Carp qw(fatalsToBrowser);

use lib '/opt/bcr/2008-0612/linux-debian-x86_64/lib/perl5/site_perl/5.10.0/';
use GD::Graph::hbars;
use GD::Graph::mixed;
use MIME::Base64;
use ADAPTConfig;

use DBI;
use DBConfig;

use Bio::Trace::ABIF;
use Algorithm::CurveFit;

use File::Temp qw(tempfile);
use Data::Dumper; #do not comment out!!!!

#use lib '/opt/bcr/2008-0612/linux-debian-x86_64/lib/perl5/site_perl/5.10.0/x86_64-linux';
#use Acme::Damn;

###########################################################

my $q = new CGI;
$| = 1; # Do not buffer output
&run();

###########################################################

sub run {
    my ($imageMaps,$moDivs);
    &printHeader();

    #connect to mysql database
    my $dsn = "DBI:mysql:database=".MYSQL_DB.";host=".MYSQL_HOST.";port=".MYSQL_PORT;
    my $dbh = DBI->connect($dsn,MYSQL_USER,'',
			   {
#			       RaiseError => 1,
			       AutoCommit => 1
			   });

    #reading data file
    my ($dataHash,$number,$raw,$input,$standard,$types) = &readDataFile();

    &writeLog($number,$raw);

    if(!$dbh) {
	#could not connect to db
	&printWarnings('Could not connect to the database.'.$q->br().$q->br().'Please try again in some minutes or contact the administrator of this service to get help.'.$q->br().$q->br());
    } elsif($dataHash < 0) {
	#-21 = no peaks found in file
	&printWarnings('Could not find peaks in uploaded trace file.'.$q->br().$q->br().$q->u('Reasons could be:').$q->br().'- you have set the value for the fragment length too high'.$q->br().'- your input data file contains no data'.$q->br().'- your input data trace file is of low quality (e.g. peaks can not be distiguished from noise)'.$q->br().'- you forgot to select the size standard'.$q->br().$q->br().'Please go back and try again by clicking "'.BUTTON_BACK.'" or contact the administrator of this service to get help.'.$q->br().$q->br());
    } elsif(!$dataHash || scalar(keys %{$dataHash}) == 0) {
	#could not upload data file
	#could not parse or read data file
	&printWarnings('Could not open or parse input data file.'.$q->br().$q->br().$q->u('Reasons could be:').$q->br().'- you have stopped the file upload or an upload error occurs'.$q->br().'- your input data file contains no data'.$q->br().'- your input data file format is invalid (e.g. no header line)'.$q->br().$q->br().'Please go back and try again by clicking "'.BUTTON_BACK.'".'.$q->br().$q->br());
    } else {
	$dbh->do('USE '.MYSQL_DB);

	#remove values outside fragment length range and fluorescence intensity
	my ($goodDataHash,$removedDataHash,$low) = &removeOutsideValues($dataHash);
	my $removedDataLine = scalar(keys %$removedDataHash) > 0 ? $q->b('No valid peaks: ').join(", ",keys %$removedDataHash) : undef;

	#get output list
	my $outputlist = &getOutputList();

	#generate mysql filter for input params
	my $filter = &generateFilter();

	#find fragments length for given primers in DB
	my $lengthids = &findFragmentsForPrimers($dbh,$filter);

	#find database entries
	my ($length,$orgn,$ids,$count) = &findMatchingIds($goodDataHash,$lengthids);

	#generating output parts
	my (%outputs,$id,%types);
	$id = 'ainputparams';
	if(exists $outputlist->{$id}) {
	    $outputs{$id} = {title => OUTPUTS->{general}->{$id},
			     show => 0,
			     order => 1,
			     color => HEADER_BG_COLOR,
			     id => $id,
			     data => &generateParamsTable($number)};
	}
	$id = 'aprimermatchings';
	if(exists $outputlist->{$id}) {
	    $outputs{$id} = {title => OUTPUTS->{general}->{$id},
			     show => 0,
			     order => 3,
			     color => HEADER_BG_COLOR,
			     id => $id,
			     data => &generatePrimerMatchingTable($dbh,$lengthids,$id)};
	}
# 	    $id = 'primermatchchart';
# 	    if(exists $outputlist->{$id}) {
# 		$outputs{$id} = {title => 'Primer matching fragment length',
# 				 show => 0,
# 				 order => 4,
# 				 color => HEADER_BG_COLOR,
# 				 id => $id,
# 				 data => &generatePrimerMatchingChart($lengthids,$id)};
# 	    }
	$id = 'tracefileplots';
	if(exists $outputlist->{$id}) {
	    $outputs{$id} = {title => OUTPUTS->{plots}->{$id},
			     show => 0,
			     order => 12,
			     color => HEADER_BG_COLOR,
			     id => $id,
			     data => &generateTracePlots($raw,$low,$id)};
	}
	if(exists $types->{'abif'}) {
	    $id = 'rawdataplots';
	    if(exists $outputlist->{$id}) {
		$outputs{$id} = {title => OUTPUTS->{plots}->{$id},
				 show => 0,
				 order => 10,
				 color => HEADER_BG_COLOR,
				 id => $id,
				 data => &generateRawDataPlots($input,$id)};
	    }
	    $id = 'standardplots';
	    if(exists $outputlist->{$id}) {
		$outputs{$id} = {title => OUTPUTS->{plots}->{$id},
				 show => 0,
				 order => 11,
				 color => HEADER_BG_COLOR,
				 id => $id,
				 data => &generateStandardPlots($standard,$id)};
	    }
	}
	if($count) {
	    $id = 'lengthtable';
	    if(exists $outputlist->{$id}) {
		$outputs{$id} = {title => OUTPUTS->{general}->{$id},
				 show => 0,
				 order => 6,
				 color => HEADER_BG_COLOR,
				 id => $id,
				 data => &generateLengthTable($dbh,$length,$removedDataLine,$id)};
	    }
	    $id = 'orgntable';
	    if(exists $outputlist->{$id}) {
		$outputs{$id} = {title => OUTPUTS->{general}->{$id},
				 show => 0,
				 order => 7,
				 color => HEADER_BG_COLOR,
				 id => $id,
				 data => &generateOrganismTable($dbh,$orgn,$removedDataLine,$id)};
	    }
	    $id = 'phylumhittable';
	    if(exists $outputlist->{$id}) {
		$outputs{$id} = {title => OUTPUTS->{general}->{$id},
				 show => 0,
				 order => 9,
				 color => HEADER_BG_COLOR,
				 id => $id,
				 data => &generatePhylumHitTable($dbh,$ids,$id)};
	    }
	    my $order = 20;
	    foreach my $kind ('pathogenic','trophic') {
		foreach my $type ('average') {
		    $id = $kind.$type;
		    if(exists $outputlist->{$id}) {
			my ($tableData,$chartData,$divData,$which) = &generateFractionData($dbh,$orgn,$length,$goodDataHash,TYPES->{$kind},$type);
			my $content = &generateFractionContent(TYPES->{$kind},$which,$id.'table',$tableData,$id.'chart',$chartData,$divData,\$imageMaps,\$moDivs,$type);
			$outputs{$id} = {title => OUTPUTS->{metadata}->{$id},
					 show => 0,
					 order => $order++,
					 color => HEADER_BG_COLOR,
					 id => $id,
					 data => $content};
		    }
		}
	    }
	    if(scalar(keys %$ids)>1) {
		$id = 'mdblength';
		if(exists $outputlist->{$id}) {
		    $outputs{$id} = {title => 'Multiple samples grouped by database length',
				     show => 0,
				     order => 41,
				     color => HEADER_BG_COLOR,
				     id => $id,
				     data => &generateMultipleDbTable($length,$id)};
		}
		$id = 'minputlength';
		if(exists $outputlist->{$id}) {
		    $outputs{$id} = {title => 'Multiple samples grouped by input length',
				     show => 0,
				     order => 40,
				     color => HEADER_BG_COLOR,
				     id => $id,
				     data => &generateMultipleInputTable($length,$id)};
		}
	    }
	}
	$dbh->disconnect();
	print &generateOutput(\%outputs);
	$moDivs .= &generateMenuDiv(\%outputs);
    }
    &printFooter($imageMaps,$moDivs,);
}

sub printHeader {
    print
	$q->header(),
	$q->start_html(-title => 'ADAPT Results',
		       -onload => 'hideloader()',
		       -style => CSS_FILE,
		       -script => {-language => 'JAVASCRIPT',
                                   -src => JS_FILE}),
	$q->start_center(),
	$q->a({-href => 'ADAPTHome.cgi'},
	      $q->img({-src => '../../'.ADAPT_DIR.'adapt.png',
		       -border => '0',
		       -alt => 'ADAPT '.VERSION.' logo - home'})),
	$q->a({-href => 'ADAPTInput.cgi',},
	      $q->img({-src => '../../'.ADAPT_DIR.'program2.png',
		       -border => '0',
		       -alt => 'ADAPT '.VERSION.' program',
#	     -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'program2.png'.'";',
#	     -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'program1.png'.'";'
		      })),
	$q->a({-href => 'ADAPTDatabase.cgi',},
	      $q->img({-src => '../../'.ADAPT_DIR.'database1.png',
		       -border => '0',
		       -alt => 'ADAPT '.VERSION.' database',
		       -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'database2.png'.'";',
		       -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'database1.png'.'";'})),
	$q->a({-href => 'ADAPTHelp.cgi',},
	      $q->img({-src => '../../'.ADAPT_DIR.'help1.png',
		       -border => '0',
		       -alt => 'ADAPT '.VERSION.' help',
		       -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'help2.png'.'";',
		       -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'help1.png'.'";'})),
	$q->a({-href => 'ADAPTContact.cgi',},
	      $q->img({-src => '../../'.ADAPT_DIR.'contact1.png',
		       -border => '0',
		       -alt => 'ADAPT '.VERSION.' contact',
		       -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'contact2.png'.'";',
		       -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'contact1.png'.'";'})),
	'<div id="outputloading" style="position:fixed; width:99%; text-align:center; top:300px;"><img src="'.'../../'.ADAPT_DIR.'outputloader.gif" border=0 alt="Output loading animation"><br /><br /><font style="color:#3366cc;">Loading ...</font></div>',
	'<script>
  var ld=(document.all);var ns4=document.layers;var ns6=document.getElementById&&!document.all;var ie4=document.all;
  if (ns4) ld=document.outputloading;
  else if (ns6) ld=document.getElementById("outputloading").style;
  else if (ie4)ld=document.all.outputloading.style;
  function hideloader() {if(ns4){ld.visibility="hidden";}else if (ns6||ie4) ld.display="none";}
 </script>',
    $q->br()x2,
    $q->start_form({-method => 'post',
		    -name => 'output'}),
    $q->start_table({-border =>'0',
		     -cellspacing => '0',
		     -width => TABLE_WIDTH});
}

sub printFooter {
    my ($imageMaps,$moDivs) = @_;
    print
	$q->end_table(),
	$q->end_form(),
	FOOTER,
	$q->end_center(),
	($imageMaps||''),
	($moDivs||''),
	GOOGLE_ANALYTICS,
	$q->end_html();
}

sub printWarnings {
    my ($message) = @_;
    foreach($q->param()) {
	next if($_ eq 'upload');
	print $q->hidden(-name => $_,
			 -default => [$q->param($_)]);
    }
    print
	$q->Tr($q->td({-align => 'center',
		       -colspan => '2',
		       -class => 'warningContent'},
		      $q->font({-class => 'error_message'},
			       $q->b('Warning:')),
		      $q->br(),
		      $q->br(),
		      $q->font({-class => 'error_message2'},
			       $message),
		      $q->br())),
	$q->Tr($q->td({-colspan => '2',
			    -class => 'groupEmpty'},
			   '&nbsp;')),
	$q->Tr($q->td({-align => 'center',
		       -class => 'tableButton',
		       -colspan => '2'},
		      $q->button({-value => BUTTON_BACK,
				  -name => 'goback',
				  -class => 'buttonoutput',
				  -onClick => 'javascript:history.go(-1);'}),
		      $q->br()x3));
}

sub readDataFile {
    my %hash;
    my %raw;
    my @pfiles;
    foreach($q->Vars) {
	push(@pfiles,$_) if(/^file\_(\d+)$/ig && $q->param($_));
    }
    my %types;
    my %inputs;
    my %standard;
    foreach(@pfiles) {
	my $fh = $q->param($_);
	my $id = Dumper $fh;
	chomp($id);
	$id =~ s/^.*\{\'(.+)\'\}.*$/$1/;
	my $fname = $q->tmpFileName($fh);
#	my $fname = damn($q->{'.tmpfiles'}->{'*'.$id}->{'name'});
	my $abif = Bio::Trace::ABIF->new();
#	$abif->open_abif($$fname);
	$abif->open_abif($fname);
	my $peaks;
	if($abif->is_abif_open()) { #input is in abif format
	    (my $name = $id) =~ s/Fh\:\:fh\d{5}(.*).fsa/$1/;
	    $name =~ s/\s//g;
	    $name .= '__a';
	    my ($peaks,$rawpeaks,$input,$curveparams,$peaks5,$sse,$sst) = &processABIF($abif);
	    $inputs{$name} = $input;
	    return -21 unless($peaks);
	    $hash{$name} = $peaks;
	    $raw{$name} = $rawpeaks;
	    $standard{$name}->{curve} = $curveparams;
	    $standard{$name}->{peaks} = $peaks5;
	    $standard{$name}->{sse} = $sse;
	    $standard{$name}->{sst} = $sst;
	    $types{'abif'} = 1;
	} else { #input is not in abif format
	    open(FILE,"perl -p -e 's/\r/\n/g;s/\n\n/\n/g' < $fname |") or print STDERR "Could not open file $fname: $!";
	    my @data = <FILE>;
	    close(FILE);
#	    my @data = <$fh>;
#	    die Dumper \@data;
	    my $firstline = shift(@data);
	    chomp($firstline);
	    $firstline =~ s/[\r\n]//g;
	    my @firstlineA = split(/\t/,$firstline);
	    my ($index_s,$index_n,$index_h);
	    my $index = 0;
	    foreach my $header (@firstlineA) {
		if($header =~ /^\s*Sample\sFile\sName$/i) {
		    $index_n = $index;
		} elsif($header =~ /^\s*Size$/i) {
		    $index_s = $index;
		} elsif($header =~ /^\s*Height$/i) {
		    $index_h = $index;
		}
		$index++;
	    }
#	    die Dumper $index_s,$index_n,$index_h,\@firstlineA;
	    return 0 unless(defined $index_s && defined $index_h);
	    foreach my $line (@data){
		chomp($line);
		$line =~ s/[\r\n]//g;
		my @lineValues = split(/\t/,$line);
		my ($tmpName,$tmpLength,$tmpHeight);
		$tmpName = ($index_n ? $lineValues[$index_n] : 'Noname');
		$tmpLength = $lineValues[$index_s];
		$tmpHeight = $lineValues[$index_h];
#		$tmpName =~ /^[A-H][0-1][0-9]\_(.+)\_\d{3}\.fsa$/;
		my $one;
#		$one = $1;
#		$tmpName =~ /^(.+)\.fsa$/;
#		$one = $1 unless($one);
#		$one = $tmpName unless($one);
		($one = $tmpName) =~ s/\.fsa//;
		$one =~ s/\s//g;
		$one .= '__t';
		next if($one eq '' || $tmpLength !~ /^([+-]?)(?:\d+(?:\.\d*)?|\.\d+)$/);
		$hash{$one}->{sprintf("%.2f",$tmpLength)} = $tmpHeight;
		$raw{$one}->{sprintf("%.2f",$tmpLength)} = $tmpHeight;
	    }
	    $types{'tsv'} = 1;
	}
	$abif->close_abif();
    }
    if(scalar(keys %types)<2) {
	foreach my $id (keys %hash) {
	    (my $id2 = $id) =~ s/\_\_[at]$//;
	    $hash{$id2} = delete $hash{$id};
	}
	foreach my $id (keys %raw) {
	    (my $id2 = $id) =~ s/\_\_[at]$//;
	    $raw{$id2} = delete $raw{$id};
	}
	foreach my $id (keys %inputs) {
	    (my $id2 = $id) =~ s/\_\_[at]$//;
	    $inputs{$id2} = delete $inputs{$id};
	}
	foreach my $id (keys %standard) {
	    (my $id2 = $id) =~ s/\_\_[at]$//;
	    $standard{$id2} = delete $standard{$id};
	}
    }
#    die Dumper \%hash,$q->param('files'),\%raw,\%inputs,\%standard,\%types;

    return (\%hash,$q->param('files'),\%raw,\%inputs,\%standard,\%types);
}

sub writeLog {
    my ($number, $raw) = @_;
    my @data = ();
    my $names = join(",",keys %$raw);
    push(@data,('browser:'.$ENV{'HTTP_USER_AGENT'},'files:'.(($number||0)-1),'names:'.$names));
    my $params = PARAMS;
    my $methods = (grep(/methods/,$q->param())) ? 1 : 0;
    my @outputs;
    foreach my $p ($q->param()) {
	next if($p eq 'files' || $p =~ /^file\_\d+/ || $q->param($p) eq '');
	next if($p eq 'sizest' && $q->param($p) eq '');
	next if($p eq 'sizesl' && $q->param('sizest') ne '');
	next if($p eq 'sizesl' && $q->param($p) eq ' ');
	next if($p eq 'allnone');
	push(@data,$p.':'.join(",",$q->param($p)));
    }
    push(@data,join(", ",@outputs)) if(@outputs);
    push(@data,($params->{METHODS.''} || METHODS)) unless($methods);
    my $string = join("\t",@data);
    &addToLogFile($string);
}

sub addToLogFile {
    my $string = shift;
    my $log = LOG_FILE;
    &checkLogFile($log);
    my $time = sprintf("[%02d/%02d/%04d %02d:%02d:%02d]",sub {($_[4]+1,$_[3],$_[5]+1900,$_[2],$_[1],$_[0])}->(
localtime));
    open(LOG,">>$log") or die "ERROR: could not open file $log: $!\n";
    print LOG $time."\t".$string."\n";
    close(LOG);
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

#process abi file format inputs
sub processABIF {
    my $abif = shift;
    my (@ch1,@ch5,$mean,$max,$min,$peaks1,$peaks5,%raw);

    #get standard sizes from input
    my $std;
    if($q->param('sizest')) {
	$std = $q->param('sizest');
	$std =~ s/[\n\r\s]//;
	my @tmp = split(/\,/,$std);
	return 0 unless(scalar(@tmp)>1);
	$std = \@tmp;
    } elsif($q->param('sizesl') ne ' ') {
	$std = SIZE_STD->{$q->param('sizesl')};
    } else {
	return 0;
    }

    #standard data in channel 5
    @ch5 = $abif->raw_data_for_channel(5);
    my $ch5new = &smoothCMA(\@ch5);
    $ch5new = &baseline($ch5new);
    $ch5new = &subMean($ch5new);
#   print Dumper($ch5new),"<br>"x10;#die;
    $peaks5 = &findStdPeaks($ch5new);
#   print join("\n",sort {$a <=> $b} (keys %$peaks5)),"<br>"x10;

    #samples data in channel 1
    @ch1 = $abif->raw_data_for_channel(1);
    my $ch1new = &smoothCMA(\@ch1);
    my $ch1newb = &baseline($ch1new);
    my $ch1news = &subMean($ch1newb);
#   print Dumper($ch1new);die;
    $peaks1 = &findPeaks($ch1news);
#   die join("\n",sort {$a <=> $b} (keys %$peaks1));

    #estimate standard size curve
    my ($curveparams,$sse,$sst) = &estimateSizeCurve($peaks5,$std);
#    die Dumper($peaks5);

    #map standard size to standard peaks
    &mapStdToPeaks($peaks5,$std);
#   print Dumper($peaks5),"<br>"x10;

    #clean standard peaks without defined size standard
    &cleanPeaks($peaks5);

    #calculate size for sample peaks
    &calcSizeSamplePeaks($peaks1,$peaks5,$curveparams);

    #old method without curve fitting for size outside standard range
#    $ch5new = &mapSizeToPoints($peaks5,scalar(@$ch5new));
#    print Dumper($ch5new),"<br>"x10;
#    &getPtSize($peaks1,$ch5new);

    my %output;
    foreach(values %$peaks1) {
	$output{int($_->{size}*100+0.5)/100} = $_->{height} if($_->{size});
	$raw{int($_->{size}*100+0.5)/100} = $_->{height} if($_->{size});
    }
    return (\%output,\%raw,[\@ch1,\@ch5],$curveparams,$peaks5,$sse,$sst);
}

#calculate the central mooving average to smooth curve
sub smoothCMA {
    my $input = shift;
    my @output;
    my $window = 11; #odd number
    my $start = ($window-1)/2;
    my $length = scalar(@$input);
    my $end = $length-$start;
    my $cma = 0;
    $cma += $input->[$_] foreach(0..$window-1);
#    $cma /= $window;
#    $cma = int($cma+0.5);
    $output[$_] = $cma foreach(0..$start);
    $start++;
    foreach($start..$end) {
	$output[$_] = ($output[$_-1] || 0) + ($input->[$_+$start-1] || 0) - ($input->[$_-$start] || 0);
    }
    $output[$_] = $output[$end-1] foreach($end..$length-1);
    foreach(0..$length-1) {
	$output[$_] = int($output[$_]/$window+0.5);
    }
    return \@output;
}

#calculate the baseline and subtract from current values
sub baseline {
    my $input = shift;
    my @output;
    my $window = 51; #odd number
    my $length = scalar(@$input);
    my $start = ($window-1)/2;
    my $end = $length-$start;
    my $min = $input->[0] || 0;
    $min = ($input->[$_]<$min ? $input->[$_] : $min) foreach(1..$window);
    $output[$_] = ($input->[$_]-$min) foreach(0..$start);
    my $tmp;
    foreach my $i ($start+1..$end) {
	$tmp = $input->[$i+$start];
	if(defined $tmp && $tmp<=$min) {
	    $min = $tmp;
	} elsif($input->[$i-$start-1] == $min) {
	    $min = ($input->[$_]<$min ? $input->[$_] : $min) foreach($i-$start..$i+$start);
	}
	$output[$i] = $input->[$i]-$min;
    }
    $output[$_] = $output[$end-1] foreach($end..$length-1);
    return \@output;
}

#substract the mean over all point from each point
sub subMean {
    my $input = shift;
    my @output;
    my $mean = 0;
    $mean += $_ foreach(@$input);
    $mean /= scalar(@$input);
    #add 10%
    $mean *= 1.1;
    $mean = int($mean+0.5);
    push(@output,($_-$mean<0 ? 0 : $_-$mean)) foreach(@$input);
    return \@output;
}

#detect the peaks in the trace data for the standard
sub findStdPeaks {
    my $input = shift;
    my %output;
    my $oldpt = 0;
    my $up;
    my $high;
    my $low;
    my $counter = 1;
    my $count = 1;
    my $meanheight = 0;
    foreach my $pt (@$input) {
	if($pt < $oldpt) {
	    if($up) {
		if(($meanheight/$count)*0.3 < $oldpt && $oldpt > 10) {
		    $output{$counter}->{height} = $oldpt;
		    $meanheight += $oldpt;
		    $count++;
		}
	    }
	    $up = 0;
	} elsif($pt > $oldpt) {
	    $up = 1;
	}
	$oldpt = $pt;
	$counter++;
    }
    return \%output;
}

#detect the peaks in the trace data
sub findPeaks {
    my $input = shift;
    my %output;
    my $oldpt = 0;
    my $up;
    my $high;
    my $low;
    my $counter = 1;
    foreach my $pt (@$input) {
	if($pt < $oldpt) {
	    if($up) {
		$output{$counter}->{height} = $oldpt;
	    }
	    $up = 0;
	} elsif($pt > $oldpt) {
	    $up = 1;
	}
	$oldpt = $pt;
	$counter++;
    }
    return \%output;
}

#estimate size standard curve
sub estimateSizeCurve {
    my ($peaks5,$std) = @_;
    my $n = (scalar(@$std) < scalar(keys %$peaks5) ? scalar(@$std) : scalar(keys %$peaks5));
    my @x = (sort {$a <=> $b} keys %$peaks5)[0..$n-1];
    my @y = @$std[0..$n-1];
    my $max_iter = 200; # maximum iterations
    my $variable = 'x';
    my $error = 0.00001;

    #try to fit line to data using Algorithm::CurveFit module
    my $formula = 'a + b * x';
    my @parameters = (
	# Name    Guess   Accuracy
	['a',     1,     $error],
	['b',     1,     $error],
	);
    my $square_residual = Algorithm::CurveFit->curve_fit(
	formula            => $formula,
	params             => \@parameters,
	variable           => $variable,
	xdata              => \@x,
	ydata              => \@y,
	maximum_iterations => $max_iter,
	);
    my ($la,$lb) = map { $_->[1] } @parameters;
#    print Dumper $la,$lb;die;

    #try to fit 2nd degree polynimial to data using Algorithm::CurveFit module
    $formula = 'a + b * x + c * x^2';
    @parameters = (
	# Name    Guess   Accuracy
	['a',     1,     $error],
	['b',     1,     $error],
	['c',     1,     $error],
	);
    $square_residual = Algorithm::CurveFit->curve_fit(
	formula            => $formula,
	params             => \@parameters,
	variable           => $variable,
	xdata              => \@x,
	ydata              => \@y,
	maximum_iterations => $max_iter,
	);
    my ($pa,$pb,$pc) = map { $_->[1] } @parameters;
#    print Dumper $pa,$pb,$pc;die;

    #calculate sum of squares error (SSE)
    my $lsse = &calcSSE($peaks5,\@x,\@y,$la,$lb);
    my $psse = &calcSSE($peaks5,\@x,\@y,$pa,$pb,$pc);
    my $sst = &calcSST(\@y);

    return (($psse < $lsse ? ([$pa,$pb,$pc],$psse) : ([$la,$lb,0],$lsse)),$sst);
}

#calculate sum of squares errors (SSE)
sub calcSSE {
    my ($peaks5,$x,$y,$xa,$xb,$xc) = @_;
    my $sse = 0;
    my $n = scalar(@$x)-1;
    $xc = 0 unless(defined $xc);
    my $error = $xc ? 'pSSE' : 'lSSE';
    my $tmp;
    foreach my $i (0..$n) {
	$tmp = ($y->[$i]-($xa+$xb*$x->[$i]+$xc*$x->[$i]**2))**2;
	$sse += $tmp;
	$peaks5->{$x->[$i]}->{$error} = $tmp;
    }
    return $sse;
}

#calculate sum of squares for the total (SST)
sub calcSST {
    my $y = shift;
    my $sst = 0;
    my $n = scalar(@$y);
    my $meany = 0;
    $meany += $_ foreach(@$y);
    $meany /= $n;
    foreach my $i (0..$n-1) {
	$sst += ($y->[$i]-$meany) ** 2;
    }
    return $sst;
}


#map the values of the std to the peaks
sub mapStdToPeaks {
    my $peaks = shift;
    my $std = shift;
    my $counter = 0;
#    print join("<br />",@$std).'<br />';
    foreach my $key(sort {$a <=> $b } keys %$peaks) {
	return unless($std->[$counter]);
	$peaks->{$key}->{std} = $std->[$counter];
	$counter++;
#	print $key.'<br />';
    }
}

#remove peaks without defined standard size
sub cleanPeaks {
    my $peaks = shift;
    foreach(keys %$peaks) {
	delete $peaks->{$_} unless(exists $peaks->{$_}->{std});
    }
}

#calculate size for sample peaks
sub calcSizeSamplePeaks {
    my ($peaks1,$peaks5,$curveparams) = @_;
    my ($xa,$xb,$xc) = @$curveparams;
    my ($startx,$starty,$endx,$endy,$tmp,$m,$n);
    $xc = 0 unless(defined $xc);
    my @stdpeaks = sort { $a <=> $b } keys %$peaks5;
    my @smppeaks = sort { $a <=> $b } keys %$peaks1;
    my $first = $stdpeaks[0];
    my $last  = $stdpeaks[scalar(@stdpeaks)-1];
    foreach my $pt (@smppeaks) {
	if($pt < $first) { #smaller than range of defined size standard
	    $tmp = ($xa+$xb*$pt+$xc*$pt**2);
	    if($tmp < 0) { #negative size not possible
		delete $peaks1->{$pt};
		next;
	    }
	} elsif($pt > $last) { #larger than range of defined size standard
	    $tmp = ($xa+$xb*$pt+$xc*$pt**2);
	} else { #peak inside of defined size standard range
	    #set start values
	    unless($startx && $endx) {
		$startx = shift(@stdpeaks);
		$endx = shift(@stdpeaks);
	    }
	    next unless($startx && $endx);
	    #$pt is not in current size interval of standard
	    while($pt > $endx) {
		$startx = $endx;
		$endx = shift(@stdpeaks);
	    }
	    #get y values (size of size standard)
	    $starty = $peaks5->{$startx}->{std};
	    $endy = $peaks5->{$endx}->{std};
	    #calculate equation for line through two points
	    $m = ($endy-$starty)/($endx-$startx);
	    $n = $starty-$m*$startx;
	    #calculate y value (size) for x value ($pt) using equation
	    $tmp = $m*$pt+$n;
	}
	$peaks1->{$pt}->{size} = sprintf("%.2f",$tmp);
    }
}

#map the standard size values to the point values
sub mapSizeToPoints {
    my $peaks = shift;
    my $length = shift;
    my ($starts,$startp,$ends,$endp);
    my $step;
    my @output;
    my $last;
    my @peak = sort {$a <=> $b } keys %$peaks;
    foreach my $i (0..scalar(@peak)-2) {
	next unless(exists $peaks->{$peak[$i+1]}->{std});
	$startp = $peak[$i];
	$endp = $peak[$i+1];
	$starts = $peaks->{$startp}->{std};
	$ends = $peaks->{$endp}->{std};
	$step = ($ends-$starts)/($endp-$startp);
	$output[$startp] = $starts;
	$output[$endp] = $ends;
	$last = $i;
	foreach my $j ($startp+1..$endp-1) {
	    $output[$j] = $output[$j-1]+$step;
	}
    }
    #estimate higher values (above size standard max value)
    my ($x1,$x2,$y1,$y2,$m,$n);
    my $off = 0;
    $x1 = $peak[$off];
    $y1 = $peaks->{$x1}->{std};
    $x2 = $peak[$last-$off];
    $y2 = $peaks->{$x2}->{std};
    $m = ($x2-$x1 == 0 ? 0 : ($y2-$y1)/($x2-$x1));
    $n = $y1-$m*$x1;
    foreach my $i (0..$length) {
	$output[$i] = int(($output[$i] ? $output[$i] : ($i>$endp ? $m*$i+$n : 0))*100+0.5)/100;
#	next if($output[$i]);
#	$output[$i] = 0;
    }
    return \@output;
}

#get size for each detected peak in the channel 1 data
sub getPtSize {
    my $peaks = shift;
    my $ch5new = shift;
    foreach(keys %$peaks) {
	$peaks->{$_}->{size} = $ch5new->[$_];
    }
}

sub calcMean {
    my ($type,$datahash,$minlength,$maxlength) = @_;
    my $mean = 0;
    my @data;
    foreach my $length (keys %$datahash) {
	next unless($length >= $minlength && $length <= $maxlength);
	push(@data,$datahash->{$length});
    }
    return 0 unless(scalar(@data));
    return $data[0] if(scalar(@data) == 1);
    if($type eq 'imean') {
	my $interquartilemean = 0;
	my @lengths = sort {$a <=> $b} @data;
	my $n = scalar(@lengths);
	my $rest = $n % 4;
	my $q = 1-$rest/4;
	my $p = ($n-$rest)/4;
	my ($start,$stop);
	if($rest) {
	    $start = int($n/4)+2;
	    $stop = int(3*$n/4);
	} else {
	    $start = $n/4+1;
	    $stop = 3*$n/4;
	}
	my $sum = 0;
	foreach($start..$stop) {
	    $sum += $lengths[$_-1];
	}
	if($rest > 0) {
	    $sum += $q*($lengths[$start-2]+$lengths[$stop])
	}
	$interquartilemean = $sum * 2 / $n;
	$mean = $interquartilemean;
    } elsif($type eq 'gmean') {
	my $geommean = 1;
	foreach(@data) {
	    $geommean *= $_**(1/scalar(@data));
	}
	$mean = $geommean;
    } elsif($type eq 'amean') {
	my $amean = 0;
	foreach(@data) {
	    $amean += $_;
	}
	$amean /= scalar(@data);
	$mean = $amean;
    } else {
	my $power;
	$power = 2 if($type eq 'p2mean');
	$power = 3 if($type eq 'p3mean');
	my $powermean = 0;
	foreach(@data) {
	    $powermean += $_**$power;
	}
	$powermean = ($powermean/scalar(@data))**(1/$power);
	$mean = $powermean;
    }
    return $mean;
}

sub removeOutsideValues {
    my $hash = shift;
    my %newHash;
    my %remHash;
    my %low;
    my $minlength = $q->param('minlength');
    my $maxlength = $q->param('maxlength');
    my $cutoffcalc = $q->param('cutoffcalc') || 0;
    my $cutoffmin = $q->param('cutoffmin') || 0;
    my $minvalue = $q->param('cutoff') || 0;
    $cutoffcalc = 1 if(!$cutoffcalc && !$cutoffmin);
    my $meantype = $q->param('methods') || METHODS;
    foreach my $name (keys %$hash) {
	my $mean = &calcMean($meantype,$hash->{$name},$minlength,$maxlength);
	$low{$name} = $mean if($cutoffcalc);
	$low{$name} = $minvalue if($cutoffmin && (exists $low{$name} && $low{$name}<$minvalue) || !exists $low{$name});
	next unless($mean>0);
	foreach my $length (keys %{$hash->{$name}}) {
	    next unless($length >= $minlength && $length <= $maxlength);
	    my $height = $hash->{$name}->{$length};
	    next if($cutoffcalc && $height < $mean);
	    next if($cutoffmin && $height < $minvalue);
	    $newHash{$name}->{$length} = $height;
	}
	$remHash{$name} = 1 unless(exists $newHash{$name});
    }
    return (\%newHash,\%remHash,\%low);
}


sub getOutputList {
    my %outputs;
    foreach my $o ('outputsg','outputsp','outputsd','outputsm') {
	foreach my $v ($q->param($o)) {
	    foreach (values %{(OUTPUTS)}) {
		$outputs{$v} = 1 if($_->{$v});
	    }
	}
    }
    return \%outputs;
}

sub generateFilter {
    my $filter = ' ';
    my @tmp;
    foreach($q->param('domain')) {
	push(@tmp,'taxon.kingdom=\''.$_.'\'');
    }
    $filter .= '('.join(" OR ",@tmp).') AND ' if(@tmp);
    @tmp = ();
    foreach($q->param('datasource')) {
	push(@tmp,'source.name=\''.$_.'\'');
    }
    $filter .= '('.join(" OR ",@tmp).')' if(@tmp);
    return $filter;
}

sub findFragmentsForPrimers {
    my ($dbh,$filter) = @_;
    my ($regex,%lengthids,$fw,$rv,$stm,$aref);

    $fw = $q->param('forwardt') ? $q->param('forwardt') : PRIMERS->{forward}->{(split(/\s/,$q->param('forward')))[0]};
    $rv = $q->param('reverset') ? $q->param('reverset') : PRIMERS->{reverse}->{(split(/\s/,$q->param('reverse')))[0]};
    $regex = &convertPrimersToRegex($fw,$rv);

    $stm = 'SELECT DISTINCT region.id,region.sequence,organism_region.organism_id from region INNER JOIN (entry,source,region_entry,organism_region,organism,taxon) ON (entry.id=region_entry.entry_id AND region_entry.region_id=region.id AND entry.source_id = source.id AND region.id=organism_region.region_id AND organism_region.organism_id=organism.id AND organism.taxon_id=taxon.id) WHERE '.$filter;
    $aref = $dbh->selectall_arrayref($stm);
#    print Dumper $regex;
    foreach(@$aref) {
	if($_->[1] =~ m/$regex/g) {
	    $lengthids{length}->{($+[0]-$-[0]+1)}->{$_->[0]}++;
	    $lengthids{region}->{$_->[0]}->{$_->[2]}++;
	    $lengthids{organism}->{$_->[2]}->{match}->{$_->[0]} = ($+[0]-$-[0]+1);
	} else {
	    $lengthids{organism}->{$_->[2]}->{nomatch}->{$_->[0]} = 1;
	}
    }
    return \%lengthids;
}

sub findMatchingIds {
    my ($goodDataHash,$lengthids) = @_;
    my (%length,$count,$stm,$aref,%orgn,%ids);
    $count = 0;
    my $lower500 = $q->param('lower500');
    my $lower1000 = $q->param('lower1000');
    my $upper1000 = $q->param('upper1000');
    foreach my $name (keys %$goodDataHash) {
	foreach my $inputLength (keys %{$goodDataHash->{$name}}) {
	    next if(!$inputLength);
	    #round off to nearests number, with .5 round up
	    my $roundedLength = int($inputLength+0.5);
	    #apply binning
	    my $plusminus = ($roundedLength < 600) ? $lower500 : (($roundedLength < 900) ? $lower1000 : $upper1000);
	    my $startLength = $roundedLength-$plusminus;
	    my $stopLength  = $roundedLength+$plusminus;
	    #search for matching fragments
	    foreach my $l ($startLength..$stopLength) {
		if(exists $lengthids->{length}->{$l}) {
		    foreach my $region_id (keys %{$lengthids->{length}->{$l}}) {
			push(@{$ids{$name}->{$inputLength}},$region_id);
			foreach my $orgn_id (keys %{$lengthids->{region}->{$region_id}}) {
			    #length table data
			    $length{$name}->{$inputLength}->{$l}->{$region_id}->{$orgn_id} = 1;
			    #organism table data
			    %{$orgn{$name}->{$orgn_id}->{nomatch}} = %{$lengthids->{organism}->{$orgn_id}->{nomatch}} if(exists $lengthids->{organism}->{$orgn_id}->{nomatch} && !exists $orgn{$name}->{$orgn_id}->{nomatch});
			    %{$orgn{$name}->{$orgn_id}->{nohit}} = %{$lengthids->{organism}->{$orgn_id}->{match}} if(exists $lengthids->{organism}->{$orgn_id}->{match} && !exists $orgn{$name}->{$orgn_id}->{nohit});

			    $orgn{$name}->{$orgn_id}->{hit}->{$region_id} = $lengthids->{organism}->{$orgn_id}->{match}->{$region_id} if(exists $orgn{$name}->{$orgn_id}->{nohit}->{$region_id});
			    delete $orgn{$name}->{$orgn_id}->{nohit}->{$region_id};
			    delete $orgn{$name}->{$orgn_id}->{nohit} unless(scalar(keys %{$orgn{$name}->{$orgn_id}->{nohit}}));
			    $count++;
			}
		    }
		}
	    }
	    #add non matching names and input lengths
	    $length{$name}->{$inputLength} = {} unless(exists $length{$name}->{$inputLength});
	    $orgn{$name} = {} unless(exists $orgn{$name});
	    $ids{$name}->{$inputLength} = () unless(exists $ids{$name}->{$inputLength});
	}
    }
    unless($count) {
	&printWarnings('Could not find any matching fragments in the database.'.$q->br().$q->br().'Please check your input file and make sure you selected the correct size standard if you used <code>.fsa</code> or <code>.ab1</code> files as input.'.$q->br().'If you still see this message, please contact the administrator of this service to get help.'.$q->br().$q->br().'Please go back and try again by clicking "'.BUTTON_BACK.'".'.$q->br());
#	exit;
    }
    return (\%length,\%orgn,\%ids,$count);
}

sub findITSEntries {
    my ($goodDataHash,$dbh,$filter) = @_;
    my ($stm,$aref);
    my $lower500 = $q->param('lower500');
    my $lower1000 = $q->param('lower1000');
    my $upper1000 = $q->param('upper1000');
    my %ITSids;
    my $count = 0;
    foreach my $name (keys %$goodDataHash) {
	foreach my $inputLength (keys %{$goodDataHash->{$name}}) {
	    next if(!$inputLength);
	    #round off to nearests number, with .5 round up
	    my $roundedLength = int($inputLength+0.5);
	    my $binSize = ($roundedLength < 600) ? $lower500 : (($roundedLength < 900) ? $lower1000 : $upper1000);
	    my $startLength = $roundedLength-$binSize;
	    my $stopLength = $roundedLength+$binSize;
	    #query database
	    $stm = 'SELECT DISTINCT region.id FROM region INNER JOIN (entry,source,region_entry,organism_region,organism,taxon) ON (entry.id=region_entry.entry_id AND region_entry.region_id=region.id AND entry.source_id = source.id AND region.id=organism_region.region_id AND organism_region.organism_id=organism.id AND organism.taxon_id=taxon.id) WHERE region.kind=\'ITS\' AND region.length BETWEEN '.$startLength.' AND '.$stopLength.$filter.' ORDER BY region.length';
	    $aref = $dbh->selectall_arrayref($stm);
	    my @ids = map{$_->[0]}@$aref;
	    $ITSids{$name}->{$inputLength} = \@ids;
	    $count++ if(@$aref && scalar(@ids)>0);
	}
    }
    unless($count) {
#	&printWarnings('Could not find any matching ITS length in the database.'.$q->br().$q->br().'Please check your input file and make sure you selected the correct size standard if you used <code>.fsa</code> or <code>.ab1</code> files as input.'.$q->br().'If you still see this message, please contact the administrator of this service to get help.'.$q->br().$q->br().'Please go back and try again by clicking "'.BUTTON_BACK.'".'.$q->br());
#	exit;
    }
    return (\%ITSids,$count);
}

sub generateParamsTable {
    my $number = shift;
    my $content;
    my $params = PARAMS;
    my $methods = (grep(/methods/,$q->param())) ? 1 : 0;
    my @tableData;
    foreach my $p ($q->param()) {
	next if($p eq 'files' || $p eq 'file_'.($number-1) || $q->param($p) eq '');
	next if($p eq 'sizest' && $q->param($p) eq '');
	next if($p eq 'sizesl' && $q->param('sizest') ne '');
	next if($p eq 'sizesl' && $q->param($p) eq ' ');
	next if($p eq 'allnone' || $p eq 'resolution');
	next if($p eq 'forward' && $q->param('forwardt'));
	next if($p eq 'reverse' && $q->param('reverset'));
	push(@tableData,[$params->{$p} || $p, ($p =~ /^cutoff.+/ ? 'yes' : $params->{$q->param($p)} || join(", ",($p =~ /^outputs\w$/ ? map { OUTPUTS->{($p eq 'outputsg' ? 'general' : ($p eq 'outputsp' ? 'plots' : ($p eq 'outputsd' ? 'metadata' : ($p eq 'outputsm' ? 'multiple' : ''))))}->{$_} } $q->param($p) : $q->param($p))))]);
    }
    push(@tableData,[$params->{methods}||'method',$params->{METHODS.''}||METHODS]) unless($methods);
    $content = &generateTableContent(['Parameter','Value'],\@tableData,1);
    return $content;
}

sub generateTracePlots {
    my ($dataHash,$lowH,$id) = @_;
    my @graphs;
    my %intH;
    my $minlength = $q->param('minlength');
    my $maxlength = $q->param('maxlength');
    my $meantype = $q->param('methods') || METHODS;
    my $counter = 1;
    my $min = 1000;
    my $max = 2000;
    my $step = 20;
    my (@data,$ymax,$xmax,$value,$low,$tmp);
    foreach my $name (sort keys %$dataHash) {
	@data = ();
	%intH = ();
	$ymax = 0;
	$xmax = int((reverse sort {$a <=> $b} keys %{$dataHash->{$name}})[0]+0.5);
	$xmax = $min unless($xmax-51 > $min);
	$xmax = $max unless($xmax < $max);
	$xmax = int($xmax/$step+1)*$step if($xmax % $step);
	$low = $lowH->{$name};
	$dataHash->{$name}->{0} = 0 unless(exists $dataHash->{$name}->{0});
	$dataHash->{$name}->{$minlength} = 0 unless(exists $dataHash->{$name}->{$minlength});
	foreach my $m (values %{$dataHash->{$name}}) {
	    $ymax = $m if($m > $ymax);
	}
	$ymax = int($ymax*1.02/5+1)*5;
	foreach my $x (keys %{$dataHash->{$name}}) {
	    $tmp = int($x+0.5);
	    $intH{$tmp} = ((exists $intH{$tmp} && $intH{$tmp} > $dataHash->{$name}->{$x}) ? $intH{$tmp} : $dataHash->{$name}->{$x});
	}
	for my $x (0..$xmax) {
	    push(@{$data[0]},$x);
	    push(@{$data[2]},(($x < $minlength || $x > $maxlength) ? $ymax : 0));
	    $value = $intH{$x} || 0;
	    push(@{$data[1]},($low < $ymax ? $low : $ymax));
	    push(@{$data[3]},$value);
	}
	my $graph = GD::Graph::mixed->new(TABLE_WIDTH-10,200);
	$graph->set(x_label => 'Fragment length',
		    y_label => 'Intensity',
		    title => $name,
		    types => [ qw( area area lines ) ],
		    default_type => 'lines',
		    y_max_value => $ymax,
		    y_min_value => 0,
		    x_max_value => $xmax,
		    x_min_value => 0,
		    y_tick_number => 5,
#		    line_width => 3,
		    tick_length => -3,
		    text_space => 11,
		    transparent => 0,
#		    long_ticks       => 1, #show grid
#		    y_ticks          => 1,
#		    y_tick_number    => 10,
		    x_tick_number => $step,
		    x_label_position => 1/2,
#		    show_values      => 0,
#		    x_labels_vertical => 1,
		    dclrs => ['gold','lgray','lblue']
	    ) or warn $graph->error;
	$graph->set_x_label_font(GD::gdMediumBoldFont);
	$graph->set_y_label_font(GD::gdMediumBoldFont);
	$graph->set_x_axis_font(GD::gdSmallFont);
	$graph->set_y_axis_font(GD::gdTinyFont);
#  $graph->set_values_font(GD::gdMediumBoldFont);
	$graph->set_legend_font(GD::gdLargeFont);
	$graph->set_legend('Intensity threshold','Outside length range','Trace data');
	my $idc = $id.$counter++;
	my $hidden = &generateHiddenContent(0,\@data,$idc,[$name]);
	push(@graphs,(&generateImagePart($idc,$graph->plot(\@data),$hidden),'<br />Intensity threshold value for "'.$name.'" using "'.PARAMS->{$meantype}.'": <b>'.sprintf("%.2f",$low).'</b><br />'));
    }
    return join("<br>",@graphs);
}

sub generateStandardPlots {
    my ($standard,$id) = @_;
    return 0 unless(defined $standard);
    my @graphs;
    my $counter = 1;
    my (@data,$ymax,$xmin,$xmax,$xa,$xb,$xc,$peaks,$sse,$sst,$r2,@tmp,$m);
    #normally <30000 data points per input file
    foreach my $name (sort keys %$standard) {
	@data = ();
	$ymax = 0;
	$sse = $standard->{$name}->{sse};
	$sst = $standard->{$name}->{sst};
	$r2 = ($sst-$sse)/$sst;
	($xa,$xb,$xc) = @{$standard->{$name}->{curve}};
	$xc = 0 unless(defined $xc);
	$peaks = $standard->{$name}->{peaks};
	@tmp = sort { $a <=> $b } keys %$peaks;
	$xmin = $tmp[0]-100;
	$xmax = $xmin;
	foreach my $pt ($xmin..$tmp[scalar(@tmp)-1]+100) {
	    push(@{$data[0]},++$xmax);
	    $m = ($xa+$xb*$pt+$xc*$pt**2);
	    push(@{$data[1]},$m); #curve fit
	    push(@{$data[2]},(exists $peaks->{$pt} ? $peaks->{$pt}->{std} : undef)); #size standard
	    $ymax = $m if($m > $ymax);
	}
	$ymax = int($ymax/100+1)*100;
	$xmax = int($xmax/10+1)*10;
	$xmin = int($xmin/10-1)*10;
	my $graph = GD::Graph::mixed->new(TABLE_WIDTH-10,200);
	$graph->set(x_label => 'Data point',
		    y_label => 'Fragment length',
		    title => $name,
		    types => [ qw( lines points ) ],
		    default_type => 'lines',
		    y_max_value => $ymax,
		    y_min_value => 0,
		    x_max_value => $xmax,
		    x_min_value => $xmin,
		    y_tick_number => $ymax/100,
		    x_tick_number => 10,
		    marker_size => 3,
		    line_width => 1,
		    tick_length => -3,
		    text_space => 11,
		    transparent => 0,
		    long_ticks       => 1, #show grid
		    x_ticks          => 0,
		    x_label_position => 1/2,
#		    show_values      => 0,
#		    x_labels_vertical => 1,
		    dclrs => ['dgray','lblue']
	    ) or warn $graph->error;
	$graph->set_x_label_font(GD::gdMediumBoldFont);
	$graph->set_y_label_font(GD::gdMediumBoldFont);
	$graph->set_x_axis_font(GD::gdSmallFont);
	$graph->set_y_axis_font(GD::gdTinyFont);
#  $graph->set_values_font(GD::gdMediumBoldFont);
	$graph->set_legend_font(GD::gdLargeFont);
	$graph->set_legend('Fitted curve','Size standard');
	my $idc = $id.$counter++;
#	my $hidden = &generateHiddenContent(0,\@data,$id,[$name]);
	my $hidden = '';
	push(@graphs,&generateImagePart($id,$graph->plot(\@data),$hidden,1));
	my $accuracy = 5;
	push(@graphs,$q->font({-class => 'footer'},'<i>y</i> = '.($xc ? abs(&reformatNumber($xc,$accuracy))."<i>x</i><sup>2</sup>" : '').($xb<0 ? ' - ' : ' + ').abs(&reformatNumber($xb,$accuracy)).'<i>x</i>'.($xa<0 ? ' - ' : ' + ').abs(&reformatNumber($xa,$accuracy)).'&nbsp;&nbsp;&nbsp; --- &nbsp;&nbsp;&nbsp;'.'R<sup>2</sup> = '.sprintf("%.5f",$r2)).$q->br());
    }
    return join("<br />",@graphs);
}

sub reformatNumber {
    my $number = shift;
    my $accuracy = shift;
    $number =~ /^(.*)e([-+]\d+)$/;
    my $new = $1 || 0;
    my $tens = $2 || 0;
    my $out = int($number * (10 ** $accuracy) + 0.5)/(10 ** $accuracy);
    if($number != 0 && $tens && ($out == 0 || $out =~ /e/)) {
	$number = sprintf("%.0f",$new).'e'.$tens;
    } else {
	$number = sprintf("%.".$accuracy."f",$number);
    }
    return $number;
}

sub generateRawDataPlots {
    my ($inputs,$id) = @_;
    return 0 unless(defined $inputs);
    #normally 23024 data points per input file
    my @graphs;
    my $counter = 1;
    my (@data,$ymax1,$ymax2,$xmax,$tmp);
    foreach my $name (sort keys %$inputs) {
	@data = ();
	$ymax1 = 0;
	$ymax2 = 0;
	$xmax = 0;
	foreach my $m (@{$inputs->{$name}->[0]}) {
	    $ymax2 = $m if($m > $ymax2);
	    $tmp = $inputs->{$name}->[1]->[$xmax];
	    $ymax1 = $tmp if($tmp > $ymax1);
	    push(@{$data[2]},($m < 0 ? 0 : $m)); #sample
	    push(@{$data[1]},($tmp < 0 ? 0 : $tmp)); #standard
	    push(@{$data[0]},++$xmax); #++ bc data points start at 1, array at 0
#	    print ($m < 0 ? ("0,") : ($m.","));
	}
	$ymax1 = int($ymax1*1.02/5+1)*5;
	$ymax2 = int($ymax2*1.02/5+1)*5;
	$xmax = int($xmax/8+1)*8;
	my $graph = GD::Graph::mixed->new(TABLE_WIDTH-10,200);
	$graph->set(x_label => 'Data point',
#		    y_label => 'Intensity',
		    y1_label => 'Standard intensity',
		    y2_label => 'Sample intensity',
		    two_axes => 1,
#		    y_min_value => 0,
#		    y_max_value => $ymax,
		    y1_max_value => $ymax1,
		    y2_max_value => $ymax2,
		    title => $name,
		    types => [ qw( lines lines ) ],
		    default_type => 'lines',
		    x_max_value => $xmax,
		    x_min_value => 0,
		    y_tick_number => 5,
#		    line_width => 3,
		    tick_length => -3,
		    text_space => 11,
		    transparent => 0,
#		    long_ticks       => 1, #show grid
#		    y_ticks          => 1,
#		    y_tick_number    => 10,
		    x_tick_number => 8,
		    x_label_position => 1/2,
#		    show_values      => 0,
#		    x_labels_vertical => 1,
		    dclrs => ['lgray','lblue']
	    ) or warn $graph->error;
	$graph->set_x_label_font(GD::gdMediumBoldFont);
	$graph->set_y_label_font(GD::gdMediumBoldFont);
	$graph->set_x_axis_font(GD::gdSmallFont);
	$graph->set_y_axis_font(GD::gdTinyFont);
	$graph->set_values_font(GD::gdMediumBoldFont);
	$graph->set_legend_font(GD::gdLargeFont);
	$graph->set_legend('Standard raw data','Sample raw data');
	my $idc = $id.$counter++;
#	my $hidden = &generateHiddenContent(0,\@data,$id,[$name]);
	my $hidden = '';
	push(@graphs,&generateImagePart($id,$graph->plot(\@data),$hidden,1));
    }
    return join("<br />"x2,@graphs);
}

sub generatePrimerMatchingTable {
    my ($dbh,$lengthids,$id) = @_;
    my ($stm,$href,$ids);
    my ($hidden,$contentA,$contentD,$missing);
    $ids = 'organism.id='.join(" OR organism.id=",keys %{$lengthids->{organism}});
    $stm = 'SELECT organism.id,organism.name,taxon.kingdom,taxon.phylum,trophic.kind as t,pathogenic.kind as p FROM organism LEFT JOIN (taxon,trophic,pathogenic) ON (organism.taxon_id=taxon.id AND organism.pathogenic_id=pathogenic.id AND organism.trophic_id=trophic.id) WHERE '.$ids;
    $href = $dbh->selectall_hashref($stm,'id');
    my %data;
    foreach my $id (keys %$href) {
	if(exists $lengthids->{organism}->{$id}->{match}) {
	    $data{kingdom}->{$href->{$id}->{kingdom}}->{matching}->{orgn}->{all}++ unless(exists $lengthids->{organism}->{$id}->{nomatch});
	    $data{kingdom}->{$href->{$id}->{kingdom}}->{matching}->{orgn}->{any}++;
	    $data{kingdom}->{$href->{$id}->{kingdom}}->{matching}->{reg} += scalar(keys %{$lengthids->{organism}->{$id}->{match}});
	    $data{phylum}->{$href->{$id}->{phylum}}->{matching}->{orgn}->{all}++ unless(exists $lengthids->{organism}->{$id}->{nomatch});
	    $data{phylum}->{$href->{$id}->{phylum}}->{matching}->{orgn}->{any}++;
	    $data{phylum}->{$href->{$id}->{phylum}}->{matching}->{reg} += scalar(keys %{$lengthids->{organism}->{$id}->{match}});
	    $data{trophic}->{$href->{$id}->{t}}->{matching}->{orgn}->{all}++ unless(exists $lengthids->{organism}->{$id}->{nomatch});
	    $data{trophic}->{$href->{$id}->{t}}->{matching}->{orgn}->{any}++;
	    $data{trophic}->{$href->{$id}->{t}}->{matching}->{reg} += scalar(keys %{$lengthids->{organism}->{$id}->{match}});
	    $data{pathogenicity}->{$href->{$id}->{p}}->{matching}->{orgn}->{all}++ unless(exists $lengthids->{organism}->{$id}->{nomatch});
	    $data{pathogenicity}->{$href->{$id}->{p}}->{matching}->{orgn}->{any}++;
	    $data{pathogenicity}->{$href->{$id}->{p}}->{matching}->{reg} += scalar(keys %{$lengthids->{organism}->{$id}->{match}});
	}
	if (exists $lengthids->{organism}->{$id}->{nomatch}) {
	    $data{kingdom}->{$href->{$id}->{kingdom}}->{missing}->{orgn}->{all}++ unless(exists $lengthids->{organism}->{$id}->{match});
	    $data{kingdom}->{$href->{$id}->{kingdom}}->{missing}->{orgn}->{any}++;
	    $data{kingdom}->{$href->{$id}->{kingdom}}->{missing}->{reg} += scalar(keys %{$lengthids->{organism}->{$id}->{nomatch}});
	    $data{phylum}->{$href->{$id}->{phylum}}->{missing}->{orgn}->{all}++ unless(exists $lengthids->{organism}->{$id}->{match});
	    $data{phylum}->{$href->{$id}->{phylum}}->{missing}->{orgn}->{any}++;
	    $data{phylum}->{$href->{$id}->{phylum}}->{missing}->{reg} += scalar(keys %{$lengthids->{organism}->{$id}->{nomatch}});
	    $data{trophic}->{$href->{$id}->{t}}->{missing}->{orgn}->{all}++ unless(exists $lengthids->{organism}->{$id}->{match});
	    $data{trophic}->{$href->{$id}->{t}}->{missing}->{orgn}->{any}++;
	    $data{trophic}->{$href->{$id}->{t}}->{missing}->{reg} += scalar(keys %{$lengthids->{organism}->{$id}->{nomatch}});
	    $data{pathogenicity}->{$href->{$id}->{p}}->{missing}->{orgn}->{all}++ unless(exists $lengthids->{organism}->{$id}->{match});
	    $data{pathogenicity}->{$href->{$id}->{p}}->{missing}->{orgn}->{any}++;
	    $data{pathogenicity}->{$href->{$id}->{p}}->{missing}->{reg} += scalar(keys %{$lengthids->{organism}->{$id}->{nomatch}});
	}
    }
    my (@tableData,@tableDataD);
    foreach my $group ('kingdom','phylum','trophic','pathogenicity') {
	foreach my $subgroup (sort keys %{$data{$group}}) {
	    my $matching = $data{$group}->{$subgroup}->{matching};
	    my $missing  = $data{$group}->{$subgroup}->{missing};
	    push(@tableData,[ucfirst($group),$subgroup,($matching->{orgn}->{all} || 0).' ('.($missing->{orgn}->{all} || 0).')',($matching->{orgn}->{any} || 0).' ('.($missing->{orgn}->{any} || 0).')',($matching->{reg} ||0).' ('.($missing->{reg} || 0).')']);
	}
    }
    my $header = ['Categorie',' ','# Organisms matching (not matching) primer set with all regions','# Organisms matching (not matching) primer set with any region','# Regions matching (not matching) primer set'];
    $hidden = &generateHiddenContent($header,\@tableData,$id.'_a');
    map {$_->[2] =~ s/(.*)(\s\(.*\))/\<b\>$1\<\/b\>$2/;
	 $_->[3] =~ s/(.*)(\s\(.*\))/\<b\>$1\<\/b\>$2/;
	 $_->[4] =~ s/(.*)(\s\(.*\))/\<b\>$1\<\/b\>$2/;} @tableData;
    $contentA = &generateTableContent($header,\@tableData,2);
    my $chart = &generatePrimerMatchingChart($lengthids,'primermatchchart');
    return &generateTablePart($id,$hidden,$contentA).($q->br()x2).$chart;
}

sub generatePrimerMatchingChart {
    my ($lengthids,$id) = @_;
    my ($hidden,@data,$xmax);
    my $step = 10;
    my $max = 3000; #MAX_LENGTH
    my $min = 2000; #Min length
    $xmax = (reverse sort {$a <=> $b} keys %{$lengthids->{length}})[0];
    $xmax = $max unless($xmax < $max);
    $xmax = $min if($xmax < $min);
    $xmax = int($xmax/$step+1)*$step if($xmax % $step);
    for my $x (0..$xmax) {
	push(@{$data[0]},$x);
	push(@{$data[1]},(exists $lengthids->{length}->{$x} ? scalar(keys %{$lengthids->{length}->{$x}}) : 0));
    }
    my @colors = ('blue');
    my $height = 200+50+40;
    my $graph = GD::Graph::lines->new(TABLE_WIDTH-10,$height);
    $graph->set(
		x_label          => 'Fragment length',
		y_label          => 'Number of fragments',
		title            => 'Length distribution of fragments matching primer set',
#		legend_spacing   => 5,
#		legend_placement => 'RT', #B[LCR] | R[TCB]
#		bar_width        => 8,
#		bar_spacing      => 1,
#		bargroup_spacing => 5,
#		long_ticks       => 1, #show grid
#		x_ticks          => 0,
	        x_tick_number    => $step,
#		y_tick_number    => 10,
	        y_min_value      => 0,
#	        x_min_value      => 0,
	        x_max_value      => $xmax,
		x_label_position => 1/2,
#		show_values      => 1,
	        box_axis         => 0,
                line_width       => 1,
	        tick_length      => -3,
		text_space       => 11,
	        transparent      => 0,
		dclrs => \@colors
		) or warn $graph->error;
    $graph->set_x_label_font(GD::gdMediumBoldFont);
    $graph->set_y_label_font(GD::gdMediumBoldFont);
    $graph->set_x_axis_font(GD::gdSmallFont);
    $graph->set_y_axis_font(GD::gdSmallFont);
    $graph->set_values_font(GD::gdTinyFont);
    my $chart = $graph->plot(\@data) or die $graph->error;
    $hidden = &generateHiddenContent(0,\@data,$id,0,\@colors);
    return &generateImagePart($id,$chart,$hidden);
}

sub generateLengthTable {
    my ($dbh,$length,$removedDataLine,$id) = @_;
    my ($stm,$href,$ids);
    my ($hidden,$contentA,$contentD,$missing);
    my %tmp;
    foreach(values %$length) {#name
	foreach(values %$_) {#input fragment length
	    foreach my $x (values %$_) {#db fragment length
		foreach my $regid (keys %$x) {#region id
		    $tmp{orgnid}->{$_} = 1 foreach(keys %{$x->{$regid}}); #orgnanism id
		    $tmp{regid}->{$regid} = 1; #region id
		}
	    }
	}
    }
    $ids = 'id='.join(" OR id=",keys %{$tmp{orgnid}});
    $stm = 'SELECT id,name,taxid FROM organism WHERE '.$ids;
    $href = $dbh->selectall_hashref($stm,'id');
    my (@tableData,@tableDataD);
    my (%names,@nomatch);
    foreach my $name (sort keys %$length) {
	my $add = 0;
	foreach my $inputlength (sort {$a <=> $b} keys %{$length->{$name}}) {
	    if(scalar(keys %{$length->{$name}->{$inputlength}})) {
		foreach my $dblength (sort {$a <=> $b} keys %{$length->{$name}->{$inputlength}}) {
		    foreach my $region_id (sort {$a <=> $b} keys %{$length->{$name}->{$inputlength}->{$dblength}}) {
			foreach my $orgn_id (keys %{$length->{$name}->{$inputlength}->{$dblength}->{$region_id}}) {
			    my $orgn_name = (exists $href->{$orgn_id} ? $href->{$orgn_id}->{name} : 'unknown');
			    $names{$orgn_name} = (exists $href->{$orgn_id} ? $href->{$orgn_id}->{taxid} : 0);
			    push(@tableData,[$name,$inputlength.' ('.int($inputlength+0.5).')',$dblength,$region_id,$orgn_name]);
			    push(@tableDataD,[$name,$inputlength.' ('.int($inputlength+0.5).')',$dblength,$region_id,$orgn_name]);
			    $add = 1;
			}
		    }
		}
	    } else {
		push(@tableDataD,[$name,$inputlength,'-','-','-']);
	    }
	}
	push(@nomatch,$name) unless($add);
    }
    $missing = $removedDataLine.$q->br() if($removedDataLine);
    $missing .= $q->font({-class => 'table_info2'},$q->b('No matching length: ').join(", ",@nomatch)).($q->br()x2) if(@nomatch);
    my $header = ['Sample name','Input length','Matching DB length','Region ID','Organism name'];
    $hidden = &generateHiddenContent($header,\@tableData,$id.'_a');
    map {$_->[3]=$q->a({href => 'showRegion.cgi?id='.$_->[3], target => '_blank'},$_->[3]);
	 $_->[4]=$q->a({href => LINKOUT_TAX.$names{$_->[4]}, target => '_blank'},$_->[4]);} @tableData;
    $contentA = &generateTableContent($header,\@tableData,1);
    $header = ['Sample name','Input length','Matching DB length','Region ID','Organism name'];
    $contentD = &generateTableContent($header,\@tableDataD,1);
    $hidden .= &generateHiddenContent($header,\@tableDataD,$id.'_d');
    my $labels = {'d' => 'All length',
		  'a' => 'Length with match'};
    return &generateTablePart($id,$hidden,$contentA,$contentD,$missing,$labels);
}

sub generateOrganismTable {
    my ($dbh,$orgn,$removedDataLine,$id) = @_;
    my ($stm,$href,$ids);
    my ($hidden,$contentAll,$contentAny,$missing);
    $missing = '';
    my %tmp;
    foreach(values %$orgn) {#name
	$tmp{$_} = 1 foreach(keys %{$_}); #organism id
    }
    $ids = 'organism.id='.join(" OR organism.id=",keys %tmp);
    $stm = 'SELECT organism.id,name,trophic.kind as t,pathogenic.kind as p,organism.taxid FROM organism LEFT JOIN (trophic,pathogenic) ON (organism.trophic_id=trophic.id AND organism.pathogenic_id=pathogenic.id) WHERE '.$ids;
    $href = $dbh->selectall_hashref($stm,'id');
    my (@tableDataAll,@tableDataAny,@nomatch,%names);
    foreach my $name (sort keys %$orgn) {
	if(scalar(keys %{$orgn->{$name}})) {
	    foreach my $orgn_id (sort {$href->{$a}->{name} cmp $href->{$b}->{name}} keys %{$orgn->{$name}}) {
		my $orgn_name = (exists $href->{$orgn_id} ? $href->{$orgn_id}->{name} : 'unknown');
		my $trophic = (exists $href->{$orgn_id} ? $href->{$orgn_id}->{t} : 'unknown');
		my $pathogenic = (exists $href->{$orgn_id} ? $href->{$orgn_id}->{p} : 'unknown');
		$names{$orgn_name} = (exists $href->{$orgn_id} ? $href->{$orgn_id}->{taxid} : 0);
		my (@hit,@nohit);
		@hit = sort {$a <=> $b} values %{$orgn->{$name}->{$orgn_id}->{hit}} if(exists $orgn->{$name}->{$orgn_id}->{hit});
		@nohit = sort {$a <=> $b} values %{$orgn->{$name}->{$orgn_id}->{nohit}} if(exists $orgn->{$name}->{$orgn_id}->{nohit});
		my $countnomatch = (exists $orgn->{$name}->{$orgn_id}->{nomatch} ? scalar(keys %{$orgn->{$name}->{$orgn_id}->{nomatch}}) : 0);
		my $countmatch = scalar(@hit)+scalar(@nohit);
		my $all = (scalar(@nohit) == 0 && scalar(@hit) > 0 ? 'x' : '');
		push(@tableDataAny,[$name,$orgn_name,$countmatch.' out of '.($countmatch+$countnomatch),join("; ",@hit) || '-',join("; ",@nohit) || '-',$trophic,$pathogenic,$all]);
		push(@tableDataAll,[$name,$orgn_name,$countmatch.' out of '.($countmatch+$countnomatch),join("; ",@hit) || '-',$trophic,$pathogenic]) if($all);

	    }
	} else {
	    push(@nomatch,$name);
	}
    }
    my $headerAny = ['Sample name','Potentially matching organism','# Regions with primer match','Length of region(s) matching data','Length of region(s) missing in input data','T*','P*','All*'];
    my $headerAll = ['Sample name','Potentially matching organism','# Regions with primer match','Length of region(s) matching data','T*','P*'];
    $hidden = &generateHiddenContent($headerAny,\@tableDataAny,$id.'_d');
    $hidden .= &generateHiddenContent($headerAll,\@tableDataAll,$id.'_a');
    map {$_->[1]=$q->a({href => LINKOUT_TAX.$names{$_->[1]}, target => '_blank'},$_->[1]);
	 $_->[4]=$q->img({-src => '../../'.ADAPT_DIR.$_->[4].'.png',-border => '0',-alt => $_->[4]});
	 $_->[5]=$q->img({-src => '../../'.ADAPT_DIR.$_->[5].'.png',-border => '0',-alt => $_->[5]});} @tableDataAll;
    map {$_->[1]=$q->a({href => LINKOUT_TAX.$names{$_->[1]}, target => '_blank'},$_->[1]);
	 $_->[5]=$q->img({-src => '../../'.ADAPT_DIR.$_->[5].'.png',-border => '0',-alt => $_->[5]});
	 $_->[6]=$q->img({-src => '../../'.ADAPT_DIR.$_->[6].'.png',-border => '0',-alt => $_->[6]});
	 $_->[7]=$q->img({-src => '../../'.ADAPT_DIR.'ok.png',-border => '0',-alt => 'ok'}) if($_->[7]);} @tableDataAny;
    $contentAll = &generateTableContent($headerAll,\@tableDataAll,2);
    $contentAny = &generateTableContent($headerAny,\@tableDataAny,2);
    $missing = $removedDataLine.$q->br() if($removedDataLine);
    $missing .= $q->font({-class => 'table_info2'},$q->b('No primer matches: ').join(", ",@nomatch)).$q->br() if(@nomatch);
    my $legend = $q->start_table({-border =>'0',-cellpadding => '2',-cellspacing => '0'}).$q->Tr($q->td({-class => 'legend'},$q->font({-class => 'table_info2'},'<b>* Legend:&nbsp;&nbsp;</b>')).$q->td({-class => 'legend'},$q->font({-class => 'table_info2'},'<u>T</u>rophicity&nbsp;&nbsp;')).$q->td({-class => 'legend'},$q->img({-src => '../../'.ADAPT_DIR.'autotrophic.png',-border => '0',-alt => 'green'})).$q->td({-class => 'legend'},$q->font({-class => 'table_info2'},' autotrophic').('&nbsp;'x3)).$q->td({-class => 'legend'},$q->img({-src => '../../'.ADAPT_DIR.'heterotrophic.png',-border => '0',-alt => 'blue'})).$q->td({-class => 'legend'},$q->font({-class => 'table_info2'},' heterotrophic').('&nbsp;'x3)).$q->td({-class => 'legend'},$q->img({-src => '../../'.ADAPT_DIR.'unknown.png',-border => '0',-alt => 'gray'})).$q->td({-class => 'legend'},$q->font({-class => 'table_info2'},' unknown').('&nbsp;'x3))).$q->Tr($q->td({-class => 'legend'},$q->font({-class => 'table_info2'},'&nbsp;')).$q->td({-class => 'legend'},$q->font({-class => 'table_info2'},'<u>P</u>athogenicity&nbsp;&nbsp;')).$q->td({-class => 'legend'},$q->img({-src => '../../'.ADAPT_DIR.'pathogenic.png',-border => '0',-alt => 'red'})).$q->td({-class => 'legend'},$q->font({-class => 'table_info2'},' pathogenic').('&nbsp;'x3)).$q->td({-class => 'legend'},$q->img({-src => '../../'.ADAPT_DIR.'nonpathogenic.png',-border => '0',-alt => 'green'})).$q->td({-class => 'legend'},$q->font({-class => 'table_info2'},' nonpathogenic')).('&nbsp;'x3).$q->td({-class => 'legend'},$q->img({-src => '../../'.ADAPT_DIR.'unknown.png',-border => '0',-alt => 'gray'})).$q->td({-class => 'legend'},$q->font({-class => 'table_info2'},' unknown'))).$q->Tr($q->td({-class => 'legend'},$q->font({-class => 'table_info2'},'&nbsp;')).$q->td({-class => 'legend'},$q->font({-class => 'table_info2'},'<u>All</u>')).$q->td({-class => 'legend'},$q->img({-src => '../../'.ADAPT_DIR.'ok.png',-border => '0',-alt => 'all'})).$q->td({-class => 'legend',-colspan => 5},$q->font({-class => 'table_info2'},'Input data matches all fragment lengths of this organism'))).$q->end_table();
    my $labels = {'a' => 'all fragments are matching',
		  'd' => 'any fragment is matching'};
    return &generateTablePart($id,$hidden,$contentAll,$contentAny,$missing.$legend,$labels);
}

sub generatePhylumHitTable {
    my ($dbh,$regids,$id) = @_;
    my ($hidden,$contentA,$contentD);
    #abbreviated table
    my %tmp;
    foreach(values %$regids) {
	foreach(values %$_) {
	    $tmp{$_} = 1 foreach(@$_);
	}
    }
    my $ids = 'region.id='.join(" OR region.id=",keys %tmp);
    my ($stm,$href);
    $stm = 'SELECT region.id,kingdom,phylum FROM taxon INNER JOIN (region,organism_region,organism) ON (region.id=organism_region.region_id AND organism.id=organism_region.organism_id AND taxon.id=organism.taxon_id) WHERE '.$ids;
    $href = $dbh->selectall_hashref($stm,"id");
    my (%taxa,@tableData);
    foreach my $nameH (values %$regids) {
	foreach my $inputLength (values %$nameH) {
	    foreach my $id (@{$inputLength}) {
		$taxa{$href->{$id}->{kingdom}}->{$href->{$id}->{phylum}}->{hitCount}++;
	    }
	}
    }
    foreach my $kingdom (sort keys %taxa) {
	foreach my $phylum (sort keys %{$taxa{$kingdom}}) {
	    push(@tableData,[$kingdom,$phylum,$taxa{$kingdom}->{$phylum}->{hitCount}]);
	}
    }
    $contentA = &generateTableContent(['Domain (Kingdom)','Phylum','# Matching Regions'],\@tableData,1);
    $hidden = &generateHiddenContent(['Domain (Kingdom)','Phylum','# Matching Regions'],\@tableData,$id.'_a');
    #detailed table
    my (%taxaD,@tableDataD);
    foreach my $name (keys %$regids) {
	foreach my $inputLength (values %{$regids->{$name}}) {
	    foreach my $id (@{$inputLength}) {
		$taxaD{$name}->{$href->{$id}->{kingdom}}->{$href->{$id}->{phylum}}->{hitCount}++;
	    }
	}
    }
    foreach my $name (sort keys %taxaD) {
	foreach my $kingdom (sort keys %{$taxaD{$name}}) {
	    foreach my $phylum (sort keys %{$taxaD{$name}->{$kingdom}}) {
		push(@tableDataD,[$name,$kingdom,$phylum,$taxaD{$name}->{$kingdom}->{$phylum}->{hitCount}]);
	    }
	}
    }
    $contentD = &generateTableContent(['Sample name','Domain (Kingdom)','Phylum','# Matching Regions'],\@tableDataD,1);
    $hidden .= &generateHiddenContent(['Sample name','Domain (Kingdom)','Phylum','# Matching Regions'],\@tableDataD,$id.'_d');
    #generate and return table div
    return &generateTablePart($id,$hidden,$contentA,$contentD);
}

sub generateHitTable {
    my ($dbh,$ITSids,$removedDataLine,$id) = @_;
    my ($stm,$aref);
    my ($hidden,$contentA,$contentD);
    #abbreviated table
    my @tableData;
    foreach my $name (sort keys %$ITSids) {
	foreach my $inputLength (sort {$a<=>$b} keys %{$ITSids->{$name}}) {
	    my @ids = @{$ITSids->{$name}->{$inputLength}};
	    if(@ids && scalar(@ids)>0) {
		$stm = 'SELECT \''.$name.'\',CONCAT('.$inputLength.',\' (\',ROUND('.$inputLength.',0),\')\'),length,COUNT(tropha.kind),COUNT(trophh.kind),COUNT(pathop.kind),COUNT(pathon.kind) FROM region INNER JOIN (organism_region,organism) ON (region.id=organism_region.region_id AND organism_region.organism_id=organism.id) LEFT JOIN (SELECT organism.id,kind FROM organism,trophic WHERE trophic.kind=\'autotrophic\' AND organism.trophic_id=trophic.id) AS tropha ON tropha.id=organism.id LEFT JOIN (SELECT organism.id,kind FROM organism,trophic WHERE trophic.kind=\'heterotrophic\' AND organism.trophic_id=trophic.id) AS trophh ON trophh.id=organism.id LEFT JOIN (SELECT organism.id,kind FROM organism,pathogenic WHERE pathogenic.kind=\'pathogenic\' AND organism.pathogenic_id=pathogenic.id) AS pathop ON pathop.id=organism.id LEFT JOIN (SELECT organism.id,kind FROM organism,pathogenic WHERE pathogenic.kind=\'nonpathogenic\' AND organism.pathogenic_id=pathogenic.id) AS pathon ON pathon.id=organism.id WHERE region.id='.join(" OR region.id=",@ids).' GROUP BY length ORDER BY length';
		$aref = $dbh->selectall_arrayref($stm);
	    } else {
		$aref = undef;
	    }
	    if($aref) {
		push(@tableData,@$aref);
	    } else {
		push(@tableData,[$name,$inputLength,'no hit',0,0,0,0])
	    }
	}
    }
    $hidden .= &generateHiddenContent(['Sample name','Input length','DB length','Autotrophic hits','Heterotrophic hits','Pathogenic hits','Nonpathogenic hits'],\@tableData,$id.'_a');
    $contentA = &generateTableContent(['Sample name','Input length','DB length','Autotrophic hits','Heterotrophic hits','Pathogenic hits','Nonpathogenic hits'],\@tableData,1);
    #detailed table
    my (@tableDataD,@tableDataH);
    foreach my $name (sort keys %$ITSids) {
	(my $tmpname = $name) =~ s/(.{10})/$1 /g;
	foreach my $inputLength (sort {$a<=>$b} keys %{$ITSids->{$name}}) {
	    my @ids = @{$ITSids->{$name}->{$inputLength}};
	    if(@ids && scalar(@ids)>0) {
		$stm = 'SELECT \''.$name.'\',CONCAT('.$inputLength.',\' (\',ROUND('.$inputLength.',0),\')\'),length,trophic.kind AS trophic,pathogenic.kind AS pathogenic,CONCAT(taxon.genus,\' \',taxon.species) as gs,taxid,sequence FROM region INNER JOIN (organism_region,organism,trophic,pathogenic,taxon) ON (region.id=organism_region.region_id AND organism_region.organism_id=organism.id AND organism.trophic_id=trophic.id AND organism.pathogenic_id=pathogenic.id AND organism.taxon_id=taxon.id) WHERE region.id='.join(" OR region.id=",@ids).' ORDER BY length,trophic,pathogenic,gs';
		$aref = $dbh->selectall_arrayref($stm);
	    } else {
		$aref = undef;
	    }
	    if($aref) {
		push(@tableDataH,@$aref);
	    } else {
		push(@tableDataH,[$name,$inputLength.' ('.int($inputLength+0.5).')','no hit','-','-','-','-']);
	    }
	    if(@ids && scalar(@ids)>0) {
	    $stm = 'SELECT \''.$tmpname.'\',CONCAT('.$inputLength.',\' (\',ROUND('.$inputLength.',0),\')\'),length,trophic.kind AS trophic,pathogenic.kind AS pathogenic,CONCAT(\'<a href="'.LINKOUT_TAX.'\',taxid,\'" target="_blank">\',taxon.genus,\' \',taxon.species,\'</a>\') AS taxid,CONCAT(\'<a href="showSeq.cgi?id=\',region.id,\'" target="_blank">\',LEFT(sequence,5),\'...</a>\') AS seq FROM region INNER JOIN (organism_region,organism,trophic,pathogenic,taxon) ON (region.id=organism_region.region_id AND organism_region.organism_id=organism.id AND organism.trophic_id=trophic.id AND organism.pathogenic_id=pathogenic.id AND organism.taxon_id=taxon.id) WHERE region.id='.join(" OR region.id=",@ids).' ORDER BY length,trophic,pathogenic,genus,species';
	    $aref = $dbh->selectall_arrayref($stm);
	    }
	    if($aref) {
		push(@tableDataD,@$aref);
	    } else {
		push(@tableDataD,[$tmpname,$inputLength.' ('.int($inputLength+0.5).')','no hit','-','-','-','-']);
	    }
	}
    }
    $hidden .= &generateHiddenContent(['Sample name','Input length','DB length','Trophic','Pathogenicity','Genus species','Sequence'],\@tableDataH,$id.'_d');
    $contentD = &generateTableContent(['Sample name','Input length','DB length','Trophic','Pathogenicity','Genus species','Sequence'],\@tableDataD,1,2);
    #generate and return table div
    return &generateTablePart($id,$hidden,$contentA,$contentD,$removedDataLine);
}

sub generateFractionData {
    my ($dbh,$orgn,$length,$goodDataHash,$types,$fraction) = @_;
    my ($stm,$href,$ids);
    my %tmp;
    foreach(values %$orgn) {#name
	$tmp{$_} = 1 foreach(keys %{$_}); #organism id
    }
    $ids = 'organism.id='.join(" OR organism.id=",keys %tmp);
    $stm = 'SELECT organism.id,'.$types->{table}.'.kind as kind FROM organism LEFT JOIN '.$types->{table}.' ON organism.'.$types->{table}.'_id='.$types->{table}.'.id WHERE '.$ids;
    $href = $dbh->selectall_hashref($stm,'id');
    %tmp = ();
    foreach my $name (sort keys %$orgn) {
	if(scalar(keys %{$orgn->{$name}})) {
	    foreach my $orgn_id (keys %{$orgn->{$name}}) {
		my $kind = (exists $href->{$orgn_id} ? $href->{$orgn_id}->{kind} : 'unknown');
		my (@hit,@nohit);
		@hit = sort {$a <=> $b} values %{$orgn->{$name}->{$orgn_id}->{hit}} if(exists $orgn->{$name}->{$orgn_id}->{hit});
		@nohit = values %{$orgn->{$name}->{$orgn_id}->{nohit}} if(exists $orgn->{$name}->{$orgn_id}->{nohit});
		foreach(@hit) {
		    $tmp{any}->{$_}->{$kind}++;
		    $tmp{all}->{$_}->{$kind}++ unless(scalar(@nohit));
		}
	    }
	}
    }

    my %data;
    foreach my $name (sort keys %$length) {
	foreach my $inputlength (keys %{$length->{$name}}) {
	    if(scalar(keys %{$length->{$name}->{$inputlength}})) { #db matching length
		foreach my $dblength (sort {$a <=> $b} keys %{$length->{$name}->{$inputlength}}) {
		    foreach my $kind ($types->{a},$types->{b},'unknown') {
			 $data{$name}->{$inputlength}->{any}->{$kind} += (exists $tmp{any}->{$dblength}->{$kind} ? $tmp{any}->{$dblength}->{$kind} : 0);
			 $data{$name}->{$inputlength}->{all}->{$kind} += (exists $tmp{all}->{$dblength}->{$kind} ? $tmp{all}->{$dblength}->{$kind} : 0);
		    }
		}
	    }
	}
    }

    #loop trough input files (names)
    my (@tableDataAnyW,@tableDataAnyWo,@tableDataAllW,@tableDataAllWo); #table data
    my (@chartDataAnyW,@chartDataAnyWo,@chartDataAllW,@chartDataAllWo); #chart data
    my (@divDataAnyW,@divDataAnyWo,@divDataAllW,@divDataAllWo); #data for tooltip div's
    my ($AnyW_a,$AnyW_b,$AnyW_u,$AnyW_n,$AnyWo_a,$AnyWo_b,$AnyWo_u,$AllW_a,$AllW_b,$AllW_u,$AllW_n,$AllWo_a,$AllWo_b,$AllWo_u); #Average fraction B for type a, b, unknown, no hit
    my ($S_w,$S_anywo,$S_allwo);
    foreach my $name (sort keys %$goodDataHash) {
	#calculate sum S for with and without db matches
	$S_w = $S_anywo = $S_allwo = 0;
	foreach my $inputlength (keys %{$goodDataHash->{$name}}) {
	    $S_w += $goodDataHash->{$name}->{$inputlength};
	    my $sum_m_ij = 0;
	    $sum_m_ij += $_ foreach(values %{$data{$name}->{$inputlength}->{all}});
	    if($sum_m_ij && scalar(keys %{$length->{$name}->{$inputlength}})) {
		$S_allwo += $goodDataHash->{$name}->{$inputlength};
	    }
	    if(scalar(keys %{$length->{$name}->{$inputlength}})) {
		$S_anywo += $goodDataHash->{$name}->{$inputlength} ; #db matching length
	    }
	}

	#calculate average fraction
	$AnyW_a = $AnyW_b = $AnyW_u = $AnyW_n = $AnyWo_a = $AnyWo_b = $AnyWo_u = $AllW_a = $AllW_b = $AllW_u = $AllW_n = $AllWo_a = $AllWo_b = $AllWo_u = 0;
	my (@aLengthAll,@bLengthAll,@uLengthAll,@nLengthAll,@aLengthAny,@bLengthAny,@uLengthAny,@nLengthAny); #used length
	foreach my $inputlength (keys %{$goodDataHash->{$name}}) {
	    my $h_i= $goodDataHash->{$name}->{$inputlength};
 	    my $F_i_w = 100*$h_i/$S_w;
	    my $F_i_anywo = $S_anywo ? 100*$h_i/$S_anywo : 0;
	    my $F_i_allwo = $S_allwo ? 100*$h_i/$S_allwo : 0;

	    #all
	    my $sum_m_ij = 0;
	    $sum_m_ij += $_ foreach(values %{$data{$name}->{$inputlength}->{all}});
	    if($sum_m_ij == 0 || scalar(keys %{$length->{$name}->{$inputlength}}) == 0) { #no hit to database for all fragment length
		$AllW_n += $F_i_w;
 		push(@nLengthAll,$inputlength);
	    } else { #at least 1 hit to database
		my $tmp_w = $sum_m_ij ? ($F_i_w / $sum_m_ij) : 0;
		my $tmp_wo = $sum_m_ij ? ($F_i_allwo / $sum_m_ij) : 0;
		if($data{$name}->{$inputlength}->{all}->{$types->{a}}) {
		    $AllW_a += $data{$name}->{$inputlength}->{all}->{$types->{a}} * $tmp_w;
		    $AllWo_a += $data{$name}->{$inputlength}->{all}->{$types->{a}} * $tmp_wo;
		    push(@aLengthAll,$inputlength);
		}
		if($data{$name}->{$inputlength}->{all}->{$types->{b}}) {
		    $AllW_b += $data{$name}->{$inputlength}->{all}->{$types->{b}} * $tmp_w;
		    $AllWo_b += $data{$name}->{$inputlength}->{all}->{$types->{b}} * $tmp_wo;
		    push(@bLengthAll,$inputlength);
		}
		if($data{$name}->{$inputlength}->{all}->{'unknown'}) {
		    $AllW_u += $data{$name}->{$inputlength}->{all}->{'unknown'} * $tmp_w;
		    $AllWo_u += $data{$name}->{$inputlength}->{all}->{'unknown'} * $tmp_wo;
		    push(@uLengthAll,$inputlength);
		}
	    }

	    #any
	    $sum_m_ij = 0;
	    $sum_m_ij += $_ foreach(values %{$data{$name}->{$inputlength}->{any}});
	    if(scalar(keys %{$length->{$name}->{$inputlength}}) == 0) { #no hit to database
 		$AnyW_n += $F_i_w;
		push(@nLengthAny,$inputlength);
	    } else { #at least 1 hit to database
		my $tmp_w = $sum_m_ij ? ($F_i_w / $sum_m_ij) : 0;
		my $tmp_wo = $sum_m_ij ? ($F_i_anywo / $sum_m_ij) : 0;
		if($data{$name}->{$inputlength}->{any}->{$types->{a}}) {
		    $AnyW_a += $data{$name}->{$inputlength}->{any}->{$types->{a}} * $tmp_w;
		    $AnyWo_a += $data{$name}->{$inputlength}->{any}->{$types->{a}} * $tmp_wo;
		    push(@aLengthAny,$inputlength);
		}
		if($data{$name}->{$inputlength}->{any}->{$types->{b}}) {
		    $AnyW_b += $data{$name}->{$inputlength}->{any}->{$types->{b}} * $tmp_w;
		    $AnyWo_b += $data{$name}->{$inputlength}->{any}->{$types->{b}} * $tmp_wo;
		    push(@bLengthAny,$inputlength);
		}
		if($data{$name}->{$inputlength}->{any}->{'unknown'}) {
		    $AnyW_u += $data{$name}->{$inputlength}->{any}->{'unknown'} * $tmp_w;
		    $AnyWo_u += $data{$name}->{$inputlength}->{any}->{'unknown'} * $tmp_wo;
		    push(@uLengthAny,$inputlength);
		}
	    }
	} #input length
	#table data
	push(@tableDataAnyW,[$name,sprintf("%.2f",$AnyW_a),sprintf("%.2f",$AnyW_b),sprintf("%.2f",$AnyW_u),sprintf("%.2f",$AnyW_n)]);
	push(@tableDataAnyWo,[$name,sprintf("%.2f",$AnyWo_a),sprintf("%.2f",$AnyWo_b),sprintf("%.2f",$AnyWo_u)]);
	push(@tableDataAllW,[$name,sprintf("%.2f",$AllW_a),sprintf("%.2f",$AllW_b),sprintf("%.2f",$AllW_u),sprintf("%.2f",$AllW_n)]);
	push(@tableDataAllWo,[$name,sprintf("%.2f",$AllWo_a),sprintf("%.2f",$AllWo_b),sprintf("%.2f",$AllWo_u)]);
	#chart data
	push(@{$chartDataAnyW[0]},$name);push(@{$chartDataAnyW[1]},$AnyW_a);push(@{$chartDataAnyW[2]},$AnyW_b);push(@{$chartDataAnyW[3]},$AnyW_u);push(@{$chartDataAnyW[4]},$AnyW_n);
	push(@{$chartDataAnyWo[0]},$name);push(@{$chartDataAnyWo[1]},$AnyWo_a);push(@{$chartDataAnyWo[2]},$AnyWo_b);push(@{$chartDataAnyWo[3]},$AnyWo_u);
	push(@{$chartDataAllW[0]},$name);push(@{$chartDataAllW[1]},$AllW_a);push(@{$chartDataAllW[2]},$AllW_b);push(@{$chartDataAllW[3]},$AllW_u);push(@{$chartDataAllW[4]},$AllW_n);
	push(@{$chartDataAllWo[0]},$name);push(@{$chartDataAllWo[1]},$AllWo_a);push(@{$chartDataAllWo[2]},$AllWo_b);push(@{$chartDataAllWo[3]},$AllWo_u);
	#div data
	push(@divDataAnyW,[$name,'a',$types->{acolor},sprintf("%.2f",$AnyW_a),join(", ",sort{$a<=>$b}@aLengthAny)]);
	push(@divDataAnyW,[$name,'b',$types->{bcolor}, sprintf("%.2f",$AnyW_b),join(", ",sort{$a<=>$b}@bLengthAny)]);
	push(@divDataAnyW,[$name,'u','lightgray', sprintf("%.2f",$AnyW_u),join(", ",sort{$a<=>$b}@uLengthAny)]);
	push(@divDataAnyW,[$name,'nh','white',    sprintf("%.2f",$AnyW_n),join(", ",sort{$a<=>$b}@nLengthAny)]);
	push(@divDataAnyWo,[$name,'a',$types->{acolor},sprintf("%.2f",$AnyWo_a),join(", ",sort{$a<=>$b}@aLengthAny)]);
	push(@divDataAnyWo,[$name,'b',$types->{bcolor}, sprintf("%.2f",$AnyWo_b),join(", ",sort{$a<=>$b}@bLengthAny)]);
	push(@divDataAnyWo,[$name,'u','lightgray', sprintf("%.2f",$AnyWo_u),join(", ",sort{$a<=>$b}@uLengthAny)]);
	push(@divDataAllW,[$name,'a',$types->{acolor},sprintf("%.2f",$AllW_a),join(", ",sort{$a<=>$b}@aLengthAll)]);
	push(@divDataAllW,[$name,'b',$types->{bcolor}, sprintf("%.2f",$AllW_b),join(", ",sort{$a<=>$b}@bLengthAll)]);
	push(@divDataAllW,[$name,'u','lightgray', sprintf("%.2f",$AllW_u),join(", ",sort{$a<=>$b}@uLengthAll)]);
	push(@divDataAllW,[$name,'nh','white',    sprintf("%.2f",$AllW_n),join(", ",sort{$a<=>$b}@nLengthAll)]);
	push(@divDataAllWo,[$name,'a',$types->{acolor},sprintf("%.2f",$AllWo_a),join(", ",sort{$a<=>$b}@aLengthAll)]);
	push(@divDataAllWo,[$name,'b',$types->{bcolor}, sprintf("%.2f",$AllWo_b),join(", ",sort{$a<=>$b}@bLengthAll)]);
	push(@divDataAllWo,[$name,'u','lightgray', sprintf("%.2f",$AllWo_u),join(", ",sort{$a<=>$b}@uLengthAll)]);
    }
    my @tableData = (\@tableDataAnyW,\@tableDataAnyWo,\@tableDataAllW,\@tableDataAllWo);
    my @chartData = (\@chartDataAnyW,\@chartDataAnyWo,\@chartDataAllW,\@chartDataAllWo);
    my @divData = (\@divDataAnyW,\@divDataAnyWo,\@divDataAllW,\@divDataAllWo);
    my @which = ('anyw','anywo','allw','allwo');
    return (\@tableData,\@chartData,\@divData,\@which);
}

sub generateFractionContent {
    my ($types,$which,$idT,$tableData,$idC,$chartData,$divData,$imageMaps,$moDivs,$type) = @_;
    my ($hidden,%contentT,%contentC,$cumulate,$height);
    $cumulate = 1;
    foreach my $a (@$which) {
	#generate table
	my $dataT = shift(@$tableData);
	my $header = ['Sample name',ucfirst($types->{a}),ucfirst($types->{b}),'Unknown'];
	push(@$header,'No match') if($a =~ /w$/);
	$hidden .= &generateHiddenContent($header,$dataT,$idT.'_'.$a);
	map {$_->[1].=' %';$_->[2].=' %';$_->[3].=' %';$_->[4].=' %' if($a =~ /w$/);} @$dataT;
	$contentT{$a} = &generateTableContent($header,$dataT,1);
	#generate chart
	my $dataC = shift(@$chartData);
	my $div = shift(@$divData);
	my $number = scalar(@{$dataC->[0]});
	$height = $number*10+50+40;
	my @legend = (ucfirst($types->{a}),ucfirst($types->{b}),'Unknown');
	my @colors = ($types->{acolorC},$types->{bcolorC},'lgray');
	if($a =~ /w$/) {
	    push(@legend,'No match');
	    push(@colors,'white');
	}
	my $graph = GD::Graph::hbars->new(TABLE_WIDTH-10,$height);
	$graph->set(
		x_label          => 'Sample names',
		y_label          => 'Percentage',
#		title            => 'ADAPT results',
		legend_spacing   => 5,
		legend_placement => 'RT', #B[LCR] | R[TCB]
		y_max_value      => 100,
#		bar_width        => 8,
		bar_spacing      => 1,
#		bargroup_spacing => 3,
		long_ticks       => 1, #show grid
		x_ticks          => 0,
		y_tick_number    => 10,
		x_label_position => 1/2,
		show_values      => 0,
		cumulate         => $cumulate,
		dclrs => \@colors
		) or warn $graph->error;
	$graph->set_x_label_font(GD::gdMediumBoldFont);
	$graph->set_y_label_font(GD::gdMediumBoldFont);
	$graph->set_x_axis_font(GD::gdSmallFont);
	$graph->set_y_axis_font(GD::gdTinyFont);
#       $graph->set_values_font(GD::gdMediumBoldFont);
	$graph->set_legend_font(GD::gdLargeFont);
	$graph->set_legend(@legend);
	$contentC{$a} = $graph->plot($dataC) or die $graph->error;
	$hidden .= &generateHiddenContent(0,$dataC,$idC.$a,\@legend,\@colors);
	#generate image map
	my $imagemap = '<map name="chartMap_'.$idC.$a.'">'."\n";
	my @mapData = $graph->get_hotspot;
	shift(@mapData);
	my $index = -1;
	my @typeIds = ('a','b','u','nh');
	foreach my $type (@mapData) {
	    my $tmp = '_'.shift(@typeIds);
	    foreach my $cords (@$type) {
		$index++;
		next if(!@$cords[1] || !@$cords[3] ||@$cords[1] == @$cords[3]);
		$imagemap .= "\t".'<area id="'.$idC.$a.$dataC->[0]->[$index].$tmp.'" shape="rect" coords="'.@$cords[1].','.@$cords[2].','.@$cords[3].','.@$cords[4].'" onMouseOver="showTooltip(\'c_'.$idC.$a.$dataC->[0]->[$index].$tmp.'\')" onMouseOut="hideTooltip()">'."\n";
	    }
	    $index = -1;
	}
	$imagemap .= '</map>'."\n";
	$$imageMaps .= $imagemap;

	#generate mouseover divs
	my $divs;
	$divs = &generateMODivContent($div,$idC.$a);
	$$moDivs .= $divs;
    }
    return &generateFractionPart($idT,\%contentT,$idC,\%contentC,$hidden);
}

sub generateFractionChartContent {
    my ($chartData,$divData,$types,$which,$id,$imageMaps,$moDivs,$fraction) = @_;
    my ($hidden,%content,$cumulate,$height);
    $cumulate = 1;
    foreach my $a (@$which) {
	my $data = shift(@$chartData);
	my $div = shift(@$divData);
	#generate chart
	my $number = scalar(@{$data->[0]});
	$height = $number*10+50+40;
	my @legend = (ucfirst($types->{a}),ucfirst($types->{b}),'Unknown');
	my @colors = ($types->{acolorC},$types->{bcolorC},'lgray');
	if($a =~ /w$/) {
	    push(@legend,'No match');
	    push(@colors,'white');
	}
	my $graph = GD::Graph::hbars->new(TABLE_WIDTH-10,$height);
	$graph->set(
		x_label          => 'Sample names',
		y_label          => 'Percentage',
#		title            => 'ADAPT results',
		legend_spacing   => 5,
		legend_placement => 'RT', #B[LCR] | R[TCB]
		y_max_value      => 100,
#		bar_width        => 8,
		bar_spacing      => 1,
#		bargroup_spacing => 3,
		long_ticks       => 1, #show grid
		x_ticks          => 0,
		y_tick_number    => 10,
		x_label_position => 1/2,
		show_values      => 0,
		cumulate         => $cumulate,
		dclrs => \@colors
		) or warn $graph->error;
	$graph->set_x_label_font(GD::gdMediumBoldFont);
	$graph->set_y_label_font(GD::gdMediumBoldFont);
	$graph->set_x_axis_font(GD::gdSmallFont);
	$graph->set_y_axis_font(GD::gdTinyFont);
#  $graph->set_values_font(GD::gdMediumBoldFont);
	$graph->set_legend_font(GD::gdLargeFont);
	$graph->set_legend(@legend);
	$content{$a} = $graph->plot($data) or die $graph->error;
	$hidden .= &generateHiddenContent(0,$data,$id.$a,\@legend,\@colors);

	#generate image map
	my $imagemap = '<map name="chartMap_'.$id.$a.'">'."\n";
	my @mapData = $graph->get_hotspot;
	shift(@mapData);
	my $index = -1;
	my @typeIds = ('a','b','u','nh');
	foreach my $type (@mapData) {
	    my $tmp = '_'.shift(@typeIds);
	    foreach my $cords (@$type) {
		$index++;
		next if(!@$cords[1] || !@$cords[3] ||@$cords[1] == @$cords[3]);
		$imagemap .= "\t".'<area id="'.$id.$a.$data->[0]->[$index].$tmp.'" shape="rect" coords="'.@$cords[1].','.@$cords[2].','.@$cords[3].','.@$cords[4].'" onMouseOver="showTooltip(\'c_'.$id.$a.$data->[0]->[$index].$tmp.'\')" onMouseOut="hideTooltip()">'."\n";
	    }
	    $index = -1;
	}
	$imagemap .= '</map>'."\n";
	$$imageMaps .= $imagemap;

	#generate mouseover divs
	my $divs;
	$divs = &generateMODivContent($div,$id.$a);
	$$moDivs .= $divs;
    }
    #generate and return chart data
    return &generateFractionImagePart($id,\%content,$hidden);
}

sub generateMultipleInputTable {
    my ($length,$id) = @_;
    #check if multiple samples
    return undef if(scalar(keys %$length)<2);
    my ($hidden,$contentA,$contentD);
    my %tmp;
    foreach my $name (keys %$length) {
	foreach my $inputLength (sort {$a <=> $b} keys %{$length->{$name}}) {
	    #round off to nearests number, with .5 round up
	    my $roundedLength = int($inputLength+0.5);
	    $tmp{$roundedLength}->{names}->{$name} = $inputLength;
	    @{$tmp{$roundedLength}->{dblength}} = keys %{$length->{$name}->{$inputLength}} unless(exists $tmp{$roundedLength}->{dblength});
	}
    }
    #abbreviated+detailed table
    my (@tableData,@tableDataD);
    foreach my $roundedLength (sort {$a <=> $b} keys %tmp) {
	my @dblength = (exists $tmp{$roundedLength}->{dblength} ? @{$tmp{$roundedLength}->{dblength}} : undef);
	my $dbLengths = (@dblength ? join("; ",@dblength) : 'no hit');
	my $names = join("; ",sort keys %{$tmp{$roundedLength}->{names}});
	push(@tableData,[$roundedLength,$dbLengths,$names]);
	foreach my $name (sort keys %{$tmp{$roundedLength}->{names}}) {
	    push(@tableDataD,[$roundedLength,$dbLengths,$name,$tmp{$roundedLength}->{names}->{$name}]);
	}
    }
    my $header = ['Rounded input length','Matching database length','Sample name'];
    $hidden = &generateHiddenContent($header,\@tableData,$id.'_a');
    $contentA = &generateTableContent($header,\@tableData,3);
    push(@$header,'Input length');
    $hidden .= &generateHiddenContent($header,\@tableDataD,$id.'_d');
    $contentD = &generateTableContent($header,\@tableDataD,4,1);
    #generate and return table div
    return &generateTablePart($id,$hidden,$contentA,$contentD);
}

sub generateMultipleDbTable {
    my ($length,$id) = @_;
    #check if multiple samples
    return undef if(scalar(keys %$length)<2);
    my ($hidden,$contentA,$contentD);
    my %tmp;
    foreach my $name (keys %$length) {
	foreach my $inputLength (sort {$a <=> $b} keys %{$length->{$name}}) {
	    my @dblengths =  keys %{$length->{$name}->{$inputLength}};
	    @dblengths = 'no hit' unless(scalar(@dblengths));
	    foreach(@dblengths) {
		push(@{$tmp{$_}->{$inputLength}},$name);
	    }
	}
    }
    #abbreviated+detailed table
    my (@tableData,@tableDataD);
    foreach my $dbLength (sort {$a <=> $b} keys %tmp) {
	my (%name,@inputLengths);
	foreach my $inputLength (sort {$a <=> $b} keys %{$tmp{$dbLength}}) {
	    my $names = $tmp{$dbLength}->{$inputLength};
	    push(@inputLengths,$inputLength);
	    foreach(@$names) {
		$name{$_} = 1;
		push(@tableDataD,[$dbLength,$inputLength,$_]);
	    }
	}
	push(@tableData,[$dbLength,join("; ",@inputLengths),join("; ",sort keys %name)]);
    }
    my $header = ['Matching length in database','Input fragment length','Sample name'];
    $hidden = &generateHiddenContent($header,\@tableData,$id.'_a');
    $contentA = &generateTableContent($header,\@tableData,3);
    $hidden .= &generateHiddenContent($header,\@tableDataD,$id.'_d');
    $contentD = &generateTableContent($header,\@tableDataD,3,0);
    #generate and return table div
    return &generateTablePart($id,$hidden,$contentA,$contentD);
}

sub generateOutput {
    my $outputs = shift;
    my $content;
    $content .= $q->hidden(-name => 'id', -default => '',-id => 'id');
    $content .= $q->hidden(-name => 'id2', -default => '',-id => 'id2');
    my @keys = sort {$outputs->{$a}->{order} <=> $outputs->{$b}->{order}} keys %$outputs;
    foreach my $id (@keys) {
	$content .= &generatePartContent($outputs->{$id}->{title},
					 1, #$outputs->{$id}->{show},
					 $outputs->{$id}->{color},
					 $outputs->{$id}->{id}.'D',
					 $outputs->{$id}->{data});
    }
    $content .= $q->Tr($q->td({-align => 'center',
			       -class => 'tableButton',
			       -colspan => '2'},
#			      $q->button({-value => ' CHANGE INPUT ',
#					  -name => 'new',
#					  -class => 'buttonoutput',
#					  -onClick => 'history.go(-1);'}),
#			      '&nbsp;'x70,
			      $q->button({-value => ' NEW INPUT ',
					  -name => 'new',
					  -class => 'buttonoutput',
					  -onClick => 'location=\'ADAPTInput.cgi\''})));
    return $content;
}

sub generateTableContent {
    my ($header,$data,$left,$cols) = @_;
    my $niceData = &generateNiceTableData($data,$cols);
    my $highlight = 0;
    my $content = $q->start_table({-border =>'0',
				-cellpadding => '2',
				-cellspacing => '1',
				-width => '100%'});
    $content .= $q->Tr({-valign => 'middle'},
		       map { $q->th({-class => 'hideTableHeader'},$_) } @$header
		       );
    foreach my $tr (@$niceData) {
	my @tds;
	($highlight = $highlight ? 0 : 1) if($tr->[0]>0);
	my $count = 0;
	while(@$tr) {
	    my $rowspan = shift(@$tr);
	    my $value = shift(@$tr);
	    $count++;
	    next unless($rowspan);
	    push(@tds, $q->td({-rowspan => $rowspan,
 			       -align => (($left-$count>=0)?'left':'center'),
 			       -class => 'tbg'.$highlight},
 			      $q->font({-class => 'table_font2'},$value)));
	}
 	$content .= $q->Tr(@tds);
    }
    $content .= $q->end_table();
    return $content;
}

sub generateNiceTableData {
    my ($data,$cols) = @_;
    my @niceData;
    my @tmp;
    my $xnb = scalar(@{$data->[0]})-1; #rows
    my $ynb = scalar(@$data)-1;        #cols
    for my $index (0..$xnb) {
	my $value;
	my $count = 1;
	foreach my $tr (@$data) {
	    unless(defined $value) {
		$value = $tr->[$index];
	    } elsif(defined $tr->[$index] && $value eq $tr->[$index]
		    && (($index>0 && defined $tmp[$index] && scalar(@{$tmp[$index]})>0 && $tmp[$index-1]->[scalar(@{$tmp[$index]})] != 0) ? ($count < $tmp[$index-1]->[scalar(@{$tmp[$index]})]) : 1)
		    && ($index>0 && !defined $tmp[$index] ? ($count < $tmp[$index-1]->[0]) : 1)
		) {
		$count++;
	    } else {
		push(@{$tmp[$index]},$count);
		while($count-- > 1) {
		    push(@{$tmp[$index]},0);
		}
		$count = 1;
		$value = $tr->[$index];
	    }
	}
	push(@{$tmp[$index]},$count);
	while($count-- > 1) {
	    push(@{$tmp[$index]},0);
	}
    }
    for my $y (0..$ynb) {
	for my $x (0..$xnb) {
	    if(defined $cols && $x>$cols) {
		$tmp[$x]->[$y] = 1;
	    } elsif($x>0) {
		$tmp[$x]->[$y] = 1 if($tmp[$x-1]->[$y] == 1);
		$tmp[$x]->[$y] = 1 if($tmp[$x-1]->[$y] == 0 && $tmp[$x-1]->[$y+1] && ($tmp[$x]->[$y-1] == 1 || ($tmp[$x]->[$y-1] == 0 && $tmp[$x]->[$y] > 0)));
		$tmp[$x]->[1] += 1 if($tmp[$x]->[$y] == 0 && $y > 0 && $y <= $tmp[0]->[1] && $tmp[$x]->[1] < $tmp[0]->[1]);
		$tmp[$x]->[$y] = 1 if($tmp[$x]->[$y-1] == 1 && $y > 0 && $tmp[$x]->[$y] == 0);
		$tmp[$x]->[$y] -=1 if($tmp[$x]->[$y] > 1 && $tmp[0]->[$ynb] == 1 && $tmp[$x]->[$y]+$y-1 == $ynb);
	    } elsif($y>0) {
		$tmp[$x]->[$y] = 1 if($tmp[$x]->[$y-1] == 1 && $tmp[$x]->[$y] == 0);
	    }
	}
    }
    for my $y (0..$ynb) {
	my @vals;
	for my $x (0..$xnb) {
	    push(@vals,$tmp[$x]->[$y]);
	    push(@vals,$data->[$y]->[$x]);
	}
	push(@niceData,\@vals);
    }
    return \@niceData;
}

sub generateHiddenContent {
    my ($header,$data,$id,$legend,$colors) = @_;

    #get data
    my @hidden;
    if($legend) {
	push(@hidden,'#legend:'.join("\t",@$legend));
    }
    if($colors) {
	push(@hidden,'#colors:'.join("\t",@$colors));
    }
    if($header) {
	push(@hidden,join("\t",@$header));
    }
    foreach my $row (@$data) {
	push(@hidden,join("\t",map {defined $_ ? $_ : 0} @$row));
    }

    #write to tmp file
    my $tmpfh = File::Temp->new( TEMPLATE => 'adaptXXXXXXXXXX',
				 DIR => TMP_DIR_CGI,
				 SUFFIX => '.tmp',
				 UNLINK => 0);
    my $filename = $tmpfh->filename;
    print $tmpfh join("\n",@hidden);

    #return file name
    return $q->hidden(-name => 'exportData_'.$id,-default => $filename);
}

sub generateMODivContent {
    my ($divData,$id) = @_;
    my $content;
    foreach(@$divData) {
	$content .= '<div class="tooltip" id="c_'.$id.$_->[0].'_'.$_->[1].'">'."\n";
	$content .= "\t".'<div class="head" style="background-color:'.$_->[2].';"><code>'.$_->[0].'</code></div><div class="content"><code>';
	$content .= $q->start_table({-border =>'0',
				     -cellpadding => '2',
				     -cellspacing => '0',
				     -width => '100%'});
	$content .= $q->Tr({-valign => 'middle'},
			   $q->td({-class => 'divtdleft'},
				  'Proportion:'),
			   $q->td({-class => 'divtdright'},
				  $_->[3].'%'));
	$content .= $q->Tr({-valign => 'middle'},
			   $q->td({-class => 'divtdleft'},
				  'Used length:'),
			   $q->td({-class => 'divtdright'},
				  $_->[4]));
	$content .= $q->end_table();
	$content .= '</div></div>'."\n";
    }
    return $content;
}

sub generateMenuDiv {
    my ($outputs) = @_;
    my $content;
    my @keys;
    my $tmp;
    my $count = 0;
    my $width = $q->param('resolution');
    $content .= '<div class="menu" id="menu" style="right:'.(int(($width - TABLE_WIDTH)/2)-170).'px;">'."\n";
    $content .= "\t".'<div class="groupHeader" style="background:'.HEADER_BG_COLOR.';" align="left"><b>&nbsp;Show/Hide menu</b>'.('&nbsp;'x12).$q->font({-class => 'shbutton',
													     -onClick => 'document.getElementById(\'menu\').style.display=\'none\';'},
													     '[x]').'</div>';
    $content .= '<div class="groupContent">';
    $content .= $q->start_table({-border =>'0',
				 -cellpadding => '3',
				 -cellspacing => '0'});
    foreach my $kind ('general','plots','metadata','multiple') {
	@keys = ();
	foreach my $key (keys %{OUTPUTS->{$kind}}) {
	    push(@keys,$key) if(exists $outputs->{$key});
	    push(@keys,$key.'table') if(exists $outputs->{$key.'table'});
	    push(@keys,$key.'chart') if(exists $outputs->{$key.'chart'});
	}
	next unless(@keys);
	$count++;
	$tmp .= $q->Tr($q->td({-class => 'tbg0',
			       -width => '80%',
			       -align => 'left'},
			      $q->font({-class => 'menutext'},
				       $q->a({-href => 'ADAPTOutput.cgi#goto'.$kind},ucfirst($kind)))),
		       $q->td({-class => 'tbg0',
			       -align => 'left'},
			      $q->font({-class => 'shbutton',
					-onClick => 'var mids=[\''.join("\',\'",@keys).'\'];var mnum='.scalar(@keys).';for(var i=0; i<mnum; i++){ document.getElementById(mids[i]+\'DT\').style.display=\'block\';document.getElementById(mids[i]+\'DB\').innerHTML=\'hide&nbsp;&and;\';}'},
				       'show')),
		       $q->td({-class => 'tbg0',
			       -align => 'left'},
			      $q->font({-class => 'shbutton',
					-onClick => 'var mids=[\''.join("\',\'",@keys).'\'];var mnum='.scalar(@keys).';for(var i=0; i<mnum; i++){ document.getElementById(mids[i]+\'DT\').style.display=\'none\';document.getElementById(mids[i]+\'DB\').innerHTML=\'show&nbsp;&or;\';}'},
				       'hide')));
    }
    if($count > 1) {
	@keys = sort {$outputs->{$a}->{order} <=> $outputs->{$b}->{order}} keys %$outputs;
	$content .= $q->Tr($q->td({-class => 'tbg0',
				   -align => 'left'},
				  $q->font({-class => 'menutext'},
					   'All')),
			   $q->td({-class => 'tbg0',
				   -align => 'left'},
				  $q->font({-class => 'shbutton',
					    -name => 'allms',
					    -id => 'allms',
					    -onClick => 'var mids=[\''.join("\',\'",@keys).'\'];var mnum='.scalar(@keys).';for(var i=0; i<mnum; i++){ document.getElementById(mids[i]+\'DT\').style.display=\'block\';document.getElementById(mids[i]+\'DB\').innerHTML=\'hide&nbsp;&and;\';}'},
					   'show')),
			   $q->td({-class => 'tbg0',
				   -align => 'left'},
				  $q->font({-class => 'shbutton',
					    -name => 'allmh',
					    -id => 'allmh',
					    -onClick => 'var mids=[\''.join("\',\'",@keys).'\'];var mnum='.scalar(@keys).';for(var i=0; i<mnum; i++){ document.getElementById(mids[i]+\'DT\').style.display=\'none\';document.getElementById(mids[i]+\'DB\').innerHTML=\'show&nbsp;&or;\';}'},
					   'hide')));
    }
    $content .= $tmp;
    $content .= $q->end_table();
    $content .= '</div></div>'."\n";
    return $content;
}

sub generatePartContent {
    my ($title,$show,$color,$id,$content) = @_;
    my $part;
    #find group name to put jump link to
    my $jlink = '';
    my $tmp = $id;
    $tmp =~ s/D$//;
    $tmp =~ s/table$//;
    $tmp =~ s/chart$//;
    foreach my $kind ('general','plots','metadata','multiple') {
	$jlink = $kind if(exists OUTPUTS->{$kind}->{$tmp});
    }
    #put content together
    $part .= $q->Tr($q->td({-align => 'left',
			    -class => 'groupHeader',
#			    -width => '90%',
			    -style => ($color?'background-color:'.$color.';':'')},
			   $q->a({-name => 'goto'.$jlink}),
			   $q->font({-class => 'groupTitle'},
				    $title)),
		    $q->td({-align => 'right',
			    -class => 'groupHeader',
			    -width => '45px',
#			    -style => ($color?'background-color:'.$color.';':'')
			   },
			   $q->font({-class => 'shbutton',
				     -name => $id.'B',
				     -id => $id.'B',
				     -onClick => 'if(document.getElementById(\''.$id.'T\').style.display==\'block\'){document.getElementById(\''.$id.'T\').style.display=\'none\';document.getElementById(\''.$id.'B\').innerHTML=\'show&nbsp;&or;\';} else {document.getElementById(\''.$id.'T\').style.display=\'block\';document.getElementById(\''.$id.'B\').innerHTML=\'hide&nbsp;&and;\';}'},
				    $show?'hide&nbsp;&and;':'show&nbsp;&or;'),
		    ));
    $part .= $q->Tr($q->td({-align => 'center',
			    -colspan => '2',
			    -class => 'groupContent'},
			   $q->div({-id => $id.'T',
				    -style => 'display:'.($show?'block':'none')},
				   $content)));
    $part .= $q->Tr($q->td({-colspan => '2',
			    -class => 'groupEmpty'},
			   '&nbsp;'));
    return $part;
}

sub generateTablePart {
    my ($id,$hidden,$table1,$table2,$extra,$labels) = @_;
    my $tablePart;
    $tablePart .= ($hidden.
 		   $q->b('Export format: ').
  		   $q->radio_group(-name => 'exportFormat_'.$id,
  				   -values => ['csv','tsv'],
  				   -default => 'csv',
  				   -labels => {'csv' => '.csv',
  					       'tsv' => '.tsv'}).
 		   ('&nbsp;'x5).
		   $q->button({-value => 'Save',
			       -name => 'export'.$id,
			       -class => 'savebutton',
			       -onClick => 'document.getElementById(\'id\').value="'.$id.'";document.forms.output.action="exportTable.cgi";document.forms.output.submit();'}).
		   $q->hr().
		   ($table2 ? $q->b('Show: ').
		    $q->radio_group(-name => 'showTable_'.$id,
				    -values => ['d','a'],
				    -default => 'a',
				    -labels => ($labels ? $labels : {'d' => 'detailed',
								     'a' => 'abbreviated'}),
				    -attributes => {'d' => {-onClick => 'document.getElementById(\''.$id.'bT\').style.display=\'block\';document.getElementById(\''.$id.'aT\').style.display=\'none\';'},
						    'a' => {-onClick => 'document.getElementById(\''.$id.'aT\').style.display=\'block\';document.getElementById(\''.$id.'bT\').style.display=\'none\';'}}) : '').
		   $q->div({-id => $id.'aT',
			    -style => 'display:block;'},
			   $table1).
		   ($table2 ? $q->div({-id => $id.'bT',
				       -style => 'display:none;'},
				      $table2) : $q->hidden(-name => 'showTable_'.$id,-default => ['a'])));
    $tablePart .= $q->br().$q->font({-class => 'table_info'},$extra) if($extra);
    return $tablePart;
}

sub generateFractionPart {
    my ($idT,$tables,$idC,$images,$hidden,$extra) = @_;
    my $tablePart;
    my $id = $idT;
    $tablePart = $hidden.
	$q->start_table({-border =>'0',-cellpadding => '2',-cellspacing => '0'}).
	$q->Tr($q->td({-class => 'legend2',-width => '60px',-align => 'right'},$q->font({-class => 'table_info2'},'<b>Views:&nbsp;</b>')).
	       $q->td({-class => 'legend2',-width => '60px'},
		      $q->img({-src => '../../'.ADAPT_DIR.'table1.png',-border => '0',
			       -alt => 'table',
			       -id => 'table'.$id,
			       -onMouseOver => 'if(this.alt != "table3"){this.src="'.'../../'.ADAPT_DIR.'table2.png'.'";}',
			       -onMouseOut => 'if(this.alt != "table3"){this.src="'.'../../'.ADAPT_DIR.'table1.png'.'";}',
			       -onClick => 'this.src="'.'../../'.ADAPT_DIR.'table3.png'.'";this.alt="table3";document.getElementById(\'chart'.$id.'\').src="'.'../../'.ADAPT_DIR.'chart1.png'.'";document.getElementById(\'chart'.$id.'\').alt="chart";document.getElementById(\''.$id.'exportTable\').style.display=\'block\';document.getElementById(\''.$id.'exportChart\').style.display=\'none\';var show;for (var i=0;i<document.forms.output.show_'.$id.'.length;i++){show=document.forms.output.show_'.$id.'[i].value;document.getElementById(\''.$id.'\'+show+\'C\').style.display=\'none\';if(document.forms.output.show_'.$id.'[i].checked){document.getElementById(\''.$id.'\'+show+\'T\').style.display=\'block\';}}'}).
		      $q->img({-src => '../../'.ADAPT_DIR.'chart3.png',-border => '0',
			       -alt => 'chart3',
			       -id => 'chart'.$id,
			       -onMouseOver => 'if(this.alt != "chart3"){this.src="'.'../../'.ADAPT_DIR.'chart2.png'.'";}',
			       -onMouseOut => 'if(this.alt != "chart3"){this.src="'.'../../'.ADAPT_DIR.'chart1.png'.'";}',
			       -onClick => 'this.src="'.'../../'.ADAPT_DIR.'chart3.png'.'";this.alt="chart3";document.getElementById(\'table'.$id.'\').src="'.'../../'.ADAPT_DIR.'table1.png'.'";document.getElementById(\'table'.$id.'\').alt="table";document.getElementById(\''.$id.'exportChart\').style.display=\'block\';document.getElementById(\''.$id.'exportTable\').style.display=\'none\';var show;for (var i=0;i<document.forms.output.show_'.$id.'.length;i++){show=document.forms.output.show_'.$id.'[i].value;document.getElementById(\''.$id.'\'+show+\'T\').style.display=\'none\';if(document.forms.output.show_'.$id.'[i].checked){document.getElementById(\''.$id.'\'+show+\'C\').style.display=\'block\';}}'})).
	       $q->td({-class => 'legend2',-width => '280px'},'&nbsp;').
	       $q->td({-class => 'legend2',-width => '110px',-align => 'right'},$q->font({-class => 'table_info2'},$q->b('Export&nbsp;format:&nbsp;'))).
	       $q->td({-class => 'legend2'},
		      $q->div({-id => $id.'exportTable',
			       -style => 'display:none;'},
			      $q->font({-class => 'table_info2'},
				       $q->radio_group(-name => 'exportFormat_'.$idT,
						       -values => ['csv','tsv'],
						       -default => 'csv',
						       -labels => {'csv' => '.csv',
								   'tsv' => '.tsv'})),
			      ,'&nbsp;'x2,
			      $q->button({-value => 'Save',
					  -name => 'export'.$idT,
					  -class => 'savebutton',
					  -onClick => 'var show;for (var i=0;i<document.forms.output.show_'.$id.'.length;i++){if(document.forms.output.show_'.$id.'[i].checked){show=document.forms.output.show_'.$id.'[i].value;}}document.getElementById(\'id2\').value=show;document.getElementById(\'id\').value="'.$idT.'";document.forms.output.action="exportTable.cgi";document.forms.output.submit();'})).
		      $q->div({-id => $id.'exportChart',
			       -style => 'display:block;'},
			      $q->font({-class => 'table_info2'},
				       $q->radio_group(-name => 'imageFormat_'.$idC,
						       -values => ['png','jpeg','gif'],
						       -default => 'png',
						       -labels => {'png' => '.png',
								   'jpeg' => '.jpg',
								   'gif' => '.gif'})),
			      '&nbsp;'x2,
			      $q->button({-value => 'Save',
					  -name => 'saveImage_'.$idC,
					  -class => 'savebutton',
					  -onClick => 'var show;for (var i=0;i<document.forms.output.show_'.$id.'.length;i++){if(document.forms.output.show_'.$id.'[i].checked){show=document.forms.output.show_'.$id.'[i].value;}}document.getElementById(\'id2\').value=show;document.getElementById(\'id\').value="'.$idC.'";document.forms.output.action="exportChart.cgi";document.forms.output.submit();'})))).
        $q->Tr($q->td({-class => 'legend2',-colspan => 6,-width => (TABLE_WIDTH-80).'px'},$q->font({-style => 'font-size:3pt'},'&nbsp;'))).
	$q->Tr($q->td({-class => 'legend2',-colspan => 6,-align => 'center'},
		      $q->font({-class => 'table_info2'},
			       '<b>Show:</b>&nbsp;',
			       $q->radio_group(-name => 'show_'.$id,
					       -values => ['allw','allwo','anyw','anywo'],
					       -default => ['allwo'],
					       -labels => {'anyw' => 'Any fragment is matching',
							   'anywo' => 'Any, without no match',
							   'allw' => 'All fragments are matching',
							   'allwo' => 'All, without no match'},
					       -attributes => {'anyw' => {-onClick => 'if(document.getElementById(\'table'.$id.'\').alt==\'table3\'){document.getElementById(\''.$id.'anywT\').style.display=\'block\';document.getElementById(\''.$id.'anywoT\').style.display=\'none\';document.getElementById(\''.$id.'allwT\').style.display=\'none\';document.getElementById(\''.$id.'allwoT\').style.display=\'none\';}else{document.getElementById(\''.$id.'anywC\').style.display=\'block\';document.getElementById(\''.$id.'anywoC\').style.display=\'none\';document.getElementById(\''.$id.'allwC\').style.display=\'none\';document.getElementById(\''.$id.'allwoC\').style.display=\'none\';}'},
							       'anywo' => {-onClick => 'if(document.getElementById(\'table'.$id.'\').alt==\'table3\'){document.getElementById(\''.$id.'anywoT\').style.display=\'block\';document.getElementById(\''.$id.'anywT\').style.display=\'none\';document.getElementById(\''.$id.'allwT\').style.display=\'none\';document.getElementById(\''.$id.'allwoT\').style.display=\'none\';}else{document.getElementById(\''.$id.'anywoC\').style.display=\'block\';document.getElementById(\''.$id.'anywC\').style.display=\'none\';document.getElementById(\''.$id.'allwC\').style.display=\'none\';document.getElementById(\''.$id.'allwoC\').style.display=\'none\';}'},
							       'allw' => {-onClick => 'if(document.getElementById(\'table'.$id.'\').alt==\'table3\'){document.getElementById(\''.$id.'allwT\').style.display=\'block\';document.getElementById(\''.$id.'anywoT\').style.display=\'none\';document.getElementById(\''.$id.'anywT\').style.display=\'none\';document.getElementById(\''.$id.'allwoT\').style.display=\'none\';}else{document.getElementById(\''.$id.'allwC\').style.display=\'block\';document.getElementById(\''.$id.'anywoC\').style.display=\'none\';document.getElementById(\''.$id.'anywC\').style.display=\'none\';document.getElementById(\''.$id.'allwoC\').style.display=\'none\';}'},
							       'allwo' => {-onClick => 'if(document.getElementById(\'table'.$id.'\').alt==\'table3\'){document.getElementById(\''.$id.'allwoT\').style.display=\'block\';document.getElementById(\''.$id.'anywoT\').style.display=\'none\';document.getElementById(\''.$id.'allwT\').style.display=\'none\';document.getElementById(\''.$id.'anywT\').style.display=\'none\';}else{document.getElementById(\''.$id.'allwoC\').style.display=\'block\';document.getElementById(\''.$id.'anywoC\').style.display=\'none\';document.getElementById(\''.$id.'allwC\').style.display=\'none\';document.getElementById(\''.$id.'anywC\').style.display=\'none\';}'}})))).
	$q->end_table();
    $tablePart .= $q->hr();
    $tablePart .= $q->div({-id => $id.'anywT',
			   -style => 'display:none;'},
			  $tables->{'anyw'}).
		  $q->div({-id => $id.'anywoT',
			   -style => 'display:none;'},
			  $tables->{'anywo'}).
		  $q->div({-id => $id.'allwT',
			   -style => 'display:none;'},
			  $tables->{'allw'}).
       	          $q->div({-id => $id.'allwoT',
			   -style => 'display:none;'},
			  $tables->{'allwo'}).
		  $q->div({-id => $id.'anywC',
			    -style => 'display:none;'},
			   $q->img({-src => (USED_BROWSER ? &inline_image($images->{'anyw'}) : &external_image($images->{'anyw'},$idC.'anyw')),
				    -border => '0',
				    -usemap => '#chartMap_'.$idC.'anyw'})).
		   $q->div({-id => $id.'anywoC',
			    -style => 'display:none;'},
			   $q->img({-src => (USED_BROWSER ? &inline_image($images->{'anywo'}) : &external_image($images->{'anywo'},$idC.'anywo')),
				    -border => '0',
				    -usemap => '#chartMap_'.$idC.'anywo'})).
		   $q->div({-id => $id.'allwC',
			    -style => 'display:none;'},
			   $q->img({-src => (USED_BROWSER ? &inline_image($images->{'allw'}) : &external_image($images->{'allw'},$idC.'allw')),
				    -border => '0',
				    -usemap => '#chartMap_'.$idC.'allw'})).
		   $q->div({-id => $id.'allwoC',
			    -style => 'display:block;'},
			   $q->img({-src => (USED_BROWSER ? &inline_image($images->{'allwo'}) : &external_image($images->{'allwo'},$idC.'allwo')),
				    -border => '0',
				    -usemap => '#chartMap_'.$idC.'allwo'}));
    $tablePart .= $q->br().$q->font({-class => 'table_info'},$extra) if($extra);
    return $tablePart;
}

sub generateImagePart {
    my ($id,$image,$hidden,$noexport) = @_;
    my $imagePart;
    $imagePart .= $hidden if($hidden);
    $imagePart .= ($q->b('Image format: ').
		   $q->radio_group(-name => 'imageFormat_'.$id,
				   -values => ['png','jpeg','gif'],
				   -default => 'png',
				   -labels => {'png' => '.png',
					       'jpeg' => '.jpg',
					       'gif' => '.gif'}).
		   ('&nbsp;'x5).
		   $q->button({-value => 'Save',
			       -name => 'saveImage_'.$id,
			       -class => 'savebutton',
			       -onClick => 'document.getElementById(\'id\').value="'.$id.'";document.forms.output.action="exportChart.cgi";document.forms.output.submit();'}).
		   $q->hr()) unless($noexport);
    $imagePart .= $q->img({-src => (USED_BROWSER ? &inline_image($image) : &external_image($image,$id)),
			   -border => '0',
			   -usemap => '#chartMap_'.$id});
    return $imagePart;
}

sub generateFractionImagePart {
    my ($id,$images,$hidden,$noexport) = @_;
    my $imagePart;
    $imagePart = $hidden if($hidden);
    $imagePart .= ($q->b('Image format: ').
		   $q->radio_group(-name => 'imageFormat_'.$id,
				   -values => ['png','jpeg','gif'],
				   -default => 'png',
				   -labels => {'png' => '.png',
					       'jpeg' => '.jpg',
					       'gif' => '.gif'}).
		   ('&nbsp;'x5).
		   $q->button({-value => 'Save',
			       -name => 'saveImage_'.$id,
			       -class => 'savebutton',
			       -onClick => 'document.getElementById(\'id\').value="'.$id.'";document.forms.output.action="exportChart.cgi";document.forms.output.submit();'}).
		   $q->hr()) unless($noexport);
    $imagePart .= $q->b('Show: ').
		  $q->radio_group(-name => 'showChart_'.$id,
				  -values => ['allw','allwo','anyw','anywo'],
				  -default => ['allwo'],
				  -labels => {'anyw' => 'any with',
					      'anywo' => 'any without',
					      'allw' => 'all with',
					      'allwo' => 'all without'},
				  -attributes => {'anyw' => {-onClick => 'document.getElementById(\''.$id.'anywC\').style.display=\'block\';document.getElementById(\''.$id.'anywoC\').style.display=\'none\';document.getElementById(\''.$id.'allwC\').style.display=\'none\';document.getElementById(\''.$id.'allwoC\').style.display=\'none\';'},
						  'anywo' => {-onClick => 'document.getElementById(\''.$id.'anywoC\').style.display=\'block\';document.getElementById(\''.$id.'anywC\').style.display=\'none\';document.getElementById(\''.$id.'allwC\').style.display=\'none\';document.getElementById(\''.$id.'allwoC\').style.display=\'none\';'},
						  'allw' => {-onClick => 'document.getElementById(\''.$id.'allwC\').style.display=\'block\';document.getElementById(\''.$id.'anywoC\').style.display=\'none\';document.getElementById(\''.$id.'anywC\').style.display=\'none\';document.getElementById(\''.$id.'allwoC\').style.display=\'none\';'},
						  'allwo' => {-onClick => 'document.getElementById(\''.$id.'allwoC\').style.display=\'block\';document.getElementById(\''.$id.'anywoC\').style.display=\'none\';document.getElementById(\''.$id.'allwC\').style.display=\'none\';document.getElementById(\''.$id.'anywC\').style.display=\'none\';'}}).
		   $q->div({-id => $id.'anywC',
			    -style => 'display:none;'},
			   $q->img({-src => (USED_BROWSER ? &inline_image($images->{'anyw'}) : &external_image($images->{'anyw'},$id.'anyw')),
				    -border => '0',
				    -usemap => '#chartMap_'.$id.'anyw'})).
		   $q->div({-id => $id.'anywoC',
			    -style => 'display:none;'},
			   $q->img({-src => (USED_BROWSER ? &inline_image($images->{'anywo'}) : &external_image($images->{'anywo'},$id.'anywo')),
				    -border => '0',
				    -usemap => '#chartMap_'.$id.'anywo'})).
		   $q->div({-id => $id.'allwC',
			    -style => 'display:none;'},
			   $q->img({-src => (USED_BROWSER ? &inline_image($images->{'allw'}) : &external_image($images->{'allw'},$id.'allw')),
				    -border => '0',
				    -usemap => '#chartMap_'.$id.'allw'})).
		   $q->div({-id => $id.'allwoC',
			    -style => 'display:block;'},
			   $q->img({-src => (USED_BROWSER ? &inline_image($images->{'allwo'}) : &external_image($images->{'allwo'},$id.'allwo')),
				    -border => '0',
				    -usemap => '#chartMap_'.$id.'allwo'}));
    return $imagePart;
}


sub inline_image {
    return "data:image/png;base64,".MIME::Base64::encode_base64((ref $_[0] && $_[0]->isa('GD::Image')) ? $_[0]->png : $_[0]);
}

sub external_image {
    my ($content,$id) = @_;
    &checkForOldFiles();
    my $filename = time().'_'.$id.'.png';
    my $url = TMP_DIR_CGI.$filename;
    open(IMG,">$url") or return "Could not create image file: $!";
    binmode IMG;
    print IMG $content->png;
    close(IMG);
    return TMP_DIR_WEB.$filename;
}

sub checkForOldFiles {
    my $time = time();
    my $url = TMP_DIR_CGI;
    opendir(BIN, $url) or die "Could not open dir: $!\n";
    while (defined (my $file = readdir BIN)) {
	next if($file eq '.' || $file eq '..');
	$file =~ m/^(\d+)\_.+\.png/;
	unlink($url.$file) if($1 && ($time-$1)>100000);
    }
    closedir(BIN);
    return;
}

sub calculateRatio {
    my ($a,$b) = @_;
    unless($a || $b) {
	return 'no hit';
    } elsif($a == $b) {
	return '1 : 1';
    } elsif($a == 0 || $b == 0) {
	return ($a == 0 ? '0 : 1' : '1 : 0');
    } else {
	return (int($a+0.5)/100).' : '.(int($b+0.5)/100);
    }
}

sub revcomp {
    my $seq = shift;
    $seq = reverse($seq);
    $seq = lc($seq);
    $seq =~ tr/gatcmrwsykvhdb/ctagkyswrmbdhv/;
    return $seq;
}

sub convertPrimersToRegex {
    my ($f,$r) = @_;
    return join("",map {AMBIGUITY_CODE->{$_}} split(//,lc($f))).'.*'.join("",map {AMBIGUITY_CODE->{$_}} split(//,&revcomp(lc($r))));
}
