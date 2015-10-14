#!/home/local/AD3/ndiquatt/Vpythons/labscripts/vpython/bin/python
from bs4 import BeautifulSoup
import mechanize
import datetime
import os
import yaml
import urlparse
import gcal


# Scrape Sona
def scrape_slots(username, password, url):
    # Browser
    br = mechanize.Browser()

    # Settings
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    # Open page and select login form
    mainpage = urlparse.urlparse(url)
    mainpage = '{0}://{1}'.format(mainpage.scheme, mainpage.netloc)
    br.open(mainpage)
    br.select_form(name="aspnetForm")

    # Fill out and submit form
    br["ctl00$ContentPlaceHolder1$userid"] = username
    br["ctl00$ContentPlaceHolder1$pw"] = password
    br.submit()

    # Open studies page
    slots_html = br.open(url)

    # Soupify
    soup = BeautifulSoup(slots_html, "html.parser")

    # Get the studies rows
    slot_rows = soup.select("table tbody tr")

    # Date Parser
    def pdate(dstr):

        # Split and remove blanks
        clean_str = filter(None, dstr.split('\n'))

        # Make start and end strings
        day = '{1}{2}'.format(*tuple(clean_str[0].split(','))).lstrip()
        start = clean_str[1].split(' - ')[0]
        end = clean_str[1].split(' - ')[1]
        dtime = '{} {}'.format(day, start)
        dtimend = '{} {}'.format(day, end)
        dtime = datetime.datetime.strptime(dtime, '%B %d %Y %I:%M %p')
        dtimend = datetime.datetime.strptime(dtimend, '%B %d %Y %I:%M %p')

        return dtime, dtimend

    # Parse studies
    slots = []
    for row in slot_rows:
        columns = row.find_all('td')
        start, end = pdate(columns[0].get_text())
        name = columns[2].get_text().split('\n')[1]

        slots.append({'name': name,
                      'start': start,
                      'end': end})

    return slots


def main(sonasystem, einfo):
    try:

        # Scrape slots
        signups = scrape_slots(einfo['user'],
                               einfo['pass'],
                               einfo['url'])

        # Scrape Calendar
        events = gcal.calevents(einfo['calid'])

        # Iterate through slots
        for slot in signups:
            # Grab corresponding calendar event
            cevent = []
            cevent = [event for event in events
                      if event['start'].replace(tzinfo=None) == slot['start']]

            if cevent:
                # Select subject name
                sname = cevent[0]['name'].split(' - ')[1]

                # Check that names match
                if slot['name'] != sname:
                    gcal.update_event(einfo['calid'],
                                      cevent[0]['eid'],
                                      slot['name'])

            else:
                gcal.mkevent(slot, einfo['calid'], sonasystem)

        # Delete unneeded calendar events
        for calevent in events:
            keep = []
            keep = [slot for slot in signups
                    if slot['start'] == calevent['start'].replace(tzinfo=None)]

            if not keep:
                gcal.delevent(einfo['calid'], calevent[0]['eid'])

        # Log it
        with open(str(os.getcwd()) + '/log.txt', 'a') as f:
            f.write(str(datetime.datetime.now()) + ",success\n")

    except Exception, e:
        # Log it
        with open(str(os.getcwd()) + '/err.txt', 'a') as f:
            f.write(str(datetime.datetime.now()) + "," + str(e) + "\n")


if __name__ == "__main__":
    # Load secrets
    with open('config.yaml', 'r') as f:
        config = yaml.load(f)

    # Initiate Google Calendar Interface
    gcal = gcal.CalMaster()

    for key, val in config.iteritems():
        main(key, val)
