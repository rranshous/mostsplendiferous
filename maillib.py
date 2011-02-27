from datetime import datetime
from email import encoders
from email.charset import Charset
from email.header import Header
from email.message import _formatparam, SEMISPACE
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import cStringIO
import email.utils
import mimetypes
import os.path
import shutil
import smtplib
from mx.DateTime import Parser
import string
import re

__all__ = ['emailError', 'Mail', 'Attachment', 'send_email']

def _encode_text(text):
    """
    Encodes the text in the best-matching character set, returning the encoded 
    text and character set used. This uses a very basic character set algorithm 
    that sticks mainly to US/Latin character sets and switches to UTF-8 after that.

    @param text: the text to encode
    @type text: string
    @return: a 2-element tuple with the encoded text and character set used
    @rtype: tuple
    """
    for charset in ['us-ascii', 'iso-8859-1', 'utf-8']:
        try:
            text = text.encode(charset)
            return (text, charset)
        except UnicodeEncodeError:
            pass
    return (text, None)

def _contains_gmoffset(datetime_str):
	"""
	
	@param datetime_str: string representing date and time
	@return: True if contains gmoffset/False if no gmoffset
	@rtype: boolean
	"""
	#Matches on :Seconds GMOFFSET
	regex = ":[0-9]{2} -?[0-9]+$"
	if re.search(regex,datetime_str) is not None:
		return True
	return False
	

def _strip_gmoffset(datetime_str):
	"""
	Removes the gmoffset from date and time strings
	
	@param datetime_str: string representing date and time to strip
	gmoffset from... eg Wed, 22 Sep 2010 17:43:42 -0400
	@return: string without the gmoffset
	@rtype: string
	"""
	
	# Given format Wed, 22 Sep 2010 17:43:42 -0400
	# split on white space exluding gmoffset
	datetime_prts = datetime_str.split()[:-1]
	
	# Rejoin elements
	datetime_wo_gmoffset = string.join(datetime_prts," ")
	return datetime_wo_gmoffset

def _parse_datetime_str(datetime_str):
	"""
	Parse strings with date and time information
	
	@param datetime_str: string representing date and time
	@return: 9 element tuple representing datetime
	@rtype: tuple
	"""
	if _contains_gmoffset(datetime_str) :
		datetime_str = _strip_gmoffset(datetime_str)
	return Parser.DateTimeFromString(datetime_str).timetuple()
	
class emailError(Exception):
    
    def __init__(self,value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)

class Mail(object):
    """
    Core component of the maillib. Represents an email message.
    """
    
    def _get_template_path(self):
        return self._template_path

    def _set_template_path(self,path):
        # if we have a path, lets go ahead and setup our template
        self._template_path = path
        try:
            fh = open(self._template_path,'r')
            self.template_text = fh.read()
            fh.close()
            if path.endswith('.mako'):
                self.type = 'mako'
        except:
            raise

    # map the template_path attribute as a property
    template_path = property(fget=_get_template_path,
                             fset=_set_template_path)
    
    def __init__(self, **kwargs):
        
        # setup our variables
        self.to = []
        self.cc = []
        self.bcc = []
        self.sender = None
        self.reply_to = None
        self.subject = None
        self._template_path = None
        self.template_text = None
        self.replacement_dict = {}
        self.attachments = []
        self.headers = {}
        self.type = None
        self.use_templating = True
        self.body_type = 'html'
        self.smtp_port = None
        self.username = None
        self.password = None

        # attempt to get the default server
        try:
            from altaUtils import config
            self.server = config['SMTP_server']
        except:
            self.server = None
        
        # we want to look at email addresses (to, cc, and bcc) first
        if 'to' in kwargs:
            self.to = self._parse_addresses(kwargs['to'])
            del kwargs['to']
        if 'cc' in kwargs:
            self.cc = self._parse_addresses(kwargs['cc'])
            del kwargs['cc']
        if 'bcc' in kwargs:
            self.bcc = self._parse_addresses(kwargs['bcc'])
            del kwargs['bcc']
        
        # now we need to assign the other values
        for key, value in kwargs.iteritems():
            if hasattr(self, key):
                setattr(self, key, value)

    def add_attachment(self, **kwargs):
        self.attachments.append(Attachment(**kwargs))

    def send(self):
        """
        Builds and sends out the message to all recipients.
        """

        # basic checks
        if not self.server or not self.sender or not self.to:
            raise emailError("Must specify server, sender, and recipient.")

        # put the current date / time into the replacement dict
        now = datetime.now()
        if 'date' not in self.replacement_dict:
            self.replacement_dict['date'] = '%i/%i/%s' % (now.month, now.day, now.strftime('%y'))
        if 'time' not in self.replacement_dict:
            self.replacement_dict['time'] = '%i:%0.2i %s' % (int(now.strftime('%I')), now.minute, 
                                                             now.strftime('%p'))

        # grab the template text and subject
        text = self.template_text or ''
        subject = self.subject or ''

        # prepare the template and subject
        if self.use_templating:
            if self.type == 'mako':
                from mako.template import Template
                text = Template(text).render_unicode(**self.replacement_dict)
            else:
                try:
                    text = text % self.replacement_dict
                except Exception:
                    pass
            try:
                subject = subject % self.replacement_dict
            except Exception:
                pass

        # start creating the message; using Header directly for potentially 
        # long headers since MIMEMultipart overrides its default space folding 
        # character with a hard tab, which Outlook 2003 and earlier (and 
        # possibly other email clients) doesn't unfold back into a space
        message = MIMEMultipart()
        if self.reply_to:
            message['Reply-To'] = Header(self.reply_to, header_name='Reply-To')
        message['From'] = Header(self.sender, header_name='From')
        message['To'] = ''
        if self.cc:
             message['Cc'] = Header(', '.join(self.cc), header_name='Cc')
        message['Subject'] = Header(subject.strip(), header_name='Subject')
        message['Date'] = email.utils.formatdate(localtime=True)
        message['Message-ID'] = email.utils.make_msgid()

        # add any custom headers
        for key, value in self.headers.iteritems():
            header = Header(value, header_name=key)
            if key in message:
                message.replace_header(key, header)
            else:
                message[key] = header
        
        # start off with a text/html
        text, charset = _encode_text(text)    
        
        if self.body_type == 'plain':
            body = MIMEText(text, _charset=charset)
        else:            
            body = MIMEText(text, _subtype='html', _charset=charset)
        
        if 'MIME-Version' in body:
            del body['MIME-Version']
        message.attach(body)
        
        # if there are attachment, add them
        for attachment in self.attachments:
            message.attach(attachment.get_mime_object())

        # now, send out each email
        for to in self.to:
            self._send_email(self.sender, to, self.cc, self.bcc, message)

    def _send_email(self, sender, to, cc, bcc, message):
        """
        Handles the actual message sending.
        """
        
        # set the "To" message header
        message.replace_header('To', Header(to, header_name='To'))

        # create the list of recipients
        recipients = [to]
        if cc:
            recipients += cc
        if bcc:
            recipients += bcc
        
        # connect to the server
        s = smtplib.SMTP(self.server,self.smtp_port)

        if self.username and self.password:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(self.username,self.password)

        # send the mail
        try:
            rCode = s.sendmail(sender, recipients, message.as_string())
            if rCode:
                raise emailError('Email could not be sent to %s' % ', '.join(recipients))
        except Exception, ex:
            raise emailError(str(ex))
        finally:
            s.quit()

    def _parse_addresses(self, addresses):
        """
        Parse whatever is specified into a list of email addresses
        """

        # start off with an empty list
        address_list = []

        # we could be getting a list or a string
        if addresses:
            if isinstance(addresses, (tuple, list)):
                for address in addresses:
                    address_list += address.split(';')
            else:
                address_list = addresses.split(';')

        # return the final list, removing blanks
        return [address for address in address_list if len(address.strip()) > 0]

