#!/usr/bin/env python3
"""
Test Script for AskFlash MCP Phase 3: Agent Containers

This script tests the individual agent containers:
- Intent Agent
- Executor Agent  
- Web Search Agent
- Moderator Agent

Tests include health checks, RabbitMQ connectivity, and end-to-end functionality.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List

import aio_pika
import redis.asyncio as redis
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase3AgentTester:
    """Test suite for MCP agent containers"""
    
    def __init__(self):
        self.redis_url = "redis://localhost:6379"
        self.redis_password = "askflash123"
        self.rabbitmq_url = "amqp://askflash:askflash123@localhost:5672/"
        
        # Agent endpoints
        self.agents = {
            "intent-agent": "http://localhost:8010",
            "executor-agent": "http://localhost:8011", 
            "websearch-agent": "http://localhost:8012",
            "moderator-agent": "http://localhost:8013"
        }
        
        # Test results
        self.test_results = []
        self.failed_tests = []
        
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("🧪 Starting AskFlash MCP Phase 3 Agent Tests")
        logger.info("=" * 60)
        
        # Test 1: Agent Health Checks
        await self.test_agent_health_checks()
        
        # Test 2: Agent Capabilities
        await self.test_agent_capabilities()
        
        # Test 3: RabbitMQ Connectivity
        await self.test_rabbitmq_connectivity()
        
        # Test 4: Redis Connectivity
        await self.test_redis_connectivity()
        
        # Test 5: Intent Agent Functionality
        await self.test_intent_agent_functionality()
        
        # Test 6: Executor Agent Functionality
        await self.test_executor_agent_functionality()
        
        # Test 7: Web Search Agent Functionality (if implemented)
        await self.test_websearch_agent_functionality()
        
        # Test 8: Moderator Agent Functionality (if implemented)
        await self.test_moderator_agent_functionality()
        
        # Test 9: End-to-End Message Flow
        await self.test_end_to_end_message_flow()
        
        # Test 10: Error Handling
        await self.test_error_handling()
        
        # Generate summary
        await self.generate_test_summary()
    
    async def test_agent_health_checks(self):
        """Test 1: Verify all agents are healthy"""
        logger.info("🔍 Test 1: Agent Health Checks")
        
        for agent_name, base_url in self.agents.items():
            try:
                response = requests.get(f"{base_url}/health", timeout=10)
                
                if response.status_code == 200:
                    health_data = response.json()
                    
                    if health_data.get("status") == "healthy":
                        self._record_success(f"{agent_name} health check", 
                                           f"Agent is healthy with all components operational")
                    else:
                        self._record_failure(f"{agent_name} health check",
                                           f"Agent reports unhealthy status: {health_data}")
                else:
                    self._record_failure(f"{agent_name} health check",
                                       f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self._record_failure(f"{agent_name} health check", str(e))
        
        logger.info("✅ Agent health checks completed\n")
    
    async def test_agent_capabilities(self):
        """Test 2: Verify agent capabilities"""
        logger.info("🔍 Test 2: Agent Capabilities")
        
        expected_capabilities = {
            "intent-agent": ["query_analysis", "intent_classification", "complexity_assessment"],
            "executor-agent": ["comprehensive_reasoning", "document_synthesis", "contextual_response_generation"],
            "websearch-agent": ["web_search", "content_extraction", "search_result_processing"],
            "moderator-agent": ["content_moderation", "response_validation", "quality_assessment"]
        }
        
        for agent_name, base_url in self.agents.items():
            try:
                response = requests.get(f"{base_url}/capabilities", timeout=10)
                
                if response.status_code == 200:
                    capabilities = response.json()
                    expected = expected_capabilities.get(agent_name, [])
                    actual = capabilities.get("capabilities", [])
                    
                    if all(cap in actual for cap in expected):
                        self._record_success(f"{agent_name} capabilities",
                                           f"All expected capabilities present: {expected}")
                    else:
                        missing = [cap for cap in expected if cap not in actual]
                        self._record_failure(f"{agent_name} capabilities",
                                           f"Missing capabilities: {missing}")
                else:
                    self._record_failure(f"{agent_name} capabilities",
                                       f"HTTP {response.status_code}")
                    
            except Exception as e:
                self._record_failure(f"{agent_name} capabilities", str(e))
        
        logger.info("✅ Agent capabilities check completed\n")
    
    async def test_rabbitmq_connectivity(self):
        """Test 3: Verify RabbitMQ connectivity"""
        logger.info("🔍 Test 3: RabbitMQ Connectivity")
        
        try:
            connection = await aio_pika.connect_robust(self.rabbitmq_url)
            channel = await connection.channel()
            
            # Check if agent queues exist
            queues_to_check = ["intent.task", "executor.task", "moderator.task", "websearch.task"]
            
            for queue_name in queues_to_check:
                try:
                    queue = await channel.declare_queue(queue_name, durable=True, passive=True)
                    self._record_success(f"RabbitMQ queue {queue_name}",
                                       "Queue exists and is accessible")
                except Exception as e:
                    self._record_failure(f"RabbitMQ queue {queue_name}", str(e))
            
            await connection.close()
            
        except Exception as e:
            self._record_failure("RabbitMQ connection", str(e))
        
        logger.info("✅ RabbitMQ connectivity check completed\n")
    
    async def test_redis_connectivity(self):
        """Test 4: Verify Redis connectivity"""
        logger.info("🔍 Test 4: Redis Connectivity")
        
        try:
            redis_client = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                decode_responses=True
            )
            
            # Test basic operations
            test_key = f"test:phase3:{uuid.uuid4()}"
            test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}
            
            # Set value
            await redis_client.setex(test_key, 60, json.dumps(test_value))
            
            # Get value
            retrieved = await redis_client.get(test_key)
            
            if retrieved:
                parsed = json.loads(retrieved)
                if parsed.get("test") == True:
                    self._record_success("Redis connectivity",
                                       "Successfully stored and retrieved test data")
                else:
                    self._record_failure("Redis connectivity",
                                       "Data integrity issue")
            else:
                self._record_failure("Redis connectivity",
                                   "Failed to retrieve test data")
            
            # Cleanup
            await redis_client.delete(test_key)
            await redis_client.close()
            
        except Exception as e:
            self._record_failure("Redis connectivity", str(e))
        
        logger.info("✅ Redis connectivity check completed\n")
    
    async def test_intent_agent_functionality(self):
        """Test 5: Intent Agent specific functionality"""
        logger.info("🔍 Test 5: Intent Agent Functionality")
        
        try:
            # Test manual intent analysis
            test_query = "What are the latest trends in artificial intelligence and machine learning?"
            
            response = requests.post(
                f"{self.agents['intent-agent']}/api/v1/analyze",
                json={"query": test_query, "user_id": "test_user"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "analysis" in result:
                    analysis = result["analysis"]
                    
                    # Check key analysis components
                    required_keys = ["intent_classification", "complexity_assessment", "processing_strategy"]
                    
                    if all(key in analysis for key in required_keys):
                        self._record_success("Intent Agent analysis",
                                           f"Complete analysis with intent: {analysis['intent_classification'].get('primary_intent')}")
                    else:
                        missing = [key for key in required_keys if key not in analysis]
                        self._record_failure("Intent Agent analysis",
                                           f"Missing analysis components: {missing}")
                else:
                    self._record_failure("Intent Agent analysis",
                                       "Invalid response format")
            else:
                self._record_failure("Intent Agent analysis",
                                   f"HTTP {response.status_code}: {response.text}")
        
        except Exception as e:
            self._record_failure("Intent Agent functionality", str(e))
        
        logger.info("✅ Intent Agent functionality test completed\n")
    
    async def test_executor_agent_functionality(self):
        """Test 6: Executor Agent specific functionality"""
        logger.info("🔍 Test 6: Executor Agent Functionality")
        
        try:
            # Test manual execution
            test_data = {
                "query": "Explain the benefits of microservices architecture",
                "context": "Software development discussion",
                "documents": [
                    {
                        "id": "doc1",
                        "title": "Microservices Guide",
                        "content": "Microservices architecture allows for independent deployment, scalability, and technology diversity. It breaks down monolithic applications into smaller, manageable services."
                    }
                ],
                "strategy": {"approach": "standard_query", "complexity_level": "medium"}
            }
            
            response = requests.post(
                f"{self.agents['executor-agent']}/api/v1/execute",
                json=test_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and "execution_result" in result:
                    execution = result["execution_result"]
                    
                    # Check key execution components
                    required_keys = ["response", "reasoning_metadata", "sources"]
                    
                    if all(key in execution for key in required_keys):
                        response_data = execution["response"]
                        confidence = response_data.get("confidence_score", 0)
                        
                        self._record_success("Executor Agent reasoning",
                                           f"Generated response with {confidence:.2f} confidence")
                    else:
                        missing = [key for key in required_keys if key not in execution]
                        self._record_failure("Executor Agent reasoning",
                                           f"Missing execution components: {missing}")
                else:
                    self._record_failure("Executor Agent reasoning",
                                       "Invalid response format")
            else:
                self._record_failure("Executor Agent reasoning",
                                   f"HTTP {response.status_code}: {response.text}")
        
        except Exception as e:
            self._record_failure("Executor Agent functionality", str(e))
        
        logger.info("✅ Executor Agent functionality test completed\n")
    
    async def test_websearch_agent_functionality(self):
        """Test 7: Web Search Agent functionality (placeholder)"""
        logger.info("🔍 Test 7: Web Search Agent Functionality")
        
        try:
            response = requests.get(f"{self.agents['websearch-agent']}/health", timeout=10)
            
            if response.status_code == 200:
                self._record_success("Web Search Agent basic check",
                                   "Agent is responding (implementation pending)")
            else:
                self._record_failure("Web Search Agent basic check",
                                   f"HTTP {response.status_code}")
        
        except Exception as e:
            self._record_failure("Web Search Agent functionality", 
                               f"Not implemented yet: {str(e)}")
        
        logger.info("✅ Web Search Agent functionality test completed\n")
    
    async def test_moderator_agent_functionality(self):
        """Test 8: Moderator Agent functionality (placeholder)"""
        logger.info("🔍 Test 8: Moderator Agent Functionality")
        
        try:
            response = requests.get(f"{self.agents['moderator-agent']}/health", timeout=10)
            
            if response.status_code == 200:
                self._record_success("Moderator Agent basic check",
                                   "Agent is responding (implementation pending)")
            else:
                self._record_failure("Moderator Agent basic check",
                                   f"HTTP {response.status_code}")
        
        except Exception as e:
            self._record_failure("Moderator Agent functionality",
                               f"Not implemented yet: {str(e)}")
        
        logger.info("✅ Moderator Agent functionality test completed\n")
    
    async def test_end_to_end_message_flow(self):
        """Test 9: End-to-end message flow between agents"""
        logger.info("🔍 Test 9: End-to-End Message Flow")
        
        try:
            # Create a test task and publish to intent queue
            task_id = f"test_e2e_{uuid.uuid4()}"
            
            # Connect to RabbitMQ
            connection = await aio_pika.connect_robust(self.rabbitmq_url)
            channel = await connection.channel()
            
            # Create test message for intent analysis
            test_message = {
                "task_id": task_id,
                "query": "How do microservices improve software development?",
                "user_id": "test_user"
            }
            
            # Publish to intent queue
            intent_queue = await channel.declare_queue("intent.task", durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(json.dumps(test_message).encode()),
                routing_key="intent.task"
            )
            
            # Wait for processing
            await asyncio.sleep(10)
            
            # Check if intent analysis was created
            redis_client = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                decode_responses=True
            )
            
            intent_result_key = f"intent_result:{task_id}"
            intent_data = await redis_client.get(intent_result_key)
            
            if intent_data:
                self._record_success("End-to-end message flow",
                                   f"Intent analysis completed for task {task_id}")
            else:
                self._record_failure("End-to-end message flow",
                                   "Intent analysis not found in Redis")
            
            await redis_client.close()
            await connection.close()
            
        except Exception as e:
            self._record_failure("End-to-end message flow", str(e))
        
        logger.info("✅ End-to-end message flow test completed\n")
    
    async def test_error_handling(self):
        """Test 10: Error handling capabilities"""
        logger.info("🔍 Test 10: Error Handling")
        
        # Test invalid requests to each agent
        for agent_name, base_url in self.agents.items():
            try:
                # Test with missing required fields
                if agent_name == "intent-agent":
                    response = requests.post(
                        f"{base_url}/api/v1/analyze",
                        json={"query": "", "user_id": "test"},  # Empty query
                        timeout=10
                    )
                elif agent_name == "executor-agent":
                    response = requests.post(
                        f"{base_url}/api/v1/execute",
                        json={"query": ""},  # Empty query
                        timeout=10
                    )
                else:
                    # Skip if not implemented
                    continue
                
                if response.status_code >= 400:
                    self._record_success(f"{agent_name} error handling",
                                       f"Properly rejected invalid request with {response.status_code}")
                else:
                    self._record_failure(f"{agent_name} error handling",
                                       "Should have rejected invalid request")
                    
            except Exception as e:
                self._record_failure(f"{agent_name} error handling", str(e))
        
        logger.info("✅ Error handling test completed\n")
    
    def _record_success(self, test_name: str, message: str):
        """Record successful test"""
        result = {
            "test": test_name,
            "status": "PASS",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        logger.info(f"✅ {test_name}: {message}")
    
    def _record_failure(self, test_name: str, error: str):
        """Record failed test"""
        result = {
            "test": test_name,
            "status": "FAIL", 
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        self.failed_tests.append(result)
        logger.error(f"❌ {test_name}: {error}")
    
    async def generate_test_summary(self):
        """Generate comprehensive test summary"""
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len(self.failed_tests)
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests:
            logger.info("\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                logger.info(f"  • {failure['test']}: {failure['error']}")
        
        # Save detailed results
        results_file = f"test_results_phase3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "phase": "Phase 3 - Agent Containers",
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
                },
                "test_results": self.test_results,
                "failed_tests": self.failed_tests
            }, indent=2)
        
        logger.info(f"\n📄 Detailed results saved to: {results_file}")
        
        if failed_tests == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Phase 3 agents are operational.")
        else:
            logger.info(f"\n⚠️  {failed_tests} tests failed. Please review and fix issues.")

async def main():
    """Run the test suite"""
    tester = Phase3AgentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 