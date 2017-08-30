package DBConfig;

use strict;

use constant MYSQL_USER => 'adaptuser';
use constant MYSQL_PW   => 'passwd';
use constant MYSQL_DB   => 'adapttest';
use constant MYSQL_HOST => 'localhost';
use constant MYSQL_PORT => 3306;

use constant EMAIL => 'youremail@gmail.com'; # used to contact if there are problems with queries or if NCBI is changing software interfaces that might specifically affect requests

use constant NCBI_SLEEP => 0.3; # NCBI user requirement: Make no more than one request every 3 seconds
use constant NCBI_TOOLNAME => 'adapt'; # NCBI requests that developers sending batch requests include a constant 'tool' argument for all requests using the utilities
use constant RELDATE => 8; # 0 = all; alternative mindate=YYYY/MM/DD&maxdate=YYYY/MM/DD
use constant SEARCH_TERM => 'Bacteria[Organism] OR Archaea[Organism]'; # +AND+Proteobacteria[Organism]
use constant SEARCH_DB1 => 'genome'; 
use constant SEARCH_DB2 => 'sequences';
use constant EUTILS => 'http://www.ncbi.nlm.nih.gov/entrez/eutils/';
use constant LINKOUT_TAX => 'http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=';
use constant LINKOUT_SEQ => 'http://www.ncbi.nlm.nih.gov/sites/entrez?Cmd=ShowDetailView&TermToSearch=';
use constant LINKOUT_SEED => 'http://www.theseed.org/linkin.cgi?';

use constant LPROKS => 'ftp://ftp.ncbi.nih.gov/genomes/Bacteria/lproks_0.txt';
use constant SEED_DATA_URL => 'http://bioseed.mcs.anl.gov/~redwards/FIG/ribosomal_rnas.cgi';

use constant WIDTH_PRINT => 79;

use constant ERROR_LOG => 'error.log';
use constant CREATEDB_LOG => 'log/createDB.log';
use constant UPDATEDB_LOG => 'log/updateDB.log';
use constant PERL_PATH => '/usr/bin/';
use constant DEV_NULL => '/dev/null';
use constant GBK_DIR => '/tmp/adapt/gbk_files/';
`mkdir -p '/tmp/adapt/gbk_files/genome'`;
use constant GBK_OLDDB => GBK_DIR.'olddb/';
#mkdir(GBK_OLDDB) unless(-d GBK_OLDDB);
use constant GBK_GENOME => GBK_DIR.'genome/';
use constant OLDDB_FILE => 'ADAPT_DB.txt';

use constant MAX_LENGTH     => 3000;
use constant MIN_LENGTH_16S => 300;
use constant MIN_LENGTH_23S => 300;
use constant MIN_LENGTH_ITS => 0;

use constant ABBREVS => {u => 'unknown',
			 h => 'heterotrophic',
			 a => 'autotrophic',
			 p => 'pathogenic',
			 n => 'nonpathogenic'};

