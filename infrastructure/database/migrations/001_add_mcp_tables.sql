-- Migration: Add MCP Task Management Tables
-- Date: 2024-12-27
-- Description: Add tables for Master Control Program (MCP) task coordination

-- Task histories for MCP coordination
CREATE TABLE IF NOT EXISTS task_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    plan JSONB NOT NULL,
    template VARCHAR(100) NOT NULL DEFAULT 'standard_query',
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    current_stage VARCHAR(100),
    completed_stages JSONB DEFAULT '[]'::jsonb,
    context TEXT,
    response JSONB,
    error TEXT,
    progress_percentage INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT task_histories_status_check CHECK (status IN ('in_progress', 'complete', 'failed', 'aborted')),
    CONSTRAINT task_histories_progress_check CHECK (progress_percentage >= 0 AND progress_percentage <= 100)
);

-- Create indexes for task_histories
CREATE INDEX IF NOT EXISTS idx_task_histories_user_id ON task_histories(user_id);
CREATE INDEX IF NOT EXISTS idx_task_histories_status ON task_histories(status);
CREATE INDEX IF NOT EXISTS idx_task_histories_started_at ON task_histories(started_at);
CREATE INDEX IF NOT EXISTS idx_task_histories_template ON task_histories(template);

-- DAG templates for reusable task patterns
CREATE TABLE IF NOT EXISTS task_dag_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    stages JSONB NOT NULL,
    conditions JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure stages is a valid array
    CONSTRAINT task_dag_templates_stages_check CHECK (jsonb_typeof(stages) = 'array')
);

-- Create indexes for task_dag_templates
CREATE INDEX IF NOT EXISTS idx_task_dag_templates_name ON task_dag_templates(name);
CREATE INDEX IF NOT EXISTS idx_task_dag_templates_active ON task_dag_templates(is_active);

-- Agent performance tracking
CREATE TABLE IF NOT EXISTS agent_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL,
    task_id UUID REFERENCES task_histories(id) ON DELETE CASCADE,
    stage VARCHAR(100) NOT NULL,
    duration_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure duration is non-negative if specified
    CONSTRAINT agent_performance_duration_check CHECK (duration_ms IS NULL OR duration_ms >= 0)
);

