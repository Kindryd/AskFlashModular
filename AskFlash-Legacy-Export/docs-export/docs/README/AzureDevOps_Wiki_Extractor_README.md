
# 🧭 Azure DevOps Wiki Index Extractor

This guide helps you extract a **full structured index** of a Project Wiki in Azure DevOps, which normally uses lazy loading and virtual DOM — making it hard to scrape in one go.

---

## ✅ What This Does

- Logs every wiki page **path** as you scroll through the tree.
- Reconstructs full structure with **depth levels**.
- Outputs a **clean JSON file** with `title`, `path`, and `level`.

---

## 🧰 Tools Used

- JavaScript (run in browser console)
- Python (to format console output into structured JSON)

---

## 🧪 Step-by-Step Instructions

### 1. Open Azure DevOps Wiki

- Navigate to your Project Wiki.
- Expand **as many sections** as you want to capture.

---

### 2. Paste This JavaScript in the Browser Console

Press `F12` → Console → Paste this:

```js
const seen = new Set();
const stack = [];

function buildPath(title, level) {
    while (stack.length && stack[stack.length - 1].level >= level) {
        stack.pop();
    }
    const path = stack.length ? `${stack[stack.length - 1].path}/${title}` : title;
    stack.push({ title, path, level });
    return path;
}

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const row = entry.target;
            const level = parseInt(row.getAttribute("aria-level") || "1");
            const span = row.querySelector(".tree-name-text");
            if (span) {
                const title = span.textContent.trim();
                const id = `${level}::${title}`;
                if (!seen.has(id)) {
                    const path = buildPath(title, level);
                    console.log(`[WIKI-INDEX] ${path}`);
                    seen.add(id);
                }
            }
        }
    });
}, {
    root: null,
    rootMargin: '0px',
    threshold: 1.0
});

function observeVisibleRows() {
    document.querySelectorAll("tr.bolt-tree-row").forEach(row => {
        if (!row.dataset.wikiObserved) {
            observer.observe(row);
            row.dataset.wikiObserved = "true";
        }
    });
}

observeVisibleRows();

const mutationObserver = new MutationObserver(() => {
    observeVisibleRows();
});

mutationObserver.observe(document.body, {
    childList: true,
    subtree: true
});

console.log("✅ Wiki visibility logger with auto-rebinding is active. Scroll slowly and watch for logs.");
```

> 🧭 Slowly scroll through the wiki sidebar.  
> 🔁 The script will log each path as it becomes visible.

---

### 3. Save the Console Output

Once done scrolling:
- Right-click → **Save console output as...**  
- Save it to `wiki_console_output.txt`

---

### 4. Run the Python Script to Parse It

Save this Python script as `parse_wiki_console_output.py`:

```python
import json

INPUT_FILE = "wiki_console_output.txt"
OUTPUT_FILE = "cleaned_wiki_index.json"

wiki_entries = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if "[WIKI-INDEX]" not in line:
            continue
        path = line.split("[WIKI-INDEX]")[-1].strip()
        parts = path.split("/")
        title = parts[-1]
        level = len(parts)
        wiki_entries.append({
            "title": title,
            "path": path,
            "level": level
        })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(wiki_entries, f, indent=2)

print(f"✅ Output saved to {OUTPUT_FILE}")
```

Then run:

```bash
python parse_wiki_console_output.py
```

---

## 📦 Output

You’ll get a file like this:

```json
[
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
```

---

## 🧠 Notes

- This works around DevOps' **virtualized DOM and lazy loading**.
- You must **scroll through all content manually**.
- Works great for snapshotting a **complete wiki hierarchy**.

---

## 🪄 Bonus Ideas

- Save the logs to `localStorage` automatically.
- Rebuild it as a browser extension or userscript.
