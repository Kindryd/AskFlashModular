-- AskFlash Modular Database Schema
-- Shared PostgreSQL database with logical table ownership per container

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- CONVERSATION.CONTAINER Tables
-- =============================================================================

CREATE TABLE conversation_histories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversation_histories(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE frequent_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    query_text TEXT NOT NULL,
    query_count INTEGER DEFAULT 1,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- EMBEDDING.CONTAINER Tables
-- =============================================================================

CREATE TABLE wikis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url TEXT,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'indexing', 'completed', 'failed')),
    last_indexed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE wiki_page_indexes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wiki_id UUID NOT NULL REFERENCES wikis(id) ON DELETE CASCADE,
    page_title VARCHAR(500) NOT NULL,
    page_url TEXT,
    content_hash VARCHAR(64),
    embedding_id VARCHAR(100), -- Reference to Qdrant vector ID
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- =============================================================================
-- AI-ORCHESTRATOR.CONTAINER Tables
-- =============================================================================

CREATE TABLE rulesets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rules JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ADAPTIVE-ENGINE.CONTAINER Tables
-- =============================================================================

CREATE TABLE user_habits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    habit_type VARCHAR(100) NOT NULL,
    habit_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE learning_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    insight_type VARCHAR(100) NOT NULL,
    insight_data JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- SHARED/REFERENCE Tables (Read-only for most containers)
-- =============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- =============================================================================
-- Indexes for Performance
-- =============================================================================

-- Conversation indexes
CREATE INDEX idx_conversation_histories_user_id ON conversation_histories(user_id);
CREATE INDEX idx_conversation_histories_created_at ON conversation_histories(created_at);
CREATE INDEX idx_conversation_messages_conversation_id ON conversation_messages(conversation_id);
CREATE INDEX idx_conversation_messages_timestamp ON conversation_messages(timestamp);
CREATE INDEX idx_frequent_queries_user_id ON frequent_queries(user_id);

-- Embedding indexes
CREATE INDEX idx_wikis_status ON wikis(status);
CREATE INDEX idx_wikis_type ON wikis(type);
CREATE INDEX idx_wiki_page_indexes_wiki_id ON wiki_page_indexes(wiki_id);
CREATE INDEX idx_wiki_page_indexes_content_hash ON wiki_page_indexes(content_hash);

-- AI Orchestrator indexes
CREATE INDEX idx_rulesets_is_active ON rulesets(is_active);
CREATE INDEX idx_rulesets_created_by ON rulesets(created_by);
CREATE INDEX idx_integrations_type ON integrations(type);
CREATE INDEX idx_integrations_is_enabled ON integrations(is_enabled);

-- Adaptive Engine indexes
CREATE INDEX idx_user_habits_user_id ON user_habits(user_id);
CREATE INDEX idx_user_habits_habit_type ON user_habits(habit_type);
CREATE INDEX idx_learning_insights_user_id ON learning_insights(user_id);
CREATE INDEX idx_learning_insights_expires_at ON learning_insights(expires_at);

-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- =============================================================================
-- Triggers for updated_at timestamps
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_conversation_histories_updated_at BEFORE UPDATE ON conversation_histories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_rulesets_updated_at BEFORE UPDATE ON rulesets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_integrations_updated_at BEFORE UPDATE ON integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_habits_updated_at BEFORE UPDATE ON user_habits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Sample Data for Development
-- =============================================================================

-- Insert a default admin user
INSERT INTO users (id, email, name, role) VALUES 
    ('00000000-0000-0000-0000-000000000001', 'admin@askflash.com', 'System Admin', 'admin');

-- Insert a default ruleset
INSERT INTO rulesets (id, name, description, rules, created_by) VALUES 
    ('00000000-0000-0000-0000-000000000001', 
     'Default Ruleset', 
     'Default AI routing and processing rules',
     '{"default_model": "gpt-4", "max_tokens": 4000, "temperature": 0.7}',
     '00000000-0000-0000-0000-000000000001');

-- Insert a default integration
INSERT INTO integrations (id, name, type, config) VALUES 
    ('00000000-0000-0000-0000-000000000001',
     'OpenAI Integration',
     'openai',
     '{"api_key_ref": "OPENAI_API_KEY", "default_model": "gpt-4"}');

COMMIT; 