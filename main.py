from __future__ import print_function
import datetime
import os
from lectio import Lectio
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
calendarId = os.environ["calendarId"]
l = Lectio(681)
load_dotenv()


def getService():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        creds = Credentials(
            token="h",
            refresh_token=os.environ["refresh_token"],
            token_uri=os.environ["token_uri"], 
            client_id=os.environ["client_id"],
            client_secret=os.environ["client_secret"],
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


def main():
    print(os.environ["user"])
    l.authenticate(os.environ["user"], os.environ["pass"])
    schedule = l.get_schedule_for_student(os.environ["student_id"])

    service = getService()

    for i, day in enumerate(schedule):
        for j, lesson in enumerate(day):
            id = "lec"+str(i)+str(j)
            event = {
                'summary': (lesson.subject if lesson.subject != None else lesson.title) + (" | " + lesson.room if lesson.room != None else ""),
                'location': lesson.room,
                'description': (lesson.title + "\n" if lesson.title != None else "") + lesson.teacher,
                'start': {
                    'dateTime': lesson.start_time.isoformat(),
                    'timeZone': 'Europe/Copenhagen',
                },
                'end': {
                    'dateTime': lesson.end_time.isoformat(),
                    'timeZone': 'Europe/Copenhagen',
                },
                'id': id
            }
            try:
                service.events().get(calendarId=calendarId, eventId=id).execute()
                calendarevent = service.events().update(
                    calendarId=calendarId, eventId=id, body=event).execute()
            except Exception as e:
                print(e)
                calendarevent = service.events().insert(
                    calendarId=calendarId, body=event).execute()
            print(calendarevent.get('htmlLink'))


if __name__ == '__main__':
    main()
