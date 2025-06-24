# 🚀 Azure DevOps Wiki Auto-Expander & Index Extractor

This enhanced script automatically **expands all tree items** in Azure DevOps Project Wiki and then extracts the complete structured index without manual scrolling.

---

## ✅ What This Does

- **Automatically expands** all collapsible wiki sections
- **Waits for content** to load dynamically
- **Recursively finds** and expands nested items
- **Captures complete structure** with depth levels
- **Outputs clean JSON** with `title`, `path`, and `level`

---

## 🧰 Tools Used

- JavaScript (run in browser console)
- Python (to format console output into structured JSON)

---

## 🧪 Step-by-Step Instructions

### 1. Open Azure DevOps Wiki

- Navigate to your Project Wiki
- **Don't expand anything manually** - the script will do it

---

### 2. Paste This Enhanced JavaScript in Browser Console

Press `F12` → Console → Paste this complete script:

```javascript
// Azure DevOps Wiki Auto-Expander & Index Extractor (Fixed Version)
// This script automatically expands all tree items and captures the complete structure
// Fixed: Only expands collapsed items, never closes expanded ones
// Added: Stop command functionality

const WikiAutoExpander = {
    seen: new Set(),
    stack: [],
    expandedCount: 0,
    processedButtons: new Set(), // Track processed buttons to avoid double-clicking
    shouldStop: false, // Stop flag
    
    // Build hierarchical path from title and level
    buildPath(title, level) {
        while (this.stack.length && this.stack[this.stack.length - 1].level >= level) {
            this.stack.pop();
        }
        const path = this.stack.length ? `${this.stack[this.stack.length - 1].path}/${title}` : title;
        this.stack.push({ title, path, level });
        return path;
    },

    // Stop the expansion process
    stop() {
        this.shouldStop = true;
        console.log('🛑 Stop requested. The script will finish the current batch and then stop.');
    },

    // Check if an expand button is actually collapsed (not expanded)
    isButtonCollapsed(button) {
        // Multiple ways to check if button represents a collapsed state
        const ariaExpanded = button.getAttribute('aria-expanded');
        const isExpanded = button.classList.contains('is-expanded') || 
                          button.classList.contains('expanded') ||
                          ariaExpanded === 'true';
        
        // Also check parent row for expanded state indicators
        const row = button.closest('tr, .tree-row, [data-testid="tree-row"]');
        if (row) {
            const rowExpanded = row.classList.contains('is-expanded') ||
                              row.querySelector('.expanded') ||
                              row.getAttribute('aria-expanded') === 'true';
            
            if (rowExpanded) return false;
        }
        
        return !isExpanded;
    },

    // Generate unique ID for button to track processed ones
    getButtonId(button) {
        // Try to get a unique identifier for the button
        const row = button.closest('tr, .tree-row, [data-testid="tree-row"]');
        if (row) {
            const textElement = row.querySelector('.tree-name-text, .bolt-tree-row-content, .tree-item-text');
            if (textElement) {
                const text = textElement.textContent.trim();
                const level = row.getAttribute('aria-level') || '1';
                return `${level}::${text}`;
            }
        }
        
        // Fallback to button position
        const rect = button.getBoundingClientRect();
        return `btn_${Math.round(rect.top)}_${Math.round(rect.left)}`;
    },

    // Find all truly expandable (collapsed) tree items
    findExpandableItems() {
        const expandButtons = [];
        
        // Look for various expand button selectors used in Azure DevOps
        const selectors = [
            '.bolt-tree-expand-button',
            '.tree-expand-button', 
            '[data-testid="tree-expand-button"]',
            '.bolt-button.bolt-tree-expand-button'
        ];
        
        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(btn => {
                if (btn.offsetParent !== null) { // Only visible elements
                    const buttonId = this.getButtonId(btn);
                    
                    // Skip if already processed
                    if (this.processedButtons.has(buttonId)) {
                        return;
                    }
                    
                    // Only include if actually collapsed
                    if (this.isButtonCollapsed(btn)) {
                        expandButtons.push(btn);
                    }
                }
            });
        });
        
        return expandButtons;
    },

    // Click an expand button and wait for content
    async expandItem(button) {
        try {
            const buttonId = this.getButtonId(button);
            
            // Mark as processed immediately to avoid double-clicking
            this.processedButtons.add(buttonId);
            
            console.log(`🔧 Expanding item ${this.expandedCount + 1}... (ID: ${buttonId.substring(0, 50)})`);
            button.click();
            this.expandedCount++;
            
            // Wait for dynamic content to load
            await this.waitForContent();
        } catch (error) {
            console.warn('⚠️ Failed to expand item:', error);
        }
    },

    // Wait for new content to load
    waitForContent() {
        return new Promise(resolve => {
            let attempts = 0;
            const maxAttempts = 20; // 2 seconds max wait
            
            const checkInterval = setInterval(() => {
                attempts++;
                if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    resolve();
                }
                
                // Check if loading indicators are gone
                const loadingElements = document.querySelectorAll(
                    '.bolt-spinner, .loading, .bolt-progress-indicator, [data-testid="loading"]'
                );
                
                if (loadingElements.length === 0) {
                    clearInterval(checkInterval);
                    setTimeout(resolve, 100); // Small delay for stability
                }
            }, 100);
        });
    },

    // Expand all items recursively
    async expandAllItems() {
        console.log('🚀 Starting automatic expansion of all wiki items...');
        console.log('💡 To stop the script at any time, run: WikiAutoExpander.stop()');
        
        let round = 1;
        let expandableItems;
        
        do {
            // Check stop flag
            if (this.shouldStop) {
                console.log('🛑 Expansion stopped by user request.');
                break;
            }
            
            console.log(`📖 Expansion round ${round}...`);
            expandableItems = this.findExpandableItems();
            
            if (expandableItems.length === 0) {
                console.log('✅ No more expandable items found.');
                break;
            }
            
            console.log(`🔍 Found ${expandableItems.length} expandable items in round ${round}`);
            
            // Expand items in batches to avoid overwhelming the UI
            for (let i = 0; i < expandableItems.length; i += 3) {
                // Check stop flag before each batch
                if (this.shouldStop) {
                    console.log('🛑 Expansion stopped by user request.');
                    return;
                }
                
                const batch = expandableItems.slice(i, i + 3);
                
                // Expand batch items
                for (const button of batch) {
                    // Double-check button is still valid and collapsed
                    if (button.offsetParent !== null && this.isButtonCollapsed(button)) {
                        await this.expandItem(button);
                    }
                }
                
                // Wait between batches
                await new Promise(resolve => setTimeout(resolve, 200));
            }
            
            // Wait for all content to stabilize
            await this.waitForContent();
            round++;
            
        } while (expandableItems.length > 0 && round < 50 && !this.shouldStop); // Safety limit + stop check
        
        if (!this.shouldStop) {
            console.log(`🎉 Expansion complete! Expanded ${this.expandedCount} items in ${round - 1} rounds.`);
        }
    },

    // Capture all visible wiki items
    captureWikiStructure() {
        console.log('📋 Capturing wiki structure...');
        this.seen.clear();
        this.stack = [];
        
        const rows = document.querySelectorAll("tr.bolt-tree-row, .tree-row, [data-testid='tree-row']");
        
        rows.forEach(row => {
            if (row.offsetParent !== null) { // Only visible rows
                const level = parseInt(row.getAttribute("aria-level") || "1");
                
                // Try multiple selectors for the text content
                const textSelectors = [
                    ".tree-name-text",
                    ".bolt-tree-row-content", 
                    ".tree-item-text",
                    "[data-testid='tree-item-text']",
                    ".ms-List-cell .ms-Button-textContainer"
                ];
                
                let span = null;
                for (const selector of textSelectors) {
                    span = row.querySelector(selector);
                    if (span) break;
                }
                
                if (span) {
                    const title = span.textContent.trim();
                    if (title) {
                        const id = `${level}::${title}`;
                        if (!this.seen.has(id)) {
                            const path = this.buildPath(title, level);
                            console.log(`[WIKI-INDEX] ${path}`);
                            this.seen.add(id);
                        }
                    }
                }
            }
        });
        
        console.log(`✅ Captured ${this.seen.size} unique wiki items.`);
    },

    // Reset the expander state for a new wiki
    reset() {
        this.seen.clear();
        this.stack = [];
        this.expandedCount = 0;
        this.processedButtons.clear();
        this.shouldStop = false;
        console.log('🔄 WikiAutoExpander reset. Ready for a new wiki.');
    },

    // Main execution function
    async run() {
        console.log('🎯 Starting Azure DevOps Wiki Auto-Expander...');
        console.log('💡 To stop the script at any time, run: WikiAutoExpander.stop()');
        console.log('🔄 To reset for a new wiki, run: WikiAutoExpander.reset()');
        
        try {
            // Step 1: Expand all items
            await this.expandAllItems();
            
            if (!this.shouldStop) {
                // Step 2: Wait for final stabilization
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Step 3: Capture the complete structure
                this.captureWikiStructure();
                
                console.log('🏁 Wiki auto-expansion and capture complete!');
                console.log('💾 Right-click in console → "Save console output as..." → wiki_console_output.txt');
            }
            
        } catch (error) {
            console.error('❌ Error during wiki expansion:', error);
        }
    }
};

// Make WikiAutoExpander globally accessible for stop/reset commands
window.WikiAutoExpander = WikiAutoExpander;

// Start the process
WikiAutoExpander.run();
```

