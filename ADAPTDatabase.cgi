#!/usr/bin/perl

use strict;
use warnings;
use CGI;
#use CGI::Pretty;
use CGI::Carp qw(fatalsToBrowser);
use ADAPTConfig;

use DBI;
use DBConfig;

#use GD;
use lib '/opt/bcr/2008-0612/linux-debian-x86_64/lib/perl5/site_perl/5.10.0/';
use GD::Graph::hbars;
use GD::Graph::lines;
use MIME::Base64;

use File::Temp qw(tempfile);
use Data::Dumper;

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

    if(!$dbh) {
	#could not connect to db
	&printWarnings('Could not connect to the database.'.$q->br().$q->br().'Please try again in some minutes or contact the administrator of this service to get help.'.$q->br().$q->br());
    } else {
	$dbh->do('USE '.MYSQL_DB);

	#generating output parts
	my (%outputs,$id,%types);
	$id = 'generalinfo';
	$outputs{$id} = {title => 'General information',
			 show => 1,
			 order => 1,
			 color => HEADER_BG_COLOR,
			 id => $id,
			 data => &generateGeneralInfoTable($dbh)};
	$id = 'regionlengthplot';
	$outputs{$id} = {title => '16S-ITS-23S length information',
			 show => 0,
			 order => 15,
			 color => HEADER_BG_COLOR,
			 id => $id,
			 data => &generateRegionLengthPlot($dbh,$id)};
	$id = 'taxoninfo';
	$outputs{$id} = {title => 'Taxonomy information table',
			 show => 0,
			 order => 10,
			 color => HEADER_BG_COLOR,
			 id => $id,
			 data => &generateTaxonInfoTable($dbh,$id)};
	%types = (table  => 'pathogenic',
		  a      => 'nonpathogenic',
		  b      => 'pathogenic',
		  acolor => 'limegreen',
		  bcolor => 'orangered',
		  acolorC => 'green',
		  bcolorC => 'red');
	$id = 'pathogenicityinfo';
	my ($tableData,$tableDataD,$chartData,$divData) = &generateData($dbh,\%types,$id);
	my $table = &generateDataTableContent($tableData,$tableDataD,\%types,$id.'table');
	my $chart = &generateDataChartContent($chartData,$divData,\%types,$id.'chart',\$imageMaps,\$moDivs);
	$outputs{$id.'table'} = {title => 'Pathogenicity information table',
				 show => 0,
				 order => 20,
				 color => HEADER_BG_COLOR,
				 id => $id.'table',
				 data => $table};
	$outputs{$id.'chart'} = {title => 'Pathogenicity information chart',
				 show => 0,
				 order => 21,
				 color => HEADER_BG_COLOR,
				 id => $id.'chart',
				 data => $chart};
	%types = (table   => 'trophic',
		  a       => 'autotrophic',
		  b       => 'heterotrophic',
		  acolor  => 'lightgreen',
		  bcolor  => 'lightblue',
		  acolorC => 'lgreen',
		  bcolorC => 'lblue');
	$id = 'trophicinfo';
#	my ($tableData,$tableDataD,$chartData,$divData) = &generateData($dbh,\%types,$id);
	$table = &generateDataTableContent($tableData,$tableDataD,\%types,$id.'table');
	$chart = &generateDataChartContent($chartData,$divData,\%types,$id.'chart',\$imageMaps,\$moDivs);
	$outputs{$id.'table'} = {title => 'Trophic information table',
				 show => 0,
				 order => 30,
				 color => HEADER_BG_COLOR,
				 id => $id.'table',
				 data => $table};
	$outputs{$id.'chart'} = {title => 'Trophic information chart',
				 show => 0,
				 order => 31,
				 color => HEADER_BG_COLOR,
				 id => $id.'chart',
				 data => $chart};

	$dbh->disconnect();
	print &generateOutput(\%outputs);
#	$moDivs .= &generateMenuDiv(\%outputs);
    }

    &printFooter($imageMaps,$moDivs);
}

