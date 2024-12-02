from collections.abc import Sequence
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from . import gauth
from . import calendar
import json
from . import toolhandler

class GetCalendarEventsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("get_calendar_events")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Retrieves calendar events from the user's Google Calendar within a specified time range.",
            inputSchema={
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "description": "Start time in RFC3339 format (e.g. 2024-12-01T00:00:00Z). Defaults to current time if not specified."
                    },
                    "time_max": {
                        "type": "string", 
                        "description": "End time in RFC3339 format (e.g. 2024-12-31T23:59:59Z). Optional."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return (1-2500)",
                        "minimum": 1,
                        "maximum": 2500,
                        "default": 250
                    },
                    "show_deleted": {
                        "type": "boolean",
                        "description": "Whether to include deleted events",
                        "default": False
                    }
                },
                "required": []
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        calendar_service = calendar.CalendarService()
        events = calendar_service.get_events(
            time_min=args.get('time_min'),
            time_max=args.get('time_max'),
            max_results=args.get('max_results', 250),
            show_deleted=args.get('show_deleted', False)
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(events, indent=2)
            )
        ]
