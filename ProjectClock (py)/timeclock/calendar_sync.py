from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class CalendarSync:
    """Handles calendar integration and synchronization"""

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    TOKEN_FILE = 'token.json'
    CREDENTIALS_FILE = 'credentials.json'

    def __init__(self):
        self.creds = None
        self.service = None

    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API"""
        if os.path.exists(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'r') as token:
                self.creds = Credentials.from_authorized_user_file(
                    self.TOKEN_FILE, self.SCOPES
                )

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.CREDENTIALS_FILE):
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            with open(self.TOKEN_FILE, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('calendar', 'v3', credentials=self.creds)
        return True

    def add_work_schedule(self, start_time: datetime, end_time: datetime,
                         description: str, timezone_str: str = 'UTC') -> Optional[str]:
        """Add a work schedule event to the calendar"""
        try:
            if not self.service:
                if not self.authenticate():
                    return None

            event = {
                'summary': 'Work Schedule',
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone_str,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone_str,
                },
                'reminders': {
                    'useDefault': True
                }
            }

            event = self.service.events().insert(
                calendarId='primary', body=event).execute()
            return event.get('id')

        except HttpError as error:
            print(f'An error occurred: {error}')
            return None

    def update_work_schedule(self, event_id: str, start_time: datetime,
                           end_time: datetime, description: str,
                           timezone_str: str = 'UTC') -> bool:
        """Update an existing work schedule event"""
        try:
            if not self.service:
                if not self.authenticate():
                    return False

            event = self.service.events().get(
                calendarId='primary', eventId=event_id).execute()

            event['start'] = {
                'dateTime': start_time.isoformat(),
                'timeZone': timezone_str
            }
            event['end'] = {
                'dateTime': end_time.isoformat(),
                'timeZone': timezone_str
            }
            event['description'] = description

            self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            return True

        except HttpError:
            return False

    def delete_work_schedule(self, event_id: str) -> bool:
        """Delete a work schedule event"""
        try:
            if not self.service:
                if not self.authenticate():
                    return False

            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True

        except HttpError:
            return False

    def get_work_schedules(self, start_date: datetime,
                          end_date: datetime,
                          timezone_str: str = 'UTC') -> list[Dict[str, Any]]:
        """Get all work schedule events within a date range"""
        try:
            if not self.service:
                if not self.authenticate():
                    return []

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                timeZone=timezone_str,
                q='Work Schedule'
            ).execute()

            return events_result.get('items', [])

        except HttpError:
            return []