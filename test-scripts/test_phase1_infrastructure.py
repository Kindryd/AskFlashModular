#!/usr/bin/env python3
"""
Test Script for Phase 1: Infrastructure Enhancement

This script tests the infrastructure components added in Phase 1:
- RabbitMQ setup and queue initialization
- Enhanced Redis configuration and connectivity
- Database migration and MCP table creation

Usage:
    python test-scripts/test_phase1_infrastructure.py
"""

import sys
import time
import json
import logging
import psycopg2
import redis
import pika
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase1InfrastructureTest:
    """Test suite for Phase 1 infrastructure components"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        
        # Connection configurations
        self.postgres_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'askflashdb',
            'user': 'postgres',
            'password': 'postgres'
        }
        
        self.redis_config = {
            'host': 'localhost',
            'port': 6379,
            'password': 'askflash123'
        }
        
        self.rabbitmq_config = {
            'host': 'localhost',
            'port': 5672,
            'username': 'askflash',
            'password': 'askflash123'
        }
    
    def run_all_tests(self) -> bool:
        """Run all Phase 1 tests"""
        logger.info("🚀 Starting Phase 1 Infrastructure Tests...")
        
        tests = [
            ("PostgreSQL Connection", self.test_postgres_connection),
            ("MCP Database Tables", self.test_mcp_tables),
            ("Redis Connection", self.test_redis_connection),
            ("Redis Streams", self.test_redis_streams),
            ("Redis Pub/Sub", self.test_redis_pubsub),
            ("RabbitMQ Connection", self.test_rabbitmq_connection),
            ("RabbitMQ Queues", self.test_rabbitmq_queues),
            ("Queue Initialization", self.test_queue_initialization),
            ("End-to-End Message Flow", self.test_e2e_message_flow)
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
    
    def test_postgres_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            
            logger.info(f"PostgreSQL Version: {version[0]}")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return False
    
    def test_mcp_tables(self) -> Dict:
        """Test MCP table creation and structure"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()
            
            # Check if MCP tables exist
            required_tables = [
                'task_histories',
                'task_dag_templates', 
                'agent_performance',
                'task_stage_logs',
                'agent_health'
            ]
            
            existing_tables = []
            for table in required_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table,))
                
                if cursor.fetchone()[0]:
                    existing_tables.append(table)
            
            # Check DAG templates
            cursor.execute("SELECT COUNT(*) FROM task_dag_templates;")
            template_count = cursor.fetchone()[0]
            
            # Check views
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views 
                    WHERE table_schema = 'public' 
                    AND table_name = 'task_analytics'
                );
            """)
            analytics_view_exists = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            result = {
                'required_tables': len(required_tables),
                'existing_tables': len(existing_tables),
                'missing_tables': list(set(required_tables) - set(existing_tables)),
                'dag_templates': template_count,
                'analytics_view': analytics_view_exists
            }
            
            logger.info(f"Tables: {len(existing_tables)}/{len(required_tables)}, Templates: {template_count}")
            
            return len(existing_tables) == len(required_tables) and template_count > 0
            
        except Exception as e:
            logger.error(f"MCP tables test failed: {e}")
            return False
    
    def test_redis_connection(self) -> bool:
        """Test Redis connection with password"""
        try:
            r = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                password=self.redis_config['password'],
                decode_responses=True
            )
            
            # Test basic operations
            r.set('test_key', 'test_value', ex=10)
            value = r.get('test_key')
            r.delete('test_key')
            
            # Test Redis info
            info = r.info()
            redis_version = info.get('redis_version', 'unknown')
            
            logger.info(f"Redis Version: {redis_version}")
            return value == 'test_value'
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    def test_redis_streams(self) -> bool:
        """Test Redis streams functionality"""
        try:
            r = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                password=self.redis_config['password'],
                decode_responses=True
            )
            
            stream_key = 'test_stream'
            
            # Add to stream
            stream_id = r.xadd(stream_key, {
                'test_field': 'test_value',
                'timestamp': str(time.time())
            })
            
            # Read from stream
            entries = r.xrange(stream_key)
            
            # Cleanup
            r.delete(stream_key)
            
            logger.info(f"Stream test: Added {stream_id}, Read {len(entries)} entries")
            return len(entries) == 1
            
        except Exception as e:
            logger.error(f"Redis streams test failed: {e}")
            return False
    
    def test_redis_pubsub(self) -> bool:
        """Test Redis pub/sub functionality"""
        try:
            r = redis.Redis(
                host=self.redis_config['host'],
                port=self.redis_config['port'],
                password=self.redis_config['password'],
                decode_responses=True
            )
            
            channel = 'test_channel'
            message = 'test_message'
            
            # Publish message
            subscribers = r.publish(channel, message)
            
            logger.info(f"Pub/Sub test: Published to {subscribers} subscribers")
            return True  # No subscribers expected in test
            
        except Exception as e:
            logger.error(f"Redis pub/sub test failed: {e}")
            return False
    
    def test_rabbitmq_connection(self) -> bool:
        """Test RabbitMQ connection"""
        try:
            credentials = pika.PlainCredentials(
                self.rabbitmq_config['username'],
                self.rabbitmq_config['password']
            )
            
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_config['host'],
                port=self.rabbitmq_config['port'],
                credentials=credentials
            )
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Get server properties
            server_properties = connection.server_properties
            
            channel.close()
            connection.close()
            
            logger.info(f"RabbitMQ Version: {server_properties.get('version', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {e}")
            return False
    
    def test_rabbitmq_queues(self) -> Dict:
        """Test RabbitMQ queue existence"""
        try:
            credentials = pika.PlainCredentials(
                self.rabbitmq_config['username'],
                self.rabbitmq_config['password']
            )
            
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_config['host'],
                port=self.rabbitmq_config['port'],
                credentials=credentials
            )
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Check required queues
            required_queues = [
                'intent.task',
                'embedding.task',
                'executor.task', 
                'moderator.task',
                'websearch.task',
                'mcp.responses'
            ]
            
            existing_queues = []
            for queue_name in required_queues:
                try:
                    method = channel.queue_declare(queue=queue_name, passive=True)
                    existing_queues.append(queue_name)
                    logger.info(f"Queue {queue_name}: {method.method.message_count} messages")
                except Exception:
                    logger.warning(f"Queue {queue_name} does not exist")
            
            channel.close()
            connection.close()
            
            result = {
                'required_queues': len(required_queues),
                'existing_queues': len(existing_queues),
                'missing_queues': list(set(required_queues) - set(existing_queues))
            }
            
            return len(existing_queues) == len(required_queues)
            
        except Exception as e:
            logger.error(f"RabbitMQ queues test failed: {e}")
            return False
    
    def test_queue_initialization(self) -> bool:
        """Test queue initialization script functionality"""
        try:
            # Import and run the initialization script
            sys.path.append('infrastructure/rabbitmq')
            from init_queues import RabbitMQInitializer
            
            initializer = RabbitMQInitializer(
                host=self.rabbitmq_config['host'],
                port=self.rabbitmq_config['port'],
                username=self.rabbitmq_config['username'],
                password=self.rabbitmq_config['password']
            )
            
            success = initializer.initialize_all()
            
            logger.info(f"Queue initialization: {'SUCCESS' if success else 'FAILED'}")
            return success
            
        except Exception as e:
            logger.error(f"Queue initialization test failed: {e}")
            return False
    
    def test_e2e_message_flow(self) -> bool:
        """Test end-to-end message flow across all systems"""
        try:
            # Test Redis task creation
            from shared.redis_manager import RedisTaskManager
            
            task_manager = RedisTaskManager(
                redis_url=f"redis://{self.redis_config['host']}:{self.redis_config['port']}",
                password=self.redis_config['password']
            )
            
            # Create a test task
            task_id = task_manager.create_task(
                user_id='test_user',
                query='Test query for e2e flow',
                plan=['intent_analysis', 'embedding_lookup', 'response_packaging'],
                template='test_template'
            )
            
            # Verify task creation
            task_data = task_manager.get_task(task_id)
            
            # Test progress events
            task_manager.emit_progress_event(
                task_id=task_id,
                stage='testing',
                message='E2E test progress event'
            )
            
            # Test RabbitMQ message flow
            credentials = pika.PlainCredentials(
                self.rabbitmq_config['username'],
                self.rabbitmq_config['password']
            )
            
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_config['host'],
                port=self.rabbitmq_config['port'],
                credentials=credentials
            )
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Publish test message
            test_payload = {
                'task_id': task_id,
                'query': 'Test query',
                'user_id': 'test_user'
            }
            
            channel.basic_publish(
                exchange='mcp.tasks',
                routing_key='intent.task',
                body=json.dumps(test_payload)
            )
            
            # Try to consume the message
            method_frame, header_frame, body = channel.basic_get(
                queue='intent.task',
                auto_ack=True
            )
            
            channel.close()
            connection.close()
            
            # Verify message was consumed
            consumed_payload = json.loads(body) if body else None
            
            logger.info(f"E2E Test: Task {task_id[:8]}..., Message consumed: {consumed_payload is not None}")
            
            return (task_data is not None and 
                   task_data['task_id'] == task_id and
                   consumed_payload is not None and
                   consumed_payload['task_id'] == task_id)
            
        except Exception as e:
            logger.error(f"E2E message flow test failed: {e}")
            return False
    
    def print_summary(self, passed: int, total: int):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 PHASE 1 INFRASTRUCTURE TEST SUMMARY")
        logger.info("="*60)
        
        for test_name, result in self.results.items():
            status_emoji = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            logger.info(f"{status_emoji} {test_name}: {result['status']}")
            
            if result['status'] != 'PASS' and 'details' in result:
                details = result['details']
                if 'error' in details:
                    logger.info(f"    Error: {details['error']}")
                elif 'missing_tables' in details:
                    logger.info(f"    Missing tables: {details['missing_tables']}")
        
        logger.info("-"*60)
        success_rate = (passed / total) * 100
        logger.info(f"Overall Result: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if passed == total:
            logger.info("🎉 All Phase 1 infrastructure tests PASSED!")
            logger.info("✅ Ready to proceed to Phase 2: MCP Core Implementation")
        else:
            logger.info("⚠️  Some tests FAILED. Please fix issues before proceeding.")
            logger.info("📋 Check docker-compose logs and ensure all services are running:")
            logger.info("   docker-compose logs postgres redis rabbitmq")
        
        logger.info("="*60)

def main():
    """Main function"""
    tester = Phase1InfrastructureTest()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 