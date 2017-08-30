package ADAPTConfig;

use strict;

use constant THRESHOLD => '279';
use constant MINLENGTH => '100';
use constant MAXLENGTH => '2000';
use constant LOWER500  => '2';
use constant LOWER1000 => '3';
use constant UPPER1000 => '3';
use constant METHODS   => 'amean';
use constant CUTOFF    => '100';

use constant ABBREV => {a => 'autotroph',
			h => 'heterotroph',
			u => 'unknown',
			n => 'nonpathogenic',
			p => 'pathogenic'};

use constant PLACES => {'CC' => "Cancun Mexico",
			'TB' => "Tobago",
			'BT' => "Bocas del Toro, Panama",
			'KIR' => "Kiritimati (Christmas), Line Islands",
			'KIN' => "Kingman, Line Islands",
			'TAB' => "Tabuaeren, Line Islands",
			'PAL' => "Palmyra, Line Islands"};

use constant PARAMS => {'upload' => 'Uploaded file',
			'threshold' => 'Fragment size threshold',
			'lower500' => '+/- for fragments < 600',
			'lower1000' => '+/- for fragments < 900',
			'upper1000' => '+/- for fragments &#8805; 900',
			'methods' => 'Threshold calculation method',
			'imean'  => 'Interquartile mean',
			'gmean'  => 'Geometric mean',
			'amean'  => 'Arithmetic mean',
			'p2mean' => 'Quadratic mean (Power 2 mean)',
			'p3mean' => 'Cubic mean (Power 3 mean)',
			'cutoff' => 'Min threshold value',
			'cutoffcalc' => 'Use threshold calculation',
			'cutoffmin' => 'Use min threshold value',
			'sizesl' => 'Size standard name',
			'sizest' => 'Size standard input',
			'datasource' => 'Data source',
			'kingdom' => 'Kingdom',
			'outputsg' => 'Outputs general',
			'outputsd' => 'Outputs metadata related',
			'outputsm' => 'Multiple samples grouping',
			'outputsp' => 'Outputs plots',
			'forward' => 'Forward PCR primer',
			'reverse' => 'Reverse PCR primer',
			'forwardt' => 'Forward PCR primer',
			'reverset' => 'Reverse PCR primer',
			'maxlength' => 'Maximum fragment length',
			'minlength' => 'Minimum fragment length',
			'match' => 'Matching organism fragments'};

use constant OUTPUTS => {'general' => {'aprimermatchings' => ' Overview of fragments matching primer set',
				       'ainputparams' => ' Input parameters',
				       'lengthtable' => ' Potentially matching fragment lengths',
				       'orgntable' => ' Potentially matching organisms',
				       'phylumhittable' => ' Matching fragments by phylum'},
			 'plots' => {'rawdataplots' => ' Raw data plots (only for .fsa/.ab1 inputs)',
				     'tracefileplots' => ' Trace file (chromatogram) plots',
				     'standardplots' => ' Size standard curve fitting plots (only for .fsa/.ab1 inputs)'},
			 'metadata' => {'pathogenicaverage' => ' Pathogenicity - Average fraction',
#					'pathogenictotal' => ' Pathogenicity - Total fraction',
					'trophicaverage' => ' Trophic -  Average fraction',
#					'trophictotal' => ' Trophic - Total fraction'
			 },
			 'multiple' => {'minputlength' => 'Samples grouped by input length',
					'mdblength' => 'Samples grouped by database length'}};

use constant TYPES => {pathogenic => {table  => 'pathogenic',
				      a      => 'nonpathogenic',
				      b      => 'pathogenic',
				      acolor => 'limegreen',
				      bcolor => 'orangered',
				      acolorC => 'green',
				      bcolorC => 'red'},
		       trophic => {table   => 'trophic',
				   a       => 'autotrophic',
				   b       => 'heterotrophic',
				   acolor  => 'lightgreen',
				   bcolor  => 'lightblue',
				   acolorC => 'lgreen',
				   bcolorC => 'lblue'}};

use constant TABLE_WIDTH => 860;

use constant VERSION => 'v1.3 beta';
use constant MAILTO => 'youremail@gmail.com'
use constant SMTP => '';

use constant AMBIGUITY_CODE => { 'm' => '[ac]', 	
				 'r' => '[ag]', 	
				 'w' => '[at]',
				 's' => '[cg]',
				 'y' => '[ct]',
				 'k' => '[gt]',
				 'v' => '[acg]',
				 'h' => '[act]',
				 'd' => '[agt]',
				 'b' => '[cgt]',
				 'n' => '[acgt]',
				 'a' => 'a',
				 'c' => 'c',
				 'g' => 'g',
				 't' => 't'};

