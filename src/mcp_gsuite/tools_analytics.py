from collections.abc import Sequence
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from . import gauth
from . import analytics
import json
from . import toolhandler

class ListAnalyticsPropertiesToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("list_analytics_properties")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""Lists all Google Analytics properties accessible by the user. 
            Call it before using other analytics tools to get the property IDs.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                },
                "required": [toolhandler.USER_ID_ARG]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        analytics_service = analytics.AnalyticsService(user_id=user_id)
        properties = analytics_service.list_properties()
        
        if not properties:
            return [TextContent(text="No Google Analytics properties found for this user.", type="text")]
        
        result_text = "Google Analytics Properties:\n\n"
        for prop in properties:
            result_text += f"Property ID: {prop.get('property_id')}\n"
            result_text += f"Display Name: {prop.get('display_name')}\n"
            result_text += f"Property Type: {prop.get('property_type')}\n"
            result_text += f"Created: {prop.get('create_time')}\n"
            result_text += f"Account: {prop.get('account')}\n\n"
        
        return [TextContent(text=result_text, type="text")]


class RunAnalyticsReportToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("run_analytics_report")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="""Run a report on Google Analytics data to retrieve metrics and dimensions for a specific property.
            Commonly used metrics include 'activeUsers', 'totalUsers', 'newUsers', 'sessions', 'screenPageViews'.
            Commonly used dimensions include 'date', 'deviceCategory', 'country', 'browser', 'operatingSystem', 'pageTitle', 'pagePath'.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "__user_id__": self.get_user_id_arg_schema(),
                    "property_id": {
                        "type": "string",
                        "description": "The Google Analytics property ID (format: '123456789' or 'properties/123456789')"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for the report in YYYY-MM-DD format. Defaults to 7 days ago if not specified."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for the report in YYYY-MM-DD format. Defaults to today if not specified."
                    },
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of metrics to include in the report. Defaults to ['activeUsers'] if not specified."
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of dimensions to include in the report. Defaults to ['date'] if not specified."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return. Defaults to 10000.",
                        "default": 10000
                    }
                },
                "required": [toolhandler.USER_ID_ARG, "property_id"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        user_id = args.get(toolhandler.USER_ID_ARG)
        if not user_id:
            raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")
        
        property_id = args.get("property_id")
        if not property_id:
            raise RuntimeError("Missing required argument: property_id")
        
        # Prepare date range
        date_range = None
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        if start_date or end_date:
            date_range = {}
            if start_date:
                date_range["start_date"] = start_date
            if end_date:
                date_range["end_date"] = end_date
        
        # Get other parameters
        metrics = args.get("metrics")
        dimensions = args.get("dimensions")
        limit = args.get("limit", 10000)
        
        # Run the report
        analytics_service = analytics.AnalyticsService(user_id=user_id)
        report = analytics_service.run_report(
            property_id=property_id,
            date_range=date_range,
            metrics=metrics,
            dimensions=dimensions,
            limit=limit
        )
        
        # Check for errors
        if "error" in report:
            return [TextContent(
                text=f"Error running Google Analytics report: {report.get('error')}",
                logging_level=LoggingLevel.ERROR,
                type="text"
            )]
        
        # Format the result
        result_text = f"Google Analytics Report for Property: {report.get('property_id')}\n\n"
        
        # Add date range
        date_range_info = report.get('date_range', {})
        result_text += f"Date Range: {date_range_info.get('start_date', 'N/A')} to {date_range_info.get('end_date', 'N/A')}\n\n"
        
        # Add headers
        dimensions_headers = report.get('dimensions_headers', [])
        metrics_headers = report.get('metrics_headers', [])
        
        result_text += "Results:\n"
        
        # Format as table if there are rows
        rows = report.get('rows', [])
        if rows:
            # Create header row
            header_row = ""
            for dim in dimensions_headers:
                header_row += f"{dim}\t"
            for metric in metrics_headers:
                header_row += f"{metric}\t"
            result_text += f"{header_row.strip()}\n"
            
            # Add separator
            result_text += "-" * len(header_row) + "\n"
            
            # Add data rows
            for row in rows:
                row_text = ""
                for dim in dimensions_headers:
                    row_text += f"{row.get(dim, 'N/A')}\t"
                for metric in metrics_headers:
                    row_text += f"{row.get(metric, 'N/A')}\t"
                result_text += f"{row_text.strip()}\n"
        else:
            result_text += "No data found for the specified parameters.\n"
        
        # Add raw data as JSON for potential further processing
        result_text += "\nRaw Data (JSON):\n"
        result_text += json.dumps(report, indent=2)
        
        return [TextContent(text=result_text, type="text")] 