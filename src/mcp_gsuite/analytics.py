from googleapiclient.discovery import build
from . import gauth
import logging
import traceback
from datetime import datetime, timedelta
import pytz
import json
import httplib2

class AnalyticsService:
    def __init__(self, user_id: str):
        """
        Initialize the Google Analytics service.
        
        Args:
            user_id (str): The email of the user to authenticate as
        """
        credentials = gauth.get_stored_credentials(user_id=user_id)
        if not credentials:
            raise RuntimeError("No OAuth2 credentials stored")
        
        # Create an HTTP object and authorize it with the credentials
        http = httplib2.Http()
        http = credentials.authorize(http)
        
        # Build the service with the authorized HTTP object
        self.service = build('analyticsdata', 'v1beta', http=http)
    
    def list_properties(self):
        """
        List all Google Analytics properties accessible by the user.
        
        Returns:
            list: List of GA4 properties
        """
        try:
            # We need to use the Analytics Admin API to list properties
            # Create an HTTP object with the credentials
            http = self.service._http
            
            # Build the admin service using the same HTTP object that already has credentials
            admin_service = build('analyticsadmin', 'v1beta', http=http)
            
            # First, list all accounts the user has access to
            accounts_response = admin_service.accounts().list().execute()
            accounts = accounts_response.get('accounts', [])
            
            result = []
            for account in accounts:
                account_name = account.get('name')
                if account_name:
                    try:
                        # List properties for this account using the correct filter format
                        # The filter should be in the format "parent:accounts/123456"
                        properties_response = admin_service.properties().list(
                            filter=f"parent:{account_name}"
                        ).execute()
                        
                        properties = properties_response.get('properties', [])
                        for property in properties:
                            result.append({
                                'property_id': property.get('name', '').split('/')[-1],
                                'display_name': property.get('displayName', ''),
                                'create_time': property.get('createTime', ''),
                                'account': property.get('account', ''),
                                'property_type': property.get('propertyType', '')
                            })
                    except Exception as e:
                        logging.error(f"Error listing properties for account {account_name}: {str(e)}")
                        continue
            
            return result
        except Exception as e:
            logging.error(f"Error listing GA properties: {str(e)}")
            logging.error(traceback.format_exc())
            return []
    
    def run_report(self, property_id, date_range=None, metrics=None, dimensions=None, limit=10000):
        """
        Run a report on Google Analytics data.
        
        Args:
            property_id (str): The Google Analytics property ID (format: "properties/123456789")
            date_range (dict, optional): Date range for the report. Format: {'start_date': 'YYYY-MM-DD', 'end_date': 'YYYY-MM-DD'}
                                        If not provided, defaults to last 7 days.
            metrics (list, optional): List of metrics to include. Defaults to ['activeUsers']
            dimensions (list, optional): List of dimensions to include. Defaults to ['date']
            limit (int, optional): Maximum number of rows to return. Defaults to 10000.
            
        Returns:
            dict: The report data
        """
        try:
            # Set default date range to last 7 days if not provided
            if not date_range:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                date_range = {'start_date': start_date, 'end_date': end_date}
            
            # Set default metrics and dimensions if not provided
            if not metrics:
                metrics = ['activeUsers']
            if not dimensions:
                dimensions = ['date']
            
            # Format property ID if needed
            if not property_id.startswith('properties/'):
                property_id = f'properties/{property_id}'
            
            # Prepare request body
            request_body = {
                'dateRanges': [{
                    'startDate': date_range['start_date'],
                    'endDate': date_range['end_date']
                }],
                'metrics': [{'name': m} for m in metrics],
                'dimensions': [{'name': d} for d in dimensions],
                'limit': limit
            }
            
            # Execute the report
            response = self.service.properties().runReport(
                property=property_id,
                body=request_body
            ).execute()
            
            # Process the response
            result = {
                'property_id': property_id,
                'date_range': date_range,
                'dimensions_headers': [dim.get('name') for dim in response.get('dimensionHeaders', [])],
                'metrics_headers': [metric.get('name') for metric in response.get('metricHeaders', [])],
                'rows': []
            }
            
            # Process rows
            for row in response.get('rows', []):
                dimension_values = [dim.get('value') for dim in row.get('dimensionValues', [])]
                metric_values = [metric.get('value') for metric in row.get('metricValues', [])]
                
                result_row = {}
                
                # Add dimensions to result row
                for i, dim_name in enumerate(result['dimensions_headers']):
                    if i < len(dimension_values):
                        result_row[dim_name] = dimension_values[i]
                
                # Add metrics to result row
                for i, metric_name in enumerate(result['metrics_headers']):
                    if i < len(metric_values):
                        result_row[metric_name] = metric_values[i]
                
                result['rows'].append(result_row)
            
            return result
        except Exception as e:
            logging.error(f"Error running GA report: {str(e)}")
            logging.error(traceback.format_exc())
            return {'error': str(e), 'traceback': traceback.format_exc()} 