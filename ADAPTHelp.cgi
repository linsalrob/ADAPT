#!/usr/bin/perl

use strict;
use warnings;
use CGI;
#use CGI::Pretty;
use CGI::Carp qw(fatalsToBrowser);
use ADAPTConfig;
use DBConfig;

my $browser = USED_BROWSER;
my $q = new CGI;

print 
    $q->header(),
    $q->start_html(-title => 'ADAPT Help',
		   -style => CSS_FILE,
		    -script => {-language => 'JAVASCRIPT',
			        -src => JS_FILE_MU}),
    $q->start_center(),
    $q->a({-name => 'top'}),
    $q->a({-href => 'ADAPTHome.cgi'},
    $q->img({-src => '../../'.ADAPT_DIR.'adapt.png',
	     -border => '0',
	     -alt => 'ADAPT '.VERSION.' logo - home'})),
    $q->a({-href => 'ADAPTInput.cgi',},
    $q->img({-src => '../../'.ADAPT_DIR.'program1.png',
	     -border => '0',
	     -alt => 'ADAPT '.VERSION.' program',
	     -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'program2.png'.'";',
	     -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'program1.png'.'";'})),
    $q->a({-href => 'ADAPTDatabase.cgi',},
    $q->img({-src => '../../'.ADAPT_DIR.'database1.png',
	     -border => '0',
	     -alt => 'ADAPT '.VERSION.' database',
	     -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'database2.png'.'";',
	     -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'database1.png'.'";'})),
    $q->a({-href => 'ADAPTHelp.cgi',},
    $q->img({-src => '../../'.ADAPT_DIR.'help2.png',
	     -border => '0',
	     -alt => 'ADAPT '.VERSION.' help',
#	     -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'help2.png'.'";',
#	     -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'help1.png'.'";'
	    })),
    $q->a({-href => 'ADAPTContact.cgi',},
    $q->img({-src => '../../'.ADAPT_DIR.'contact1.png',
	     -border => '0',
	     -alt => 'ADAPT '.VERSION.' contact',
	     -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'contact2.png'.'";',
	     -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'contact1.png'.'";'})),
    $q->br()x2,

    $q->start_table({-border =>'0',
		     -width => TABLE_WIDTH,
		     -cellspacing => '0'}),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
