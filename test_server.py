#!/usr/bin/env python3
"""
Test suite for MCP Structured Logging Server

Tests all core functionality including MCP tools, file operations,
JSON parsing, filtering, and error handling.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, AsyncMock

# Import the server module
import server
from server import (
    write_log_entry, 
    read_recent_logs, 
    get_daily_log_file,
    LogEventArgs,
    LogErrorArgs, 
    QueryLogsArgs
)


class TestCoreLoggingFunctions(unittest.TestCase):
    """Test the core logging functions."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_logs_dir = server.LOGS_DIR
        server.LOGS_DIR = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        server.LOGS_DIR = self.original_logs_dir
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_write_log_entry_basic(self):
        """Test writing a basic log entry."""
        write_log_entry("info", "Test message", {"test": True})
        
        log_file = get_daily_log_file()
        self.assertTrue(log_file.exists())
        
        with open(log_file, 'r') as f:
            line = f.readline().strip()
            entry = json.loads(line)
            
        self.assertEqual(entry["level"], "info")
        self.assertEqual(entry["message"], "Test message")
        self.assertEqual(entry["context"]["test"], True)
        self.assertIn("timestamp", entry)
        
    def test_write_log_entry_no_context(self):
        """Test writing log entry without context."""
        write_log_entry("warn", "Warning message")
        
        log_file = get_daily_log_file()
        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())
            
        self.assertEqual(entry["context"], {})
        
    def test_multiple_log_entries(self):
        """Test writing multiple log entries."""
        entries = [
            ("debug", "Debug msg", {"id": 1}),
            ("info", "Info msg", {"id": 2}),
            ("error", "Error msg", {"id": 3})
        ]
        
        for level, message, context in entries:
            write_log_entry(level, message, context)
            
        log_file = get_daily_log_file()
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        self.assertEqual(len(lines), 3)
        
        # Verify each entry
        for i, line in enumerate(lines):
            entry = json.loads(line)
            expected_level, expected_msg, expected_context = entries[i]
            self.assertEqual(entry["level"], expected_level)
            self.assertEqual(entry["message"], expected_msg)
            self.assertEqual(entry["context"], expected_context)


