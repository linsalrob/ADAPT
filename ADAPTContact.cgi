#!/usr/bin/perl

use strict;
use warnings;
use CGI;
#use CGI::Pretty;
use CGI::Carp qw(fatalsToBrowser);
use ADAPTConfig;

use lib '/opt/bcr/2008-0612/linux-debian-x86_64/lib/perl5/site_perl/5.10.0/';
use MIME::Lite::TT::HTML;


my $browser = USED_BROWSER;
my $q = new CGI;

my $numbers = &generateNumbers();
print
    $q->header(),
    $q->start_html(-title => 'ADAPT Contact',
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
    $q->img({-src => '../../'.ADAPT_DIR.'contact2.png',
	     -border => '0',
	     -alt => 'ADAPT '.VERSION.' contact',
#	     -onMouseOver => 'this.src="'.'../../'.ADAPT_DIR.'contact2.png'.'";',
#	     -onMouseOut => 'this.src="'.'../../'.ADAPT_DIR.'contact1.png'.'";'
	     })),
    $q->br()x2;

unless($q->param('send')) {
    print
	$q->start_form({-method => 'post',
			-name => 'contact',
			-onSubmit => 'return false',
			-action => 'ADAPTContact.cgi'}),
	$q->hidden(-name => 'send',
		   -default => '0'),
	$q->start_table({-border =>'0',
			 -width => TABLE_WIDTH,
			 -cellspacing => '0'}),
	$q->Tr($q->td({-colspan => '2',
		       -align => 'left',
		       -background => '#000000',
		       -class => 'background0'},
		      $q->font({-class => 'tableQuestion'},
			       'Contact me'))),
	$q->Tr($q->td({-colspan => '1',
		       -align => 'left',
		       -class => 'tableOptions'},
		      $q->start_table({-border =>'0',
				       -width => '100%',
				       -class => 'tableBlank2'}),
		      $q->Tr($q->td({-align => 'right',
				     -valign => 'top',
				     -width => '140',
				     -class => 'tableBlank2b'},
				    $q->font({-class => 'table_info'},
					     '&nbsp;Your name&nbsp;&nbsp;')),
			     $q->td({-align => 'left',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->input({-size => '50',
					       -maxlength => '50',
					       -name => 'name',
					       -id => 'name',
					       -value => ''}),
				    $q->br()x2)),
		      $q->Tr($q->td({-align => 'right',
				     -valign => 'top',
				     -class => 'tableBlank2b'},
				    $q->font({-class => 'table_info'},
					     '&nbsp;Your email&nbsp;&nbsp;')),
			     $q->td({-align => 'left',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->input({-size => '50',
					       -maxlength => '50',
					       -name => 'email',
					       -id => 'email',
					       -value => ''}),
				    '&nbsp;&nbsp;',
				    $q->checkbox(-name => 'cc',
						 -checked => 0,
						 -value => 1,
						 -label => ''),
				    $q->font({-class => 'table_info'},
					     'Cc yourself'),
				    $q->br()x2)),
		      $q->Tr($q->td({-align => 'right',
				     -valign => 'top',
				     -class => 'tableBlank2b'},
				    $q->font({-class => 'table_info'},
					     '&nbsp;Subject&nbsp;&nbsp;')),
			     $q->td({-align => 'left',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->input({-size => '70',
					       -maxlength => '100',
					       -name => 'subject',
					       -id => 'subject',
					       -value => ''}),
				    $q->br()x2)),
		      $q->Tr($q->td({-align => 'right',
				     -valign => 'top',
				     -class => 'tableBlank2b'},
				    $q->font({-class => 'table_info'},
					     '&nbsp;Message&nbsp;&nbsp;')),
			     $q->td({-align => 'left',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->textarea(-name => 'message',
						 -default => '',
						 -rows => 8,
						 -columns => 70),
				    $q->br()x2)),
		      $q->Tr($q->td({-align => 'right',
				     -valign => 'top',
				     -class => 'tableBlank2b'},
				    $q->font({-class => 'table_info'},
					     '&nbsp;What is '.join(" + ",@$numbers).' ?&nbsp;&nbsp;')),
			     $q->td({-align => 'left',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->input({-size => '50',
					       -maxlength => '50',
					       -name => 'test',
					       -id => 'test',
					       -value => ''}),
				    '&nbsp;&nbsp;',
				    $q->font({-class => 'footer'},
					     '(this prevents me from unwanted email)'))),
		      $q->Tr($q->td({-align => 'right',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->font({-class => 'table_info'},
					     '&nbsp;')),
			     $q->td({-align => 'left',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->br(),
				    $q->button({-value => 'SEND MESSAGE',
						-id => 'submitb',
						-name => 'submitb',
						-class => 'buttonsubmit',
						-onClick => 'if(document.forms.contact.name.value == false){alert(\'Please complete the "Your name" field.\');return false;}else{if(document.forms.contact.email.value == false){alert(\'Please complete the "Your email" field.\');return false;}else{if(document.forms.contact.subject.value == false){alert(\'Please complete the "Subject" field.\');return false;}else{if(document.forms.contact.message.value == false){alert(\'Please complete the "Message" field.\');return false;}else{if(document.forms.contact.test.value != '.($numbers->[0]+$numbers->[1]).'){alert(\'Your answer is either incorrect or you did not complete the "What is '.join(" + ",@$numbers).' ?" field.\nTip: '.($numbers->[0]+$numbers->[1]).'\');return false;}else{document.forms.contact.send.value=1;document.forms.contact.submit();}}}}}',
						-name => 'submitB'}),
				    $q->br()x3)),
		      $q->Tr($q->td({-align => 'right',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->font({-class => 'footer'},
					     '<b>Note:</b>&nbsp;&nbsp;')),
			     $q->td({-align => 'left',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->font({-class => 'footer'},
					     'I read every message that comes through this form. I will respond to any message that seeks a response as soon as I can.'))),
		      $q->end_table(),
	       )),
	$q->end_table(),
	$q->end_form();
} else {
    #send email
    my $params = $q->Vars;
    my $name = $params->{'name'};
    my $email = $params->{'email'};
    my $subject = $params->{'subject'};
    my $message = $params->{'message'};
    my $cc = (exists $params->{'cc'} ? 1 : 0);

    #write email log in case of unexpected failures of email send
    &writeLog($name,$email,$subject,$message,$cc);


    #MIME::Lite::TT::HTML stuff
    my %tparams;
    $tparams{name} = $name;
    $tparams{message}  = $message;

    my %options;
    $options{INCLUDE_PATH} = TT_FILES;

    my $msg = MIME::Lite::TT::HTML->new(
	TimeZone    => 'America/Los_Angeles',
	From        =>  $email,
	To          =>  MAILTO,
	Cc          => ($cc ? $email : undef),
	Subject     =>  '[ADAPT] '.$subject,
	Template    =>  {
	    text    =>  'contact.txt.tt',
	    html    =>  'contact.html.tt',
	},
	TmplOptions =>  \%options,
	TmplParams  =>  \%tparams,
	);

    $msg->send();
#    print '$msg->send(\'smtp\', '.SMTP.', Timeout => 60, LocalPort => 8025);';

    #print message of success
    print
	$q->start_table({-border =>'0',
			 -width => TABLE_WIDTH,
			 -cellspacing => '0'}),
	$q->Tr($q->td({-colspan => '2',
		       -align => 'left',
		       -background => '#000000',
		       -class => 'background0'},
		      $q->font({-class => 'tableQuestion'},
			       'Contact me'))),
	$q->Tr($q->td({-colspan => '2',
		       -align => 'left',
		       -class => 'tableOptions'},
		      $q->start_table({-border =>'0',
				       -width => '100%',
				       -class => 'tableBlank2'}),
		      $q->Tr($q->td({-align => 'right',
				     -valign => 'top',
				     -width => '140',
				     -class => 'tableBlank2b'},
				    $q->font({-class => 'table_info'},
					     '&nbsp;')),
			     $q->td({-align => 'left',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->br()x2,
				    $q->font({-class => 'footer'},
					     '<b>Your email was sent successfully.</b>'),
				    $q->br()x4,)),
		      $q->Tr($q->td({-align => 'right',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->font({-class => 'footer'},
					     '<b>Note:</b>&nbsp;&nbsp;')),
			     $q->td({-align => 'left',
				     -valign => 'top',
				     -class => 'tableBlank2'},
				    $q->font({-class => 'footer'},
					     'I read every message that comes through this form. I will respond to any message that seeks a response as soon as I can.'))),
		      $q->end_table(),
	       )),
	$q->end_table();
}

print
    FOOTER,
    $q->end_center(),
    GOOGLE_ANALYTICS,
    $q->end_html();

sub generateNumbers {
    my ($x,$y);
    $x = int(rand(998))+1;
    $y = int(rand(8))+1;
    return [$x,$y];
}

sub writeLog {
    my ($name,$email,$subject,$message,$cc) = @_;
    my $string = join("\t",($name,$email,$subject,$message,$cc,$ENV{'HTTP_USER_AGENT'}));
    &addToLogFile($string);
}

sub addToLogFile {
    my $string = shift;
    my $log = LOG_EMAIL;
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
