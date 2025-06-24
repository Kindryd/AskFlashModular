# Microsoft Teams Integration Setup Guide

## Prerequisites

1. **Azure Account**: Access to Azure portal for bot registration
2. **Teams Admin Access**: Ability to install custom apps in Microsoft Teams
3. **Flash AI Backend**: Running Flash AI Assistant backend

## Step 1: Bot Framework Registration

### Option A: Azure Bot Service (Recommended for Production)

1. Go to [Azure Portal](https://portal.azure.com)
2. Create new resource → "Azure Bot"
3. Configure bot settings:
   - **Bot handle**: `flash-ai-assistant`
   - **Subscription**: Your Azure subscription
   - **Resource group**: Create or select existing
   - **Pricing tier**: F0 (Free) for development
   - **Bot type**: "User-Assigned Managed Identity" or "Multi Tenant"
4. After creation, note down:
   - **Microsoft App ID**: This becomes `TEAMS_APP_ID`
   - **Microsoft App Password**: Generate and note as `TEAMS_APP_PASSWORD`

### Option B: Teams Developer Portal (Easier for Development)

1. Go to [Teams Developer Portal](https://dev.teams.microsoft.com)
2. Click "Apps" → "New app"
3. Configure basic information:
   - **Name**: Flash AI Assistant
   - **Description**: Enterprise AI assistant for Flash Group
   - **Developer**: Flash Group
4. Go to "App features" → "Bot"
5. Create new bot or use existing Bot Framework registration
6. Note the App ID and generate App Password

## Step 2: Environment Configuration

Add the following environment variables to your `.env` file:

```bash
# Microsoft Teams Bot Framework Configuration
TEAMS_APP_ID=your-microsoft-app-id-here
TEAMS_APP_PASSWORD=your-microsoft-app-password-here
TEAMS_TENANT_ID=your-azure-tenant-id-here
API_URL=https://your-domain.com

# Example for development
# TEAMS_APP_ID=12345678-1234-1234-1234-123456789012
# TEAMS_APP_PASSWORD=your-generated-app-password
# TEAMS_TENANT_ID=87654321-4321-4321-4321-210987654321
# API_URL=https://askflash.your-domain.com
```

## Step 3: Webhook Configuration

1. **Determine your webhook URL**:
   ```
   https://your-domain.com/api/v1/teams/messages
   ```

2. **Configure in Azure Bot Service**:
   - Go to your bot in Azure Portal
   - Navigate to "Configuration"
   - Set "Messaging endpoint" to your webhook URL
   - Save configuration

3. **Configure in Teams Developer Portal**:
   - Go to your app → "App features" → "Bot"
   - Set "Bot endpoint address" to your webhook URL
   - Save configuration

## Step 4: Teams App Installation

### Create App Package

1. **Get app manifest**:
   ```bash
   curl https://your-domain.com/api/v1/teams/manifest
   ```

2. **Create app icons**:
   - `color-icon.png`: 192x192 px with Flash branding
   - `outline-icon.png`: 32x32 px outline version

3. **Create app package**:
   - Create a `.zip` file containing:
     - `manifest.json` (from API call above)
     - `color-icon.png`
     - `outline-icon.png`

### Install in Teams

1. **Upload app package**:
   - Open Microsoft Teams
   - Go to "Apps" → "Manage your apps" → "Upload an app"
   - Upload your `.zip` package

2. **Add to team/chat**:
   - Find "Flash AI Assistant" in your apps
   - Click "Add" → Choose team, channel, or personal chat

## Step 5: Testing

### Health Check
```bash
curl https://your-domain.com/api/v1/teams/health
```

### Test Endpoint
```bash
curl -X POST https://your-domain.com/api/v1/teams/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Flash AI!", "mode": "company"}'
```

### Teams Chat Testing

1. **Direct message**: Send a message to Flash AI bot
2. **Channel mention**: Use `@Flash AI what is our deployment process?`
3. **Slash commands**: Try `/flash help` or `/flash company how do I...`

## Troubleshooting

### Common Issues

1. **Webhook not receiving messages**:
   - Verify webhook URL is publicly accessible (HTTPS required)
   - Check Azure Bot Service messaging endpoint configuration
   - Ensure Bot Framework credentials are correct

2. **Bot not responding**:
   - Check backend logs for errors
   - Verify OpenAI API key is configured
   - Test with `/api/v1/teams/test` endpoint first

3. **Authentication errors**:
   - Verify TEAMS_APP_ID and TEAMS_APP_PASSWORD are correct
   - Check that bot is properly registered in Azure

### Debug Information

```bash
# Check Teams configuration
curl https://your-domain.com/api/v1/teams/config

# View application logs
docker-compose logs backend

# Test individual components
curl -X POST https://your-domain.com/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer fake-token" \
  -d '{"query": "test", "ruleset_id": 4, "mode": "company"}'
```

## Security Considerations

1. **HTTPS Required**: Teams requires HTTPS for webhook endpoints
2. **Authentication**: Bot Framework validates requests automatically
3. **Rate Limiting**: Consider implementing rate limiting for Teams requests
4. **Data Privacy**: Teams messages are logged - ensure compliance

## Production Deployment

1. **Use proper domain**: Configure production domain in API_URL
2. **SSL Certificate**: Ensure valid SSL certificate for webhook endpoint
3. **Monitoring**: Set up monitoring for Teams webhook endpoint
4. **Backup**: Backup Teams app configuration and credentials

## Support Commands

Once installed, users can use these commands in Teams:

- `@Flash AI help` - Show help information
- `/flash company [question]` - Ask company-specific question
- `/flash general [question]` - Ask general AI question
- `/flash help` - Display help message

## Next Steps

After successful setup:

1. **User Training**: Train Flash Group employees on Teams bot usage
2. **Feedback Collection**: Gather user feedback for improvements
3. **Analytics**: Monitor usage patterns and response quality
4. **Feature Enhancement**: Consider adding file upload, voice support, etc.

---

For additional support, refer to the [Teams Integration Plan](teams_integration_plan.md) or contact the development team. 