#		  $q->a({-name => 'top'}),
		  $q->font({-class => 'tableQuestion'},
			   'Help content'))),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   $q->a({-href => 'ADAPTHelp.cgi#ADAPT'}, '1. What is ADAPT?').$q->br(),
			   $q->a({-href => 'ADAPTHelp.cgi#ADAPTdb'}, '2. What is ADAPTdb?').$q->br(),
			   $q->a({-href => 'ADAPTHelp.cgi#ARISA'}, '3. What is ARISA?').$q->br(),
			   $q->a({-href => 'ADAPTHelp.cgi#findITS'}, '4. How do we find 16S-ITS-23S regions?').$q->br(),
			   $q->a({-href => 'ADAPTHelp.cgi#fractions'}, '5. How are the fractions calculated?').$q->br(),
			   $q->a({-href => 'ADAPTHelp.cgi#more'}, '6. What should I do if I have more questions?').$q->br(),
			   ))),
    $q->Tr($q->td({-colspan => '2',
		   -class => 'background0'},
		  '&nbsp;')),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->a({-name => 'ADAPT'}),
		  $q->font({-class => 'tableQuestion'},
			   '1. What is ADAPT?')),
	   $q->td({-colspan => '1',
		   -align => 'right',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'footer'},
		  $q->a({-href => 'ADAPTHelp.cgi#top'},'top')))),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   'There are more and more researchers interested in exploring microbial community samples, and Automated Ribosomal Intergenic Spacer Analysis (ARISA) profiles provide a cheap and convenient method to visualize the temporal and spatial changes that are occurring in a community. ADAPT is the first tool designed to analyze ARISA data sets, and the only online resource capable of highlighting those differences based on the metadata associated with the organisms.',
			   $q->br()x2,
			   'ADAPT ('.$q->b('A').'RISA '.$q->b('D').'ata '.$q->b('A').'nalysis program for '.$q->b('P').'athogenic and '.$q->b('T').'rophic comparison) is a web-application and was originally developed and designed for the data analysis needs of the '.$q->a({-href => 'http://phage.sdsu.edu',-target => '_blank'},'Rohwer Lab').' at '.$q->a({-href => 'http://www.sdsu.edu',-target => '_blank'},'San Diego State University (SDSU)').'. Since then, ADAPT was further developed to fit the needs of researchers in other labs.',
			   $q->br()x2,
			   'ADAPT is a web-based bioinformatics tool to taxonomically characterize ARISA data sets by comparing the ARISA profiles to our existing ADAPTdb database. Based on the comparison results, the program provides the user with a likely representation of what species are in the analyzed samples. Additionally, the program also performs pathogenicity and autotrophic/heterotrophic comparisons of organisms among different ARISA samples using the additional organism information for each 16S-ITS-23S region in the ADAPTdb database, and provides a table and graphical representation of the autotrophic/heterotrophic and the pathogenic/non-pathogenic average fraction for each sample.'.$q->br().'If the input file contains data from more than one sample, ADAPT also compares the profiles between samples to highlight similarities and differences among those samples.',
			   $q->br()x2,
			   'The program is publicly available through a user-friendly web interface, which allows onsite analysis of ARISA data sets and computation of the output. The interactive web interface facilitates navigation through the output and export functionality for subsequent analysis.',
			   $q->br()))),
    $q->Tr($q->td({-colspan => '2',
		   -class => 'background0'},
		  '&nbsp;')),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->a({-name => 'ADAPTdb'}),
		  $q->font({-class => 'tableQuestion'},
			   '2. What is ADAPTdb?')),
	   $q->td({-colspan => '1',
		   -align => 'right',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'footer'},
			   $q->a({-href => 'ADAPTHelp.cgi#top'},'top')))),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   'The database <b>ADAPTdb</b> was created to store and maintain 16S-ITS-23S regions along with information about their source organisms. The data stored in ADAPTdb is retrieved from different data resources, such as the SEED and NCBI sequence databases.',
			   $q->br()x2,
			   'Data currently stored in ADAPTdb inlcudes: data source, accession and version information, organism name, taxonomy, trophic classification, pathogenicity, host description, ITS and flanking 16S/23S region sequence. The ADAPT web-interface describes the current content of the ADAPTdb database under the menu "DATABASE".',
			   $q->br()))),
    $q->Tr($q->td({-colspan => '2',
		   -class => 'background0'},
		  '&nbsp;')),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->a({-name => 'ARISA'}),
		  $q->font({-class => 'tableQuestion'},
			   '3. What is ARISA?')),
	   $q->td({-colspan => '1',
		   -align => 'right',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'footer'},
		  $q->a({-href => 'ADAPTHelp.cgi#top'},'top')))),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   $q->b('ARISA').' ('.$q->b('A').'utomated '.$q->b('R').'ibosomal '.$q->b('I').'ntergenic '.$q->b('S').'pacer '.$q->b('A').'nalysis) is a method for analyzing the composition of microbial communities and is both faster and cheaper than other community profiling techniques. ARISA relies on the analysis of intergenic regions called Internal Transcribed Spacers (ITS), which are located between the 16S and 23S rRNA genes. The method was first developed by Fisher and Triplett ['.$q->a({-href => 'http://www.pubmedcentral.nih.gov/articlerender.fcgi?tool=pubmed&pubmedid=10508099',-target => '_blank'},'PMID: 10508099').'] and is widely used by marine microbial ecologists.',
			   $q->br(),
			   'In the basic approach, the ITS-region between 16S and 23S rRNA genes of the extracted DNA is amplified using PCR with fluorescently labeled primers, and the sample is run on a sequencing machine (see figure below). The length of the intergenic spacer region (including the parts of the 16S and 23S rRNA genes where the primers bind) is measured from the trace output. ARISA data analysis steps include profile filtering, data transformation, database search, value calculation, and sample comparison.',
			   $q->br()x2,
			   '<center>',
			   $q->img({-src => '../../'.ADAPT_DIR.'arisa.png',-border => '1',-alt => 'Basic ARISA workflow'}),
			   '</center>',
