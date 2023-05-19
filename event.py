from version0 import get_credentials 
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

calendar_Id = 'your google email'
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