sub printHeader {
    print
	$q->header(),
	$q->start_html(-title => 'ADAPT Database info',
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
	      $q->img({-src => '../../'.ADAPT_DIR.'program1.png',
		       -border => '0',
		       -alt => 'ADAPT '.VERSION.' program',
	     -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'program2.png'.'";',
	     -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'program1.png'.'";'
		      })),
	$q->a({-href => 'ADAPTDatabase.cgi',},
	      $q->img({-src => '../../'.ADAPT_DIR.'database2.png',
		       -border => '0',
		       -alt => 'ADAPT '.VERSION.' database',
#		       -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'database2.png'.'";',
#		       -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'database1.png'.'";'
		      })),
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
	'<div id="outputloading" style="position:fixed; width:99%; text-align:center; top:300px;"><img src="'.'../../'.ADAPT_DIR.'outputloader.gif" border=0 alt="Loading animation"><br /><br /><font style="color:#3366cc;">Loading ...</font></div>',
	'<script>
  var ld=(document.all);var ns4=document.layers;var ns6=document.getElementById&&!document.all;var ie4=document.all;
  if (ns4) ld=document.outputloading;
  else if (ns6) ld=document.getElementById("outputloading").style;
  else if (ie4)ld=document.all.outputloading.style;
  function hideloader() {if(ns4){ld.visibility="hidden";}else if (ns6||ie4) ld.display="none";}
 </script>',
	$q->br()x2,
	$q->start_form({-method => 'post',
			-name => 'database'}),
	$q->start_table({-border =>'0',
			 -width => TABLE_WIDTH,
			 -cellspacing => '0'});
}

sub printFooter {
    my ($imageMaps,$moDivs) = @_;
    print
	$q->end_table(),
	$q->end_form(),
	FOOTER,
	$q->end_center(),
	$imageMaps,
	$moDivs,
	GOOGLE_ANALYTICS,
	$q->end_html();
}

sub printWarnings {
    my ($message) = @_;
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
#	$q->Tr($q->td({-align => 'center',
#		       -class => 'tableButton',
#		       -colspan => '2'},
#		      $q->button({-value => BUTTON_BACK,
#				  -name => 'goback',
#				  -class => 'buttonoutput',
#				  -onClick => 'javascript:history.go(-1);'}),
#		      $q->br()x3))
	;
}

sub generateGeneralInfoTable {
    my $dbh = shift;
    my ($stm,$aref,$content,@tableData);

    #data source
    $stm = 'SELECT DISTINCT name FROM source INNER JOIN entry ON entry.source_id=source.id;';
    $aref = $dbh->selectall_arrayref($stm);
    push(@tableData,['Data source',scalar(@$aref).' ('.join(", ",map{$_->[0]}@$aref).')']);

    #number entries from data sources
    $stm = 'SELECT COUNT(*) FROM entry';
    $aref = $dbh->selectrow_arrayref($stm);
    push(@tableData,['Retrieved entry',$aref->[0]]);

    #number 16S-ITS-23S region entries
    $stm = 'SELECT COUNT(*) FROM region';
    $aref = $dbh->selectrow_arrayref($stm);
    push(@tableData,['16S-ITS-23S region',$aref->[0]]);

    #number organism entries
    $stm = 'SELECT COUNT(*) FROM organism';
    $aref = $dbh->selectrow_arrayref($stm);
    push(@tableData,['Organism',$aref->[0]]);

    #taxon
    $stm = 'SELECT CONCAT((SELECT COUNT(DISTINCT kingdom) FROM taxon),\', \',(SELECT COUNT(DISTINCT phylum) FROM taxon),\', \',(SELECT COUNT(DISTINCT genus) FROM taxon),\', \',(SELECT COUNT(*) FROM taxon));';
    $aref = $dbh->selectrow_arrayref($stm);
    push(@tableData,['Taxon (Kingdom, Phylum, Genus, Species)',$aref->[0]]);

    $content = &generateTableContent(['Entry type','Number of entries'],\@tableData,0);

    $stm = 'SELECT CONCAT(DATE(MAX(adding_date)),\' (\',DATEDIFF((SELECT NOW()),MAX(adding_date)),\' days ago)\') FROM entry;';
    $aref = $dbh->selectrow_arrayref($stm);
    $content .= $q->br().$q->font({-class => 'table_info'},$q->b('Last database update: ').$aref->[0]);

    return $content;
}