#			   $q->br()
		  ))),
    $q->Tr($q->td({-colspan => '2',
		   -class => 'background0'},
		  '&nbsp;')),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->a({-name => 'findITS'}),
		  $q->font({-class => 'tableQuestion'},
			   '4. How do we find 16S-ITS-23S regions?')),
	   $q->td({-colspan => '1',
		   -align => 'right',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'footer'},
		  $q->a({-href => 'ADAPTHelp.cgi#top'},'top')))),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   'The 16S-ITS-23S regions are parsed out from the data retrieved from different external data resources. Currently, we are using the NCBI and The SEED databases as data resources.',
			   $q->br(),
			   'The process of finding 16S-ITS-23S regions requires several steps. Details of how we retrieve the data, search for 16S and 23S regions, and find valid ITS regions can be found below. All valid 16S-ITS-23S regions are added to the ADAPTdb database, which is used by ADAPT for its analysis.',
			   $q->br()x2,
			   $q->b('Retrieve data from external data resource (databases):'),
			   $q->br(),
			   '<ul>',
			   '<li>NCBI databases - using ESearch and EFetch from the Entrez Programming Utilities (eUtils)</li>',
			   '<li>The SEED - using SOAP (Simple Object Access Protocol) web services</li>',
			   '</ul>',
			   $q->br(),
			   $q->b('Search for 16S and 23S regions:'),
			   $q->br(),
			   '<ul>',
			   '<li>NCBI data:</li>',
			   '<ul>',
			   '<li>check if GBK file contains 16S <u>and</u> 23S rRNA annotations<br />(use regular expressions for "16S ribosomal RNA", "23S ribosomal RNA", "16S rRNA", "23S rRNA", and its variations)</li>',
			   '<li>find feature type "rRNA"</li>',
			   '<li>check for description containing "rRNA" or "ribosomal RNA" (usually in "/product=" definition)</li>',
			   '&rArr;&nbsp;description contains 16S for 16S regions',
			   $q->br(),
			   '&rArr;&nbsp;description contains 23S for 23S regions',
			   $q->br()x2,
			   '</ul>',
			   '<li>The SEED data: </li>',
			   '<ul>',
			   '<li>find all RNAs in genome (use rnas_of() function)</li>',
			   '<li>check for annotation containing "SSU rRNA" and "LSU rRNA" (use function_of() function)</li>',
			   '&rArr;&nbsp;SSU rRNA regions are 16S regions',
			   $q->br(),
			   '&rArr;&nbsp;LSU rRNA regions are 23S regions',
			   '</ul>',
			   '</ul>',
			   $q->br(),
			   $q->b('Steps to find valid ITS regions*:'),
#			   $q->br(),
			   '<ol>',
			   '<li>find all 16S regions in contig</li>',
			   '<li>find all 23S regions in same contig</li>',
			   '<li>discard overlapping regions on same strand (16S with 16S, 23S with 23S, 16S with 23S)</li>',
			   '<li>check for each 16S region in contig: <i>(see figure below for example)</i></li>',
			   '<ul>',
			   '<li>16S region before 23S on forward strand</li>',
			   '<li>16S region behind 23S on on reverse strand</li>',
			   '<li>16S and 23S region is at least 300 bp long</li>',
			   '<li>region between 16S and 23S region is less than '.MAX_LENGTH.' bp long</li>',
			   '&rArr;&nbsp;found valid 16S-ITS-23S region',
			   '</ul>',
			   '<li>repeat step 4 until no 16S regions left</li>',
			   '</ol>',
