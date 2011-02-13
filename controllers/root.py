import cherrypy
from lib.base import *
import csv
import StringIO
from cherrypy.lib import file_generator

NOT_COMING = 'I AM NOT coming'
COMING = 'I AM coming'

class Root(BaseController):
    """ sits @ The root of the app """

    @cherrypy.expose
    def index(self):
        return render('/index.html')

    @cherrypy.expose
    def guest_list(self):
        guests = m.Guest.query.order_by(m.Guest.name).all()
        return render('/rsvp_list.html',guests=guests)

    @cherrypy.expose
    def guest(self,gid):
        try:
            guest = m.Guest.get(gid)
            if not guest:
                raise e.ValidationException('Guest not found')
        except e.ValidationException, ex:
            add_flash(ex)
        except:
            raise
        return render('/guest.html',guest=guest,NOT_COMING=NOT_COMING,
                                                COMING=COMING)

    @cherrypy.expose
    def guest_list_report(self):
        guests = m.Guest.query.order_by(m.Guest.name).all()
        csv_data = []
        header = ['Guest','RSVPd','Attending']
        for guest in guests:
            d = []
            d.append(guest.name)
            d.append('1' if guest.rsvpd else '0')
            d.append('1' if guest.attending else '0')
            csv_data.append(d)
        csv_buffer = StringIO.StringIO()
        csv_report = csv.writer(csv_buffer)
#        csv_report.writeheader(header)
        csv_report.writerow(header)
        csv_report.writerows(csv_data)
        csv_buffer.seek(0)
        cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="guest_list.csv"'
        return file_generator(csv_buffer)

    @cherrypy.expose
    def rsvp(self,gid,attending,comment=''):
        try:
            guest = m.Guest.get(gid)
            if not guest:
                raise e.ValidationException('Guest not found')
            guest.attending = True if attending == COMING else False
            comment = comment.strip().strip()
            guest.comment = comment
            guest.rsvpd = True
            not_ = 'not' if not guest.attending else ''
            m.session.commit()
            return redirect('/guest?gid=%s' % guest.id)

        except e.ValidationException, ex:
            add_flash(ex)
        except:
            raise

        return redirect('/guest')

    @cherrypy.expose
    def reception_details(self):
        return render('/reception_details.html')