sub generateRegionLengthPlot {
    my ($dbh,$id) = @_;
    my ($stm,$href,$xmax);
    my ($hidden,@data);
    $stm = 'SELECT length,COUNT(id) AS entries FROM region GROUP BY length ORDER BY length';
    $href = $dbh->selectall_hashref($stm,'length');
    my $step = 15;
    my $max = 6000; #MAX_LENGTH
    $xmax = (reverse sort {$a <=> $b} keys %$href)[0];
    $xmax = $max unless($xmax < $max);
    $xmax = int($xmax/$step+1)*$step if($xmax % $step);
    for my $x (0..$xmax) {
	push(@{$data[0]},$x);
	push(@{$data[1]},(exists $href->{$x} ? $href->{$x}->{entries} : 0));
    }
    my @colors = ('blue');
    my $height = 200+50+40;
    my $graph = GD::Graph::lines->new(TABLE_WIDTH-10,$height);
    $graph->set(
		x_label          => 'Length',
		y_label          => 'Number of distinct entries',
#		title            => '',
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
#    $graph->set_legend_font(GD::gdLargeFont);
#    $graph->set_legend('Database entries','Length hits');
    my $chart = $graph->plot(\@data) or die $graph->error;
    $hidden = &generateHiddenContent(0,\@data,$id,0,\@colors);
    return &generateImagePart($id,$chart,$hidden);
}

sub generateTaxonInfoTable {
    my ($dbh,$id) = @_;
    my ($stm,$aref);
    my ($hidden,$contentA,$contentD);
    #abbreviated table
    $stm = 'SELECT kingdom,phylum,CONCAT(COUNT(*),\' (\',ROUND((COUNT(*)*100)/(SELECT COUNT(*) FROM organism),2),\'%)\') FROM taxon INNER JOIN organism ON organism.taxon_id=taxon.id GROUP BY phylum ORDER BY kingdom,phylum';
    $aref = $dbh->selectall_arrayref($stm);
    $contentA = &generateTableContent(['Kingdom','Phylum','Number of organisms'],$aref,1);
    $hidden = &generateHiddenContent(['Kingdom','Phylum','Number of organisms'],$aref,$id.'_a');

    #detailed table
    $stm = 'SELECT kingdom,phylum,CONCAT(tmp.number,\' (\',ROUND((tmp.number*100)/(SELECT COUNT(*) FROM organism),2),\'%)\'),CONCAT(COUNT(*),\' (\',ROUND((COUNT(*)*100)/(SELECT COUNT(*) FROM organism_region INNER JOIN region ON region.id=organism_region.region_id),2),\'%)\'),ROUND(COUNT(*)/tmp.number,2) FROM taxon INNER JOIN (SELECT phylum AS p,COUNT(*) AS number FROM taxon INNER JOIN organism ON organism.taxon_id=taxon.id GROUP BY phylum ORDER BY kingdom,phylum) AS tmp ON tmp.p=taxon.phylum INNER JOIN organism ON organism.taxon_id=taxon.id INNER JOIN organism_region ON organism_region.organism_id=organism.id INNER JOIN region ON organism_region.region_id=region.id GROUP BY phylum ORDER BY kingdom,phylum;';
    $aref = $dbh->selectall_arrayref($stm);
    $contentD = &generateTableContent(['Kingdom','Phylum','Number of organisms','Number of Regions','Regions per organism'],$aref,1);
    $hidden .= &generateHiddenContent(['Kingdom','Phylum','Number of organisms','Number of Regions','Regions per organism'],$aref,$id.'_d');

    #generate and return table div
    return &generateTablePart($id,$hidden,$contentA,$contentD);
}

sub generateData {
    my ($dbh,$types,$id) = @_;
    my ($stm,$aref1,$aref2,$aref3,$aref4);
    my (@tableData,@tableDataD); #table data abbreviated and detailed (D)
    my (@chartData,@divData); #chart data with data for tooltip div's

    #abbreviated table
    $stm = 'SELECT '.$types->{table}.'.kind as Kind,CONCAT(COUNT(*),\' (\',ROUND((COUNT(*)*100)/(SELECT COUNT(*) FROM organism),2),\'%)\') AS \'Number of organisms\' FROM '.$types->{table}.' INNER JOIN organism ON organism.'.$types->{table}.'_id='.$types->{table}.'.id GROUP BY '.$types->{table}.'.kind ORDER BY '.$types->{table}.'.kind';
    $aref1 = $dbh->selectall_arrayref($stm);
    @tableData = @$aref1;

    #detailed table
    $stm = 'SELECT '.$types->{table}.'.kind as a,taxon.phylum as Phylum,CONCAT(COUNT(*),\' (\',ROUND((COUNT(*)*100)/(SELECT COUNT(*) FROM organism),2),\'%)\') AS \'Number of organisms\' FROM '.$types->{table}.' INNER JOIN organism ON organism.'.$types->{table}.'_id='.$types->{table}.'.id INNER JOIN taxon ON organism.taxon_id=taxon.id GROUP BY '.$types->{table}.'.kind,taxon.phylum ORDER BY '.$types->{table}.'.kind,taxon.phylum';
    $aref2 = $dbh->selectall_arrayref($stm);
    @tableDataD = @$aref2;

    #chart data
    $stm = 'SELECT '.$types->{table}.'.kind as Kind,ROUND((COUNT(*)*100)/(SELECT COUNT(*) FROM organism),2) FROM '.$types->{table}.' INNER JOIN organism ON organism.'.$types->{table}.'_id='.$types->{table}.'.id GROUP BY '.$types->{table}.'.kind ORDER BY '.$types->{table}.'.kind';
    $aref3 = $dbh->selectall_arrayref($stm);
    push(@chartData,([' '],map{[$_->[1]]}@$aref3));

    #div data
    $stm = 'SELECT '.$types->{table}.'.kind as Kind,taxon.phylum as Phylum FROM '.$types->{table}.' INNER JOIN organism ON organism.'.$types->{table}.'_id='.$types->{table}.'.id INNER JOIN taxon ON organism.taxon_id=taxon.id GROUP BY '.$types->{table}.'.kind,taxon.phylum ORDER BY '.$types->{table}.'.kind,taxon.phylum';
    $aref4 = $dbh->selectall_arrayref($stm);
    my %tmp;
    foreach(@$aref4) {
	$tmp{$_->[0]}->{$_->[1]} = 1;
    }
    push(@divData,[$types->{a},'a',$types->{acolor},sprintf("%.2f",$aref3->[0]->[1]),join("<br />",sort keys %{$tmp{$types->{a}}})]);
    push(@divData,[$types->{b},'b',$types->{bcolor},sprintf("%.2f",$aref3->[1]->[1]),join("<br />",sort keys %{$tmp{$types->{b}}})]);
    push(@divData,['unknown','u','lightgray',sprintf("%.2f",$aref3->[2]->[1]),join("<br />",sort keys %{$tmp{'unknown'}})]);

    return (\@tableData,\@tableDataD,\@chartData,\@divData);
}

sub generateDataTableContent {
    my ($tableData,$tableDataD,$types,$id) = @_;
    my ($hidden,$contentA,$contentD);
    $hidden = &generateHiddenContent([ucfirst($types->{table}).($types->{table} eq 'pathogenic' ? 'ity':''),'Number of organisms'],$tableData,$id.'_a');
    $contentA = &generateTableContent([ucfirst($types->{table}).($types->{table} eq 'pathogenic' ? 'ity':''),'Number of organisms'],$tableData,1);
    $hidden .= &generateHiddenContent([ucfirst($types->{table}).($types->{table} eq 'pathogenic' ? 'ity':''),'Phylum','Number of organisms'],$tableDataD,$id.'_d');
    $contentD = &generateTableContent([ucfirst($types->{table}).($types->{table} eq 'pathogenic' ? 'ity':''),'Phylum','Number of organisms'],$tableDataD,1);
    #generate and return table div
    return &generateTablePart($id,$hidden,$contentA,$contentD);
}

sub generateDataChartContent {
    my ($chartData,$divData,$types,$id,$imageMaps,$moDivs) = @_;
    my ($hidden,$contentA,$contentD,$cumulate,$height);

    #generate chart
    $cumulate = 1;
    my $number = scalar(@{$chartData->[0]});
    $height = $number*10+50+40;
    my @legend = (ucfirst($types->{a}),ucfirst($types->{b}),'Unknown');
    my @colors = ($types->{acolorC},$types->{bcolorC},'lgray');
    my $graph = GD::Graph::hbars->new(TABLE_WIDTH-10,$height);
    $graph->set(
#		x_label          => ' ',
		y_label          => 'Percentage',
#		title            => 'ADAPT results',
		legend_spacing   => 5,
		legend_placement => 'BC', #B[LCR] | R[TCB]
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
    my $chart = $graph->plot($chartData) or die $graph->error;
    $hidden = &generateHiddenContent(0,$chartData,$id,\@legend,\@colors);

    #generate image map
    my $imagemap = '<map name="chartMap_'.$id.'">'."\n";
    my @mapData = $graph->get_hotspot;
    shift(@mapData);
    my $index = -1;
    my @typeIds = ('a','b','u','nh');
    foreach my $type (@mapData) {
 	my $tmp = '_'.shift(@typeIds);
 	foreach my $cords (@$type) {
 	    $index++;
 	    next if(!@$cords[1] || !@$cords[3] ||@$cords[1] == @$cords[3]);
 	    $imagemap .= "\t".'<area id="'.$id.$tmp.'" shape="rect" coords="'.@$cords[1].','.@$cords[2].','.@$cords[3].','.@$cords[4].'" onMouseOver="showTooltip(\'c_'.$id.$tmp.'\')" onMouseOut="hideTooltip()">'."\n";
 	}
 	$index = -1;
    }
    $imagemap .= '</map>'."\n";
    $$imageMaps .= $imagemap;

    #generate mouseover divs
    my $divs;
    $divs = &generateMODivContent($divData,$id);
    $$moDivs .= $divs;

    #generate and return chart data
    return &generateImagePart($id,$chart,$hidden);
}

sub generateOutput {
    my $outputs = shift;
    my $content;
    $content .= $q->hidden(-name => 'id', -default => '',-id => 'id');
    my @keys = sort {$outputs->{$a}->{order} <=> $outputs->{$b}->{order}} keys %$outputs;
    foreach my $id (@keys) {
	$content .= &generatePartContent($outputs->{$id}->{title},
					 $outputs->{$id}->{show},
					 $outputs->{$id}->{color},
					 $outputs->{$id}->{id}.'D',
					 $outputs->{$id}->{data});
    }
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
	$content .= '<div class="tooltip" id="c_'.$id.'_'.$_->[1].'">'."\n";
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
				  'Phyla:'),
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
    foreach my $key ('generalinfo','taxoninfo','pathogenicityinfo','trophicinfo') {
	@keys = ();
	push(@keys,$key) if(exists $outputs->{$key});
	push(@keys,$key.'table') if(exists $outputs->{$key.'table'});
	push(@keys,$key.'chart') if(exists $outputs->{$key.'chart'});
	next unless(@keys);
	$count++;
	$tmp .= $q->Tr($q->td({-class => 'tbg0',
			       -width => '80%',
			       -align => 'left'},
			      $q->font({-class => 'menutext'},
				       $q->a({-href => 'ADAPTDatabase.cgi#goto'.$key},ucfirst($key)))),
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
    foreach my $kind ('general','plots','pathogenicity','trophic','multiple') {
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
    my ($id,$hidden,$table1,$table2,$extra) = @_;
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
			       -onClick => 'document.getElementById(\'id\').value="'.$id.'";document.forms.database.action="exportTable.cgi";document.forms.database.submit();'}).
		   $q->hr().
		   ($table2 ? $q->b('Show: ').
		    $q->radio_group(-name => 'showTable_'.$id,
				    -values => ['d','a'],
				    -default => 'a',
				    -labels => {'d' => 'detailed',
						'a' => 'abbreviated'},
				    -attributes => {'d' => {-onClick => 'document.getElementById(\''.$id.'bT\').style.display=\'block\';document.getElementById(\''.$id.'aT\').style.display=\'none\';'},
						    'a' => {-onClick => 'document.getElementById(\''.$id.'aT\').style.display=\'block\';document.getElementById(\''.$id.'bT\').style.display=\'none\';'}}) : '').
		   $q->div({-id => $id.'aT',
			    -style => 'display:block;'},
			   $table1).
		   ($table2 ? $q->div({-id => $id.'bT',
				       -style => 'display:none;'},
				      $table2) : ''));
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
			       -onClick => 'document.getElementById(\'id\').value="'.$id.'";document.forms.database.action="exportChart.cgi";document.forms.database.submit();'}).
		   $q->hr()) unless($noexport);
    $imagePart .= $q->img({-src => (USED_BROWSER ? &inline_image($image) : &external_image($image,$id)),
			   -border => '0',
			   -usemap => '#chartMap_'.$id});
    return $imagePart;
}

sub inline_image {
    my ($content) = @_;
    return "data:image/png;base64,".MIME::Base64::encode_base64((ref $_[0] && $_[0]->isa('GD::Image')) ? $_[0]->png : $_[0]);
}

sub external_image {
    my ($content,$id) = @_;
    &checkForOldFiles();
    my $filename = time().'_'.$id.'.png';
    my $url = TMP_DIR_CGI.$filename;
    open(IMG,">$url") or return "Could not create image file: $!\n";
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
#	print $1."\n";
	unlink($url.$file) if(($time-$1)>100000);
    }
    closedir(BIN);
    return;
}
