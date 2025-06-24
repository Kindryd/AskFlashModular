#!/usr/bin/env python3
"""
Flash AI Stakeholder Documentation - HTML Converter
Converts markdown documentation to professional HTML format for non-technical stakeholders
"""

import os
import markdown
from pathlib import Path
import re

def create_html_template():
    """Create a professional HTML template with Flash branding"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Flash AI Assistant</title>
    <style>
        :root {{
            --flash-green: #7ed321;
            --flash-dark: #2c3e50;
            --flash-light: #ecf0f1;
            --flash-accent: #3498db;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--flash-dark);
            background-color: #fff;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, var(--flash-green), var(--flash-accent));
            color: white;
            padding: 30px;
            margin: -20px -20px 30px -20px;
            border-radius: 0 0 15px 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .nav-menu {{
            background: var(--flash-light);
            padding: 15px;
            margin: 0 -20px 30px -20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .nav-menu h3 {{
            color: var(--flash-dark);
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .nav-links {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 10px;
        }}
        
        .nav-links a {{
            display: block;
            padding: 10px 15px;
            background: white;
            color: var(--flash-dark);
            text-decoration: none;
            border-radius: 8px;
            border-left: 4px solid var(--flash-green);
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .nav-links a:hover {{
            background: var(--flash-green);
            color: white;
            transform: translateX(5px);
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: var(--flash-dark);
            margin: 25px 0 15px 0;
        }}
        
        h1 {{
            font-size: 2.2em;
            border-bottom: 3px solid var(--flash-green);
            padding-bottom: 10px;
        }}
        
        h2 {{
            font-size: 1.8em;
            color: var(--flash-accent);
            margin-top: 35px;
        }}
        
        h3 {{
            font-size: 1.4em;
            color: var(--flash-green);
        }}
        
        p {{
            margin-bottom: 15px;
            text-align: justify;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background: var(--flash-green);
            color: white;
            font-weight: 600;
        }}
        
        tr:hover {{
            background-color: #f5f5f5;
        }}
        
        .highlight {{
            background: linear-gradient(120deg, var(--flash-green) 0%, transparent 50%);
            padding: 2px 5px;
            border-radius: 3px;
        }}
        
        .metric-box {{
            background: linear-gradient(135deg, var(--flash-light), white);
            border: 2px solid var(--flash-green);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .status-good {{
            color: #27ae60;
            font-weight: bold;
        }}
        
        .status-warning {{
            color: #f39c12;
            font-weight: bold;
        }}
        
        .status-error {{
            color: #e74c3c;
            font-weight: bold;
        }}
        
        .button {{
            display: inline-block;
            background: var(--flash-green);
            color: white;
            padding: 12px 25px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 10px 10px 10px 0;
        }}
        
        .button:hover {{
            background: var(--flash-accent);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        
        .footer {{
            margin-top: 50px;
            padding: 20px;
            background: var(--flash-light);
            border-radius: 10px;
            text-align: center;
            color: var(--flash-dark);
        }}
        
        blockquote {{
            border-left: 4px solid var(--flash-green);
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            background: #f9f9f9;
            padding: 15px 20px;
            border-radius: 0 10px 10px 0;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }}
        
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
        }}
        
        .document-meta {{
            background: var(--flash-light);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 25px;
            border-left: 4px solid var(--flash-accent);
        }}
        
        .document-meta strong {{
            color: var(--flash-dark);
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .header {{
                margin: -10px -10px 20px -10px;
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .nav-menu {{
                margin: 0 -10px 20px -10px;
            }}
            
            .nav-links {{
                grid-template-columns: 1fr;
            }}
            
            table {{
                font-size: 0.9em;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🐄 {title}</h1>
        <div class="subtitle">Flash AI Assistant - Stakeholder Documentation</div>
    </div>
    
    {nav_menu}
    
    <div class="content">
        {content}
    </div>
    
    <div class="footer">
        <p><strong>Flash AI Assistant Stakeholder Documentation</strong><br>
        Generated on {date} | Production Ready System | 
        <span class="status-good">✅ Ready for Deployment</span></p>
    </div>
</body>
</html>"""