-- Create indexes for agent_performance
CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_name ON agent_performance(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_performance_task_id ON agent_performance(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_created_at ON agent_performance(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_performance_success ON agent_performance(success);

-- Task stage logs for detailed tracking
CREATE TABLE IF NOT EXISTS task_stage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES task_histories(id) ON DELETE CASCADE,
    stage VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'start', 'complete', 'fail', 'retry'
    message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure action is valid
    CONSTRAINT task_stage_logs_action_check CHECK (action IN ('start', 'complete', 'fail', 'retry'))
);

-- Create indexes for task_stage_logs
CREATE INDEX IF NOT EXISTS idx_task_stage_logs_task_id ON task_stage_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_stage_logs_stage ON task_stage_logs(stage);
CREATE INDEX IF NOT EXISTS idx_task_stage_logs_action ON task_stage_logs(action);
CREATE INDEX IF NOT EXISTS idx_task_stage_logs_created_at ON task_stage_logs(created_at);

-- Agent health monitoring
CREATE TABLE IF NOT EXISTS agent_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL,
    container_name VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'unknown', -- 'healthy', 'unhealthy', 'starting', 'stopping', 'unknown'
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cpu_usage DECIMAL(5,2), -- Percentage
    memory_usage DECIMAL(5,2), -- Percentage  
    queue_size INTEGER DEFAULT 0,
    processed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT agent_health_status_check CHECK (status IN ('healthy', 'unhealthy', 'starting', 'stopping', 'unknown')),
    CONSTRAINT agent_health_cpu_check CHECK (cpu_usage IS NULL OR (cpu_usage >= 0 AND cpu_usage <= 100)),
    CONSTRAINT agent_health_memory_check CHECK (memory_usage IS NULL OR (memory_usage >= 0 AND memory_usage <= 100)),
    CONSTRAINT agent_health_queue_check CHECK (queue_size >= 0),
    CONSTRAINT agent_health_tasks_check CHECK (processed_tasks >= 0 AND failed_tasks >= 0)
);

-- Create indexes for agent_health
CREATE INDEX IF NOT EXISTS idx_agent_health_agent_name ON agent_health(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_health_status ON agent_health(status);
CREATE INDEX IF NOT EXISTS idx_agent_health_last_heartbeat ON agent_health(last_heartbeat);
CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_health_unique_agent ON agent_health(agent_name);

-- Insert default DAG templates
INSERT INTO task_dag_templates (name, description, stages, conditions) VALUES
('standard_query', 'Standard question answering flow for most queries', 
 '["intent_analysis", "embedding_lookup", "executor_reasoning", "moderation", "response_packaging"]'::jsonb,
 '{"complexity": "medium", "requires_web_search": false, "estimated_duration_ms": 15000}'::jsonb),

('simple_lookup', 'Simple document lookup without complex reasoning',
 '["embedding_lookup", "response_packaging"]'::jsonb,
 '{"complexity": "low", "direct_answer": true, "estimated_duration_ms": 5000}'::jsonb),

('complex_research', 'Complex multi-step research with web augmentation',
 '["intent_analysis", "embedding_lookup", "web_search", "executor_reasoning", "moderation", "response_packaging"]'::jsonb,
 '{"complexity": "high", "requires_web_search": true, "estimated_duration_ms": 30000}'::jsonb),

('web_enhanced', 'Web search enhanced response for current information',
 '["intent_analysis", "web_search", "embedding_lookup", "executor_reasoning", "moderation", "response_packaging"]'::jsonb,
 '{"complexity": "medium", "requires_web_search": true, "estimated_duration_ms": 20000}'::jsonb),

('quick_answer', 'Ultra-fast response for simple factual queries',
 '["embedding_lookup", "executor_reasoning", "response_packaging"]'::jsonb,
 '{"complexity": "very_low", "direct_answer": true, "estimated_duration_ms": 3000}'::jsonb)

ON CONFLICT (name) DO NOTHING;

-- Create triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_task_histories_updated_at 
    BEFORE UPDATE ON task_histories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_dag_templates_updated_at 
    BEFORE UPDATE ON task_dag_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_health_updated_at 
    BEFORE UPDATE ON agent_health 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for task analytics
CREATE OR REPLACE VIEW task_analytics AS
SELECT 
    th.template,
    th.status,
    COUNT(*) as task_count,
    AVG(EXTRACT(EPOCH FROM (th.updated_at - th.started_at)) * 1000)::INTEGER as avg_duration_ms,
    AVG(th.progress_percentage) as avg_progress,
    COUNT(CASE WHEN th.status = 'complete' THEN 1 END) as completed_count,
    COUNT(CASE WHEN th.status = 'failed' THEN 1 END) as failed_count,
    (COUNT(CASE WHEN th.status = 'complete' THEN 1 END)::FLOAT / COUNT(*) * 100)::DECIMAL(5,2) as success_rate
FROM task_histories th
WHERE th.started_at >= NOW() - INTERVAL '24 hours'
GROUP BY th.template, th.status
ORDER BY th.template, th.status;

-- Create a view for agent performance summary
CREATE OR REPLACE VIEW agent_performance_summary AS
SELECT 
    ap.agent_name,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN ap.success = true THEN 1 END) as successful_tasks,
    COUNT(CASE WHEN ap.success = false THEN 1 END) as failed_tasks,
    AVG(ap.duration_ms)::INTEGER as avg_duration_ms,
    MIN(ap.duration_ms) as min_duration_ms,
    MAX(ap.duration_ms) as max_duration_ms,
    (COUNT(CASE WHEN ap.success = true THEN 1 END)::FLOAT / COUNT(*) * 100)::DECIMAL(5,2) as success_rate
FROM agent_performance ap
WHERE ap.created_at >= NOW() - INTERVAL '24 hours'
GROUP BY ap.agent_name
ORDER BY ap.agent_name;

-- Grant appropriate permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO askflash_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO askflash_app;

-- Add comments for documentation
COMMENT ON TABLE task_histories IS 'Main table for tracking MCP task execution and state';
COMMENT ON TABLE task_dag_templates IS 'Reusable DAG templates for different types of tasks';
COMMENT ON TABLE agent_performance IS 'Performance metrics for individual agent executions';
COMMENT ON TABLE task_stage_logs IS 'Detailed logs of task stage transitions and events';
COMMENT ON TABLE agent_health IS 'Real-time health monitoring for MCP agents';

COMMENT ON VIEW task_analytics IS 'Analytics view for task performance over the last 24 hours';
COMMENT ON VIEW agent_performance_summary IS 'Performance summary for agents over the last 24 hours'; 