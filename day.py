from functions import get_credentials 
from googleapiclient.discovery import build
import pandas as pd
import pytz
from event import Event
import datetime

class Day():
    def __init__(self,date,start_time,end_time):
        self.date = date
        self.start_time= start_time
        self.end_time = end_time
        self.events = []
        self.full = False
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds) 
        tz = pytz.timezone('America/Sao_Paulo')
        start = pd.to_datetime(self.date).replace(tzinfo=tz) #+ pd.to_timedelta(f"3 hour") #<-- Timezone
        end = pd.to_datetime(self.date).replace(tzinfo=tz) + pd.to_timedelta("24 hour") #- pd.to_timedelta('1 min')
        events_ = service.events().list(calendarId='primary', timeMin=start.isoformat(),
                                          timeMax=end.isoformat(), singleEvents=True, 
                                          orderBy='startTime').execute().get('items', [])
        for e in events_:
            temp = Event(e['summary'],pd.to_datetime(e['end']['dateTime'])
                                     -pd.to_datetime(e['start']['dateTime']),e['summary'],True)
            temp.id = [e['id']]
            temp.start_event = e['start']['dateTime']
            temp.end_event = e['end']['dateTime']
            temp.event_dic = e
            temp.scheduled = True
            if 'description' in e.keys():
                temp.description = e['description']
            self.events.append(temp)
    def next_time(self, event):
        times = []
        scheduled = event.scheduled
        if not scheduled and not self.full:
            start = self.start_time
            end = self.end_time
            events = self.events
            d = pd.to_datetime(self.date)
            d_ = d.date()
            SPTz = pytz.timezone("America/Sao_Paulo") 
            end_ = datetime.datetime(d_.year,d_.month,d_.day,end,0,0,0,SPTz) - pd.to_timedelta('6 min')
            projected_start = datetime.datetime(d_.year,d_.month,d_.day,start,0,0,0,SPTz) - pd.to_timedelta('6 min')
            while projected_start.replace(tzinfo=None) < end_.replace(tzinfo=None):
                valid = True
                projected_end = projected_start + pd.to_timedelta(f"{event.duration} min") - pd.to_timedelta('1 min')
                #-------Check for overlap --------------
                for ev in events:
                    if not pd.to_datetime(ev.start_event).replace(tzinfo=None) > projected_end.replace(tzinfo=None):
                        if not scheduled:
                            start_time = ev.start_event
                            end_time = ev.end_event
                            start_time = pd.to_datetime(start_time)
                            end_time = pd.to_datetime(end_time) - pd.to_timedelta('1 min')
                            
                            if (projected_start.replace(tzinfo=None) >= start_time.replace(tzinfo=None) and projected_start.replace(tzinfo=None) <= end_time.replace(tzinfo=None)) or(
                                    projected_end.replace(tzinfo=None) >= start_time.replace(tzinfo=None) and projected_end.replace(tzinfo=None) <= end_time.replace(tzinfo=None)) or(
                                    projected_start.replace(tzinfo=None) <= start_time.replace(tzinfo=None) and projected_end.replace(tzinfo=None) >= end_time.replace(tzinfo=None)    ):
                                valid = False
                                projected_start = end_time + pd.to_timedelta('1 min')
    
                #------------------------------------
                if valid:
                    if not scheduled:
                        times.append(projected_start)
                        break
    
            if len(times)>0:
                return times[0]
            else:
                #self.full = True
                return None
        else: return None
