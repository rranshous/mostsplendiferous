
COLUMNS = ('last_name','first_name','party_size',
           'guests','notes','email_address')

def get_data():
    import csv
    with file('./email_list.csv','rb') as fh:
        reader = csv.reader(fh,delimiter=',',quotechar='"')
        data = []
        for row in reader:
            data.append(dict(zip(COLUMNS,row)))
    return data

def add_guests():
    data = get_data()
    import models as m
    guests = []
    for d in get_data():
        guests.append(m.Guest(
            name = ('%s %s' % (d.get('first_name','').strip(),
                              d.get('last_name','').strip())).strip(),
            guests_allowed = d.get('guests',0) or 0,
            party_size = d.get('party_size',0) or 0
        ))
    return guests
