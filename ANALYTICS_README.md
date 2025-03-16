# Google Analytics Data Access

This document provides instructions on how to use the Google Analytics scripts to check URLs and other data for specific properties.

## Prerequisites

1. Make sure you have built and installed the package:
   ```
   uv build
   pip install dist/mcp_gsuite-0.4.5-py3-none-any.whl --force-reinstall
   ```

2. Ensure you have proper OAuth credentials with the following scopes:
   - `https://www.googleapis.com/auth/analytics.readonly`
   - `https://www.googleapis.com/auth/analytics.edit`

3. Make sure the following APIs are enabled in your Google Cloud project:
   - Google Analytics Data API
   - Google Analytics Admin API

## Basic URL Checking

To check URLs for a specific property (like zimtra.com with ID 319959269), use the `check_urls.py` script:

```bash
./check_urls.py --user-id your.email@example.com --property-id 319959269
```

This will retrieve the most viewed URLs (page paths) for the property over the last 30 days.

## Advanced Analytics Data

For more advanced analytics data, use the `check_analytics_data.py` script which supports different report types:

### URL Report (Default)
```bash
./check_analytics_data.py --user-id your.email@example.com --property-id 319959269
```

### Pages Report (URLs with Titles)
```bash
./check_analytics_data.py --user-id your.email@example.com --property-id 319959269 --report-type pages
```

### Referrers Report
```bash
./check_analytics_data.py --user-id your.email@example.com --property-id 319959269 --report-type referrers
```

### Custom Report
You can also create custom reports by specifying your own metrics and dimensions:

```bash
./check_analytics_data.py --user-id your.email@example.com --property-id 319959269 --report-type custom --metrics "screenPageViews,totalUsers" --dimensions "pagePath,deviceCategory"
```

## Additional Options

Both scripts support additional options:

- `--start-date YYYY-MM-DD`: Specify a custom start date (defaults to 30 days ago)
- `--end-date YYYY-MM-DD`: Specify a custom end date (defaults to today)
- `--limit N`: Limit the number of results (default is 100)
- `--output-file filename.json`: Specify a custom output file for the JSON report

## Available Metrics and Dimensions

Here are some commonly used metrics and dimensions for Google Analytics 4:

### Metrics
- `screenPageViews`: Number of app screens or web pages viewed
- `totalUsers`: Total number of users
- `newUsers`: Number of first-time users
- `activeUsers`: Number of active users
- `sessions`: Number of sessions
- `engagementRate`: The percentage of engaged sessions
- `averageSessionDuration`: Average session duration
- `conversions`: Total number of conversions

### Dimensions
- `pagePath`: The path portion of the URL
- `pageTitle`: The title of the page
- `sessionSource`: The source of the session (e.g., "google", "direct")
- `sessionMedium`: The medium of the session (e.g., "organic", "cpc")
- `deviceCategory`: The device category (e.g., "mobile", "desktop", "tablet")
- `country`: The country from which sessions originated
- `browser`: The browser used
- `operatingSystem`: The operating system used

For a complete list of metrics and dimensions, refer to the [Google Analytics Data API documentation](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema).

## Troubleshooting

If you encounter errors:

1. Make sure you have the correct property ID
2. Verify that you have access to the property in Google Analytics
3. Check that the required APIs are enabled in your Google Cloud project
4. Ensure your OAuth credentials have the necessary scopes
5. Try reauthorizing with `./reauthorize.py --user-id your.email@example.com` 