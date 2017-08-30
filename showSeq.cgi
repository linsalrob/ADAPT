#!/usr/bin/perl

use strict;
use warnings;
use CGI;
#use CGI::Pretty;
use CGI::Carp qw(fatalsToBrowser);
use ADAPTConfig;

use DBI;
use DBConfig;

#use Data::Dumper;

###########################################################

my $q = new CGI;
my $id = 
$| = 1; # Do not buffer output
&run();

###########################################################

sub run {
    &printHeader();

    #connect to mysql database
    my $dsn = "DBI:mysql:database=".MYSQL_DB.";host=".MYSQL_HOST.";port=".MYSQL_PORT;
    my $dbh = DBI->connect($dsn,MYSQL_USER,'',
			   {
#			       RaiseError => 1,
			       AutoCommit => 1
			   });
    if(!$dbh) { #could not connect to db
	&printWarnings('Could not connect to the database.'.$q->br().$q->br().'Please try again in some minutes or contact the administrator of this service to get help.');
    } else { #get data
	&getSequenceData($dbh,$q->param('id'));
    }

    &printFooter();
}

sub printHeader {
    print 
	$q->header(),
	$q->start_html(-title => 'ADAPT Show ITS information',
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
    $q->br()x2,
	$q->start_form({-method => 'post',
			-name => 'output'}),
	$q->start_table({-border =>'0',
			 -cellspacing => '0',
			 -width => TABLE_WIDTH});
}
  
sub printFooter {
    print
	$q->end_table(),
	$q->end_form(),
	FOOTER,
	$q->end_center(),
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
	$q->Tr($q->th({-align => 'center',
		       -class => 'groupEmpty',
		       -colspan => '2'},
		      $q->button({-value => 'CLOSE',
				  -name => 'closeB',
				  -class => 'buttonreset',
				  -onClick => 'window.close()'}),
		      $q->br()x3));
}

sub getSequenceData {
    my ($dbh,$id) = @_;
    my ($stm,$aref);

    $stm = 'SELECT sequence FROM region WHERE id='.$id;
    $aref = $dbh->selectrow_arrayref($stm);
    my $seq = $aref->[0];
    my $length = length($seq);
    $seq =~ s/(.{80})/$1\<br\>/g;
    $seq = '>ITSid_'.$id.' length:'.$length.$q->br().$seq;

    $stm = 'SELECT source.name,accession,linkout,contig,strand,startpos,stoppos FROM region INNER JOIN (region_entry,entry,source) ON (region.id=region_entry.region_id AND region_entry.entry_id=entry.id AND entry.source_id=source.id) WHERE region.id='.$id;
    $aref = $dbh->selectall_arrayref($stm);
#    die Dumper($aref);
    
    my $data;
    foreach(@$aref) {
	my (@content,$linkout);
	my ($db,$acc,$link,$contig,$strand,$startpos,$stoppos) = @$_;
	push(@content,['Database',$db]);
	push(@content,['Accession',$acc]);
	if($db eq 'NCBI') {
	    $linkout = '<a href="'.LINKOUT_SEQ.$link.'" target="_blank">'.LINKOUT_SEQ.$link.'</a>';
	} elsif($db eq 'SEED') {
	    $linkout = '<a href="'.LINKOUT_SEED.$link.'" target="_blank">'.LINKOUT_SEED.$link.'</a>';
	}
	push(@content,['Linkout',$linkout]);
	push(@content,['Contig',$contig]);
	push(@content,['Strand',($strand ? 'forward' : 'reverse')]);
	push(@content,['Start',$startpos]);
	push(@content,['Stop',$stoppos]);
	$data .= &generateTableContent(shift(@content),\@content,2).$q->br();
    }

    print $q->Tr($q->td({-class => 'groupHeader',
			 -style => 'background-color:'.HEADER_BG_COLOR.';',
			 -align => 'left',
			 -colspan => '2'},
			$q->font({-class => 'groupTitle'},
				 'ITS sequence'))),
          $q->Tr($q->td({-class => 'groupContent',
			 -align => 'left',
			 -colspan => '2'},
			$q->font({-class => 'sequence'},
				 $seq))),
          $q->Tr($q->td({-colspan => '2',
			 -class => 'groupEmpty'},
			'&nbsp;')),
          $q->Tr($q->td({-class => 'groupHeader',
			 -style => 'background-color:'.HEADER_BG_COLOR.';',
			 -align => 'left',
			 -colspan => '2'},
			$q->font({-class => 'groupTitle'},
				 'Retrieved from:'))),
          $q->Tr($q->td({-class => 'groupContent',
			 -align => 'left',
			 -colspan => '2'},
			$q->font({-class => 'sequence'},
				 $data))),
          $q->Tr($q->td({-colspan => '2',
			 -class => 'groupEmpty'},
			'&nbsp;')),
          $q->Tr($q->td({-align => 'center',
			 -class => 'groupEmpty',
			 -colspan => '2'},
		      $q->button({-value => 'CLOSE',
				  -name => 'closeB',
				  -class => 'buttonreset',
				  -onClick => 'window.close()'}),
		      $q->br()x3));
}


sub generateTableContent {
    my ($header,$data,$left,$cols) = @_;
    my $niceData = &generateNiceTableData($data,$cols);
    my $highlight = 0;
    my $content = $q->start_table({-border =>'0',
				   -cellpadding => '2', 
				   -cellspacing => '1',
				   -width => '100%'});
    $content .= $q->Tr({-align => 'left'},
		       map { $q->th({-class => 'hideTableHeader'},$_) } @$header);
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
 			       -class => 'hideBackground'.$highlight},
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
	    } elsif(defined $tr->[$index] && $value eq $tr->[$index]) {
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
	    if($cols && $x>$cols) {
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
