from __future__ import print_function
from operator import le
import os
from lectio import Lectio
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import time
from gservice import getService
from datetime import date, timedelta
import datetime
import pytz
import requests

load_dotenv()
calendarId = os.environ["calendarId"]
l = Lectio(681)
reach = 14
alarms = {}
scheduler = BackgroundScheduler()
""" 
def calendarCheck():
    print("Updating calendar for " + os.environ["user"] + "...")
    print("Authenticating...")
    l.authenticate(os.environ["user"], os.environ["pass"])
    print("Authenticated!")
    schedule = l.get_schedule_for_student(os.environ["student_id"])

    service = getService()

    for j,day in enumerate(schedule):
        for i, lesson in enumerate(day):
            try:
                _id = "lec"+str(hex(i))[2:]+str(j)+str(lesson.start_time.weekday())+str(lesson.start_time.year)
            except AttributeError:
                continue
            if(lesson.is_cancelled): 
                try:
                    if(service.events().get(calendarId=calendarId, eventId=_id).execute()["status"] != "cancelled"):
                        service.events().delete(calendarId=calendarId, eventId=_id).execute()
                        print("Deleted " + _id)
                except:
                    pass
                continue
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
                pass """

def activateAlarm():
    requests.get("https://api.voicemonkey.io/trigger?access_token=" + os.environ["monkey_access_token"] + "&secret_token=" + os.environ["monkey_secret_token"] + "&monkey=lectiopy")

def sched():
    scheduler.add_job(updateCalendar, 'interval', hours=1)
    scheduler.start()
    print("Schedule started")
    updateCalendar()
    print(alarms)
    while True:
        time.sleep(1)


def generateTimeID(time):
    return str(time.day) + str(time.month) + str(time.year)[-1]

def generateLessionID(lesson, schedule, get_lesson_id=False):
    time_id = generateTimeID(lesson.start_time)
    lesson_id = [schedule.index(_lesson) for _lesson in schedule if generateTimeID(_lesson.start_time) == time_id].index(schedule.index(lesson))
    _id = "lec"+time_id+str(lesson_id)
    return [_id, lesson_id] if get_lesson_id else _id

def addToCalendar(lesson, _id):
    service = getService()
    event = {
        'summary': (lesson.subject if lesson.subject != None else lesson.title) + (" | " + lesson.room if lesson.room != None else ""),
        'location': lesson.room,
        'description': lesson.url + "\n" + (lesson.title + "\n" if lesson.title != None else "") + lesson.teacher if lesson.teacher != None else lesson.url + "\n",
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
        try:
            service.events().insert(calendarId=calendarId, body=event).execute()
        except Exception as e:
            pass

def deleteEvent(_id):
    service = getService()
    try:
        service.events().delete(calendarId=calendarId, eventId=_id).execute()
    except:
        pass

def checkday(time: datetime, schedule):
    service = getService()
    # Create time_max that is the latest time possible of the day
    time_max = datetime.datetime(time.year, time.month, time.day, 23, 59, 59, tzinfo=pytz.timezone('Europe/Copenhagen')).isoformat()
    # Create time_min that is the earliest time possible of the day
    time_min = time.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.timezone("Europe/Copenhagen")).isoformat()
    events = service.events().list(calendarId=calendarId, timeMax=time_max, timeMin=time_min, showDeleted=False).execute()["items"]
    day_schedule = [_lesson for _lesson in schedule if generateTimeID(_lesson.start_time) == generateTimeID(time)]
    alarm = scheduler.add_job(activateAlarm, 'date', run_date=day_schedule[0].start_time - datetime.timedelta(minutes=75))
    alarms[time] = alarm # Add alarm to alarms dict
    for event in events:
        try:
            if(not event["description"].split("\n")[0] in [lesson.url for lesson in day_schedule] and events):
                for event in events:
                    deleteEvent([event["id"]])
                for lesson in day_schedule:
                    if(lesson.status != 2):
                        addToCalendar(lesson, generateLessionID(lesson, schedule))
        except:
            pass

def updateCalendar():
    alarms.clear()
    l.authenticate(os.environ["user"], os.environ["pass"])
    # Define start and end time as a datetime object
    start = datetime.datetime.now() + timedelta(days=0)
    end = start + timedelta(days=30)
    schedule = l.get_schedule_for_student(os.environ["student_id"], start, end)
    timestamps = []
    for i,lesson in enumerate(schedule):
        if(i % 10 == 0):
            print(round(i/len(schedule)*100, 2), "% done")
        if(generateTimeID(lesson.start_time) not in timestamps):
            timestamps.append(generateTimeID(lesson.start_time))
            checkday(lesson.start_time, schedule)
        lesson_id = generateLessionID(lesson, schedule)
        if(lesson.status == 2): 
            deleteEvent(lesson_id)
        else:
            addToCalendar(lesson, lesson_id)

    print("Calendar has been updated")

if __name__ == '__main__':
    print("Starting scheduler")
    sched()