#			   $q->br()x2,
			   '<center>',
			   $q->img({-src => '../../'.ADAPT_DIR.'pairwise_example.png',-border => '1',-alt => 'Pairwise iteration example'}),
			   '</center>',
			   $q->br(),
			   '*&nbsp;The ITS region mentioned here is refering to the ITS1 region between the 16S and 23S rRNA gene.',
			   $q->br()))),
    $q->Tr($q->td({-colspan => '2',
		   -class => 'background0'},
		  '&nbsp;')),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->a({-name => 'fractions'}),
		  $q->font({-class => 'tableQuestion'},
			   '5. How are the fractions calculated?')),
	   $q->td({-colspan => '1',
		   -align => 'right',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'footer'},
		  $q->a({-href => 'ADAPTHelp.cgi#top'},'top')))),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   'ADAPT does not only taxonomically characterize ARISA data sets, but also performs calculations on the input data. Currently, those calculations are done to find the fraction of trophic and pathogenic organisms in the input ARISA profiles. The calculations are the same for trophic or pathogenic fractions. There are different ways to calculate such fractions and ADAPT implements the average fraction calculation which is explained below. The following also contains the total fraction calculation as an additonal example of fraction calculation and to show the better use of the average fraction.',
			   $q->br()x2,
			   $q->b('Fraction calculation'),
			   $q->br(),
			   'Let <i>P = {p<sub>i</sub> }</i> represent the set of peaks in a given ARISA data set (profile), <i>i = 1, 2, ..., n</i> where <i>n</i> is the total number of peaks in <i>p<sub>i</sub></i> . If <i>F<sub>i</sub></i>&nbsp; denotes the fraction of peak <i>p<sub>i</sub></i> then this fraction is calculated as follows:',
			   $q->br(),
			   '<center><i>F<sub>i</sub> = 100 * h<sub>i</sub> &nbsp;/ S</i></center>',
