import datetime
import os.path
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS_ROOT = "Your root to your .json credentials file"
calendar_Id = 'your google calendar ID'

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(os.path.join(CREDS_ROOT, "token.json")):
        creds = Credentials.from_authorized_user_file(
            os.path.join(CREDS_ROOT, "token.json"), SCOPES
        )
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(CREDS_ROOT, "credentials.json"), SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(os.path.join(CREDS_ROOT, "token.json"), "w") as token:
            token.write(creds.to_json())
    return creds

def get_week(relative_week=0):
    
    """Returns a list of the first and last day of the week [sunday, saturday]. When relative_week=0 it returns
    the first and last day of this week, otherwise it returns the first and last day of the
    '+relative_week' week.""" 
    # Since I'm brazilian all timezones are replaced and changed to make it work
    
    SPTz = pytz.timezone("America/Sao_Paulo") 
    td = datetime.datetime.now(SPTz).date()#.isoformat()+'Z'
    start = td - datetime.timedelta(days=td.weekday()+1-7*relative_week)
    end = start + datetime.timedelta(days=6)
    return [start.isoformat()+"T00:00:00.000000",end.isoformat()+"T23:59:59.000000"]


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
            self.week_days.append(Day(i,9,22))
        for i in self.week_days:
            self.events.extend(i.events)
    def find_next_time(self, event):
        time = []
        scheduled = False
        i = 1
        while (not scheduled) and i<=5:
            #para cada dia útil da semana
            self.refresh_events()
            day = self.week_days[i]
            start = day.start_time
            end = day.end_time
            events = day.events
            d = pd.to_datetime(day.date)
            d_ = d.date()
            SPTz = pytz.timezone("America/Sao_Paulo") 
            end_ = datetime.datetime(d_.year,d_.month,d_.day,end,0,0,0,SPTz)
            projected_start = datetime.datetime(d_.year,d_.month,d_.day,start,0,0,0,SPTz)
            while projected_start.replace(tzinfo=None) < end_.replace(tzinfo=None):
                valid = True
                projected_end = projected_start + pd.to_timedelta(f"{event.duration} min") - pd.to_timedelta('1 min')
                #-------Check for overlap --------------
                for ev in events:
                    if not scheduled:
                        start_time = ev.start_event
                        end_time = ev.end_event
                        start_time = pd.to_datetime(start_time)
                        end_time = pd.to_datetime(end_time) - pd.to_timedelta('1 min')
                        
                        if (projected_start.replace(tzinfo=None) >= start_time.replace(tzinfo=None) and projected_start.replace(tzinfo=None) <= end_time.replace(tzinfo=None)) or(
                                projected_end.replace(tzinfo=None) >= start_time.replace(tzinfo=None) and projected_end.replace(tzinfo=None) <= end_time.replace(tzinfo=None)):
                            valid = False
                #------------------------------------
                if valid:
                    if not event.daily and not scheduled:
                        time.append(projected_start)
                        scheduled =True
                        break
                    elif event.daily:
                        time.append(projected_start)
                        if i == 5: scheduled=True
                        break
                projected_start = projected_start+ pd.to_timedelta('15 min')
            i = i+1
        if len(time)>0: return time
        else: return None   

    def create_event(self, event):
        
        if not event.scheduled:
            times = self.find_next_time(event)
            for t in times:
                t = pd.to_datetime(t) - pd.to_timedelta('6 min')
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
                event.scheduled = True     
    def delete_all_created_events(self):
        self.refresh_events()
        for e in self.events:
            if 'description' in e.event_dic.keys():
                if "__created_in_python__"  in e.event_dic['description']:
                    e.delete_event()
      
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
    
 
class Event():
    def __init__(self, event_name, duration, category,scheduled:bool, priority = 0, divisible= False, daily= False):
        self.event_name = event_name
        self.duration = duration
        self.category = category
        self.priority = priority
        self.divisible = divisible
        self.daily = daily
        self.scheduled = scheduled
        self.id = []
        self.event_dic = {}
        self.start_event = None
        self.end_event = None
        self.description = ""
        self.colorId = 8
        colors = {'Study':3,'Health':4,'Leisure':5,'Job':6,'Routine':7, 'Others':8, 'Hobby': 9}
        if self.category  in colors.keys():
            self.colorId = colors[self.category]
    def delete_event(self):
        if self.scheduled:
            creds = get_credentials()
            service = build("calendar", "v3", credentials=creds)
            for i in self.id:
                try:
                    service.events().delete(
                        calendarId=calendar_Id, eventId=i).execute()
                except HttpError as error:
                    print("An error occurred: %s" % error)
        else:
            return False
