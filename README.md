# mcp-gsuite MCP server

MCP server to interact with Google.

## Example prompts

Right now, this MCP server only supports gmail and calendar. It supports the following functions:

- Retrieve my latest unread messages
- Search my emails from the Scrum Master
- Retrieve all emails from accounting
- Take the email about ABC and summarize it
- Write a nice response to Alice's last email and upload a draft.
- Reply to Bob's email with a Thank you note. Store it as draft

## Components

### Tools

The server implements multiple tools to interact with G-Suite. Right now, the following tools are implemented:

- Query emails from gmail (supports full G-mail query API)
- Get email content (by id)
- Create email draft
- Delete draft (by id)
- Reply to message (and optionally send it)

### Oauth2

Gsuite requires OAuth2 authorization. So you need to setup an Oauth2 client in the Google Auth platform and copy the client id and client secret. 

Right now, the server requires the following scopes on auth:

- `openid`
- `https://mail.google.com/`
- `https://www.googleapis.com/auth/calendar`

(Note: This should be finetuned as they are way too broad..)

Then create a `.gauth.json` in your working directory:

```
{
    "web": {
        "client_id": "$your_client_id",
        "client_secret": "$your_client_secret",
        "redirect_uris": ["http://localhost:4100/code"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}
```

When you first execute one of the tools, a browser will open, redirect you to Google and ask for your credentials, scope, etc. After a successful login, it stores the credentials in a local file called `oauth2creds.json`. From that one,
the refresh token will be used.

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  
```json
{
  "mcpServers": {
    "mcp-gsuite": {
      "command": "uv",
      "args": [
        "--directory",
        "<dir_to>/mcp-gsuite",
        "run",
        "mcp-gsuite"
      ]
    }
  }
}
```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  
```json
{
  "mcpServers": {
    "mcp-gsuite": {
      "command": "uvx",
      "args": [
        "mcp-gsuite"
      ]
    }
  }
}
```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-gsuite run mcp-gsuite
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

You can also watch the server logs with this command:

```bash
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-mcp-gsuite.log
```
