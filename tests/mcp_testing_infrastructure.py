# Comprehensive Testing Infrastructure for MCP System
# Unit tests, integration tests, and performance tests

import unittest
import asyncio
import json
import time
import logging
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any, Optional
import pytest
import aiohttp
from dataclasses import dataclass
from datetime import datetime

# Test configuration
@dataclass
class TestConfig:
    """Test configuration settings"""
    test_server_url: str = "http://localhost:3000"
    test_timeout: int = 30
    performance_threshold: float = 5.0  # seconds
    memory_threshold: int = 100  # MB
    concurrent_users: int = 10
    test_data_path: str = "./test_data"

class MCPTestBase(unittest.TestCase):
    """Base test class with common utilities"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = TestConfig()
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        
    def tearDown(self):
        """Clean up after tests"""
        duration = time.time() - self.start_time
        self.logger.info(f"Test completed in {duration:.2f}s")
    
    def assert_performance(self, duration: float, threshold: float = None):
        """Assert performance meets threshold"""
        threshold = threshold or self.config.performance_threshold
        self.assertLess(
            duration, 
            threshold, 
            f"Performance threshold exceeded: {duration:.2f}s > {threshold}s"
        )
    
    def assert_valid_json(self, data: str):
        """Assert string is valid JSON"""
        try:
            json.loads(data)
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON: {e}")
    
    def assert_has_keys(self, data: Dict, required_keys: List[str]):
        """Assert dictionary has required keys"""
        missing_keys = [key for key in required_keys if key not in data]
        self.assertEqual(
            len(missing_keys), 
            0, 
            f"Missing required keys: {missing_keys}"
        )

class AttendeeIntegrationTests(MCPTestBase):
    """Test suite for Attendee Integration components"""
    
    def setUp(self):
        super().setUp()
        # Import components to test
        from attendee_integration.dispatchers.attendee_dispatcher import AttendeeDispatcher
        from attendee_integration.formatters.attendee_formatter import AttendeeFormatter
        
        self.dispatcher = AttendeeDispatcher()
        self.formatter = AttendeeFormatter()
        
        # Test data
        self.test_meeting = {
            "id": 1,
            "title": "Test Meeting",
            "date": "2025-06-20",
            "duration": "30 min",
            "participants": ["Alice", "Bob", "Charlie"],
            "status": "processed",
            "transcription": "This is a test meeting transcription.",
            "actions": [
                {
                    "id": 1,
                    "text": "Complete unit tests",
                    "assignee": "Alice",
                    "priority": "high",
                    "deadline": "2025-06-25",
                    "status": "pending"
                },
                {
                    "id": 2,
                    "text": "Review documentation",
                    "assignee": "Bob",
                    "priority": "medium",
                    "deadline": "2025-06-27",
                    "status": "pending"
                }
            ]
        }
    
    def test_dispatcher_initialization(self):
        """Test dispatcher initializes correctly"""
        self.assertIsNotNone(self.dispatcher)
        self.assertEqual(self.dispatcher.config['autoDispatch'], True)
        self.assertEqual(len(self.dispatcher.queue), 0)
    
    def test_add_action_to_queue(self):
        """Test adding action to dispatch queue"""
        action = self.test_meeting['actions'][0]
        action_id = self.dispatcher.addAction(action)
        
        self.assertIsNotNone(action_id)
        self.assertEqual(len(self.dispatcher.queue), 1)
        self.assertEqual(self.dispatcher.queue[0]['text'], action['text'])
    
    def test_queue_status(self):
        """Test queue status reporting"""
        # Add test actions
        for action in self.test_meeting['actions']:
            self.dispatcher.addAction(action)
        
        status = self.dispatcher.getQueueStatus()
        
        self.assert_has_keys(status, ['total', 'processing', 'statusCounts'])
        self.assertEqual(status['total'], 2)
    
    def test_formatter_markdown_output(self):
        """Test markdown formatting"""
        result = self.formatter.format(self.test_meeting, 'markdown', 'meeting')
        
        self.assertIsInstance(result, str)
        self.assertIn(self.test_meeting['title'], result)
        self.assertIn('## Participants', result)
        self.assertIn('## Action Items', result)
    
    def test_formatter_json_output(self):
        """Test JSON formatting"""
        result = self.formatter.format(self.test_meeting, 'json', 'meeting')
        
        self.assert_valid_json(result)
        parsed = json.loads(result)
        self.assertEqual(parsed['title'], self.test_meeting['title'])
    
    def test_formatter_html_output(self):
        """Test HTML formatting"""
        result = self.formatter.format(self.test_meeting, 'html', 'meeting')
        
        self.assertIsInstance(result, str)
        self.assertIn('<html>', result)
        self.assertIn('<title>', result)
        self.assertIn(self.test_meeting['title'], result)
    
    def test_formatter_csv_actions(self):
        """Test CSV formatting for actions"""
        result = self.formatter.format(self.test_meeting, 'csv', 'actions')
        
        self.assertIsInstance(result, str)
        lines = result.split('\n')
        self.assertGreater(len(lines), 1)  # Header + data
        self.assertIn('Text,Assignee,Priority', lines[0])
    
    def test_formatter_invalid_format(self):
        """Test handling of invalid format"""
        with self.assertRaises(Exception):
            self.formatter.format(self.test_meeting, 'invalid_format', 'meeting')
    
    @patch('attendee_integration.dispatchers.attendee_dispatcher.AttendeeDispatcher.sendToAssignee')
    async def test_dispatcher_async_processing(self, mock_send):
        """Test asynchronous dispatch processing"""
        mock_send.return_value = {"success": True}
        
        # Add action and process
        action = self.test_meeting['actions'][0]
        self.dispatcher.addAction(action)
        
        await self.dispatcher.processQueue()
        
        # Verify dispatch was called
        mock_send.assert_called_once()
        
        # Check queue status
        status = self.dispatcher.getQueueStatus()
        dispatched_count = status['statusCounts'].get('dispatched', 0)
        self.assertGreater(dispatched_count, 0)

class LangGraphAgentTests(MCPTestBase):
    """Test suite for LangGraph Agent components"""
    
    def setUp(self):
        super().setUp()
        # Mock imports since we may not have all dependencies
        self.mock_agent_config = {
            'llm_provider': 'openai',
            'model': 'gpt-4',
            'temperature': 0.1
        }
    
    @patch('langgraph_system.agents.complete_mcp_agent.ChatOpenAI')
    def test_agent_initialization(self, mock_llm):
        """Test agent initializes correctly"""
        from langgraph_system.agents.complete_mcp_agent import CompleteMCPAgent
        
        agent = CompleteMCPAgent(self.mock_agent_config)
        
        self.assertIsNotNone(agent)
        self.assertIsNotNone(agent.graph)
        mock_llm.assert_called_once()
    
    @patch('langgraph_system.agents.complete_mcp_agent.ChatOpenAI')
    async def test_agent_task_execution(self, mock_llm):
        """Test agent task execution flow"""
        from langgraph_system.agents.complete_mcp_agent import CompleteMCPAgent
        
        # Mock LLM responses
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value.content = json.dumps({
            "task_type": "code",
            "complexity": "low",
            "required_tools": [],
            "estimated_steps": 2,
            "confidence_assessment": 0.8
        })
        mock_llm.return_value = mock_llm_instance
        
        agent = CompleteMCPAgent(self.mock_agent_config)
        
        start_time = time.time()
        result = await agent.execute_task("Create a simple function")
        duration = time.time() - start_time
        
        # Verify result structure
        self.assert_has_keys(result, ['success', 'confidence', 'results', 'reasoning'])
        self.assert_performance(duration)
    
    @patch('langgraph_system.agents.optimized_mcp_agent.ChatOpenAI')
    async def test_optimized_agent_performance(self, mock_llm):
        """Test optimized agent performance"""
        from langgraph_system.agents.optimized_mcp_agent import OptimizedMCPAgent
        
        # Mock LLM responses
        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.return_value.content = json.dumps({
            "task_type": "code",
            "complexity": "low",
            "required_tools": [],
            "estimated_steps": 1,
            "confidence_assessment": 0.9,
            "optimization_level": "fast"
        })
        mock_llm.return_value = mock_llm_instance
        
        agent = OptimizedMCPAgent(self.mock_agent_config)
        
        start_time = time.time()
        result = await agent.execute_task(
            "Simple task", 
            {"optimization_level": "fast"}
        )
        duration = time.time() - start_time
        
        # Verify performance improvements
        self.assert_has_keys(result, ['success', 'confidence', 'performance'])
        self.assertIn('total_time', result['performance'])
        self.assert_performance(duration, threshold=2.0)  # Stricter for optimized

class MCPBackendTests(MCPTestBase):
    """Test suite for MCP Backend components"""
    
    def setUp(self):
        super().setUp()
        self.test_server_url = self.config.test_server_url
    
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.test_server_url}/health") as response:
                    self.assertEqual(response.status, 200)
                    data = await response.json()
                    self.assert_has_keys(data, ['status', 'timestamp'])
            except aiohttp.ClientError:
                self.skipTest("Backend server not available")
    
    async def test_adapters_endpoint(self):
        """Test adapters listing endpoint"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.test_server_url}/api/adapters") as response:
                    self.assertEqual(response.status, 200)
                    data = await response.json()
                    self.assertIsInstance(data, (list, dict))
            except aiohttp.ClientError:
                self.skipTest("Backend server not available")
    
    async def test_tools_endpoint(self):
        """Test tools listing endpoint"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.test_server_url}/api/tools") as response:
                    self.assertEqual(response.status, 200)
                    data = await response.json()
                    self.assertIsInstance(data, (list, dict))
            except aiohttp.ClientError:
                self.skipTest("Backend server not available")

class PerformanceTests(MCPTestBase):
    """Performance and load testing"""
    
    def setUp(self):
        super().setUp()
        self.concurrent_users = self.config.concurrent_users
    
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        async def make_request(session, url):
            start_time = time.time()
            try:
                async with session.get(url) as response:
                    await response.text()
                    return time.time() - start_time
            except Exception as e:
                return None
        
        url = f"{self.config.test_server_url}/health"
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                make_request(session, url) 
                for _ in range(self.concurrent_users)
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Analyze results
            successful_requests = [r for r in results if isinstance(r, float)]
            
            if successful_requests:
                avg_response_time = sum(successful_requests) / len(successful_requests)
                self.assert_performance(avg_response_time, threshold=1.0)
                self.assert_performance(total_time, threshold=10.0)
                
                self.logger.info(f"Concurrent test: {len(successful_requests)}/{self.concurrent_users} successful")
                self.logger.info(f"Average response time: {avg_response_time:.2f}s")
            else:
                self.skipTest("No successful requests in concurrent test")
    
    async def test_memory_usage(self):
        """Test memory usage during operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate memory-intensive operations
        large_data = []
        for i in range(1000):
            large_data.append({
                "id": i,
                "data": "x" * 1000,
                "timestamp": datetime.now().isoformat()
            })
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Clean up
        del large_data
        
        self.assertLess(
            memory_increase, 
            self.config.memory_threshold,
            f"Memory usage too high: {memory_increase:.2f}MB"
        )

