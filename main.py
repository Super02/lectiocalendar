from __future__ import print_function
import os
from lectio import Lectio
from dotenv import load_dotenv
import schedule
import time
from gservice import getService
from datetime import date


load_dotenv()
calendarId = os.environ["calendarId"]
l = Lectio(681)

def calendarCheck():
    print("Updating calendar for " + os.environ["user"] + "...")
    l.authenticate(os.environ["user"], os.environ["pass"])
    schedule = l.get_schedule_for_student(os.environ["student_id"])

    service = getService()

    for j,day in enumerate(schedule):
        for i, lesson in enumerate(day):
            if(lesson.start_time == None): pass
            _id = "lec"+str(hex(i))[2:]+str(j)+str(lesson.start_time.weekday())+str(lesson.start_time.year)
            event = {
                'summary': (lesson.subject if lesson.subject != None else lesson.title) + (" | " + lesson.room if lesson.room != None else ""),
                'location': lesson.room,
                'description': (lesson.title + "\n" if lesson.title != None else "") + lesson.teacher if lesson.teacher != None else "",
                'start': {
                    'dateTime': lesson.start_time.isoformat(),
                    'timeZone': 'Europe/Copenhagen',
                },
                'end': {
                    'dateTime': lesson.end_time.isoformat(),
                    'timeZone': 'Europe/Copenhagen',
                },
                'id': _id
            }
            try:
                service.events().get(calendarId=calendarId, eventId=_id).execute()
                service.events().update(calendarId=calendarId, eventId=_id, body=event).execute()
            except Exception as e:
                service.events().insert(calendarId=calendarId, body=event).execute()
            try:
                if(len(day)-1 == i):
                    while True:
                        _id = list(_id)
                        _id[3]=str(int(_id[3])+1)
                        _id="".join(_id)
                        _id = str(hex(_id))[2:]
                        if(service.events().get(calendarId=calendarId, eventId=_id).execute()["status"] != "cancelled"):
                            service.events().delete(calendarId=calendarId, eventId=_id).execute()
                            print("Deleted " + _id)
            except:
                pass
    print("Calendar has been updated")

def sched():
    print("Schedule started")
    schedule.every().hour.do(calendarCheck)
    schedule.every().day.at("07:00").do(calendarCheck)
    schedule.every().day.at("07:20").do(calendarCheck)
    schedule.every().day.at("07:30").do(calendarCheck)
    schedule.every().day.at("07:40").do(calendarCheck)
    schedule.every().day.at("08:15").do(calendarCheck)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    calendarCheck()
    sched()
