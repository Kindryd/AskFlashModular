# 🎯 Azure DevOps Wiki Indexer (Enhanced)

This enhanced script automatically **expands all tree items** in Azure DevOps Project Wiki and generates a clean, structured JSON index with minimal console noise.

---

## ✅ What This Does

- **Automatically expands** all collapsible wiki sections
- **Parameterized execution** with wiki name and ID
- **Clean console output** - minimal logging, maximum efficiency
- **Structured JSON output** - matches the expected format
- **Smart expansion logic** - only expands collapsed items
- **User control** - stop/reset commands available

---

## 🧰 Tools Used

- JavaScript (run in browser console)
- Python (optional - for automated file extraction)

---

## 🧪 Step-by-Step Instructions

### 1. Open Azure DevOps Wiki

- Navigate to your Project Wiki
- **Don't expand anything manually** - the script will do it

---

### 2. Paste This Enhanced JavaScript in Browser Console

Press `F12` → Console → Paste this complete script:

```javascript
// Azure DevOps Wiki Indexer (Enhanced)
// Clean, parameterized wiki indexing with auto-expansion
// Usage: WikiIndexer.run("SRE-DevOPS", "dc66cbaa-0364-42e8-9a23-044deb186015")

const WikiIndexer = {
    wikiName: '',
    wikiId: '',
    pages: [],
    seen: new Set(),
    stack: [],
    expandedCount: 0,
    processedButtons: new Set(),
    shouldStop: false,
    
    // Initialize with wiki parameters
    init(wikiName, wikiId) {
        this.wikiName = wikiName;
        this.wikiId = wikiId;
        this.pages = [];
        this.seen.clear();
        this.stack = [];
        this.expandedCount = 0;
        this.processedButtons.clear();
        this.shouldStop = false;
        this.captureActive = false;
    },

    // Build hierarchical path from title and level
    buildPath(title, level) {
        while (this.stack.length && this.stack[this.stack.length - 1].level >= level) {
            this.stack.pop();
        }
        const path = this.stack.length ? `${this.stack[this.stack.length - 1].path}/${title}` : title;
        this.stack.push({ title, path, level });
        return path;
    },

    // Start incremental capture using IntersectionObserver (like original extractor)
    startIncrementalCapture() {
        // Clean up existing observers
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        if (this.mutationObserver) {
            this.mutationObserver.disconnect();
        }

        // Create intersection observer to capture visible wiki items
        this.intersectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.captureWikiItem(entry.target);
                }
            });
        }, {
            root: null,
            rootMargin: '0px',
            threshold: 0.5
        });

        // Start observing existing rows
        this.observeWikiRows();

        // Create mutation observer to watch for new DOM elements
        this.mutationObserver = new MutationObserver(() => {
            this.observeWikiRows();
        });

        this.mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });

        console.log('📋 Incremental wiki capture started - pages will be captured as they become visible');
    },

    // Observe wiki rows for intersection
    observeWikiRows() {
        const rows = document.querySelectorAll("tr.bolt-tree-row, .tree-row, [data-testid='tree-row']");
        rows.forEach(row => {
            if (!row.dataset.wikiObserved && row.offsetParent !== null) {
                this.intersectionObserver.observe(row);
                row.dataset.wikiObserved = "true";
            }
        });
    },

    // Capture individual wiki item when it becomes visible
    captureWikiItem(row) {
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
                    
                    // Add to pages array immediately
                    this.pages.push({
                        title: title,
                        path: path,
                        level: level
                    });
                    
                    this.seen.add(id);
                    console.log(`📄 Captured: ${path}`);
                }
            }
        }
    },

    // Stop the indexing process
    stop() {
        this.shouldStop = true;
        console.log('🛑 WikiIndexer stopped.');
    },

    // Reset for new wiki
    reset() {
        this.init('', '');
        console.log('🔄 WikiIndexer reset.');
    },

    // Force a rescan for any missed items (useful if expansion seems incomplete)
    async rescan() {
        if (!this.wikiName || !this.wikiId) {
            console.error('❌ No active wiki session. Run WikiIndexer.run() first.');
            return;
        }
        
        console.log('🔍 Starting manual rescan for missed items...');
        this.shouldStop = false; // Clear any stop flag
        
        // Clear processed buttons to allow re-expansion
        const oldProcessedCount = this.processedButtons.size;
        this.processedButtons.clear();
        
        await this.expandAllItems();
        
        console.log(`🔍 Rescan complete. Processed ${this.processedButtons.size - oldProcessedCount} additional items`);
    },

    // Debug function to analyze why items aren't being expanded
    debug() {
        console.log('🔧 DEBUGGING: Analyzing visible unexpanded items...');
        
        // Find all visible tree rows
        const rows = document.querySelectorAll('tr.bolt-tree-row, .tree-row, [data-testid="tree-row"], .ms-List-cell');
        const unexpandedItems = [];
        
        rows.forEach(row => {
            if (row.offsetParent !== null) { // Only visible rows
                // Look for text content
                const textSelectors = [".tree-name-text", ".bolt-tree-row-content", ".tree-item-text", "[data-testid='tree-item-text']", ".ms-Button-textContainer"];
                let textElement = null;
                for (const selector of textSelectors) {
                    textElement = row.querySelector(selector);
                    if (textElement) break;
                }
                
                if (textElement) {
                    const title = textElement.textContent.trim();
                    
                    // Look for buttons in this row
                    const buttons = row.querySelectorAll('button');
                    let hasExpandButton = false;
                    let buttonInfo = [];
                    
                    buttons.forEach(btn => {
                        const ariaExpanded = btn.getAttribute('aria-expanded');
                        const classes = Array.from(btn.classList).join(' ');
                        const ariaLabel = btn.getAttribute('aria-label') || '';
                        
                        buttonInfo.push({
                            classes: classes,
                            ariaExpanded: ariaExpanded,
                            ariaLabel: ariaLabel,
                            isExpandable: this.isButtonExpandable(btn)
                        });
                        
                        if (ariaExpanded === 'false' || this.isButtonExpandable(btn)) {
                            hasExpandButton = true;
                        }
                    });
                    
                    // Check for chevron indicators
                    const hasChevronRight = row.querySelector('.ms-Icon--ChevronRight, .chevron-right, [data-icon-name="ChevronRight"]');
                    const hasChevronDown = row.querySelector('.ms-Icon--ChevronDown, .chevron-down, [data-icon-name="ChevronDown"]');
                    
                    if (hasExpandButton || hasChevronRight) {
                        unexpandedItems.push({
                            title: title,
                            hasChevronRight: !!hasChevronRight,
                            hasChevronDown: !!hasChevronDown,
                            buttons: buttonInfo
                        });
                    }
                }
            }
        });
        
        console.log(`🔧 Found ${unexpandedItems.length} potentially unexpanded items:`);
        unexpandedItems.forEach((item, index) => {
            console.log(`${index + 1}. "${item.title}"`);
            console.log(`   Chevron Right: ${item.hasChevronRight}, Chevron Down: ${item.hasChevronDown}`);
            item.buttons.forEach((btn, btnIndex) => {
                console.log(`   Button ${btnIndex + 1}: classes="${btn.classes}", aria-expanded="${btn.ariaExpanded}", expandable=${btn.isExpandable}`);
            });
        });
        
        return unexpandedItems;
    },

    // Check if button is collapsed (reverted to conservative approach)
    isButtonCollapsed(button) {
        const ariaExpanded = button.getAttribute('aria-expanded');
        const isExpanded = button.classList.contains('is-expanded') || 
                          button.classList.contains('expanded') ||
                          ariaExpanded === 'true';
        
        const row = button.closest('tr, .tree-row, [data-testid="tree-row"]');
        if (row) {
            const rowExpanded = row.classList.contains('is-expanded') ||
                              row.querySelector('.expanded') ||
                              row.getAttribute('aria-expanded') === 'true';
            if (rowExpanded) return false;
        }
        
        return !isExpanded;
    },

    // Generate unique button ID
    getButtonId(button) {
        const row = button.closest('tr, .tree-row, [data-testid="tree-row"]');
        if (row) {
            const textElement = row.querySelector('.tree-name-text, .bolt-tree-row-content, .tree-item-text');
            if (textElement) {
                const text = textElement.textContent.trim();
                const level = row.getAttribute('aria-level') || '1';
                return `${level}::${text}`;
            }
        }
        
        const rect = button.getBoundingClientRect();
        return `btn_${Math.round(rect.top)}_${Math.round(rect.left)}`;
    },

    // Find expandable items (reverted to specific wiki navigation selectors)
    findExpandableItems() {
        const expandButtons = [];
        
        // Specific selectors for wiki navigation only
        const selectors = [
            '.bolt-tree-expand-button',
            '.tree-expand-button', 
            '[data-testid="tree-expand-button"]',
            '.bolt-button.bolt-tree-expand-button'
        ];
        
        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(btn => {
                if (btn.offsetParent !== null) { // Only visible elements
                    // Ensure button is within wiki navigation area
                    const wikiContainer = btn.closest('.wiki-tree, .tree-container, .bolt-tree, [data-testid="wiki-tree"]');
                    if (wikiContainer || this.isInWikiNavigation(btn)) {
                        const buttonId = this.getButtonId(btn);
                        if (!this.processedButtons.has(buttonId) && this.isButtonCollapsed(btn)) {
                            expandButtons.push(btn);
                        }
                    }
                }
            });
        });
        
        return expandButtons;
    },

    // Check if button is within wiki navigation (not other menus)
    isInWikiNavigation(button) {
        // Look for parent containers that indicate this is wiki navigation
        const wikiIndicators = [
            '.wiki-tree',
            '.tree-container', 
            '.bolt-tree',
            '[data-testid="wiki-tree"]',
            '.ms-Nav', // Main navigation
            '.wiki-nav'
        ];
        
        for (const indicator of wikiIndicators) {
            if (button.closest(indicator)) {
                return true;
            }
        }
        
        // Check if the button is in a tree row structure (wiki navigation pattern)
        const treeRow = button.closest('tr.bolt-tree-row, .tree-row, [data-testid="tree-row"]');
        if (treeRow) {
            // Additional check: ensure it has tree-like structure
            const hasTreeText = treeRow.querySelector('.tree-name-text, .bolt-tree-row-content, .tree-item-text');
            return !!hasTreeText;
        }
        
        return false;
    },

    // Expand single item (fast mode)
    async expandItem(button) {
        try {
            const buttonId = this.getButtonId(button);
            this.processedButtons.add(buttonId);
            button.click();
            this.expandedCount++;
            // No waiting - bulk processing for speed
        } catch (error) {
            // Silent failure - no console spam
        }
    },

    // Fast content check (minimal waiting for large wikis)
    waitForContent() {
        return new Promise(resolve => {
            // Minimal wait - just check for obvious loading indicators
            const loadingElements = document.querySelectorAll(
                '.bolt-spinner, .loading, .bolt-progress-indicator, [data-testid="loading"]'
            );
            
            if (loadingElements.length === 0) {
                // No loading indicators - resolve quickly
                setTimeout(resolve, 50);
            } else {
                // Brief wait if loading detected
                setTimeout(resolve, 200);
            }
        });
    },

    // Persistent expansion for Azure DevOps lazy loading (runs until manual stop)
    async expandAllItems() {
        console.log('🔄 Starting PERSISTENT expansion for Azure DevOps lazy loading');
        console.log('📋 Will run continuously until you manually stop with WikiIndexer.stop()');
        console.log('🎯 Optimized for virtual DOM and lazy-loaded content');
        
        let round = 1;
        let lastProgressUpdate = 0;
        
        // Run indefinitely until manually stopped
        while (!this.shouldStop) {
            const expandableItems = this.findExpandableItems();
            
            if (expandableItems.length === 0) {
                // No items found - keep scanning for lazy-loaded content
                console.log(`📊 Round ${round}: Scanning for lazy-loaded content... (${this.expandedCount} total expanded)`);
                
                // Wait for potential lazy loading
                await new Promise(resolve => setTimeout(resolve, 500));
                round++;
                continue;
            }
            
            console.log(`⚡ Round ${round}: Found ${expandableItems.length} items - expanding...`);
            
            // BULK PROCESSING - click all buttons rapidly
            const validButtons = [];
            for (const button of expandableItems) {
                if (this.shouldStop) return;
                
                // Quick validation without excessive checks
                if (button.offsetParent !== null) {
                    const buttonId = this.getButtonId(button);
                    if (!this.processedButtons.has(buttonId)) {
                        validButtons.push(button);
                    }
                }
            }
            
            // Rapid-fire clicking in batches
            const batchSize = 20; // Process 20 at a time
            for (let i = 0; i < validButtons.length; i += batchSize) {
                if (this.shouldStop) return;
                
                const batch = validButtons.slice(i, i + batchSize);
                
                // Click all buttons in batch with minimal delay
                for (const button of batch) {
                    try {
                        const buttonId = this.getButtonId(button);
                        this.processedButtons.add(buttonId);
                        button.click();
                        this.expandedCount++;
                    } catch (error) {
                        // Silent continue
                    }
                }
                
                // Very brief pause between batches
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            
            // Brief wait to allow DOM updates
            await new Promise(resolve => setTimeout(resolve, 200));
            
            // Progress update every 10 expansions
            if (this.expandedCount - lastProgressUpdate >= 10) {
                console.log(`📈 Progress: ${this.expandedCount} items expanded (Round ${round})`);
                lastProgressUpdate = this.expandedCount;
            }
            
            round++;
            
            // Safety limit - but much higher and with warning
            if (round > 500) {
                console.log('⚠️ Reached 500 rounds - consider stopping manually if done');
                console.log('🛑 Run WikiIndexer.stop() when ready');
            }
        }
        
        console.log('🛑 Expansion stopped by user command');
        console.log(`📊 Final: ${this.expandedCount} items expanded over ${round - 1} rounds`);
    },

    // Final cleanup and sorting of captured pages
    finalizeCapture() {
        // Sort pages by path for consistent ordering
        this.pages.sort((a, b) => a.path.toLowerCase().localeCompare(b.path.toLowerCase()));
        
        // Clean up observers
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        if (this.mutationObserver) {
            this.mutationObserver.disconnect();
        }
        
        console.log(`📋 Finalized capture: ${this.pages.length} pages collected during navigation`);
    },

    // Generate final JSON structure and auto-download file
    generateJSON() {
        const result = {
            wiki_name: this.wikiName,
            wiki_id: this.wikiId,
            pages: this.pages.sort((a, b) => a.path.toLowerCase().localeCompare(b.path.toLowerCase()))
        };
        
        const jsonData = JSON.stringify([result], null, 2);
        
        // Auto-download file with sanitized wiki name
        const safeWikiName = this.sanitizeFilename(this.wikiName);
        this.downloadJSON(jsonData, `wiki_indexes_${safeWikiName}.json`);
        
        console.log('\n📄 WIKI-INDEX-JSON-START');
        console.log(jsonData);
        console.log('📄 WIKI-INDEX-JSON-END\n');
        
        return result;
    },

    // Sanitize filename by removing/replacing unsafe characters
    sanitizeFilename(name) {
        return name
            .replace(/[<>:"/\\|?*]/g, '_')  // Replace unsafe chars with underscore
            .replace(/\s+/g, '-')           // Replace spaces with hyphens
            .replace(/_{2,}/g, '_')         // Replace multiple underscores with single
            .replace(/-{2,}/g, '-')         // Replace multiple hyphens with single
            .replace(/^[-_]+|[-_]+$/g, ''); // Remove leading/trailing hyphens/underscores
    },

    // Auto-download JSON file with custom filename
    downloadJSON(jsonData, filename) {
        try {
            // Create blob and download link
            const blob = new Blob([jsonData], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            // Create temporary download link
            const downloadLink = document.createElement('a');
            downloadLink.href = url;
            downloadLink.download = filename;
            downloadLink.style.display = 'none';
            
            // Trigger download
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            // Clean up
            URL.revokeObjectURL(url);
            
            console.log(`📁 Auto-downloaded: ${filename}`);
        } catch (error) {
            console.warn('⚠️ Auto-download failed, copy JSON manually:', error);
        }
    },

    // Main execution function - Follows correct Azure DevOps expansion logic
    async run(wikiName, wikiId) {
        if (!wikiName || !wikiId) {
            console.error('❌ Usage: WikiIndexer.run("WIKI-NAME", "wiki-id")');
            return;
        }
        
        console.log(`🔄 Starting INTELLIGENT indexing for wiki: ${wikiName}`);
        console.log('📋 Following Azure DevOps expansion pattern:');
        console.log('   1️⃣ Expand visible ChevronRightMed items');
        console.log('   2️⃣ Capture all visible index data');
        console.log('   3️⃣ Scroll to last ChevronDownMed');
        console.log('   4️⃣ Check for new unexpanded/uncaptured items');
        console.log('   🔄 Repeat until no new items found');
        
        this.init(wikiName, wikiId);
        this.startCapture(); // Enable capture from the start
        
        let cycleCount = 0;
        const maxCycles = 50; // Safety limit
        
        try {
            while (!this.shouldStop && cycleCount < maxCycles) {
                cycleCount++;
                console.log(`🔄 Cycle ${cycleCount}: Starting thorough expansion and capture cycle`);
                
                // FIRST: Thorough expand and capture loop for current view
                let totalExpanded = 0;
                let totalCaptured = 0;
                let innerCycle = 0;
                
                // Create a temporary set to track what we've processed in this major cycle
                const cycleProcessedButtons = new Set();
                
                while (!this.shouldStop) {
                    innerCycle++;
                    console.log(`   🔍 Inner cycle ${innerCycle}: Checking current view`);
                    
                    // Capture all currently visible index data FIRST
                    const capturedCount = await this.captureVisibleItems();
                    totalCaptured += capturedCount;
                    console.log(`      📋 Captured ${capturedCount} new index items`);
                    
                    // Expand all visible ChevronRightMed items (with cycle tracking)
                    const expandedCount = await this.expandAllItems(cycleProcessedButtons);
                    totalExpanded += expandedCount;
                    console.log(`      🔧 Expanded ${expandedCount} ChevronRightMed items`);
                    
                    // If nothing was expanded or captured in this inner cycle, we're done with current view
                    if (expandedCount === 0 && capturedCount === 0) {
                        console.log(`   ✅ Current view fully processed (${totalExpanded} expanded, ${totalCaptured} captured)`);
                        break;
                    }
                    
                    // Quick delay before next inner cycle to let DOM update
                    await this.delay(200);
                    
                    // Safety check for inner cycles
                    if (innerCycle >= 10) { // Reduced from 20 to 10 for faster exit
                        console.log(`   ⚠️ Inner cycle limit reached - moving to scroll`);
                        break;
                    }
                }
                
                // THEN: Scroll to reveal more content
                const scrolled = await this.scrollToLastChevronDown();
                console.log(`   📜 Scrolled to reveal more content: ${scrolled ? 'YES' : 'NO'}`);
                
                // Check if we should continue to next cycle
                if (totalExpanded === 0 && totalCaptured === 0 && !scrolled) {
                    console.log(`   🎉 No new items found anywhere - indexing complete!`);
                    break;
                }
                
                // Additional check: if we only captured but didn't expand or scroll, we might be stuck
                if (totalExpanded === 0 && !scrolled && totalCaptured > 0) {
                    // Check if there are still unexpanded items visible
                    const stillUnexpanded = document.querySelectorAll(".bolt-tree-expand-button.ms-Icon--ChevronRightMed").length;
                    if (stillUnexpanded === 0) {
                        console.log(`   🎉 No more expandable items found - indexing complete!`);
                        break;
                    } else {
                        console.log(`   ⚠️ Still ${stillUnexpanded} unexpanded items but none were processed - forcing scroll`);
                        // Force a small scroll to try to reveal more content
                        const container = this.getScrollContainer();
                        if (container !== window) {
                            container.scrollTop += 300;
                        } else {
                            window.scrollBy(0, 300);
                        }
                        await this.delay(500);
                    }
                }
                
                // Delay before next major cycle
                await this.delay(500);
            }
            
            // Generate final results
            const result = this.generateJSON();
            const safeWikiName = this.sanitizeFilename(wikiName);
            console.log(`🎉 INTELLIGENT indexing complete after ${cycleCount} cycles!`);
            console.log(`📊 Results: ${this.pages.length} pages captured`);
            console.log(`📁 File auto-downloaded as: wiki_indexes_${safeWikiName}.json`);
            
            return result;
            
        } catch (error) {
            console.error('❌ Error during intelligent indexing:', error);
        }
    },

    // Fixed expand method - FULL VIEW rescan with cycle tracking to prevent loops
    async expandAllItems(cycleProcessedButtons = new Set()) {
        // ALWAYS rescan the entire view - don't rely on previous state
        const expandButtons = Array.from(document.querySelectorAll(".bolt-tree-expand-button.ms-Icon--ChevronRightMed")).filter(btn => {
            // Must be visible
            if (btn.offsetParent === null) return false;
            
            // Skip if we've already processed this button in this cycle
            const buttonId = this.getButtonId(btn);
            if (cycleProcessedButtons.has(buttonId)) {
                return false;
            }
            
            // Check if this button is actually collapsed (ChevronRightMed means collapsed)
            const treeRow = btn.closest("tr.bolt-tree-row");
            if (treeRow) {
                // Look for ChevronDownMed in the same row (indicates already expanded)
                const hasChevronDown = treeRow.querySelector(".ms-Icon--ChevronDownMed");
                if (hasChevronDown) {
                    return false; // Already expanded
                }
            }
            
            return true;
        });

        let expandedCount = 0;
        
        for (const button of expandButtons) {
            if (this.shouldStop) break;
            
            try {
                // Double-check the button is still valid and collapsed
                if (button.offsetParent === null) continue;
                
                // Get unique identifier for this button
                const buttonId = this.getButtonId(button);
                
                // Skip if we've processed this button in this cycle
                if (cycleProcessedButtons.has(buttonId)) {
                    continue;
                }
                
                // Get the tree name for logging
                const treeRow = button.closest("tr.bolt-tree-row");
                const treeNameText = treeRow ? treeRow.querySelector(".tree-name-text") : null;
                const itemName = treeNameText ? treeNameText.textContent.trim() : 'Unknown item';
                
                // Verify this is still a ChevronRightMed (collapsed state)
                if (!button.classList.contains('ms-Icon--ChevronRightMed')) {
                    continue; // State changed, skip
                }
                
                console.log(`🔧 Expanding: ${itemName}`);
                
                // Mark as processed BEFORE clicking to prevent re-processing
                cycleProcessedButtons.add(buttonId);
                
                // Click the expand button
                button.click();
                expandedCount++;
                this.expandedCount++;
                
                // Quick delay to let UI open before next click
                await this.delay(150);
                
                // Verify the expansion worked by checking if ChevronRightMed changed to ChevronDownMed
                const nowExpanded = treeRow && treeRow.querySelector(".ms-Icon--ChevronDownMed");
                if (nowExpanded) {
                    console.log(`✅ Successfully expanded: ${itemName}`);
                } else {
                    console.log(`⚠️ Expansion may have failed: ${itemName}`);
                }
                
            } catch (error) {
                console.log(`⚠️ Failed to expand button: ${error.message}`);
            }
        }

        return expandedCount;
    },

    // Generate a unique ID for a button to track processing within a cycle
    getButtonId(button) {
        const treeRow = button.closest("tr.bolt-tree-row");
        const treeNameText = treeRow ? treeRow.querySelector(".tree-name-text") : null;
        const itemName = treeNameText ? treeNameText.textContent.trim() : 'unknown';
        const level = treeRow ? treeRow.getAttribute("aria-level") : '0';
        
        // Create unique ID based on content and position
        return `${level}::${itemName}::${button.offsetTop}`;
    },

    // Get text description of a button for logging
    getButtonText(button) {
        if (!button) return 'Unknown';
        
        const text = button.textContent?.trim() ||
                    button.getAttribute('aria-label') ||
                    button.getAttribute('title') ||
                    button.closest('[role="treeitem"]')?.textContent?.trim() ||
                    'Unnamed button';
        
        return text.substring(0, 30);
    },

    // Step 2: Capture all currently visible index data
    async captureVisibleItems() {
        const initialCount = this.pages.length;
        
        // Find all visible wiki tree items that we haven't captured yet
        const visibleItems = Array.from(document.querySelectorAll(`
            [role="treeitem"],
            .tree-item,
            .bolt-tree-row
        `)).filter(item => {
            return item.offsetParent !== null; // Must be visible
        });

        for (const item of visibleItems) {
            if (this.shouldStop) break;
            
            // Use the existing capture logic
            this.captureWikiItem(item);
        }

        return this.pages.length - initialCount;
    },

    // Step 3: Scroll to reveal more content - improved detection
    async scrollToLastChevronDown() {
        // Try multiple strategies to find where to scroll
        
        // Strategy 1: Find the last visible tree row and scroll past it
        const allTreeRows = Array.from(document.querySelectorAll("tr.bolt-tree-row")).filter(row => {
            return row.offsetParent !== null; // Must be visible
        });
        
        if (allTreeRows.length > 0) {
            const lastRow = allTreeRows[allTreeRows.length - 1];
            const container = this.getScrollContainer();
            
            try {
                // Get current scroll position
                const beforeScroll = this.getCurrentScrollPosition();
                
                // Scroll the last row into view and then scroll a bit more
                lastRow.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'end' 
                });
                
                // Wait for scroll to complete
                await this.delay(300);
                
                // Scroll a bit more to reveal any hidden content
                if (container !== window) {
                    container.scrollTop += 200;
                } else {
                    window.scrollBy(0, 200);
                }
                
                await this.delay(200);
                
                // Check if we actually scrolled
                const afterScroll = this.getCurrentScrollPosition();
                const scrolled = Math.abs(afterScroll - beforeScroll) > 50;
                
                console.log(`   📜 Scroll attempt: before=${beforeScroll}, after=${afterScroll}, moved=${scrolled}`);
                
                return scrolled;
                
            } catch (error) {
                console.log(`   ⚠️ Scroll error: ${error.message}`);
                return false;
            }
        }
        
        // Strategy 2: Check if there are any unexpanded items still visible
        const unexpandedItems = document.querySelectorAll(".bolt-tree-expand-button.ms-Icon--ChevronRightMed");
        if (unexpandedItems.length > 0) {
            console.log(`   🔍 Found ${unexpandedItems.length} unexpanded items still visible - continuing without scroll`);
            return true; // Continue processing without scrolling
        }
        
        console.log(`   🏁 No more content to scroll to`);
        return false;
    },

    // Find the actual clickable target within an expandable element
    findClickableTarget(element) {
        // Strategy 1: Element itself is clickable
        if (element.tagName === 'BUTTON' || element.getAttribute('role') === 'button') {
            return element;
        }
        
        // Strategy 2: Find button within the element
        const button = element.querySelector('button');
        if (button) {
            return button;
        }
        
        // Strategy 3: Find clickable chevron icon
        const chevronIcon = element.querySelector('i[data-icon-name="ChevronRightMed"], .ms-Icon--ChevronRightMed');
        if (chevronIcon) {
            // Check if the icon itself is clickable, or find its parent button
            const parentButton = chevronIcon.closest('button');
            return parentButton || chevronIcon;
        }
        
        // Strategy 4: Find any element with expand-related attributes
        const expandElement = element.querySelector('[aria-label*="Expand"], [title*="Expand"]');
        if (expandElement) {
            return expandElement;
        }
        
        // Strategy 5: If element has aria-expanded, it might be clickable itself
        if (element.hasAttribute('aria-expanded')) {
            return element;
        }
        
        // Strategy 6: Find the first clickable child
        const clickableChild = element.querySelector('[role="button"], button, [onclick]');
        if (clickableChild) {
            return clickableChild;
        }
        
        // Last resort: return the element itself
        return element;
    },

    // Validate if an element is a valid expandable tree item
    isValidExpandableElement(element) {
        if (!element) return false;
        
        // Must be in a tree context
        const inTree = element.closest('[role="tree"], .tree-container, .wiki-tree, .bolt-tree') ||
                      element.getAttribute('role') === 'treeitem' ||
                      element.classList.contains('bolt-tree-row');
        
        if (!inTree) return false;
        
        // Should not be already expanded (if it has aria-expanded)
        if (element.hasAttribute('aria-expanded') && element.getAttribute('aria-expanded') === 'true') {
            return false;
        }
        
        // Look for signs that this is expandable
        const hasExpandIndicator = element.querySelector('i[data-icon-name="ChevronRightMed"]') ||
                                  element.innerHTML.includes('ChevronRightMed') ||
                                  element.querySelector('[aria-label*="Expand"]') ||
                                  element.getAttribute('aria-expanded') === 'false';
        
        return hasExpandIndicator;
    },

    // Get readable text from an element for logging
    getElementText(element) {
        if (!element) return 'Unknown';
        
        // Try to find the main text content
        const textElement = element.querySelector('.tree-name-text, .bolt-tree-row-content, .ms-Button-textContainer') ||
                           element;
        
        const text = textElement.textContent?.trim() || 
                    element.getAttribute('aria-label') || 
                    element.getAttribute('title') ||
                    'Unnamed item';
        
        return text.substring(0, 50); // Limit length for logging
    },

    // Get the main scroll container
    getScrollContainer() {
        // Try different possible scroll containers
        const selectors = [
            '.bolt-table-container.flex-grow.v-scroll-auto',
            '.wiki-tree-container',
            '.ms-ScrollablePane--contentContainer',
            '[data-testid="wiki-tree-container"]',
            '.wiki-navigation-container'
        ];

        for (const selector of selectors) {
            const container = document.querySelector(selector);
            if (container) {
                return container;
            }
        }

        // Fallback to any scrollable container in the wiki area
        const containers = document.querySelectorAll('[role="tree"], .tree-container, .wiki-container');
        for (const container of containers) {
            if (container.scrollHeight > container.clientHeight) {
                return container;
            }
        }

        // If no scroll container found yet, use the main content area or window
        const mainContent = document.querySelector('main, .main-content, .content-area, #content');
        if (mainContent) {
            console.warn('⚠️ Using main content area as scroll container');
            return mainContent;
        }

        console.warn('⚠️ Using window as scroll container fallback');
        return window;
    },

    // Helper function for delays
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    // Robust scrolling functions that work with or without scroll containers
    scrollToTop() {
        try {
            const container = this.getScrollContainer();
            if (container === window) {
                window.scrollTo(0, 0);
            } else {
                container.scrollTop = 0;
            }
        } catch (error) {
            // Fallback to window scroll
            window.scrollTo(0, 0);
        }
    },

    scrollToPosition(position) {
        try {
            const container = this.getScrollContainer();
            if (container === window) {
                window.scrollTo(0, position);
            } else {
                container.scrollTop = position;
            }
        } catch (error) {
            // Fallback to window scroll
            window.scrollTo(0, position);
        }
    },

    getCurrentScrollPosition() {
        try {
            const container = this.getScrollContainer();
            if (container === window) {
                return window.pageYOffset || document.documentElement.scrollTop;
            } else {
                return container.scrollTop;
            }
        } catch (error) {
            // Fallback to window scroll position
            return window.pageYOffset || document.documentElement.scrollTop;
        }
    },

    // Start the capture phase (call this after expansion is complete)
    startCapture() {
        if (this.captureActive) {
            console.log('📋 Capture is already active');
            return;
        }
        
        console.log('📋 Phase 2: Starting incremental capture...');
        console.log('🧭 Now scroll through the expanded wiki to capture all pages');
        console.log('🛑 Run WikiIndexer.stop() when done scrolling to download results');
        
        this.startIncrementalCapture();
        this.captureActive = true;
    },

    // Stop and generate results
    async stop() {
        this.shouldStop = true;
        
        if (this.captureActive) {
            console.log('🛑 Stopping capture and generating results...');
            this.finalizeCapture();
            
            const result = this.generateJSON();
            const safeWikiName = this.sanitizeFilename(this.wikiName);
            console.log(`📊 Final results: ${this.pages.length} pages captured`);
            console.log(`📁 File auto-downloaded as: wiki_indexes_${safeWikiName}.json`);
            
            return result;
        } else {
            console.log('🛑 Expansion stopped. Run WikiIndexer.startCapture() to begin page capture phase.');
        }
    },

    // Ultra-fast mode for massive wikis (removes most safety checks)
    async turbo(wikiName, wikiId) {
        if (!wikiName || !wikiId) {
            console.error('❌ Usage: WikiIndexer.turbo("WIKI-NAME", "wiki-id")');
            return;
        }
        
        console.log(`🚀 TURBO MODE: Ultra-fast indexing for ${wikiName}`);
        console.log('⚠️ Minimal safety checks - for experienced users only');
        
        this.init(wikiName, wikiId);
        const startTime = Date.now();
        
        // Ultra-aggressive expansion
        for (let round = 1; round <= 50; round++) {
            if (this.shouldStop) break;
            
            const buttons = document.querySelectorAll('.bolt-tree-expand-button, .tree-expand-button');
            let clickCount = 0;
            
            buttons.forEach(btn => {
                if (btn.offsetParent && !this.processedButtons.has(btn)) {
                    try {
                        btn.click();
                        this.processedButtons.add(btn);
                        clickCount++;
                    } catch (e) { /* ignore */ }
                }
            });
            
            if (clickCount === 0) break;
            
            console.log(`🚀 Turbo Round ${round}: ${clickCount} expansions`);
            await new Promise(resolve => setTimeout(resolve, 100)); // Minimal wait
        }
        
        // Immediate capture
        this.captureWikiStructure();
        const result = this.generateJSON();
        
        const duration = ((Date.now() - startTime) / 1000).toFixed(1);
        console.log(`🚀 TURBO complete in ${duration}s - ${this.pages.length} pages captured`);
        const safeWikiName = this.sanitizeFilename(wikiName);
        console.log(`📁 File auto-downloaded as: wiki_indexes_${safeWikiName}.json`);
        
        return result;
    }
};

// Make globally accessible
window.WikiIndexer = WikiIndexer;

console.log('⚡ WikiIndexer loaded - OPTIMIZED FOR LARGE WIKIS');
console.log('🚀 Usage: WikiIndexer.run("WIKI-NAME", "wiki-id") or WikiIndexer.turbo("WIKI-NAME", "wiki-id")');
console.log('🛑 Control: WikiIndexer.stop() | WikiIndexer.rescan() | WikiIndexer.reset()');
console.log('🔧 Debug: WikiIndexer.debug() - analyzes unexpanded items');

WikiIndexer.run("SRE-DevOPS", "dc66cbaa-0364-42e8-9a23-044deb186015")
```

