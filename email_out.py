from maillib import Mail
from add_guests import get_data
import models as m; m.setup()
from helpers import get_guest_token

SERVER = 'google.com'
LINK_BASE = 'http://mostsplendiferous.com'
TEMPLATE_PATH = './email_template.html'
SENDER = '"Lizz Mitchell" <lizzisgettingmarried@gmail.com>'

def send_mail():
    mailed = []
    for data in get_data():
        lookup = {'name':('%s %s' % (data.get('first_name',''),
                                     data.get('last_name',''))).strip(),
                  'party_size':data.get('party_size',1) or 1,
                  'guests':data.get('guests',0) or 0 }
        guest = m.Guest.get_by(name=lookup.get('name'))
        if not guest:
            raise Exception('no guest: %s' % lookup)
        link = '%s/%s/%s' % (LINK_BASE,guest.id,get_guest_token(guest))
        lookup['link'] = link
        mail = Mail(server=SERVER,
                    sender=SENDER,
                    to=data.get('email_address'),
                    template_path=TEMPLATE_PATH,
                    use_templating=True,
                    replacement_dict=lookup)
        r = mail.send()
        mailed.append(r)
    return mailed