---

### 3. Control the Script Execution

The script will:
- 🔍 **Find all expandable items** (only collapsed ones)
- 🔧 **Automatically expand them** (never closes already expanded items)
- ⏳ **Wait for content to load**
- 🔄 **Repeat until everything is expanded**
- 📋 **Capture the complete structure**

**Control Commands:**
- 🛑 **To Stop:** `WikiAutoExpander.stop()` (finishes current batch then stops)
- 🔄 **To Reset:** `WikiAutoExpander.reset()` (prepare for next wiki page)

Watch the console for progress updates!

---

### 4. For Multiple Wiki Pages (Optional)

If you have multiple wiki pages to process:

1. **Run the script on first wiki page**
2. **When ready to switch:** `WikiAutoExpander.stop()`
3. **Navigate to next wiki page**
4. **Reset the script:** `WikiAutoExpander.reset()`
5. **Run again:** `WikiAutoExpander.run()`

### 5. Save the Console Output

Once the script completes:
- Right-click in console → **Save console output as...**
- Save to `wiki_console_output.txt`

---

### 6. Run the Python Parser Script

Create `parse_wiki_console_output.py`:

```python
import json
import re

INPUT_FILE = "wiki_console_output.txt"
OUTPUT_FILE = "cleaned_wiki_index.json"

def parse_wiki_output():
    wiki_entries = []
    seen_paths = set()
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "[WIKI-INDEX]" not in line:
                continue
            
            # Extract path from console output
            path = line.split("[WIKI-INDEX]")[-1].strip()
            
            # Skip duplicates
            if path in seen_paths:
                continue
            seen_paths.add(path)
            
            # Build entry
            parts = path.split("/")
            title = parts[-1]
            level = len(parts)
            
            wiki_entries.append({
                "title": title,
                "path": path,
                "level": level
            })
    
    # Sort by path for consistent ordering
    wiki_entries.sort(key=lambda x: x["path"].lower())
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(wiki_entries, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Parsed {len(wiki_entries)} unique wiki entries")
    print(f"📄 Output saved to {OUTPUT_FILE}")
    
    # Show some stats
    levels = {}
    for entry in wiki_entries:
        level = entry["level"]
        levels[level] = levels.get(level, 0) + 1
    
    print("\n📊 Structure Summary:")
    for level in sorted(levels.keys()):
        print(f"   Level {level}: {levels[level]} items")

if __name__ == "__main__":
    parse_wiki_output()
```

