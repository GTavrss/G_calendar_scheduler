import datetime
import os.path
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def get_credentials():
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    CREDS_ROOT = "directory to your credentials.json file"
    creds = None
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
