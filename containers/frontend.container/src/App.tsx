import React, { useState, useEffect } from 'react';
import './App.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  mode?: string;
  sources?: Source[];
  confidence?: number;
  timestamp: string;
  isThinking?: boolean;
  thinkingId?: string;
}

interface Source {
  title: string;
  url: string;
  relevance_score?: number;
  content_preview?: string;
}

interface ThinkingStep {
  message: string;
  timestamp: string;
}

const App: React.FC = () => {
  // UI State
  const [darkMode, setDarkMode] = useState<boolean>(() => 
    localStorage.getItem('flash-theme') === 'dark'
  );
  const [mode, setMode] = useState<'company' | 'general'>('company');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState<string>('');
  const [conversationId, setConversationId] = useState<string>('');

  // Streaming State
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);

  // Environment variable handling
  const getApiUrl = (): string => {
    // Handle environment variables properly for both dev and production
    if (typeof window !== 'undefined' && (window as any)._env_?.REACT_APP_API_URL) {
      return (window as any)._env_.REACT_APP_API_URL;
    }
    return 'http://localhost:8000';
  };

  // Initialize conversation on load
  useEffect(() => {
    loadActiveConversation();
  }, [mode]);

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    localStorage.setItem('flash-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  const loadActiveConversation = async (): Promise<void> => {
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/v1/conversations/active?mode=${mode}`);
      
      if (response.ok) {
        const conversation = await response.json();
        setConversationId(conversation.conversation_id || '');
        setMessages(conversation.messages || []);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
      // Start with empty conversation on error
      setConversationId('');
      setMessages([]);
    }
  };

  const createNewConversation = async (): Promise<void> => {
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/v1/conversations/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode })
      });
      
      if (response.ok) {
        const newConv = await response.json();
        setConversationId(newConv.conversation_id);
        setMessages([]);
        setThinkingSteps([]);
      }
    } catch (error) {
      console.error('Failed to create conversation:', error);
      setError('Failed to create new conversation');
    }
  };

  const handleStreamedChat = async (userQuery: string, selectedMode: 'company' | 'general'): Promise<void> => {
    if (!userQuery.trim()) return;

    // Add user message immediately
    const userMessage: Message = {
      role: 'user',
      content: userQuery,
      timestamp: new Date().toISOString()
    };
    setMessages((prev: Message[]) => [...prev, userMessage]);
    setQuery('');
    setLoading(true);
    setIsThinking(true);
    setThinkingSteps([]);
    setError('');

    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userQuery,
          mode: selectedMode,
          ruleset_id: 1,
          conversation_id: conversationId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) {
        throw new Error('No response body reader available');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (!line.trim()) continue;

          try {
            const data = JSON.parse(line);
            
            if (data.type === 'thinking') {
              setThinkingSteps((prev: ThinkingStep[]) => [...prev, {
                message: data.message,
                timestamp: data.timestamp
              }]);
            } else if (data.type === 'response') {
              // Final response received
              setIsThinking(false);
              const assistantMessage: Message = {
                role: 'assistant',
                content: data.data.response,
                mode: data.data.mode,
                sources: data.data.sources,
                confidence: data.data.confidence,
                timestamp: data.data.timestamp
              };
              setMessages((prev: Message[]) => [...prev, assistantMessage]);
              setConversationId(data.data.conversation_id || conversationId);
            } else if (data.type === 'error') {
              setIsThinking(false);
              setError(data.message);
            }
          } catch (parseError) {
            console.warn('Failed to parse streaming data:', line);
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setError('Failed to process request. Please try again.');
      setIsThinking(false);
    } finally {
      setLoading(false);
      setIsThinking(false);
    }
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    if (query.trim() && !loading) {
      handleStreamedChat(query, mode);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (query.trim() && !loading) {
        handleStreamedChat(query, mode);
      }
    }
  };

  const toggleMode = (): void => {
    const newMode = mode === 'company' ? 'general' : 'company';
    setMode(newMode);
  };

  const toggleTheme = (): void => {
    setDarkMode(!darkMode);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1 className="app-title">
            <span className="brand-emoji">🐄</span>
            Flash AI Assistant
          </h1>
          <div className="mode-badge" data-mode={mode}>
            {mode === 'company' ? '🐄 Flash Team' : '🌐 General'}
          </div>
        </div>
        <div className="header-controls">
          <button 
            className="control-btn mode-toggle"
            onClick={toggleMode}
            title="Toggle Mode"
          >
            {mode === 'company' ? '🌐' : '🐄'}
          </button>
          <button 
            className="control-btn theme-toggle"
            onClick={toggleTheme}
            title="Toggle Theme"
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
          <button 
            className="control-btn new-chat"
            onClick={createNewConversation}
            title="New Chat"
          >
            ✨
          </button>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <div className="welcome-icon">🐄</div>
              <h2>Welcome to Flash AI Assistant</h2>
              <p>
                {mode === 'company' 
                  ? 'Ask me anything about Flash Group documentation, teams, and processes.' 
                  : 'I can help you with general questions and tasks.'}
              </p>
              <div className="mode-info">
                <strong>Current Mode:</strong> {mode === 'company' ? 'Flash Team' : 'General'}
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-content">
                <div className="message-text">{message.content}</div>
                
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <div className="sources-header">📚 Sources:</div>
                    {message.sources.map((source, idx) => (
                      <div key={idx} className="source-item">
                        <a href={source.url} target="_blank" rel="noopener noreferrer">
                          {source.title || 'Document'}
                        </a>
                        {source.relevance_score && (
                          <span className="relevance-score">
                            ({Math.round(source.relevance_score * 100)}% relevant)
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {message.confidence && (
                  <div className="confidence-indicator">
                    <div className="confidence-bar">
                      <div 
                        className="confidence-fill"
                        style={{ width: `${message.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="confidence-text">
                      {Math.round(message.confidence * 100)}% confidence
                    </span>
                  </div>
                )}

                <div className="message-timestamp">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}

          {isThinking && (
            <div className="thinking-indicator">
              <div className="thinking-header">
                <span className="thinking-icon">🧠</span>
                <span>Flash AI is thinking...</span>
              </div>
              <div className="thinking-steps">
                {thinkingSteps.map((step, index) => (
                  <div key={index} className="thinking-step">
                    <span className="step-icon">•</span>
                    <span className="step-message">{step.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}
        </div>

        <form className="input-container" onSubmit={handleSubmit}>
          <div className="input-wrapper">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={`Ask ${mode === 'company' ? 'Flash AI' : 'anything'}...`}
              className="chat-input"
              rows={1}
              disabled={loading}
              onKeyDown={handleKeyDown}
            />
            <button 
              type="submit" 
              className="send-button"
              disabled={loading || !query.trim()}
            >
              {loading ? '⏳' : '🚀'}
            </button>
          </div>
          <div className="input-footer">
            <span className="mode-indicator">
              Mode: {mode === 'company' ? '🐄 Flash Team' : '🌐 General'}
            </span>
          </div>
        </form>
      </main>
    </div>
  );
};

export default App; 