class Attachment(object):
    """
    Used by the maillib to represent attachments
    """

    def __init__(self, field=None, **kwargs):
        self.name = None
        self.data = None
        self.path = None
        if field != None:
            self.name = getattr(field, 'filename')
            if hasattr(field, 'file'):
                buffer = cStringIO.StringIO()
                shutil.copyfileobj(field.file, buffer)
                field.file.close()
                self.data = buffer.getvalue()
        if 'name' in kwargs:
            self.name = kwargs['name']
        if 'data' in kwargs:
            self.data = kwargs['data']
        if 'path' in kwargs:
            self.path = kwargs['path']
            if not self.name:
                self.name = os.path.basename(self.path)
        if not self.name:
            self.name = 'Attachment'

    def get_data(self, binary=True):
        if not self.data and self.path:
            f = open(self.path, 'rb' if binary else 'r')
            data = f.read()
            f.close()
            return data
        return self.data
    
    def get_mime_object(self):

        # encode the filename; if this isn't done manually ahead of time, 
        # email.Header.encode encodes the entire header as UTF-8 if the 
        # filename portion can't be ASCII, which isn't the preferred approach
        filename, charset = _encode_text(self.name)
        if charset:
            filename = Charset(charset).header_encode(self.name)
        
        # guess the content type based on the file's extension
        ctype, encoding = mimetypes.guess_type(self.name)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        
        # create the appropriate object; not including the "name" portion 
        # here because the Content-Type header must remain as a string for 
        # the message flattening process and that prevents fixing the header
        if maintype == 'text':
            text, charset = _encode_text(self.get_data(binary=False))
            obj = MIMEText(text, _subtype=subtype, _charset=charset)
        elif maintype == 'image':
            obj = MIMEImage(self.get_data(), _subtype=subtype)
        elif maintype == 'audio':
            obj = MIMEAudio(self.get_data(), _subtype=subtype)
        else:
            obj = MIMEBase(maintype, subtype)
            obj.set_payload(self.get_data())
            encoders.encode_base64(obj)
        
        # add the filename; using Header directly for potentially long 
        # headers since MIMEMultipart overrides its default space folding 
        # character with a hard tab, which Outlook 2003 and earlier (and 
        # possibly other email clients) doesn't unfold back into a space
        obj['Content-Disposition'] = Header(SEMISPACE.join(['attachment', _formatparam('filename', filename)]), 
                                            header_name='Content-Disposition')
        
        # remove the MIME-Version (not needed for every attachment)
        if 'MIME-Version' in obj:
            del obj['MIME-Version']
        
        # return the object
        return obj

def send_email(recipient, subject, text, sender, attachment=None):
    """
    For backwards compatibility only. Use the Mail object instead.
    
    @deprecated: Use Mail object instead.
    """

    # create a Mail object from the info
    mail = Mail(to=recipient,
                sender=sender,
                subject=subject,
                template_text=text)

    # add the attachment, if there was one
    if attachment:
        if not isinstance(attachment, dict):
            attachment = {'name': 'Attachment', 'data': attachment}
        mail.add_attachment(name=attachment['name'], data=attachment['data'])

    # for some reason, this original method ignored errors
    try:
        mail.send()
    except:
        pass