---

### 3. Run the Fully Automated Indexer

**100% Hands-Free Operation:**
```javascript
// Completely automated - does everything for you!
WikiIndexer.run("SRE-DevOPS", "dc66cbaa-0364-42e8-9a23-044deb186015")
```

**Dual-Pass Auto-Scrolling:**
1. 🚀 **Pass 1: Auto-Scroll + Expand** - Scrolls from top to bottom, expanding all collapsible items
2. 🔝 **Return to Top** - Automatically scrolls back to the top when expansion is complete
3. 📋 **Pass 2: Auto-Scroll + Capture** - Scrolls from top to bottom again, capturing all visible pages
4. 📁 **Auto-Download** - Automatically generates and downloads the JSON file

**Zero Manual Work Required:**
- ✅ **Auto-scrolling expansion** - No manual scrolling needed
- ✅ **Auto-scrolling capture** - No manual scrolling needed  
- ✅ **Smart timing** - Capture only happens on second pass (no interference)
- ✅ **Auto-download** - File ready when complete
- ✅ **Separation of concerns** - Expansion and capture are completely separate

**Just Run and Wait:**
```javascript
WikiIndexer.run("YOUR-WIKI", "your-id")  // Start it
// ☕ Go get coffee - it does everything automatically
// 📁 File will be downloaded when complete
```