def create_navigation_menu(current_file=None):
    """Create navigation menu for all documents"""
    documents = [
        ("README.html", "📋 Master Index", "Navigation guide and quick start"),
        ("01_EXECUTIVE_SUMMARY.html", "📊 Executive Summary", "Strategic overview (5 min)"),
        ("02_TECHNICAL_ARCHITECTURE.html", "🏗️ Technical Architecture", "System design (10 min)"),
        ("03_BUSINESS_CASE.html", "💰 Business Case", "Financial justification (8 min)"),
        ("04_IMPLEMENTATION_STATUS.html", "✅ Implementation Status", "Readiness report (7 min)"),
        ("05_DEMONSTRATION_GUIDE.html", "🎪 Demonstration Guide", "Live demo script (15 min)"),
        ("06_FUTURE_ROADMAP.html", "🚀 Future Roadmap", "Strategic planning (12 min)"),
        ("07_RISK_ASSESSMENT.html", "🛡️ Risk Assessment", "Risk analysis (10 min)"),
        ("08_INTEGRATION_BENEFITS.html", "🔗 Integration Benefits", "System integration (9 min)")
    ]
    
    nav_html = """
    <div class="nav-menu">
        <h3>📚 Complete Documentation Package</h3>
        <div class="nav-links">
    """
    
    for filename, title, description in documents:
        if filename == current_file:
            nav_html += f'''
            <div style="background: var(--flash-green); color: white; padding: 10px 15px; border-radius: 8px;">
                <strong>{title}</strong><br>
                <small>{description}</small>
            </div>
            '''
        else:
            nav_html += f'''
            <a href="{filename}">
                <strong>{title}</strong><br>
                <small>{description}</small>
            </a>
            '''
    
    nav_html += """
        </div>
    </div>
    """
    
    return nav_html

def enhance_markdown_content(content):
    """Enhance markdown content with additional styling"""
    # Convert status indicators to styled spans
    content = re.sub(r'✅', '<span class="status-good">✅</span>', content)
    content = re.sub(r'🟢', '<span class="status-good">🟢</span>', content)
    content = re.sub(r'🟡', '<span class="status-warning">🟡</span>', content)
    content = re.sub(r'🔴', '<span class="status-error">🔴</span>', content)
    
    # Highlight important metrics
    content = re.sub(r'\*\*(\d+%)\*\*', r'<span class="highlight"><strong>\1</strong></span>', content)
    content = re.sub(r'\*\*(\$[\d,]+)\*\*', r'<span class="highlight"><strong>\1</strong></span>', content)
    
    return content

def convert_md_to_html(md_file):
    """Convert a single markdown file to HTML"""
    print(f"Converting {md_file}...")
    
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Extract document metadata from the top of the file
    meta_match = re.search(r'\*\*Document Type\*\*: (.*?)\n.*?\*\*Audience\*\*: (.*?)\n.*?\*\*Date\*\*: (.*?)\n', md_content)
    
    if meta_match:
        doc_type, audience, date = meta_match.groups()
        meta_html = f"""
        <div class="document-meta">
            <strong>Document Type:</strong> {doc_type}<br>
            <strong>Audience:</strong> {audience}<br>
            <strong>Date:</strong> {date}
        </div>
        """
    else:
        meta_html = ""
    
    # Enhance content
    enhanced_content = enhance_markdown_content(md_content)
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
    html_content = md.convert(enhanced_content)
    
    # Add metadata at the top
    html_content = meta_html + html_content
    
    # Get file title
    title_match = re.search(r'^# (.+)$', md_content, re.MULTILINE)
    title = title_match.group(1) if title_match else md_file.stem
    
    # Create HTML filename
    html_filename = md_file.stem + '.html'
    
    # Create navigation menu
    nav_menu = create_navigation_menu(html_filename)
    
    # Generate final HTML
    template = create_html_template()
    final_html = template.format(
        title=title,
        content=html_content,
        nav_menu=nav_menu,
        date="2025-06-20"
    )
    
    # Write HTML file
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"✅ Created {html_filename}")
    return html_filename

def main():
    """Convert all markdown files to HTML"""
    print("🐄 Flash AI Assistant - HTML Converter")
    print("=" * 50)
    
    # Get all markdown files
    md_files = list(Path('.').glob('*.md'))
    
    if not md_files:
        print("❌ No markdown files found in current directory")
        return
    
    print(f"Found {len(md_files)} markdown files to convert:")
    for md_file in md_files:
        print(f"  📄 {md_file}")
    
    print("\n🔄 Converting to HTML...")
    
    html_files = []
    for md_file in md_files:
        html_file = convert_md_to_html(md_file)
        html_files.append(html_file)
    
    print(f"\n✅ Successfully converted {len(html_files)} files!")
    print("\n📁 HTML files created:")
    for html_file in html_files:
        print(f"  🌐 {html_file}")
    
    print(f"\n🎯 To view: Open any .html file in your web browser")
    print(f"🚀 Recommended start: README.html")
    print(f"\n📦 Package contents: {len(html_files)} professional HTML documents")
    print("💼 Ready for non-technical stakeholder review!")

if __name__ == "__main__":
    main() 