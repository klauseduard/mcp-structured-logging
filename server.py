#!/usr/bin/env python3
"""
Simple MCP Structured Logging Server

A minimal MCP server that lets AI agents log structured events to files 
and query recent logs using JSON Lines format.
"""

import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
from pydantic import BaseModel


# Pydantic models for validation
class LogEventArgs(BaseModel):
    level: str
    message: str
    context: Optional[Dict[str, Any]] = None


class LogErrorArgs(BaseModel):
    message: str
    error_details: str
    context: Optional[Dict[str, Any]] = None


class QueryLogsArgs(BaseModel):
    count: Optional[int] = 50
    level_filter: Optional[str] = None


# Global server instance
server = Server("structured-logging")

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


def get_daily_log_file() -> Path:
    """Get the log file path for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    return LOGS_DIR / f"{today}.jsonl"


def write_log_entry(level: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Write a structured log entry to today's log file."""
    log_entry = {
        "timestamp": datetime.now().isoformat() + "Z",
        "level": level,
        "message": message,
        "context": context or {}
    }
    
    log_file = get_daily_log_file()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


def read_recent_logs(count: int = 50, level_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read recent log entries from all log files."""
    all_entries = []
    
    # Get all log files sorted by name (newest first)
    log_files = sorted(LOGS_DIR.glob("*.jsonl"), reverse=True)
    
    for log_file in log_files:
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            # Parse JSON lines in reverse order (newest first)
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    entry = json.loads(line)
                    
                    # Apply level filter if specified
                    if level_filter and entry.get("level") != level_filter:
                        continue
                        
                    all_entries.append(entry)
                    
                    # Stop if we have enough entries
                    if len(all_entries) >= count:
                        return all_entries
                        
                except json.JSONDecodeError:
                    # Skip malformed JSON lines
                    continue
                    
        except (IOError, OSError):
            # Skip files that can't be read
            continue
    
    return all_entries


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="log_event",
            description="Write a structured log entry to the daily log file",
            inputSchema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "Log level (e.g., 'info', 'warn', 'error', 'debug')",
                        "enum": ["debug", "info", "warn", "error"]
                    },
                    "message": {
                        "type": "string",
                        "description": "The main log message"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional structured context data",
                        "additionalProperties": True
                    }
                },
                "required": ["level", "message"]
            }
        ),
        Tool(
            name="log_error",
            description="Log an error with stack trace information",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Error message description"
                    },
                    "error_details": {
                        "type": "string",
                        "description": "Detailed error information or stack trace"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context about when/where the error occurred",
                        "additionalProperties": True
                    }
                },
                "required": ["message", "error_details"]
            }
        ),
        Tool(
            name="query_logs",
            description="Query recent log entries from the log files",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of recent entries to return (default: 50)",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 1000
                    },
                    "level_filter": {
                        "type": "string",
                        "description": "Filter by log level (optional)",
                        "enum": ["debug", "info", "warn", "error"]
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "log_event":
            args = LogEventArgs(**arguments)
            write_log_entry(args.level, args.message, args.context)
            return [TextContent(
                type="text",
                text=f"Successfully logged {args.level} event: {args.message}"
            )]
            
        elif name == "log_error":
            args = LogErrorArgs(**arguments)
            # Add error details to context
            error_context = args.context or {}
            error_context["error_details"] = args.error_details
            write_log_entry("error", args.message, error_context)
            return [TextContent(
                type="text",
                text=f"Successfully logged error: {args.message}"
            )]
            
        elif name == "query_logs":
            args = QueryLogsArgs(**arguments)
            entries = read_recent_logs(args.count, args.level_filter)
            
            if not entries:
                return [TextContent(
                    type="text",
                    text="No log entries found matching the criteria."
                )]
            
            # Format the response
            result = {
                "total_entries": len(entries),
                "entries": entries
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        error_msg = f"Error executing tool '{name}': {str(e)}"
        # Log the error to our own logs
        try:
            write_log_entry("error", f"MCP tool error: {name}", {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "arguments": arguments
            })
        except:
            pass  # Don't fail if we can't log the error
            
        return [TextContent(
            type="text",
            text=error_msg
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 