class IntegrationTests(MCPTestBase):
    """End-to-end integration tests"""
    
    async def test_full_attendee_workflow(self):
        """Test complete attendee workflow"""
        # This would test the full flow from meeting upload to action dispatch
        # Skipped if components not available
        try:
            from attendee_integration.dispatchers.attendee_dispatcher import AttendeeDispatcher
            from attendee_integration.formatters.attendee_formatter import AttendeeFormatter
            
            dispatcher = AttendeeDispatcher()
            formatter = AttendeeFormatter()
            
            # Test data
            meeting_data = {
                "title": "Integration Test Meeting",
                "participants": ["Test User 1", "Test User 2"],
                "transcription": "Test transcription content",
                "actions": [
                    {
                        "text": "Test action",
                        "assignee": "Test User 1",
                        "priority": "medium",
                        "deadline": "2025-06-30"
                    }
                ]
            }
            
            # Format meeting
            formatted = formatter.format(meeting_data, 'markdown', 'meeting')
            self.assertIsInstance(formatted, str)
            
            # Dispatch actions
            for action in meeting_data['actions']:
                action_id = dispatcher.addAction(action)
                self.assertIsNotNone(action_id)
            
            # Verify queue
            status = dispatcher.getQueueStatus()
            self.assertGreater(status['total'], 0)
            
        except ImportError:
            self.skipTest("Attendee integration components not available")

