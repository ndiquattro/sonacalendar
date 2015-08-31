# Class for interacting with google calendar
import rfc3339
import httplib2
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import os
import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


# Make Class
class calMaster(object):

    # Initiate
    def __init__(self):

        # Authorize and create service
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('calendar', 'v3', http=http)

    # Authorize with Google API
    def get_credentials(self):

            # Set variables
            scopes = 'https://www.googleapis.com/auth/calendar'
            client_secret_file = 'googleauth.json'
            application_name = 'sonacalendar'
            credential_path = os.path.join(os.getcwd(), 'goauth.json')

            # Try to load stored credentials
            store = oauth2client.file.Storage(credential_path)
            credentials = store.get()

            # Get new if invalid or not there
            if not credentials or credentials.invalid:
                flow = client.flow_from_clientsecrets(client_secret_file,
                                                      scopes)
                flow.user_agent = application_name

                credentials = tools.run_flow(flow, store, flags)

            return credentials

    # Scrape Calendar events
    def calevents(self, calid):

        # Grab Events
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        eventsresult = self.service.events().list(
            calendarId=calid, timeMin=now, singleEvents=True,
            orderBy='startTime').execute()
        events = eventsresult.get('items', [])

        # Parse Events
        cevents = []
        for event in events:
            start = rfc3339.parse_datetime(event['start']['dateTime'])
            cevents.append({'name': event['summary'],
                            'start': start,
                            'eid': event['id']})

        return cevents

    def mkevent(self, vals, calid, system):

        event = {'summary': 'Nick - {}'.format(vals['name']),
                 'description': system,
                 'start': {
                     'dateTime': rfc3339.datetimetostr(vals['start'])[:-1],
                     'timeZone': 'America/Los_Angeles'},
                 'end': {
                     'dateTime': rfc3339.datetimetostr(vals['end'])[:-1],
                     'timeZone': 'America/Los_Angeles'}
                 }

        # Add event
        self.service.events().insert(calendarId=calid,
                                body=event).execute()

    def clearcal(self, calid):

        # Get list of events
        events = self.service.events().list(calendarId=calid).execute()
        events = events.get('items', [])

        # Delete them
        for event in events:
            self.service.events().delete(calendarId=calid,
                                         eventId=event['id']).execute()

    def update_event(self, calid, eid, new_name):

        # New event dict
        name = 'Nick - {}'.format(new_name)
        nevent = {'summary': name}

        # Update
        self.service.events().update(calendarId=calid, eventId=eid,
                                     event=nevent).execute()
