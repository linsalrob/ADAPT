#!/usr/bin/perl

use strict;
use warnings;
use CGI;
#use CGI::Pretty;
use CGI::Carp qw(fatalsToBrowser);
use ADAPTConfig;

my $browser = USED_BROWSER;
my $q = new CGI;

print 
    $q->header(),
    $q->start_html(-title => 'ADAPT Home',
		   -style => CSS_FILE,
		   -script => {-language => 'JAVASCRIPT',
			       -src => JS_FILE_MU}),
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
	     -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'program1.png'.'";'})),
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

    $q->start_table({-border =>'0',
		     -width => TABLE_WIDTH,
		     -cellspacing => '0'}),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'tableQuestion'},
			   'What is ADAPT?'))),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   '<b>ADAPT</b> presents a web-based system for the analysis of ARISA data sets. You can use this service to taxonomically characterize your ARISA data sets and perform pathogenic and autotrophic/heterotrophic comparisons of organisms among different ARISA samples using the metadata associated with the organisms.',
#			   $q->br(),
			   '&nbsp;'.$q->a({-href => 'ADAPTHelp.cgi'}, 'more...'),
			   $q->br()x2,
			   '<b>ADAPTdb</b> is a database that stores and maintains 16S-ITS-23S regions along with information about their source organisms. The content is based on data of the '.$q->a({-href => 'http://phage.sdsu.edu/',-target => '_blank'},'Rohwer Lab').', the '.$q->a({href => 'http://www.ncbi.nlm.nih.gov/', target => '_blank'},'NCBI databases and resources').', and '.$q->a({href=>'http://www.theseed.org/', target=>'_blank'},'The SEED database').'.', #', and the ',$q->a({href=>'http://egg.umh.es/rissc/',target=>'_blank'},'Ribosomal Internal Spacer Sequence Collection (RISSC)').
			   $q->br()x3,
			'<b>Please note that this web service is not supported anymore.</b> If you would like more information or encounter any issues, please use the contact form accessible through the menu above.'))),
    $q->Tr($q->td({-colspan => '2',
		   -class => 'background0'},
		  '&nbsp;')),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'tableQuestion'},
			   'Features'))),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   'ADAPT is able to use different file formats as the data input. You can either use <b>raw ABI data</b> provided in <code>.fsa</code> or <code>.ab1</code> files, or you can use text files containing the <b>extraced ARISA profile data</b> (usually <code>.txt</code> or <code>.tsv</code> files).',
			   $q->br()x2,
			   'Specification of different <b>filter parameters</b>, such as fragment length range, fluorescence intensity (peak-height) threshold, data source.',
			   $q->br()x2,
			   'The output page allows you easy access to the results of the ARISA data analysis. The <b>results are presented in form of tables and charts</b>, each of which can be <b>exported into different text and image formats</b> for subsequent analysis of the data.