# Test utilities
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def generate_meeting_data(num_participants: int = 3, num_actions: int = 5) -> Dict:
        """Generate realistic meeting data"""
        return {
            "id": 1,
            "title": f"Test Meeting {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "duration": "45 min",
            "participants": [f"Participant {i+1}" for i in range(num_participants)],
            "status": "processed",
            "transcription": "This is a generated test meeting transcription with various discussion points.",
            "actions": [
                {
                    "id": i+1,
                    "text": f"Test action {i+1}",
                    "assignee": f"Participant {(i % num_participants) + 1}",
                    "priority": ["low", "medium", "high"][i % 3],
                    "deadline": (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                    "status": "pending"
                }
                for i in range(num_actions)
            ]
        }
    
    @staticmethod
    def generate_agent_task(complexity: str = "medium") -> str:
        """Generate agent task based on complexity"""
        tasks = {
            "low": "Calculate the sum of numbers 1 to 10",
            "medium": "Create a function to sort a list of dictionaries by a specific key",
            "high": "Design and implement a simple web application with user authentication"
        }
        return tasks.get(complexity, tasks["medium"])

# Test runner configuration
class MCPTestRunner:
    """Custom test runner with reporting"""
    
    def __init__(self, config: TestConfig = None):
        self.config = config or TestConfig()
        self.results = {}
    
    async def run_all_tests(self):
        """Run all test suites"""
        test_suites = [
            AttendeeIntegrationTests,
            LangGraphAgentTests,
            MCPBackendTests,
            PerformanceTests,
            IntegrationTests
        ]
        
        for suite_class in test_suites:
            suite_name = suite_class.__name__
            print(f"\n{'='*50}")
            print(f"Running {suite_name}")
            print(f"{'='*50}")
            
            suite = unittest.TestLoader().loadTestsFromTestCase(suite_class)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            self.results[suite_name] = {
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0
            }
    
    def generate_report(self) -> str:
        """Generate test report"""
        report = "\n" + "="*60 + "\n"
        report += "MCP SYSTEM TEST REPORT\n"
        report += "="*60 + "\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"
        
        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_skipped = 0
        
        for suite_name, results in self.results.items():
            report += f"{suite_name}:\n"
            report += f"  Tests Run: {results['tests_run']}\n"
            report += f"  Failures: {results['failures']}\n"
            report += f"  Errors: {results['errors']}\n"
            report += f"  Skipped: {results['skipped']}\n\n"
            
            total_tests += results['tests_run']
            total_failures += results['failures']
            total_errors += results['errors']
            total_skipped += results['skipped']
        
        report += "-" * 60 + "\n"
        report += f"TOTAL SUMMARY:\n"
        report += f"  Total Tests: {total_tests}\n"
        report += f"  Total Failures: {total_failures}\n"
        report += f"  Total Errors: {total_errors}\n"
        report += f"  Total Skipped: {total_skipped}\n"
        
        success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        report += f"  Success Rate: {success_rate:.1f}%\n"
        
        return report

# Main execution
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    async def main():
        runner = MCPTestRunner()
        await runner.run_all_tests()
        
        report = runner.generate_report()
        print(report)
        
        # Save report
        with open(f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w") as f:
            f.write(report)
    
    # Execute
    asyncio.run(main())

