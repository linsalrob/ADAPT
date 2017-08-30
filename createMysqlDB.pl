#!/usr/bin/perl

use strict;
use warnings;
use DBConfig;
use DBI;

$| = 1; # Do not buffer output

#connect to mysql database
my $dsn = "DBI:mysql:database=mysql;host=".MYSQL_HOST.";port=".MYSQL_PORT;
my $dbh = DBI->connect($dsn,'root',MYSQL_PW,
		       {RaiseError => 1});

#create database
$dbh->do('CREATE DATABASE '.MYSQL_DB);
$dbh->do('USE '.MYSQL_DB);

#create tables
$dbh->do('CREATE TABLE trophic (id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,kind VARCHAR(13) NOT NULL) ENGINE=InnoDB');
$dbh->do('CREATE TABLE pathogenic (id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,kind VARCHAR(13) NOT NULL) ENGINE=InnoDB');
$dbh->do('CREATE TABLE target (id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,name VARCHAR(50) NOT NULL) ENGINE=InnoDB');
$dbh->do('CREATE TABLE source (id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,name VARCHAR(25) NOT NULL) ENGINE=InnoDB');
$dbh->do('CREATE TABLE taxon (id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,kingdom VARCHAR(12) NOT NULL,phylum VARCHAR(50) NOT NULL,genus VARCHAR(100),species VARCHAR(100)) ENGINE=InnoDB');
$dbh->do('CREATE TABLE organism (id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,name VARCHAR(255) NOT NULL,taxid INT UNSIGNED,taxon_id INT UNSIGNED NOT NULL,trophic_id TINYINT UNSIGNED NOT NULL,pathogenic_id TINYINT UNSIGNED NOT NULL,FOREIGN KEY (taxon_id) REFERENCES taxon (id) ON DELETE CASCADE ON UPDATE CASCADE,FOREIGN KEY (trophic_id) REFERENCES trophic (id) ON DELETE CASCADE ON UPDATE CASCADE,FOREIGN KEY (pathogenic_id) REFERENCES pathogenic (id) ON DELETE CASCADE ON UPDATE CASCADE) ENGINE=InnoDB');
$dbh->do('CREATE TABLE organism_target (organism_id INT UNSIGNED NOT NULL,target_id TINYINT UNSIGNED NOT NULL,PRIMARY KEY (organism_id,target_id),FOREIGN KEY (organism_id) REFERENCES organism (id) ON DELETE CASCADE ON UPDATE CASCADE,FOREIGN KEY (target_id) REFERENCES target (id) ON DELETE CASCADE ON UPDATE CASCADE) ENGINE=InnoDB');
$dbh->do('CREATE TABLE entry (id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,accession VARCHAR(15) NOT NULL,version INT UNSIGNED NOT NULL,adding_date TIMESTAMP NOT NULL,linkout VARCHAR(255),source_id TINYINT UNSIGNED NOT NULL,organism_id INT UNSIGNED NOT NULL,FOREIGN KEY (source_id) REFERENCES source (id) ON DELETE CASCADE ON UPDATE CASCADE,FOREIGN KEY (organism_id) REFERENCES organism (id) ON DELETE CASCADE ON UPDATE CASCADE) ENGINE=InnoDB');
$dbh->do('CREATE TABLE region (id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,sequence TEXT NOT NULL,length INT UNSIGNED NOT NULL) ENGINE=InnoDB');
$dbh->do('CREATE TABLE organism_region (organism_id INT UNSIGNED NOT NULL,region_id INT UNSIGNED NOT NULL,PRIMARY KEY (organism_id,region_id),FOREIGN KEY (organism_id) REFERENCES organism (id) ON DELETE CASCADE ON UPDATE CASCADE,FOREIGN KEY (region_id) REFERENCES region (id) ON DELETE CASCADE ON UPDATE CASCADE) ENGINE=InnoDB');
$dbh->do('CREATE TABLE region_entry (contig VARCHAR(30),strand TINYINT UNSIGNED,start16S INT UNSIGNED,stop16S INT UNSIGNED,start23S INT UNSIGNED,stop23S INT UNSIGNED,region_id INT UNSIGNED NOT NULL,entry_id INT UNSIGNED NOT NULL,FOREIGN KEY (region_id) REFERENCES region (id) ON DELETE CASCADE ON UPDATE CASCADE,FOREIGN KEY (entry_id) REFERENCES entry (id) ON DELETE CASCADE ON UPDATE CASCADE) ENGINE=InnoDB');

#input standard values
$dbh->do('INSERT INTO trophic (kind) VALUES (\'autotrophic\'),(\'heterotrophic\'),(\'unknown\')');
$dbh->do('INSERT INTO pathogenic (kind) VALUES (\'pathogenic\'),(\'nonpathogenic\'),(\'unknown\')');
$dbh->do('INSERT INTO source (name) VALUES (\'NCBI\'),(\'SEED\')');

#add user priviledges
$dbh->do('GRANT ALL PRIVILEGES ON '.MYSQL_DB.'.* TO '.MYSQL_USER.'@'.MYSQL_HOST);
$dbh->do('GRANT RELOAD,PROCESS ON *.* TO '.MYSQL_USER.'@'.MYSQL_HOST);
$dbh->do('FLUSH PRIVILEGES;');

#close connection
$dbh->disconnect();
