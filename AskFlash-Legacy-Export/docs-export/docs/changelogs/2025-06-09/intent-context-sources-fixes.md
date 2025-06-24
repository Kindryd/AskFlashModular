# Intent Layer & Source Context Fixes

**Date:** 2024-12-27  
**Priority:** Critical  
**Type:** Bug Fixes + Feature Enhancement

## Issues Identified & Fixed

### 1. **Intent Layer Missing Context**
- **Problem:** Intent AI incorrectly identified user intent, missing clarifications like "I meant like for example Rashelle is the SRE for Lynx and such"
- **Root Cause:** Intent AI prompt didn't handle user clarifications and follow-up context properly
- **Fix:** Enhanced Intent AI prompt with explicit context understanding rules

### 2. **Hard 5-Source Limit**
- **Problem:** System always returned exactly 5 sources regardless of relevance
- **Root Cause:** Hard-coded limit in source filtering
- **Fix:** Removed hard limit, now shows all relevant sources (threshold 0.4+) up to 10 max

### 3. **Information Loss Between Crawling & Response**
- **Problem:** Logs showed 10 docs found but AI responses seemed limited
- **Root Cause:** Misunderstanding - AI actually uses ALL sources for context, but UI only shows filtered ones
- **Fix:** Added clarifying logs and documentation

### 4. **Missing Inline Hyperlinks**
- **Problem:** AI not providing clickable links within response text
- **Root Cause:** System prompt didn't include hyperlink instructions
- **Fix:** Added comprehensive hyperlink requirements to system prompt

### 5. **AI Constrained by Filtered Sources**
- **Problem:** User concern that AI was limited to only displayed sources
- **Root Cause:** Unclear communication about what sources AI actually uses
- **Fix:** Clarified that AI uses ALL found sources, filtered list is just for UI display

## Technical Changes

### `backend/app/services/streaming_ai.py`

#### Source Filtering Logic Update
```python
# BEFORE: Hard limit to 5 sources
if len(filtered_sources) >= 5:
    break

# AFTER: Dynamic limit based on relevance, up to 10 max  
if len(filtered_sources) >= 10:
    break

# Lowered threshold from 0.5 to 0.4 for more inclusive results
relevance_threshold = 0.4  # Lowered threshold to include more sources
```

#### Enhanced System Prompt - Added Hyperlink Requirements
```python
HYPERLINK REQUIREMENTS:
- **ALWAYS include inline hyperlinks when referencing specific documents or sources**
- Format as markdown: [Document Name](https://full-url-here)
- Example: "According to the [SRE Wiki](https://dev.azure.com/flashmobilevending/SRE-DevOPS/_wiki/wikis/SRE-DevOPS_wiki/SRE-DevOPS_wiki), Rashelle works with the Stallions team"
- **DO NOT just list sources at the end - make references clickable within the response text**

INFORMATION HANDLING:
- **Use ALL available documentation sources for context, not just the ones shown in the Sources list**
- **The AI has access to more documentation than what's displayed in the final Sources list**
```

#### Context Usage Clarification
```python
logger.info(f"IMPORTANT: AI will use ALL {len(sources)} sources for context generation, not just filtered ones shown in UI")
logger.info(f"Built context from ALL {len(sources)} sources for comprehensive AI response")
logger.info(f"Using max_tokens: {max_tokens} for company mode with ALL {len(sources)} sources in context")
```

### `backend/app/services/conversation_intent_ai.py`

#### Enhanced Intent Analysis Prompt
```python
CRITICAL: For needs_documentation_search, follow these rules:
- TRUE if: user provides examples or clarifications that need verification (e.g., "I meant like Rashelle is the SRE for Lynx")
- TRUE if: user is asking for additional information beyond what was previously provided
- TRUE if: user is asking follow-up questions that expand on previous topics

CONTEXT UNDERSTANDING:
- If user says "I meant..." or "like for example..." they're providing clarification that needs documentation search
- Follow-up questions often need fresh documentation even if the topic was discussed before
- User examples and clarifications should trigger documentation search to verify and expand information
- When in doubt, default to TRUE for documentation search - it's better to over-search than miss relevant information
```

## How It Works Now

### Source Flow Clarification
1. **Search Phase:** Documentation service finds 10+ relevant sources
2. **AI Context:** ALL found sources are used to build AI context (up to context window limit)
3. **AI Response:** Generated using ALL available information
4. **UI Display:** Only most relevant sources (0.4+ threshold, max 10) shown in Sources list
5. **Inline Links:** AI includes clickable hyperlinks within response text

### Intent AI Improvements
- Better handles user clarifications and examples
- Recognizes follow-up questions that need fresh documentation
- Defaults to documentation search when uncertain
- Improved context understanding for conversational flow

## Expected Improvements

1. **More Comprehensive Responses:** AI now uses all available documentation, not limited to displayed sources
2. **Better Source Relevance:** Shows 4-10 relevant sources instead of always 5
3. **Clickable References:** Inline hyperlinks make responses more navigable
4. **Improved Follow-up Handling:** Intent AI better understands user clarifications and context
5. **No Information Loss:** Clear that AI uses ALL found documentation for context

## Testing Recommendations

1. Test follow-up questions with clarifications like "I meant like X does Y"
2. Verify inline hyperlinks appear in AI responses
3. Check that relevant sources list is dynamic (not always 5)
4. Confirm AI responses use information from all found sources
5. Test complex team/people questions for comprehensive coverage

## Files Modified

- `backend/app/services/streaming_ai.py` - Source filtering, hyperlinks, context clarification
- `backend/app/services/conversation_intent_ai.py` - Enhanced intent analysis prompt
- `docs/changelogs/2024-12-27/intent-context-sources-fixes.md` - This changelog 