**Parameters:**
- `wikiName`: Display name for your wiki (e.g., "SRE-DevOPS")
- `wikiId`: Azure DevOps wiki identifier (GUID format)

---

### 4. Control Commands

**Main Command (Usually All You Need):**
- 🚀 **Fully automated:** `WikiIndexer.run("WIKI-NAME", "wiki-id")` (does everything automatically)

**Emergency/Debug Commands:**
- 🛑 **Emergency stop:** `WikiIndexer.stop()` (stops auto-scrolling if needed)
- 🔍 **Manual rescan:** `WikiIndexer.rescan()` (if some items weren't expanded)
- 🔄 **Reset for new wiki:** `WikiIndexer.reset()`
- 🔧 **Debug expansion:** `WikiIndexer.debug()` (analyzes unexpanded items)

**Fully Automated Workflow:**
- 🚀 **One command does everything:** Auto-scroll expansion + auto-scroll capture + auto-download
- ☕ **Zero interaction needed:** Just wait for completion
- 📁 **Auto-download:** File ready when complete
- ⚠️ **Emergency stop available:** Use `WikiIndexer.stop()` only if something goes wrong

---

### 5. Automatic File Download

The script automatically downloads the JSON file with a custom name:

**File naming pattern:** `wiki_indexes_YOUR-WIKI.json`

**Examples:**
- `WikiIndexer.run("SRE-DevOPS", "id")` → Downloads `wiki_indexes_SRE-DevOPS.json`
- `WikiIndexer.run("PLATFORM", "id")` → Downloads `wiki_indexes_PLATFORM.json`
- `WikiIndexer.run("My-Team-Wiki", "id")` → Downloads `wiki_indexes_My-Team-Wiki.json`

**Backup option:** If auto-download fails, copy JSON between markers:
```
📄 WIKI-INDEX-JSON-START
[JSON content here]
📄 WIKI-INDEX-JSON-END
```

---

### 6. Save to File (Optional Python Script)

If you prefer automated file saving, create `extract_wiki_json.py`:

```python
import json
import re

def extract_wiki_json_from_console():
    """Extract JSON from console output file"""
    
    INPUT_FILE = "console_output.txt"  # Save console output here
    OUTPUT_FILE = "wiki_index.json"
    
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find JSON between markers
        start_marker = "📄 WIKI-INDEX-JSON-START"
        end_marker = "📄 WIKI-INDEX-JSON-END"
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            print("❌ JSON markers not found in console output")
            return
        
        # Extract JSON content
        json_content = content[start_idx + len(start_marker):end_idx].strip()
        
        # Parse and validate
        data = json.loads(json_content)
        
        # Save to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Wiki index saved to {OUTPUT_FILE}")
        print(f"📊 Contains {len(data[0]['pages'])} pages")
        
    except FileNotFoundError:
        print(f"❌ {INPUT_FILE} not found. Save console output first.")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    extract_wiki_json_from_console()
```

---

## 🎯 Key Features

### **Parameterized Execution**
- ✅ **Custom wiki name and ID** - passed as parameters
- ✅ **Structured output** - matches expected JSON format
- ✅ **Reusable** - run multiple wikis in same session
- ✅ **Clean interface** - simple run command

### **Clean Output**
- ✅ **Minimal console noise** - only essential messages
- ✅ **Silent expansion** - no spam during auto-expansion
- ✅ **Clear JSON markers** - easy to copy/extract
- ✅ **Summary statistics** - pages captured and expansions made

### **Smart Processing**
- ✅ **Auto-expansion** - finds and expands all collapsed items
- ✅ **Duplicate prevention** - tracks processed buttons
- ✅ **State validation** - only clicks collapsed buttons
- ✅ **Sorted output** - alphabetical page ordering

### **User Control**
- ✅ **Stop command** - graceful termination
- ✅ **Reset command** - prepare for new wiki
- ✅ **Parameter validation** - prevents invalid runs
- ✅ **Error handling** - silent failures, no console spam

---

## 🔧 Troubleshooting

### **Missing Parameters Error:**
```javascript
❌ Usage: WikiIndexer.run("WIKI-NAME", "wiki-id")
```
Ensure both parameters are provided as strings.

### **No JSON Output:**
- Check console for error messages
- Ensure you have permissions to view the wiki
- Try running `WikiIndexer.reset()` and run again

### **Incomplete Expansion:**
- Some wikis may need multiple passes
- Run the command again to catch any missed items

---

## 📦 Output Format

The script generates a JSON array with this exact structure:

```json
[
  {
    "wiki_name": "SRE-DevOPS",
    "wiki_id": "dc66cbaa-0364-42e8-9a23-044deb186015",
    "pages": [
      {
        "title": "SRE Wiki",
        "path": "SRE Wiki", 
        "level": 1
      },
      {
        "title": "Stallions Portal project",
        "path": "SRE Wiki/Stallions Portal project",
        "level": 2
      }
    ]
  }
]
```

This format is **ready to use** - no additional processing required! 🎉

---

## 🚀 Usage Examples

```javascript
// Fully automated - single wiki
WikiIndexer.run("SRE-DevOPS", "dc66cbaa-0364-42e8-9a23-044deb186015")  // Does everything automatically
// ☕ Wait for completion - file will auto-download

// Multiple wikis - fully automated sequence  
WikiIndexer.run("SRE-DevOPS", "wiki-id-1")     // Fully automated first wiki
// ☕ Wait for auto-download of first wiki
WikiIndexer.reset()                             // Reset for next wiki
WikiIndexer.run("PLATFORM", "wiki-id-2")       // Fully automated second wiki
// ☕ Wait for auto-download of second wiki

// Emergency stop (only if something goes wrong)
WikiIndexer.stop()                              // Stops auto-scrolling
```

The enhanced WikiIndexer makes Azure DevOps wiki indexing **fast, clean, and parameterized**! 🎯 