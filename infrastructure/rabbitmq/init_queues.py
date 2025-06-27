#!/usr/bin/env python3
"""
RabbitMQ Queue Initialization Script for AskFlash MCP Architecture

This script initializes the required exchanges and queues for the Master Control Program (MCP)
multi-agent architecture. It should be run after RabbitMQ is started.

Usage:
    python infrastructure/rabbitmq/init_queues.py
"""

import pika
import logging
import time
import sys
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RabbitMQInitializer:
    """Initialize RabbitMQ exchanges and queues for MCP"""
    
    def __init__(self, host: str = 'localhost', port: int = 5672, 
                 username: str = 'askflash', password: str = 'askflash123'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        
    def connect(self, max_retries: int = 5, retry_delay: int = 2) -> bool:
        """Establish connection to RabbitMQ with retry logic"""
        
        for attempt in range(max_retries):
            try:
                credentials = pika.PlainCredentials(self.username, self.password)
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
                
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                logger.info(f"Successfully connected to RabbitMQ at {self.host}:{self.port}")
                return True
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to RabbitMQ after all retries")
                    return False
    
    def setup_exchanges(self) -> bool:
        """Declare exchanges for task routing"""
        try:
            # Main exchange for MCP task distribution
            self.channel.exchange_declare(
                exchange='mcp.tasks',
                exchange_type='direct',
                durable=True
            )
            
            # Exchange for MCP events and notifications
            self.channel.exchange_declare(
                exchange='mcp.events',
                exchange_type='topic',
                durable=True
            )
            
            logger.info("Successfully declared exchanges")
            return True
            
        except Exception as e:
            logger.error(f"Failed to declare exchanges: {e}")
            return False
    
    def setup_queues(self) -> bool:
        """Declare queues for MCP agent tasks"""
        
        # Define queue configurations
        queues = [
            {
                'name': 'intent.task',
                'routing_key': 'intent.task',
                'description': 'Intent analysis and query planning tasks'
            },
            {
                'name': 'embedding.task', 
                'routing_key': 'embedding.task',
                'description': 'Vector search and document retrieval tasks'
            },
            {
                'name': 'executor.task',
                'routing_key': 'executor.task', 
                'description': 'Main AI reasoning and response generation tasks'
            },
            {
                'name': 'moderator.task',
                'routing_key': 'moderator.task',
                'description': 'Response quality assessment and moderation tasks'
            },
            {
                'name': 'websearch.task',
                'routing_key': 'websearch.task',
                'description': 'Web search and fact verification tasks'
            },
            {
                'name': 'mcp.responses',
                'routing_key': 'mcp.responses',
                'description': 'Final responses ready for delivery'
            }
        ]
        
        try:
            for queue_config in queues:
                # Declare queue with durability
                queue_result = self.channel.queue_declare(
                    queue=queue_config['name'],
                    durable=True,
                    arguments={
                        'x-message-ttl': 600000,  # 10 minutes TTL
                        'x-max-length': 1000,     # Max 1000 messages
                        'x-overflow': 'reject-publish'
                    }
                )
                
                # Bind queue to exchange
                self.channel.queue_bind(
                    exchange='mcp.tasks',
                    queue=queue_config['name'],
                    routing_key=queue_config['routing_key']
                )
                
                logger.info(f"Configured queue: {queue_config['name']} - {queue_config['description']}")
            
            logger.info("Successfully configured all MCP queues")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure queues: {e}")
            return False
    
    def setup_dead_letter_queues(self) -> bool:
        """Setup dead letter queues for failed message handling"""
        try:
            # Dead letter exchange
            self.channel.exchange_declare(
                exchange='mcp.dlx',
                exchange_type='direct',
                durable=True
            )
            
            # Dead letter queue
            self.channel.queue_declare(
                queue='mcp.dead_letter',
                durable=True
            )
            
            self.channel.queue_bind(
                exchange='mcp.dlx',
                queue='mcp.dead_letter',
                routing_key='dead_letter'
            )
            
            logger.info("Configured dead letter queues")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure dead letter queues: {e}")
            return False
    
    def verify_setup(self) -> bool:
        """Verify that all queues and exchanges are properly configured"""
        try:
            # Test message publish/consume
            test_message = '{"test": "queue_verification", "timestamp": "' + str(time.time()) + '"}'
            
            self.channel.basic_publish(
                exchange='mcp.tasks',
                routing_key='intent.task',
                body=test_message
            )
            
            # Try to get the message back
            method_frame, header_frame, body = self.channel.basic_get(
                queue='intent.task',
                auto_ack=True
            )
            
            if body:
                logger.info("Queue verification successful - messages can be published and consumed")
                return True
            else:
                logger.warning("Queue verification failed - could not retrieve test message")
                return False
                
        except Exception as e:
            logger.error(f"Queue verification failed: {e}")
            return False
    
    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Closed RabbitMQ connection")
    
    def initialize_all(self) -> bool:
        """Complete initialization process"""
        logger.info("Starting RabbitMQ initialization for AskFlash MCP...")
        
        if not self.connect():
            return False
        
        steps = [
            ("exchanges", self.setup_exchanges),
            ("queues", self.setup_queues),
            ("dead letter queues", self.setup_dead_letter_queues),
            ("verification", self.verify_setup)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Setting up {step_name}...")
            if not step_func():
                logger.error(f"Failed to setup {step_name}")
                self.close()
                return False
        
        self.close()
        logger.info("✅ RabbitMQ initialization completed successfully!")
        return True

def main():
    """Main function to run initialization"""
    initializer = RabbitMQInitializer()
    
    try:
        success = initializer.initialize_all()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Initialization interrupted by user")
        initializer.close()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        initializer.close()
        sys.exit(1)

if __name__ == "__main__":
    main() 