#!/usr/bin/perl

use strict;
use warnings;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use GD::Graph::hbars;
use GD::Graph::mixed;
use GD::Graph::lines;
use ADAPTConfig;

my $q = new CGI;

my $id = $q->param('id');
my $id2 = $q->param('id2');
my $type = ($q->param('imageFormat_'.$id) ? $q->param('imageFormat_'.$id) : $q->param('imageFormat_'.$id2));
my $data = ($q->param('showChart_'.$id) ? 'exportData_'.$id.$q->param('showChart_'.$id) : 'exportData_'.$id.$id2);
my $file = $q->param($data);
my (@chartData,@legend,@colors);
my $index = 0;
open(DATA,"<$file") or die "ERROR: could not open file $file: $!\n";
while(<DATA>) {
    chomp();
    if(/^\#legend\:(.+)$/) {
	@legend = split(/\t/,$1);
    } elsif(/^\#colors\:(.+)$/) {
	@colors = split(/\t/,$1);
    } else {
	@{$chartData[$index++]} = split(/\t/,$_);
    }
}
close(DATA);

print $q->header(-type => 'image/'.$type,
		 -content_disposition => 'attachment; filename="'.$id.($id2 ? $id2 : '').'.'.$type.'"');

my $chart;
if($id =~ /^tracefileplots\d+/) {
    my $name = $legend[0];
    my $xmax = (reverse @{$chartData[0]})[0];
    my $ymax = 0;
    foreach my $m (@{$chartData[3]}) {
	$ymax = $m if($m > $ymax);
    }
    $ymax = int($ymax*1.02/5+1)*5;
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
		    x_tick_number => 20,
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
    $chart = $graph->plot(\@chartData) or die $graph->error;
} elsif($id eq 'pathogenicaveragechart' || $id eq 'trophicaveragechart') {
    my $number = scalar(@{$chartData[0]});
    my ($height,$cumulate);
    $cumulate = 1;
    $height = $number*10+50+60;
    my $graph = GD::Graph::hbars->new(TABLE_WIDTH-10,$height);
    $graph->set(
		x_label          => 'Sample names',
		y_label          => 'Percentage',
		title            => 'ADAPT results',
		legend_spacing   => 5,
		legend_placement => 'RC', #B[LCR] | R[TCB]
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
	        transparent      => 0,
		dclrs => \@colors
		) or warn $graph->error;
    $graph->set_x_label_font(GD::gdMediumBoldFont);
    $graph->set_y_label_font(GD::gdMediumBoldFont);
    $graph->set_x_axis_font(GD::gdSmallFont);
    $graph->set_y_axis_font(GD::gdTinyFont);
#  $graph->set_values_font(GD::gdMediumBoldFont);
    $graph->set_legend_font(GD::gdLargeFont);
    $graph->set_legend(@legend);
    $chart = $graph->plot(\@chartData) or die $graph->error;    
} elsif($id eq 'pathogenicityinfochart' || $id eq 'trophicinfochart') {
    my $cumulate = 1;
    my $number = scalar(@{$chartData[0]});
    my $height = $number*10+50+40;
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
	        transparent      => 0,
		dclrs => \@colors
		) or warn $graph->error;
    $graph->set_x_label_font(GD::gdMediumBoldFont);
    $graph->set_y_label_font(GD::gdMediumBoldFont);
    $graph->set_x_axis_font(GD::gdSmallFont);
    $graph->set_y_axis_font(GD::gdTinyFont);
#  $graph->set_values_font(GD::gdMediumBoldFont);
    $graph->set_legend_font(GD::gdLargeFont);
    $graph->set_legend(@legend);
    $chart = $graph->plot(\@chartData) or die $graph->error;
} elsif($id eq 'regionlengthplot') {
    my $step = 15;
    my $xmax = 6000;
    my $height = 200+50+40;
    my $graph = GD::Graph::lines->new(TABLE_WIDTH-10,$height);
    $graph->set(
	        x_label          => 'Length',
		y_label          => 'Number of distinct entries',
		title            => 'Distribution of length for distict 16S-ITS-23S regions',
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
    $chart = $graph->plot(\@chartData) or die $graph->error;
} elsif($id eq 'primermatchchart') {
    my $step = 10;
    my $xmax = scalar(@{$chartData[0]}-1);
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
#    $graph->set_legend_font(GD::gdLargeFont);
    $chart = $graph->plot(\@chartData) or die $graph->error;
}

print $chart->$type;