use constant PRIMERS => {forward => {'1406f' => 'TGYACACACCGCCCGT',
				     'S-D-Bact-1522-b-S-20' => 'TGCGGCTGGATCCCCTCCTT',
				     'ITSF' => 'GTCGTAACAAGGTAGCCGTA'},
			 reverse => {'23Sr'  => 'GGGTTBCCCCATTCRG',
				     'L-D-Bact-132-a-A-18' => 'CCGGGTTTCCCCATTCGG',
				     'ITSReub' => 'GCCAAGGCATCCACC'}};

use constant SIZE_STD => {'350 ROX (35-350)' => [35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350],
			  '350 TAMRA (35-350)' => [35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350],
			  '400HD ROX (50-400)' => [50, 50, 90, 100, 120, 150, 160, 180, 190, 200, 220, 240, 260, 280, 290, 300, 320, 340, 360, 380, 400],
			  '500 LIZ (35-500)' => [35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500],
			  '500 ROX (35-500)' => [35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500],
			  '500XL ROX (35-500)' => [35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500],
			  '500 TAMRA (35-500)' => [35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500],
			  '500XL TAMRA (35-500)' => [35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, 400, 450, 490, 500],
			  '600 LIZ (20-600)' => [20, 40, 60, 80, 100, 114, 120, 140, 160, 180, 200, 214, 220, 240, 250, 260, 280, 300, 314, 320, 340, 360, 380, 400, 414, 420, 440, 460, 480, 500, 514, 520, 540, 560, 580, 600],
			  '1200 LIZ (20-1200)' => [20, 30, 40, 60, 80, 100, 114, 120, 140, 160, 180, 200, 214, 220, 240, 250, 260, 280, 300, 314, 320, 340, 360, 380, 400, 414, 420, 440, 460, 480, 500, 514, 520, 540, 560, 580, 600, 614, 620, 640, 660, 680, 700, 714, 720, 740, 760, 780, 800, 820, 840, 850, 860, 880, 900, 920, 940, 960, 980, 1000, 1020, 1040, 1060, 1080, 1100, 1120, 1160, 1200]};

use constant ADAPT_DIR   => 'adapt-test/';
use constant ADAPT       => 'adapt-test';
#use constant TMP_DIR_CGI => '../../'.ADAPT_DIR.'tmp/';
use constant TMP_DIR_CGI => '../../html/'.ADAPT_DIR.'tmp/';
use constant TMP_DIR_WEB => '../../'.ADAPT_DIR.'tmp/';
use constant CSS_FILE    => '../../'.ADAPT_DIR.'ADAPTstyle.css';
use constant JS_FILE     => '../../'.ADAPT_DIR.'ADAPTscript.js';
use constant JS_FILE_MU  => '../../'.ADAPT_DIR.'multipleUpload.js';
use constant LOG_FILE    => 'log/ADAPT_web.log';
use constant LOG_EMAIL   => 'log/ADAPT_contact.log';
use constant DB_FILE     => 'ADAPT_DB.txt';
use constant TT_FILES    => '';

use constant DIV_BG_COLOR => 'rgb(250,250,250)';
use constant HEADER_BG_COLOR => '#68e0f3';

use constant BUTTON_BACK => 'GO BACK';
use constant BUTTON_GOON => 'GO ON';

use constant USED_BROWSER => ($ENV{'HTTP_USER_AGENT'} =~ m/Firefox/);

use constant GOOGLE_ANALYTICS2 => '';

use constant GOOGLE_ANALYTICS => '';

use constant FOOTER => <<'CGI';
<br /><br />
<font class="footer">
    &copy;&nbsp;2009&nbsp;Robert Schmieder&nbsp;&nbsp;|
    &nbsp;<a class="noline" href="ADAPTContact.cgi">contact me</a> &nbsp;|
    &nbsp;<a target="_new" class="noline" href="http://edwards.sdsu.edu/">Edwards Lab</a> @ <a target="_new" class="noline" href="http://www.sdsu.edu/">SDSU</a>
</font>
<br />
&nbsp;
CGI

#####################################################

use base qw(Exporter);

use vars qw(@EXPORT);

@EXPORT = qw(
	     THRESHOLD
             MINLENGTH
             MAXLENGTH
	     LOWER500
	     LOWER1000
	     UPPER1000
	     METHODS
	     CUTOFF
	     ABBREV
	     PLACES
	     PARAMS
             OUTPUTS
             TYPES
	     TABLE_WIDTH
	     VERSION
	     MAILTO
             SMTP
	     TMP_DIR_WEB
	     TMP_DIR_CGI
	     AMBIGUITY_CODE
             PRIMERS
             SIZE_STD
	     CSS_FILE
	     JS_FILE
	     JS_FILE_MU
             LOG_FILE
             LOG_EMAIL
	     DB_FILE
             TT_FILES
	     ADAPT_DIR
             ADAPT
	     DIV_BG_COLOR
             HEADER_BG_COLOR
	     BUTTON_BACK
	     BUTTON_GOON
	     IUPAC_AA_CODES
	     USED_BROWSER
             GOOGLE_ANALYTICS
             FOOTER
	     );

1;

