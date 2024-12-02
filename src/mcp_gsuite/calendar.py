from apiclient.discovery import build
from . import gauth
import logging
import traceback
from datetime import datetime
import pytz

class CalendarService():
    def __init__(self):
        credentials = gauth.get_stored_credentials()
        if not credentials:
            raise RuntimeError("No Oauth2 credentials stored")
        self.service = build('calendar', 'v3', credentials=credentials)  # Note: using v3 for Calendar API
        
    def get_events(self, time_min=None, time_max=None, max_results=250, show_deleted=False):
        """
        Retrieve calendar events within a specified time range.
        
        Args:
            time_min (str, optional): Start time in RFC3339 format. Defaults to current time.
            time_max (str, optional): End time in RFC3339 format
            max_results (int): Maximum number of events to return (1-2500)
            show_deleted (bool): Whether to include deleted events
            
        Returns:
            list: List of calendar events
        """
        try:
            # If no time_min specified, use current time
            if not time_min:
                time_min = datetime.now(pytz.UTC).isoformat()
                
            # Ensure max_results is within limits
            max_results = min(max(1, max_results), 2500)
            
            # Prepare parameters
            params = {
                'calendarId': 'primary',
                'timeMin': time_min,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime',
                'showDeleted': show_deleted
            }
            
            # Add optional time_max if specified
            if time_max:
                params['timeMax'] = time_max
                
            # Execute the events().list() method
            events_result = self.service.events().list(**params).execute()
            
            # Extract the events
            events = events_result.get('items', [])
            
            # Process and return the events
            processed_events = []
            for event in events:
                processed_event = {
                    'id': event.get('id'),
                    'summary': event.get('summary'),
                    'description': event.get('description'),
                    'start': event.get('start'),
                    'end': event.get('end'),
                    'status': event.get('status'),
                    'creator': event.get('creator'),
                    'organizer': event.get('organizer'),
                    'attendees': event.get('attendees'),
                    'location': event.get('location'),
                    'hangoutLink': event.get('hangoutLink'),
                    'conferenceData': event.get('conferenceData'),
                    'recurringEventId': event.get('recurringEventId')
                }
                processed_events.append(processed_event)
                
            return processed_events
            
        except Exception as e:
            logging.error(f"Error retrieving calendar events: {str(e)}")
            logging.error(traceback.format_exc())
            return []