Since ADAPT offers different analyses for your input data and you might not need all of them, you can select the analyses and outputs you are interested in.',
			   $q->br()x2,
			   'For inputs with ARISA profiles of more than one sample, ADAPT also performs <b>multiple samples analysis</b>, by grouping the values by input fragment length, or by matching database fragment length. Samples with same length matches or same input length can be inspected easily this way.',
			   $q->br()x3,
			   $q->b('Note: ').'We recommend using the latest version of &nbsp;'.$q->a({-href => 'http://www.mozilla.com/en-US/firefox/',-target => '_blank'},
												   $q->img({-src => '../../'.ADAPT_DIR.'firefox_logo.png',
													    -border => '0',
													    -alt => 'Firefox logo'}).'&nbsp;Firefox').'.',
		  ))),
    $q->Tr($q->td({-colspan => '2',
		   -class => 'background0'},
		  '&nbsp;')),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'tableQuestion'},
			   'Screenshots'))),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->start_table({-border =>'0',
				   -width => '100%',
				   -class => 'tableBlank2'}),
		  $q->Tr($q->td({-align => 'left',
				 -valign => 'top',
				 -width => '33%',
				 -class => 'tableBlank2b'},
				$q->a({-href => '../../'.ADAPT_DIR.'plots.png',-target => '_blank'},
				      $q->img({-src => '../../'.ADAPT_DIR.'plots_tn.png',
					       -class => 'screenshot',
					       -alt => 'plots'}),
				      $q->br(),
				      $q->font({-class => 'table_info2'},
					       'Input data plots'))),
			 $q->td({-align => 'left',
				 -valign => 'top',
				 -width => '33%',
				 -class => 'tableBlank2b'},
				$q->a({-href => '../../'.ADAPT_DIR.'taxonomyinfo.png',-target => '_blank'},
				      $q->img({-src => '../../'.ADAPT_DIR.'taxonomyinfo_tn.png',
					       -class => 'screenshot',
					       -alt => 'Taxonomy info'}),
				      $q->br(),
				      $q->font({-class => 'table_info2'},
					       'Taxonomy information table'))),
			 $q->td({-align => 'left',
				 -valign => 'top',
				 -width => '33%',
				 -class => 'tableBlank2b'},
				$q->a({-href => '../../'.ADAPT_DIR.'multiplesamples.png',-target => '_blank'},
				      $q->img({-src => '../../'.ADAPT_DIR.'multiplesamples_tn.png',
					       -class => 'screenshot',
					       -alt => 'Multiple samples'}),
				      $q->br(),
				      $q->font({-class => 'table_info2'},
					       'Multiple samples grouping'))),
		  ),
		  $q->Tr(
			 $q->td({-align => 'left',
				 -valign => 'top',
				 -width => '33%',
				 -class => 'tableBlank2b'},
				$q->a({-href => '../../'.ADAPT_DIR.'metadata.png',-target => '_blank'},
				      $q->img({-src => '../../'.ADAPT_DIR.'metadata_tn.png',
					       -class => 'screenshot',
					       -alt => 'Metadata analysis results with tooltips'}),
				      $q->br(),
				      $q->font({-class => 'table_info2'},
					       'Metadata analysis results with tooltips'))),
			 $q->td({-align => 'left',
				 -valign => 'top',
				 -width => '33%',
				 -class => 'tableBlank2b'},
				$q->a({-href => '../../'.ADAPT_DIR.'organism.png',-target => '_blank'},
				      $q->img({-src => '../../'.ADAPT_DIR.'organism_tn.png',
					       -class => 'screenshot',
					       -alt => 'Potentially organisms table'}),
				      $q->br(),
				      $q->font({-class => 'table_info2'},
					       'Potentially organisms table'))),
		      $q->td({-align => 'left',
				 -valign => 'top',
				 -width => '33%',
				 -class => 'tableBlank2b'},
				$q->a({-href => '../../'.ADAPT_DIR.'showseq.png',-target => '_blank'},
				      $q->img({-src => '../../'.ADAPT_DIR.'showseq_tn.png',
					       -class => 'screenshot',
					       -alt => 'Sequence information'}),
				      $q->br(),
				      $q->font({-class => 'table_info2'},
					       '16S-ITS-23S sequence information'))),
		  ),
				    $q->end_table(),
	   )),
    $q->Tr($q->td({-colspan => '2',
		   -class => 'background0'},
		  '&nbsp;')),
    $q->Tr($q->td({-colspan => '2',
		   -align => 'left',
		   -background => '#000000',
		   -class => 'background0'},
		  $q->font({-class => 'tableQuestion'},
			   'Version changes'))),
    $q->Tr($q->td({-colspan => '1',
		   -align => 'left',
		   -class => 'tableOptions'},
		  $q->font({-class => 'table_info2'},
			   $q->b('&nbsp;April 2009 - v1.3 beta'),$q->br(),
			   '&nbsp; - improved database design',$q->br(),
			   '&nbsp; - restricted ADAPTdb to data from complete genomes (removed RISSC data)',$q->br(),
			   '&nbsp; - added data from The SEED database to ADAPTdb',$q->br(),
			   '&nbsp; - speed-up output calculations',$q->br(),
			   '&nbsp; - added menu for easier navigation through outputs',$q->br(),
			   '&nbsp; - added predefined primer sets for input',$q->br(),
			   '&nbsp; - comparisons now based on fragment length (previously ITS length)',$q->br(),
			   '&nbsp; - new output option (Overview of fragments matching primer set)',$q->br(),
			   $q->br(),
			   $q->b('&nbsp;March 2009 - v1.2 beta'),$q->br(),
			   '&nbsp; - added database filter to allow selection of data used for analysis',$q->br(),
			   '&nbsp; - extented help for inputs and content under "HELP"',$q->br(),
			   '&nbsp; - new output options (plots of input data and size standard curve fitting)',$q->br(),
			   '&nbsp; - added functionallity for selection of outputs',$q->br(),
			   $q->br(),
			   $q->b('&nbsp;February 2009 - v1.1 beta'),$q->br(),
			   '&nbsp; - added ABI raw file input in addition to text based inputs',$q->br(),
			   '&nbsp; - predefined size standards',$q->br(),
			   '&nbsp; - increased maximum number of input files',$q->br(),
			   '&nbsp; - new contact form',$q->br(),
			   '&nbsp; - improved front-end',$q->br(),
		  ))),
    $q->end_table(),
    FOOTER,
    $q->end_center(),
    GOOGLE_ANALYTICS,
    $q->end_html();