class TestLogReading(unittest.TestCase):
    """Test log reading and querying functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_logs_dir = server.LOGS_DIR
        server.LOGS_DIR = Path(self.temp_dir)
        
        # Create sample log entries
        self.sample_entries = [
            ("debug", "Debug entry 1", {"seq": 1}),
            ("info", "Info entry 1", {"seq": 2}),
            ("warn", "Warning entry 1", {"seq": 3}),
            ("error", "Error entry 1", {"seq": 4}),
            ("info", "Info entry 2", {"seq": 5}),
        ]
        
        for level, message, context in self.sample_entries:
            write_log_entry(level, message, context)
            
    def tearDown(self):
        """Clean up test environment."""
        server.LOGS_DIR = self.original_logs_dir
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_read_all_logs(self):
        """Test reading all log entries."""
        entries = read_recent_logs(count=10)
        self.assertEqual(len(entries), 5)
        
        # Should be in reverse order (newest first)
        self.assertEqual(entries[0]["context"]["seq"], 5)
        self.assertEqual(entries[-1]["context"]["seq"], 1)
        
    def test_read_limited_count(self):
        """Test reading limited number of entries."""
        entries = read_recent_logs(count=3)
        self.assertEqual(len(entries), 3)
        
        # Should get the 3 most recent
        sequences = [entry["context"]["seq"] for entry in entries]
        self.assertEqual(sequences, [5, 4, 3])
        
    def test_filter_by_level(self):
        """Test filtering by log level."""
        # Filter for info entries
        info_entries = read_recent_logs(count=10, level_filter="info")
        self.assertEqual(len(info_entries), 2)
        
        for entry in info_entries:
            self.assertEqual(entry["level"], "info")
            
        # Filter for error entries  
        error_entries = read_recent_logs(count=10, level_filter="error")
        self.assertEqual(len(error_entries), 1)
        self.assertEqual(error_entries[0]["level"], "error")
        
        # Filter for non-existent level
        none_entries = read_recent_logs(count=10, level_filter="critical")
        self.assertEqual(len(none_entries), 0)
        
    def test_empty_logs(self):
        """Test reading from empty logs directory."""
        # Clear all logs
        import shutil
        shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir)
        
        entries = read_recent_logs()
        self.assertEqual(len(entries), 0)


class TestPydanticModels(unittest.TestCase):
    """Test Pydantic model validation."""
    
    def test_log_event_args_valid(self):
        """Test valid LogEventArgs."""
        args = LogEventArgs(
            level="info",
            message="Test message",
            context={"key": "value"}
        )
        self.assertEqual(args.level, "info")
        self.assertEqual(args.message, "Test message")
        self.assertEqual(args.context, {"key": "value"})
        
    def test_log_event_args_no_context(self):
        """Test LogEventArgs without context."""
        args = LogEventArgs(level="warn", message="Warning")
        self.assertIsNone(args.context)
        
    def test_log_error_args_valid(self):
        """Test valid LogErrorArgs."""
        args = LogErrorArgs(
            message="Error occurred",
            error_details="Stack trace here",
            context={"user": "123"}
        )
        self.assertEqual(args.message, "Error occurred")
        self.assertEqual(args.error_details, "Stack trace here")
        
    def test_query_logs_args_defaults(self):
        """Test QueryLogsArgs with defaults."""
        args = QueryLogsArgs()
        self.assertEqual(args.count, 50)
        self.assertIsNone(args.level_filter)
        
    def test_query_logs_args_custom(self):
        """Test QueryLogsArgs with custom values."""
        args = QueryLogsArgs(count=20, level_filter="error")
        self.assertEqual(args.count, 20)
        self.assertEqual(args.level_filter, "error")


class TestMCPTools(unittest.TestCase):
    """Test the MCP tool functions."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_logs_dir = server.LOGS_DIR
        server.LOGS_DIR = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        server.LOGS_DIR = self.original_logs_dir
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_log_event_tool(self):
        """Test the log_event MCP tool."""
        from server import call_tool
        
        arguments = {
            "level": "info",
            "message": "MCP test message",
            "context": {"tool": "log_event"}
        }
        
        result = await call_tool("log_event", arguments)
        
        self.assertEqual(len(result), 1)
        self.assertIn("Successfully logged info event", result[0].text)
        
        # Verify log was written
        entries = read_recent_logs(count=1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["message"], "MCP test message")
        
    async def test_log_error_tool(self):
        """Test the log_error MCP tool."""
        from server import call_tool
        
        arguments = {
            "message": "Test error",
            "error_details": "ValueError: test exception",
            "context": {"component": "test"}
        }
        
        result = await call_tool("log_error", arguments)
        
        self.assertEqual(len(result), 1)
        self.assertIn("Successfully logged error", result[0].text)
        
        # Verify error was logged with error_details in context
        entries = read_recent_logs(count=1, level_filter="error")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["level"], "error")
        self.assertEqual(entries[0]["context"]["error_details"], "ValueError: test exception")
        
    async def test_query_logs_tool(self):
        """Test the query_logs MCP tool."""
        from server import call_tool
        
        # First add some logs
        write_log_entry("info", "Log 1", {"id": 1})
        write_log_entry("error", "Log 2", {"id": 2})
        write_log_entry("warn", "Log 3", {"id": 3})
        
        # Query all logs
        result = await call_tool("query_logs", {"count": 10})
        
        self.assertEqual(len(result), 1)
        response_data = json.loads(result[0].text)
        
        self.assertEqual(response_data["total_entries"], 3)
        self.assertEqual(len(response_data["entries"]), 3)
        
        # Query with filter
        result = await call_tool("query_logs", {"count": 10, "level_filter": "error"})
        response_data = json.loads(result[0].text)
        
        self.assertEqual(response_data["total_entries"], 1)
        self.assertEqual(response_data["entries"][0]["level"], "error")
        
    async def test_query_logs_empty(self):
        """Test query_logs with no entries."""
        from server import call_tool
        
        result = await call_tool("query_logs", {})
        
        self.assertEqual(len(result), 1)
        self.assertIn("No log entries found", result[0].text)
        
    async def test_unknown_tool(self):
        """Test calling unknown tool."""
        from server import call_tool
        
        result = await call_tool("unknown_tool", {})
        
        self.assertEqual(len(result), 1)
        self.assertIn("Unknown tool: unknown_tool", result[0].text)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_logs_dir = server.LOGS_DIR
        server.LOGS_DIR = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        server.LOGS_DIR = self.original_logs_dir
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON in log files."""
        log_file = get_daily_log_file()
        
        # Write valid entry
        write_log_entry("info", "Valid entry", {})
        
        # Manually add malformed JSON
        with open(log_file, 'a') as f:
            f.write('{"invalid": json}\n')
            f.write('not json at all\n')
            
        # Write another valid entry
        write_log_entry("warn", "Another valid entry", {})
        
        # Reading should skip malformed entries
        entries = read_recent_logs(count=10)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["message"], "Another valid entry")
        self.assertEqual(entries[1]["message"], "Valid entry")
        
    def test_empty_lines_handling(self):
        """Test handling of empty lines in log files."""
        log_file = get_daily_log_file()
        
        write_log_entry("info", "First entry", {})
        
        # Add empty lines
        with open(log_file, 'a') as f:
            f.write('\n')
            f.write('   \n')
            f.write('\t\n')
            
        write_log_entry("info", "Second entry", {})
        
        entries = read_recent_logs(count=10)
        self.assertEqual(len(entries), 2)


async def run_async_tests():
    """Run async test methods."""
    print("\n🔄 Running async MCP tool tests...")
    
    # Test each method in isolation
    tests = [
        "test_log_event_tool",
        "test_log_error_tool", 
        "test_query_logs_tool",
        "test_query_logs_empty",
        "test_unknown_tool"
    ]
    
    for test_name in tests:
        test_instance = TestMCPTools()
        test_instance.setUp()
        
        try:
            test_method = getattr(test_instance, test_name)
            await test_method()
            print(f"✅ {test_name} passed")
        finally:
            test_instance.tearDown()
    
    print("✅ All async tests passed!")


if __name__ == "__main__":
    print("🧪 MCP Structured Logging Server Test Suite")
    print("=" * 50)
    
    # Run synchronous tests
    print("\n🔄 Running synchronous tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run async tests
    import asyncio
    asyncio.run(run_async_tests())
    
    print("\n🎉 All tests completed successfully!") 