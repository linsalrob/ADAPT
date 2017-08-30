#!/usr/bin/perl

use strict;
use warnings;
use CGI;
use CGI::Carp qw(fatalsToBrowser);

my $q = new CGI;

my $id = $q->param('id');
my $id2 = $q->param('id2');
my $type = ($q->param('exportFormat_'.$id) ? $q->param('exportFormat_'.$id) : $q->param('exportFormat_'.$id2));
my $mime = $type eq 'tsv' ? 'tab-separated-values' : 'comma-separated-values';
my $table = ($q->param('showTable_'.$id) ? 'exportData_'.$id.'_'.$q->param('showTable_'.$id) : 'exportData_'.$id.'_'.$id2);

print $q->header(-type => 'text/'.$mime,
		 -content_disposition => 'attachment; filename="'.$id.'.'.$type.'"');

my $file = $q->param($table);
open(DATA,"<$file") or die "ERROR: could not open file $file: $!\n";
while(<DATA>) {
    next if(/^\#/);
    s/\t/\,/g if($type eq 'csv');
    print $_;
}
close(DATA);

