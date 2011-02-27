import cherrypy
from lib.base import *
from helpers import grab_token, init_token
import csv
import StringIO
from cherrypy.lib import file_generator
from decorator import decorator

NOT_COMING = 'I AM NOT coming'
COMING = 'I AM coming'
UNRSVP = 'UN-RSVPd'
NO_RSVP_CHANGE = 'NO RSVP change'

class Root(BaseController):
    """ sits @ The root of the app """

    @cherrypy.expose
    def default(self,token=None):
        # if we got a token handle it
        init_token(token)
        return redirect('/')

    @cherrypy.expose
    def index(self):
        return render('/index.html')

    @cherrypy.expose
    @grab_token
    def guest_list(self):
        guests = m.Guest.query.order_by(m.Guest.name).all()
        return render('/rsvp_list.html',guests=guests)

    @cherrypy.expose
    @grab_token
    def guest(self,gid):
        try:
            guest = m.Guest.get(gid)
            if not guest:
                raise e.ValidationException('Guest not found')
            editable = False
            if is_guest(guest) or is_admin():
                editable = True
            print 'editable: %s' % editable
        except e.ValidationException, ex:
            add_flash(ex)
        except:
            raise
        return render('/guest.html',guest=guest, editable=editable,
                                    NOT_COMING=NOT_COMING,UNRSVP=UNRSVP,
                                    COMING=COMING,
                                    NO_RSVP_CHANGE=NO_RSVP_CHANGE)

    @cherrypy.expose
    @grab_token
    def guest_list_report(self):
        guests = m.Guest.query.order_by(m.Guest.name).all()
        csv_data = []
        header = ['Guest','Party Size','RSVPd','Attending','Comment',
                  'Guests Requested', 'Guests Allowed',
                  'Guests Attending','Total']
        for guest in guests:
            d = []
            d.append(guest.name)
            d.append(guest.party_size)
            d.append('1' if guest.rsvpd else '0')
            d.append('1' if guest.attending else '0')
            d.append(guest.comment or '')
            d.append(guest.guests_requested)
            d.append(guest.guests_allowed)
            d.append(guest.guests_coming)
            d.append(guest.party_size + guest.guests_coming)
            csv_data.append(d)
        csv_buffer = StringIO.StringIO()
        csv_report = csv.writer(csv_buffer)
#        csv_report.writeheader(header)
        csv_report.writerow(header)
        csv_report.writerows(csv_data)
        csv_buffer.seek(0)
        cherrypy.response.headers['Content-type'] = 'application/xls'
        cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="guest_list.csv"'
        return file_generator(csv_buffer)

    @cherrypy.expose
    @grab_token
    def rsvp(self,gid=None,attending=False,comment='', party_size=1,
             guests_requested=0, guests_coming=0, guests_allowed=0):
        try:
            guest = m.Guest.get(gid)
            if not is_guest(guest):
                raise e.ValidationException('You can not edit this!')
            if not guest:
                raise e.ValidationException('Guest not found')

            guests_requested = int(guests_requested)
            guests_coming = int(guests_coming)
            guests_allowed = int(guests_allowed)
            party_size = int(party_size)

            if attending == COMING:
                guest.attending = True
            elif attending == NOT_COMING:
                guest.attending = False
            elif attending == UNRSVP:
                guest.rsvpd = False
                guest.attending = None

            if attending != NO_RSVP_CHANGE:
                guest.rsvpd = True

            comment = comment.strip()
            guest.comment = comment

            # if they are not coming clear guest's coming
            if not guest.attending:
                guest.guests_coming = 0

            else:
                if guest.guests_requested != guests_requested:
                    guest.guests_requested += guests_requested

                if guests_coming != guest.guests_coming:
                    guest.guests_coming = guests_coming

                if party_size != guest.party_size:
                    guest.party_size = party_size

                if is_admin() and guests_allowed != guest.guests_allowed:
                    if guests_allowed < guest.guests_coming:
                        guest_diff = guests_allowed - guest.guests_coming
                        guest.guests_requested += abs(guest_diff)
                        guest.guests_coming = guests_allowed

                    wanted = guest.guests_requested + guest.guests_coming
                    if guests_allowed >= wanted:
                        guest.guests_requested = 0

                    guest.guests_allowed = guests_allowed

            m.session.commit()

            return redirect('/guest',guest.id)

        except e.ValidationException, ex:
            add_flash(ex)
            if guest.id:
                return redirect('/guest',guest.id)
        except:
            raise

        return redirect('/guest_list')

    @cherrypy.expose
    @grab_token
    def reception_details(self):
        return render('/reception_details.html')

    @cherrypy.expose
    def add_guest(self,name=''):
        try:
            name = name.strip()
            if not name:
                raise e.ValidationException('name required')
            g = m.Guest(name=name)
            m.session.commit()
        except e.ValidatioNException, ex:
            add_flash(ex)
            redirect('/guest_list')
        except:
            raise
        return redirect('/guest',g.id)
