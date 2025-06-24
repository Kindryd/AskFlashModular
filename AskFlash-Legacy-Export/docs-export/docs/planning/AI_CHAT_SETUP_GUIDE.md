# AskFlash AI Chat Feature - Setup Guide

## 🎉 **Implementation Complete!**

The AI Chat feature has been successfully implemented and is ready for use. This guide will help you get it running.

## 🏗️ **What Was Implemented**

### ✅ **Backend Features**
- **AI Chat Endpoint**: `/api/v1/chat/chat` for processing chat requests
- **Conversation History**: `/api/v1/chat/history` for retrieving chat history
- **Dual-Mode Support**: 
  - **Company Mode**: Uses RAG with your documentation
  - **General Mode**: Direct GPT-4 conversations
- **OpenAI GPT-4 Integration**: Full async implementation
- **Vector Search**: Qdrant integration for enhanced document retrieval
- **Conversation Management**: Persistent chat history and context
- **Ruleset Integration**: AI behavior controlled by configurable rulesets

### ✅ **Frontend Features**
- **Modern Chat Interface**: Clean, responsive React component
- **Real-time Messaging**: Instant responses with loading states
- **Mode Switching**: Toggle between company and general modes
- **Source Attribution**: Shows documentation sources when available
- **Confidence Scoring**: Displays AI confidence levels
- **Conversation History**: Persistent chat sessions
- **Error Handling**: Graceful error display and recovery

### ✅ **Infrastructure**
- **Qdrant Vector Database**: Ready for document embeddings
- **PostgreSQL Integration**: Chat history stored in database
- **Docker Compose**: All services containerized
- **Environment Configuration**: Flexible configuration system

## 🚀 **Quick Start**

### 1. **Environment Setup**

Copy the environment template and configure it:

```powershell
Copy-Item env-template.txt backend\.env
```

Edit `backend\.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=your-actual-openai-api-key-here
```

### 2. **Start the Services**

Using Docker Compose (recommended):
```powershell
docker-compose up -d
```

Or manually start each service:

**Backend:**
```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```powershell
Set-Location frontend
npm start
```

### 3. **Access the Application**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Qdrant UI**: http://localhost:6333/dashboard

## 💬 **Using the Chat Feature**

### **Company Mode** (Default)
- Ask questions about your company documentation
- Get responses with source citations
- Higher confidence when relevant docs are found
- Example: "How do I deploy the application?"

### **General Mode**
- Ask general questions not related to company docs
- Direct GPT-4 responses without document search
- Good for general programming or knowledge questions
- Example: "Explain async/await in Python"

### **Features to Try**
1. **Mode Switching**: Toggle between company and general modes
2. **Conversation Continuity**: Ask follow-up questions in the same chat
3. **Source Review**: Click on source links in company mode responses
4. **New Conversations**: Start fresh chats for different topics

## 🔧 **Configuration**

### **Ruleset Configuration**
The AI behavior is controlled by rulesets in the database. The default ruleset includes:

- **AI Behavior Rules**: Professional tone, source citation requirements
- **Mode Settings**: Temperature, token limits, confidence thresholds
- **Response Guidelines**: Formatting preferences, error handling

### **Environment Variables**
Key variables you may want to adjust:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `QDRANT_HOST`: Vector database host (default: localhost)
- `EMBEDDING_MODEL`: Sentence transformer model (default: all-MiniLM-L6-v2)
- `SECRET_KEY`: JWT secret for authentication

## 🔍 **Troubleshooting**

### **Common Issues**

1. **"OpenAI API key not configured"**
   - Solution: Add your API key to `backend/.env`

2. **"Chat endpoint not found"**
   - Solution: Ensure backend is running and chat.py is properly imported

3. **"No responses in company mode"**
   - Solution: Check if documentation is indexed in Qdrant

4. **"Frontend can't connect to backend"**
   - Solution: Verify backend is running on port 8000

### **Check Service Status**

```powershell
# Check if backend is running
Invoke-RestMethod -Uri "http://localhost:8000/docs" -Method Get

# Check if Qdrant is running
Invoke-RestMethod -Uri "http://localhost:6333/dashboard" -Method Get

# Check if frontend is running
Invoke-RestMethod -Uri "http://localhost:3000" -Method Get
```

## 📚 **Next Steps**

### **Immediate Enhancements**
1. **Add Authentication**: Implement user login for personalized chats
2. **Index Documentation**: Load your company docs into Qdrant
3. **Customize Rulesets**: Adjust AI behavior for your organization
4. **Monitor Usage**: Track chat interactions and performance

### **Future Features**
1. **File Upload**: Chat about uploaded documents
2. **Integration**: Connect to Slack, Teams, or other platforms
3. **Analytics**: Usage statistics and feedback collection
4. **Advanced RAG**: Implement more sophisticated retrieval strategies

## 🎯 **Key Files**

### **Backend**
- `backend/app/api/api_v1/endpoints/chat.py` - Chat endpoints
- `backend/app/services/ai.py` - OpenAI integration
- `backend/app/schemas/chat.py` - Chat data models
- `backend/app/services/vector_store.py` - Qdrant integration

### **Frontend**
- `frontend/src/Chat.js` - Main chat component
- `frontend/src/App.js` - Navigation and layout

### **Configuration**
- `backend/.env` - Environment variables
- `docker-compose.yml` - Service orchestration
- `ARCHITECTURE.md` - Technical documentation

## ✨ **Success Indicators**

You'll know everything is working when:
- ✅ Chat interface loads at http://localhost:3000
- ✅ You can send messages and get AI responses
- ✅ Mode switching works between company and general
- ✅ Conversation history persists within a session
- ✅ Sources are shown for company mode responses
- ✅ Error messages are displayed clearly

**Congratulations! Your AskFlash AI Assistant is ready to help your team! 🚀** 