use constant PHYLA => {Bacteria => {Acidobacteria => 'h',           #acidophilic bacteria comon in soils,chemoorganotroph, aerobe, heterotroph
 				    Actinobacteria => 'h',          #high G+C Gram positives
 				    Aquificae => 'a',               #hyperthermophilic chemolithoautotrophs
 				    Bacteroidetes => 'h',           #diverse group including pathogens, commensals, and free-living bacteria
 				    Chlorobi => 'h',                 #green sulfur bacteria
				    
 				    Chlamydiae => 'h',              #obligate intracellular parasites of eukaryotic cells
 				    Chloroflexi => 'h',             #green nonsulfur bacteria, Thermomicrobia class: chemoheterotrophs 
 				    Chrysiogenetes => 'a',          #chemolithoautotrophic bacterium
 				    Cyanobacteria => 'a',           #oxygenic photosynthetic bacteria and chloroplasts
 				    Deferribacteres => 'u',         #aquatic, anaerobic bacteria
 				    'Deinococcus-Thermus' => 'h',   #extremophiles
 				    Dictyoglomi => 'u',             #thermophilic chemoorganotrophs
 				    Fibrobacteres => 'h',           #cellulose digesting, anaerobic rumen bacteria
 				    Fibrobacter => 'h',             #cellulose digesting, anaerobic rumen bacteria
 				    Firmicutes => 'h',              #low G+C Gram positives
 				    Fusobacteria => 'h',            #anaerobic heterotrophs
 				    Gemmatimonadetes => 'u',        #Gram-negative bacteria lacking DAP in their cell envelopes, aerobic
 				    Nitrospirae => 'a',             #includes nitrite oxidizers, thermophilic sulfate reducers, and acidophilic iron oxidizers
 				    Planctomycetes => 'h',          #bacteria with peptidoglycan-less cell walls and budding reproduction
 				    Proteobacteria => 'h',          #purple bacteria and relatives, photoautotroph and photoheterotroph species
 				    Spirochaetes => 'h',            #spiral-shaped chemoheterotrophs
				    Synergistetes => 'h',           #Gram-negative,rod-shaped obligate anaerobes
				    Tenericutes => 'h',             #organisms that lack a rigid cell wall and do not contain muramic acid
 				    Thermodesulfobacteria => 'a',   #thermophilic, sulfate-reducing bacteria; chemolithoautotrophic
 				    Thermotogae => 'h',             #hyperthermophilic, obligately anerobic, fermentive heterotrophs
 				    Verrucomicrobia => 'h',         #terrestrial, aquatic, some associated with eukaryotic hosts
				    'Bacteroidetes/Chlorobi group' => 'h',      #SEED data taxon
				    'Chlamydiae/Verrucomicrobia group' => 'h',  #SEED data taxon
				    'Fibrobacteres/Acidobacteria group' => 'h', #SEED data taxon
				    'Fibrobacter/Acidobacteria group' => 'h',    #SEED data taxon
				    unknown => 'u',
#				    'unclassified Bacteria' => 'u',
		       },
		       Eukaryota => {Chlorophyta => 'a',    #
				     Cryptophyta => 'a',    #
				     Diplomonadida => 'h',  #
				     Euglenozoa => 'a',     #
				     Microsporidia => 'h',  #
				     Phaeophyceae => 'a',   #
				     Rhodophyta => 'a',     #
				     Stramenopiles => 'a',  #
				     Streptophyta => 'a',
				     unknown => 'u',
		       },
		       Archaea => {Crenarchaeota => 'h',    #
				   Euryarchaeota => 'h',
				   Korarchaeota => 'h',
				   Nanoarchaeota => 'h',
				   unknown => 'u',
#				   'unclassified Archaea' => 'u',
		       }
		   };

#######################################################################

use base qw(Exporter);

use vars qw(@EXPORT);

@EXPORT = qw(
	     MYSQL_USER
	     MYSQL_PW
	     MYSQL_DB
	     MYSQL_HOST
	     MYSQL_PORT
	     EMAIL
	     NCBI_SLEEP
	     NCBI_TOOLNAME
	     RELDATE
	     SEARCH_TERM
	     SEARCH_DB1
	     SEARCH_DB2
	     EUTILS
             LINKOUT_TAX
             LINKOUT_SEQ
             LINKOUT_SEED
	     LPROKS
             SEED_DATA_URL
	     WIDTH_PRINT
	     ERROR_LOG
	     CREATEDB_LOG
	     UPDATEDB_LOG
	     PERL_PATH
	     DEV_NULL
	     GBK_DIR
	     GBK_OLDDB
	     GBK_GENOME
	     OLDDB_FILE
	     MAX_LENGTH
             MIN_LENGTH_16S
             MIN_LENGTH_23S
             MIN_LENGTH_ITS
	     ABBREVS
	     PHYLA
	     );

1;