Then run:
```bash
python parse_wiki_console_output.py
```

---

## 🎯 Key Improvements Over Manual Method

### **Smart Expansion Logic**
- ✅ **Only expands collapsed items** - never closes already expanded ones
- ✅ **Tracks processed buttons** - prevents double-clicking
- ✅ **State validation** - checks aria-expanded and CSS classes
- ✅ **Unique ID generation** - based on content + level for accuracy

### **User Control**
- ✅ **Stop command** - `WikiAutoExpander.stop()` for graceful termination
- ✅ **Reset command** - `WikiAutoExpander.reset()` for processing multiple wikis
- ✅ **Progress reporting** - detailed console output with item IDs
- ✅ **Global accessibility** - commands available from anywhere in console

### **Robust Element Detection**
- ✅ Multiple selector strategies for different Azure DevOps versions
- ✅ Handles various expand button types
- ✅ Fallback text content selectors
- ✅ Parent row state checking for expanded indicators

### **Performance Optimized**
- ✅ Batch processing to avoid UI overload
- ✅ Smart waiting for content loading
- ✅ Duplicate detection and prevention
- ✅ State validation before each click

### **Error Handling**
- ✅ Graceful failure handling
- ✅ Progress reporting with unique IDs
- ✅ Safety limits to prevent infinite loops
- ✅ User-controlled stopping mechanism

---

## 🔧 Troubleshooting

### **If Some Items Don't Expand:**
- Run the script again (some dynamic content may need multiple passes)
- Check browser console for any error messages
- Ensure you have proper permissions to view the wiki

### **If Script Seems Stuck:**
- Check the console for progress messages
- The script has safety limits and will eventually complete
- You can manually interrupt and run the capture portion

### **For Different Azure DevOps Versions:**
- The script includes multiple selector strategies
- If it doesn't work, inspect the expand buttons in DevTools to find the correct selectors

---

## 📦 Output Format

Same as the manual method - clean JSON structure:

```json
[
  {
    "title": "SRE Wiki", 
    "path": "SRE Wiki",
    "level": 1
  },
  {
    "title": "Teams",
    "path": "Teams", 
    "level": 1
  },
  {
    "title": "Platform Team",
    "path": "Teams/Platform Team",
    "level": 2
  }
]
```

---

## 🚀 Usage Tips

1. **Run during off-peak hours** - Expanding large wikis can take a few minutes
2. **Keep the browser tab active** - Background tabs may have limited JavaScript execution
3. **Check your network connection** - Dynamic loading requires stable connectivity
4. **Save intermediate results** - The script shows progress, so you can stop and save anytime

This enhanced script should capture your complete Azure DevOps wiki structure automatically! 🎉 