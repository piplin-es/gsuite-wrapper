import asyncio
from .server import app

def main():
    """Entry point for MCP server"""
    from .server import main
    asyncio.run(main())

# Optionally expose other important items at package level
__all__ = ['main', 'app']