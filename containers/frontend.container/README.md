# 🌐 Frontend Container

**Port**: 3000  
**Purpose**: Modern React-based user interface for Flash AI Assistant  
**Technology**: React 18 + TypeScript + CSS Custom Properties  

## 📌 Container Purpose

The Frontend Container provides the primary user interface for the AskFlash Modular system, delivering a modern, responsive React application with sophisticated chat interface patterns inspired by ChatGPT and Claude.

### Key Features Preserved from Legacy

- **🐄 Flash Branding**: Complete Flash Group visual identity with #7ed321 green theme
- **Dual Mode Interface**: Company/General mode switching with visual indicators
- **Streaming Chat UX**: Real-time "thinking steps" display during AI processing
- **Dark/Light Themes**: User preference-driven theme system
- **Responsive Design**: Works across desktop, tablet, and mobile devices
- **Markdown Support**: Rich text rendering with syntax highlighting
- **Source Citations**: Clickable links to documentation sources
- **Confidence Indicators**: Visual quality scoring for AI responses

## 🔗 Communication Patterns

### Outbound (Frontend → Backend)
- **Gateway API** (`http://gateway:8000`) - All backend communication
- **WebSocket Streaming** - Real-time chat updates
- **REST APIs** - Standard CRUD operations
- **Authentication** - JWT token management

### Technology Stack

```javascript
// Primary Dependencies
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0", 
  "typescript": "^4.9.5",
  "react-markdown": "^9.1.0",
  "react-syntax-highlighter": "^15.6.1",
  "axios": "^1.6.2"
}

// Development Dependencies
{
  "react-scripts": "5.0.1",
  "@types/react": "^18.2.42",
  "@types/node": "^16.18.68"
}
```

## ⚙️ Configuration

### Environment Variables

```env
# Backend Gateway
REACT_APP_API_URL=http://localhost:8000

# WebSocket Streaming
REACT_APP_WS_URL=ws://localhost:8000/ws

# Flash Branding
REACT_APP_BRAND_NAME=Flash AI Assistant
REACT_APP_BRAND_COLOR=#7ed321
REACT_APP_BRAND_EMOJI=🐄

# Feature Flags
REACT_APP_ENABLE_STREAMING=true
REACT_APP_ENABLE_THINKING_STEPS=true
REACT_APP_ENABLE_DARK_MODE=true
```

### Local Storage Management

```javascript
// User Preferences (Persistent)
localStorage.setItem('flash-theme', 'light|dark');
localStorage.setItem('flash-streaming', 'true|false');
localStorage.setItem('flash-mode', 'company|general');

// Session Management
sessionStorage.setItem('conversation-id', uuid);
sessionStorage.setItem('auth-token', jwt);
```

## 🎨 Component Architecture

### Core Components

```
Flash AI Assistant (App.js)
├── 🎯 Router & Navigation
├── 🔐 Authentication Provider
└── 💬 Chat Interface (Chat.js)
    ├── Header Component
    │   ├── 🐄 Flash Brand Logo
    │   ├── Mode Indicator (Company/General)
    │   └── Controls (Theme/New Chat/Settings)
    ├── Messages Container
    │   ├── Welcome Message (Flash-branded)
    │   ├── Conversation Messages
    │   │   ├── User Messages
    │   │   └── Assistant Messages
    │   │       ├── Markdown Content
    │   │       ├── 📚 Source Citations
    │   │       ├── 📊 Confidence Indicators
    │   │       └── 🧠 Thinking Process (Expandable)
    │   ├── 🤔 Real-time Thinking Indicator
    │   └── ⌨️ Typing Indicator
    └── Input Container
        ├── Auto-resizing Textarea
        ├── Send Button (🚀)
        └── Mode-specific Styling
```

### State Management

```typescript
// Global Application State
interface AppState {
  // UI Preferences
  theme: 'light' | 'dark';
  mode: 'company' | 'general';
  streamingEnabled: boolean;
  
  // Chat State
  messages: Message[];
  conversationId: string;
  isLoading: boolean;
  error: string | null;
  
  // Streaming State
  isThinking: boolean;
  thinkingSteps: ThinkingStep[];
  currentStep: string;
  
  // Authentication
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

// Message Interface
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  mode?: 'company' | 'general';
  sources?: Source[];
  confidence?: number;
  thinkingSteps?: ThinkingStep[];
  metadata?: Record<string, any>;
}
```

## 🧪 Testing Strategy

### Component Testing

```bash
# Unit tests for components
npm run test

# Test coverage report
npm run test:coverage

# Visual regression testing
npm run test:visual
```

### Integration Testing

```javascript
// Chat Integration Test
describe('Chat Integration', () => {
  test('should send message and receive streaming response', async () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Hello Flash AI' } });
    fireEvent.click(sendButton);
    
    // Should show thinking indicator
    expect(screen.getByText(/Flash AI is thinking/i)).toBeInTheDocument();
    
    // Should receive response
    await waitFor(() => {
      expect(screen.getByText(/Hello! I'm Flash AI/i)).toBeInTheDocument();
    });
  });
});
```

## 🐳 Docker Configuration

### Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Serve with nginx
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
```

### Build Commands

```bash
# Development
docker build -t askflash-frontend:dev .
docker run -p 3000:3000 askflash-frontend:dev

# Production
docker build -t askflash-frontend:prod --target production .
docker run -p 3000:80 askflash-frontend:prod
```

## 🔄 Legacy Migration Notes

### Preserved UI/UX Features

✅ **Flash Branding System**
- Green primary color (#7ed321)
- 🐄 Cow emoji brand identity
- "Making enterprise knowledge easier" messaging
- Custom Flash-themed loading animations

✅ **Advanced Chat Interface**
- ChatGPT/Claude-style conversation layout
- Real-time streaming with thinking steps
- Expandable thinking process history
- Source citation with clickable links
- Confidence scoring visual indicators

✅ **Theme System**
- CSS custom properties for dynamic theming
- Dark/light mode toggle with persistence
- Responsive design patterns
- Accessible color contrasts

✅ **Mode Management**
- Company/General mode switching
- Visual mode indicators in header
- Mode-specific UI styling
- Context-aware welcome messages

### Modernization Improvements

🔄 **Technology Stack Upgrade**
- React 18 with concurrent features
- TypeScript for better developer experience
- Modern CSS with custom properties
- Improved accessibility (WCAG 2.1)

🔄 **Performance Optimizations**
- Code splitting for faster initial loads
- Optimized bundle sizes
- Lazy loading for heavy components
- Efficient re-rendering patterns

🔄 **Developer Experience**
- Hot module replacement for development
- Comprehensive TypeScript types
- ESLint and Prettier configuration
- Jest testing setup with React Testing Library

## 🚀 Deployment

### Development Mode

```bash
npm start
# Runs on http://localhost:3000
# Hot reload enabled
# Proxies API calls to http://localhost:8000
```

### Production Build

```bash
npm run build
# Creates optimized production build
# Static files in build/ directory
# Ready for nginx or CDN deployment
```

---

**Frontend Container Status**: 🚧 Ready for implementation  
**Legacy Features**: ✅ All major UI/UX patterns documented  
**Next Steps**: Implement React components following legacy patterns 