#!/usr/bin/env python3
"""
Test Script for Phase 2: MCP Core Implementation

This script tests the MCP (Master Control Program) core functionality:
- Task Coordinator DAG execution
- Message Broker routing
- State Manager persistence
- MCP API endpoints

Usage:
    python test-scripts/test_phase2_mcp_core.py
"""

import asyncio
import sys
import time
import json
import logging
import requests
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase2MCPTest:
    """Test suite for Phase 2 MCP core components"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.base_url = "http://localhost:8003"
        self.test_task_id: str = ""
        
    def run_all_tests(self) -> bool:
        """Run all Phase 2 tests"""
        logger.info("🚀 Starting Phase 2 MCP Core Tests...")
        
        tests = [
            ("MCP Container Health", self.test_mcp_health),
            ("MCP Service Capabilities", self.test_mcp_capabilities),
            ("Task Creation API", self.test_task_creation),
            ("Task Status Tracking", self.test_task_status),
            ("Task Progress Monitoring", self.test_task_progress),
            ("Queue Status API", self.test_queue_status),
            ("System Status API", self.test_system_status),
            ("Analytics APIs", self.test_analytics_apis),
            ("Task Abort Functionality", self.test_task_abort),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Testing {test_name} ---")
            try:
                result = test_func()
                self.results[test_name] = {
                    'status': 'PASS' if result else 'FAIL',
                    'details': result if isinstance(result, dict) else {'success': result}
                }
                if result:
                    logger.info(f"✅ {test_name}: PASSED")
                    passed += 1
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {str(e)}")
                self.results[test_name] = {
                    'status': 'ERROR',
                    'details': {'error': str(e)}
                }
        
        # Print summary
        self.print_summary(passed, total)
        return passed == total
    
    def test_mcp_health(self) -> bool:
        """Test MCP container health check"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check required fields
                required_fields = ["status", "service", "version"]
                for field in required_fields:
                    if field not in health_data:
                        logger.error(f"Missing required field: {field}")
                        return False
                
                # Check service identification
                if health_data["service"] != "mcp":
                    logger.error(f"Expected service 'mcp', got '{health_data['service']}'")
                    return False
                
                # Check version
                if health_data["version"] != "3.0.0":
                    logger.error(f"Expected version '3.0.0', got '{health_data['version']}'")
                    return False
                
                logger.info(f"MCP Health: {health_data['status']}")
                return health_data["status"] == "healthy"
            else:
                logger.error(f"Health check failed with status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Health check request failed: {e}")
            return False
    
    def test_mcp_capabilities(self) -> bool:
        """Test MCP capabilities endpoint"""
        try:
            response = requests.get(f"{self.base_url}/capabilities", timeout=10)
            
            if response.status_code == 200:
                capabilities = response.json()
                
                # Check required capability categories
                required_categories = [
                    "task_coordination",
                    "messaging", 
                    "information_quality",
                    "intent_analysis",
                    "agent_management"
                ]
                
                for category in required_categories:
                    if category not in capabilities:
                        logger.error(f"Missing capability category: {category}")
                        return False
                
                # Check specific capabilities
                if not capabilities.get("task_coordination", {}).get("dag_execution"):
                    logger.error("DAG execution capability not found")
                    return False
                
                if not capabilities.get("messaging", {}).get("rabbitmq_queues"):
                    logger.error("RabbitMQ queues capability not found")
                    return False
                
                logger.info(f"Capabilities verified: {len(capabilities)} categories")
                return True
            else:
                logger.error(f"Capabilities check failed with status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Capabilities request failed: {e}")
            return False
    
    def test_task_creation(self) -> bool:
        """Test task creation API"""
        try:
            task_request = {
                "user_id": "test_user_phase2",
                "query": "Test query for Phase 2 MCP testing",
                "template": "simple_lookup",
                "conversation_id": "test_conversation_phase2"
            }
            
            response = requests.post(
                f"{self.base_url}/tasks/create",
                json=task_request,
                timeout=15
            )
            
            if response.status_code == 200:
                task_response = response.json()
                
                # Check required fields
                required_fields = ["task_id", "status", "template", "user_id"]
                for field in required_fields:
                    if field not in task_response:
                        logger.error(f"Missing required field in task response: {field}")
                        return False
                
                # Store task ID for subsequent tests
                self.test_task_id = task_response["task_id"]
                
                # Verify response fields
                if task_response["status"] != "created":
                    logger.error(f"Expected status 'created', got '{task_response['status']}'")
                    return False
                
                if task_response["template"] != "simple_lookup":
                    logger.error(f"Expected template 'simple_lookup', got '{task_response['template']}'")
                    return False
                
                logger.info(f"Task created: {self.test_task_id}")
                return True
            else:
                logger.error(f"Task creation failed with status {response.status_code}")
                if response.text:
                    logger.error(f"Response: {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Task creation request failed: {e}")
            return False
    
    def test_task_status(self) -> bool:
        """Test task status retrieval"""
        if not self.test_task_id:
            logger.error("No test task ID available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/tasks/{self.test_task_id}/status",
                timeout=10
            )
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Check required fields
                required_fields = [
                    "task_id", "status", "progress_percentage",
                    "started_at", "updated_at", "template", "plan"
                ]
                
                for field in required_fields:
                    if field not in status_data:
                        logger.error(f"Missing required field in status response: {field}")
                        return False
                
                # Verify task ID matches
                if status_data["task_id"] != self.test_task_id:
                    logger.error(f"Task ID mismatch: expected {self.test_task_id}, got {status_data['task_id']}")
                    return False
                
                # Verify status is valid
                valid_statuses = ["in_progress", "complete", "failed", "aborted"]
                if status_data["status"] not in valid_statuses:
                    logger.error(f"Invalid status: {status_data['status']}")
                    return False
                
                logger.info(f"Task status: {status_data['status']} ({status_data['progress_percentage']}%)")
                return True
                
            elif response.status_code == 404:
                logger.error("Task not found - may not have been persisted")
                return False
            else:
                logger.error(f"Status check failed with status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Status request failed: {e}")
            return False
    
    def test_task_progress(self) -> bool:
        """Test task progress monitoring"""
        if not self.test_task_id:
            logger.error("No test task ID available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/tasks/{self.test_task_id}/progress",
                timeout=10
            )
            
            if response.status_code == 200:
                progress_data = response.json()
                
                # Check required fields
                required_fields = [
                    "task_id", "status", "progress_percentage",
                    "thinking_steps", "total_stages", "completed_stages"
                ]
                
                for field in required_fields:
                    if field not in progress_data:
                        logger.error(f"Missing required field in progress response: {field}")
                        return False
                
                # Verify thinking steps structure
                thinking_steps = progress_data["thinking_steps"]
                if not isinstance(thinking_steps, list):
                    logger.error("Thinking steps should be a list")
                    return False
                
                logger.info(f"Progress: {progress_data['progress_percentage']}%, {len(thinking_steps)} thinking steps")
                return True
                
            elif response.status_code == 404:
                logger.error("Task not found for progress check")
                return False
            else:
                logger.error(f"Progress check failed with status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Progress request failed: {e}")
            return False
    
    def test_queue_status(self) -> bool:
        """Test queue status API"""
        try:
            response = requests.get(f"{self.base_url}/queues/status", timeout=10)
            
            if response.status_code == 200:
                queue_data = response.json()
                
                # Check required fields
                if "queues" not in queue_data or "total_queues" not in queue_data:
                    logger.error("Missing required fields in queue status response")
                    return False
                
                queues = queue_data["queues"]
                if not isinstance(queues, list):
                    logger.error("Queues should be a list")
                    return False
                
                # Check that we have the expected queues
                expected_queues = [
                    "intent.task", "embedding.task", "executor.task",
                    "moderator.task", "websearch.task", "mcp.responses"
                ]
                
                found_queues = [q.get("name") for q in queues if "name" in q]
                
                for expected_queue in expected_queues:
                    if expected_queue not in found_queues:
                        logger.warning(f"Expected queue not found: {expected_queue}")
                
                logger.info(f"Queue status: {len(queues)} queues found")
                return True
                
            else:
                logger.error(f"Queue status failed with status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Queue status request failed: {e}")
            return False
    
    def test_system_status(self) -> bool:
        """Test system status API"""
        try:
            response = requests.get(f"{self.base_url}/system/status", timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Check required fields
                required_fields = ["mcp", "services", "infrastructure"]
                for field in required_fields:
                    if field not in status_data:
                        logger.error(f"Missing required field in system status: {field}")
                        return False
                
                # Check MCP info
                mcp_info = status_data["mcp"]
                if mcp_info.get("version") != "3.0.0":
                    logger.error(f"Expected MCP version 3.0.0, got {mcp_info.get('version')}")
                    return False
                
                # Check services
                services = status_data["services"]
                expected_services = [
                    "task_coordinator", "message_broker", "state_manager",
                    "quality_analyzer", "intent_ai"
                ]
                
                for service in expected_services:
                    if service not in services:
                        logger.error(f"Missing service in status: {service}")
                        return False
                
                logger.info(f"System status: {status_data['mcp']['status']}")
                return True
                
            else:
                logger.error(f"System status failed with status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"System status request failed: {e}")
            return False
    
    def test_analytics_apis(self) -> bool:
        """Test analytics APIs"""
        try:
            # Test task analytics
            response = requests.get(f"{self.base_url}/analytics/tasks?hours=1", timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Task analytics failed with status {response.status_code}")
                return False
            
            task_analytics = response.json()
            if "period" not in task_analytics:
                logger.error("Missing period in task analytics")
                return False
            
            # Test agent analytics
            response = requests.get(f"{self.base_url}/analytics/agents?hours=1", timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Agent analytics failed with status {response.status_code}")
                return False
            
            agent_analytics = response.json()
            if "period" not in agent_analytics:
                logger.error("Missing period in agent analytics")
                return False
            
            logger.info("Analytics APIs working")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Analytics request failed: {e}")
            return False
    
    def test_task_abort(self) -> bool:
        """Test task abort functionality"""
        if not self.test_task_id:
            logger.error("No test task ID available")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/tasks/{self.test_task_id}/abort",
                timeout=10
            )
            
            if response.status_code == 200:
                abort_response = response.json()
                
                # Check required fields
                if "task_id" not in abort_response or "status" not in abort_response:
                    logger.error("Missing required fields in abort response")
                    return False
                
                if abort_response["status"] != "aborted":
                    logger.error(f"Expected status 'aborted', got '{abort_response['status']}'")
                    return False
                
                logger.info(f"Task aborted: {abort_response['task_id']}")
                return True
                
            elif response.status_code == 404:
                logger.error("Task not found for abort")
                return False
            else:
                logger.error(f"Task abort failed with status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Abort request failed: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        try:
            # Test invalid task creation
            invalid_request = {"invalid": "data"}
            response = requests.post(
                f"{self.base_url}/tasks/create",
                json=invalid_request,
                timeout=10
            )
            
            if response.status_code != 400:
                logger.error(f"Expected 400 for invalid request, got {response.status_code}")
                return False
            
            # Test non-existent task status
            response = requests.get(
                f"{self.base_url}/tasks/non-existent-task/status",
                timeout=10
            )
            
            if response.status_code != 404:
                logger.error(f"Expected 404 for non-existent task, got {response.status_code}")
                return False
            
            logger.info("Error handling working correctly")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error handling test failed: {e}")
            return False
    
    def print_summary(self, passed: int, total: int):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 PHASE 2 MCP CORE TEST SUMMARY")
        logger.info("="*60)
        
        for test_name, result in self.results.items():
            status_emoji = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            logger.info(f"{status_emoji} {test_name}: {result['status']}")
            
            if result['status'] != 'PASS' and 'details' in result:
                details = result['details']
                if 'error' in details:
                    logger.info(f"    Error: {details['error']}")
        
        logger.info("-"*60)
        success_rate = (passed / total) * 100
        logger.info(f"Overall Result: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if passed == total:
            logger.info("🎉 All Phase 2 MCP core tests PASSED!")
            logger.info("✅ Ready to proceed to Phase 3: Agent Container Creation")
        else:
            logger.info("⚠️  Some tests FAILED. Please fix issues before proceeding.")
            logger.info("📋 Check MCP container logs:")
            logger.info("   docker-compose logs mcp")
        
        logger.info("="*60)

def main():
    """Main function"""
    tester = Phase2MCPTest()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 