import pandas as pd
from day import Day
from event import Event
from googleapiclient.discovery import build
import numpy as np
from version0 import get_credentials

calendar_Id= 'your google email'

class Week():

    def __init__(self, week_start,week_end):
        self.week_start = week_start
        self.week_end = week_end
        self.week_days = []
        self.events = []
        self.full = False
        
        self.refresh_events()


        
    def refresh_events(self):
        self.events = []
        self.week_days = []
        for i in pd.date_range(self.week_start, self.week_end):
            self.week_days.append(Day(i,9,21))
        for i in self.week_days:
            self.events.extend(i.events)
            
            
    def find_next_time(self, event):
        times = []
        scheduled = event.scheduled
        if not scheduled:
            if event.daily:
                for i in np.arange(1,6):
                    d = self.week_days[i]
                    if not d.full:
                        t = d.next_time(event)
                        if t is not None:
                            times.append(t)
                return times
            else:
                i=1
                valid= False
                while not valid and i <=6 :
                    d = self.week_days[i]
                    if not d.full:
                        t = d.next_time(event)
                        if t is not None:
                            valid= True
                            times.append(t)
                        else:
                            i=i+1
                            
                    else:
                        i=i+1
                return times
        else:
            return None




    def create_event(self, event, time = None):
        if time is None:
            times = self.find_next_time(event)
        else:
            times = [time]
        if not event.scheduled:
            for t in times:
                t = pd.to_datetime(t) #- pd.to_timedelta('6 min')
                body_event = {
                        "summary": f"{event.event_name}",
                        "description": event.description + " __created_in_python__.",
                        "colorId": event.colorId,
                        "start": {
                            "dateTime": f"{t.isoformat()}",
                            "timeZone": "Brazil/East",
                        },
                        "end": {
                            "dateTime": f"{(t+pd.to_timedelta(str(event.duration)+' min')).isoformat()}",
                            "timeZone": "Brazil/East",
                        },
                        "reminders": {
                            "useDefault": True,
                        }}
                service = build('calendar', 'v3', credentials=get_credentials())         
                schedule = service.events().insert(calendarId=calendar_Id, body=body_event).execute()       
                event.id.append(schedule['id'])
                
                temp = Event(schedule['summary'],pd.to_datetime(schedule['end']['dateTime'])
                                         -pd.to_datetime(schedule['start']['dateTime']),schedule['summary'],True)
                temp.id = [schedule['id']]
                temp.start_event = schedule['start']['dateTime']
                temp.end_event = schedule['end']['dateTime']
                temp.event_dic = schedule
                temp.scheduled = True
                i = t.isoweekday()
                self.week_days[i].events.append(temp)
                #self.refresh_events()
            event.scheduled = True 
            
    def delete_all_created_events(self):
        self.refresh_events()
        for e in self.events:
            if 'description' in e.event_dic.keys():
                if "__created_in_python__"  in e.event_dic['description']:
                    e.delete_event()