#			   $q->br(),
			   'where <i>h<sub>i</sub></i> denotes the height (or intensity) of peak <i>p<sub>i</sub></i>&nbsp; and <i>S = &sum;<sub>i</sub> h<sub>i</sub></i>&nbsp; denotes a normalization factor. The normalization factor <i>S</i> ensures that the weights sum up to 100.',
			   $q->br(),
			   'Let <i>T = {t<sub>j</sub> }</i> denote the set of types (e.g. where <i>t<sub>j</sub></i>&nbsp; for trophic types is either autotrophic, heterotrophic, or unknown).',
			   $q->br()x2,
			   $q->b('Total fraction having <u>any</u> characteristics of type <i>t<sub>j</sub></i>'),
			   $q->br(),
			   'The total fraction <i>A<sub>j</sub></i>&nbsp; of type <i>t<sub>j</sub></i>&nbsp; over all peaks in the profile is computed as a sum of the peaks which have at least one matching database entry of type <i>t<sub>j</sub></i> .',
			   $q->br(),
			   'Let <i>C<sub>i,j</sub></i> = { 1 : type <i>t<sub>j</sub></i>&nbsp; has an entry in the database for peak <i>p<sub>i</sub></i>&nbsp;; 0 : otherwise }. Then',
			   $q->br(),
			   '<center><i>A<sub>j</sub>&nbsp; = &sum;<sub>i</sub>&nbsp;<big>(</big>C<sub>i,j</sub> * F<sub>i</sub>&nbsp;<big>)</big></i></center>',
			   $q->br()x2,
			   $q->b('Average fraction having characteristics of type <i>t<sub>j</sub></i>'),
			   $q->br(),
			   'The average fraction <i>B<sub>j</sub></i>&nbsp; of type <i>t<sub>j</sub></i>&nbsp; as a sum of fractions of the peaks is computed as follows: Let <i>m<sub>i,j</sub></i>&nbsp; be the number of matching database entries of type <i>t<sub>j</sub></i>&nbsp; of peak <i>p<sub>i</sub></i>&nbsp;. Then <i>&sum;<sub>j</sub>&nbsp;m<sub>i,j</sub></i>&nbsp; is the total number of of machting database entries of peak <i>p<sub>i</sub></i>&nbsp;. The fraction of matching <i>t<sub>j</sub></i>&nbsp;-type entries of peak <i>p<sub>i</sub></i>&nbsp; is given by <i>m<sub>i,j</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>i,j</sub></i>&nbsp;. The average fraction for peak <i>p<sub>i</sub></i>&nbsp; is then <i>m<sub>i,j</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>i,j</sub>&nbsp;* F<sub>i</sub></i>&nbsp;. Finally, the average fraction for all peaks <i>p<sub>i</sub></i>&nbsp; having characteristics of type <i>t<sub>j</sub></i>&nbsp; in the ARISA profile is',
			   $q->br(),
			   '<center><i>B<sub>j</sub>&nbsp; = &sum;<sub>i</sub>&nbsp; <big>(</big> m<sub>i,j</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>i,j</sub>&nbsp;* F<sub>i</sub>&nbsp; <big>)</big></i></center>',
			   $q->br()x2,
			   $q->b('A simple example'),
			   $q->br(),
			   'Let us assume a simple example of a profile with three peaks (as shown in the figure below). We have the first peak at a length of 100 and a height of 4, the second peak at a length of 200 and a height of 2, and the third peak at a length of 300 and a height of 3. Using the length to search in the database for matching ITS regions, we find that there is one hit for the first and third peak and 2 hits for the second peak. The two hits for the second peak have characteristics of different types (type <i>t<sub>1</sub></i>&nbsp; and type <i>t<sub>2</sub</i>&nbsp;).',
			   $q->br(),
			   'There are now two different possibilities of calculating the fraction for the different types: total fraction of having any characteristics of the type and average fraction having chracteristics of the type.',
			   $q->br()x2,
			   '<center>',
			   $q->img({-src => '../../'.ADAPT_DIR.'fraction_example.png',-border => '1',-alt => 'Simple fraction example'}),
			   '</center>',
			   $q->br(),
			   '<u>Calculating the total fraction having any characteristics of type <i>t<sub>j</sub></i>&nbsp;:</u>',
			   $q->br(),
			   '<i>S = &sum;<sub>i</sub> h<sub>i</sub>&nbsp; = 4 + 2 + 3 = 9</i>',
			   $q->br(),
			   '<i><b>A<sub>j=1</sub></b>&nbsp; = &sum;<sub>i</sub>&nbsp;<big>(</big>C<sub>i,j=1</sub> * F<sub>i</sub>&nbsp;<big>)</big> = 1 * F<sub>1</sub>&nbsp; + 1 * F<sub>2</sub>&nbsp; + 0 * F<sub>3</sub>&nbsp; = F<sub>1</sub>&nbsp;+ F<sub>2</sub>&nbsp; = <big>(</big>100 * h<sub>1</sub> / S<big>)</big> + <big>(</big>100 * h<sub>2</sub> / S<big>)</big> = <big>(</big>100 * 4 / 9<big>)</big> + <big>(</big>100 * 2 / 9<big>)</big> = <b>66.67 %</b></i>',
			   $q->br(),
			   '<i><b>A<sub>j=2</sub></b>&nbsp; = &sum;<sub>i</sub>&nbsp;<big>(</big>C<sub>i,j=2</sub> * F<sub>i</sub>&nbsp;<big>)</big> = 0 * F<sub>1</sub>&nbsp; + 1 * F<sub>2</sub>&nbsp; + 1 * F<sub>3</sub>&nbsp; = F<sub>2</sub>&nbsp;+ F<sub>3</sub>&nbsp; = <big>(</big>100 * h<sub>2</sub> / S<big>)</big> + <big>(</big>100 * h<sub>3</sub> / S<big>)</big> = <big>(</big>100 * 2 / 9<big>)</big> + <big>(</big>100 * 3 / 9<big>)</big> = <b>55.56 %</b></i>',
			   $q->br()x2,
			   '<u>Calculating the average fraction having characteristics of type <i>t<sub>j</sub></i>&nbsp;:</u>',
			   $q->br(),
			   '<i>S = &sum;<sub>i</sub> h<sub>i</sub>&nbsp; = 4 + 2 + 3 = 9</i>',
			   $q->br(),
			   '<i><b>B<sub>j=1</sub></b>&nbsp; = &sum;<sub>i</sub>&nbsp; <big>(</big> m<sub>i,j=1</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>i,j</sub>&nbsp;* F<sub>i</sub>&nbsp; <big>)</big> = <big>(</big> m<sub>1,j=1</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>1,j=1</sub>&nbsp;* F<sub>1</sub>&nbsp;<big>)</big> + <big>(</big> m<sub>2,j=1</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>2,j</sub>&nbsp;* F<sub>2</sub>&nbsp;<big>)</big> + <big>(</big> m<sub>3,j=1</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>3,j</sub>&nbsp;* F<sub>3</sub>&nbsp;<big>)</big></i>',
			   $q->br(),
			   '&nbsp'x7,'<i>= <big>(</big> m<sub>1,j=1</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>1,j=1</sub>&nbsp;* (100 * h<sub>1</sub>&nbsp / S)<big>)</big> + <big>(</big> m<sub>2,j=1</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>2,j</sub>&nbsp;* (100 * h<sub>2</sub>&nbsp / S)<big>)</big> + <big>(</big> m<sub>3,j=1</sub>&nbsp; /&nbsp; &sum;<sub>j</sub>&nbsp;m<sub>3,j</sub>&nbsp;* (100 * h<sub>3</sub>&nbsp / S)<big>)</big></i>',
			   $q->br(),
			   '&nbsp'x7,'<i>= <big>(</big> 1 / 1 * (100 * 4 / 9)<big>)</big> + <big>(</big> 1 / 2 * (100 * 2 / 9)<big>)</big> + <big>(</big> 0 / 1 * (100 * 3 / 9)<big>)</big> = <b>55.56 %</b></i>',
			   $q->br(),
			   '<i><b>B<sub>j=2</sub></b>&nbsp; = <big>(</big> 0 / 1 * (100 * 4 / 9)<big>)</big> + <big>(</big> 1 / 2 * (100 * 2 / 9)<big>)</big> + <big>(</big> 1 / 1 * (100 * 3 / 9)<big>)</big> = <b>44.44 %</b></i>',
			   $q->br()x2,
			   '<u>Note:</u>&nbsp; <i>&sum;<sub>j</sub>&nbsp; A<sub>j</sub>&nbsp; <b>&#8805;</b> 100 %, &nbsp;&nbsp;<i>&sum;<sub>j</sub>&nbsp; B<sub>j</sub>&nbsp; <b>=</b> 100 %',
		  ))),
    $q->Tr($q->td({-colspan => '2',
		   -class => 'background0'},
		  '&nbsp;')),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->a({-name => 'more'}),
		  $q->font({-class => 'tableQuestion'},
			   '6. What should I do if I have more questions?')),
	   $q->td({-colspan => '1',
		   -align => 'right',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'footer'},
		  $q->a({-href => 'ADAPTHelp.cgi#top'},'top')))),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   'Please use the contact form to get answers to any additional question. The contact form can be found by clicking on "CONTACT" in the right top corner of the menu.',
			   $q->br()))),
    $q->end_table(),
    FOOTER,
    $q->end_center(),
    GOOGLE_ANALYTICS,
    $q->end_html();

