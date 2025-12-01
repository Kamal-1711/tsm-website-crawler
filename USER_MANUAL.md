# TSM WEBSITE STRUCTURE ANALYSIS DASHBOARD

## Complete User Manual v1.0

---

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0-blue.svg" alt="Version 1.0">
  <img src="https://img.shields.io/badge/Status-Production-green.svg" alt="Production Ready">
  <img src="https://img.shields.io/badge/Platform-Web-orange.svg" alt="Web Platform">
</p>

---

## 📚 TABLE OF CONTENTS

1. [Overview & Introduction](#1-overview--introduction)
2. [Getting Started](#2-getting-started-first-time-users)
3. [Installation & Setup](#3-installation--setup)
4. [Dashboard Interface Tour](#4-dashboard-interface-tour)
5. [Tab-by-Tab Feature Guide](#5-tab-by-tab-feature-guide)
6. [How-To Guides](#6-how-to-guides)
7. [Understanding Your Data](#7-understanding-your-data)
8. [Interpreting Reports](#8-interpreting-reports)
9. [Troubleshooting](#9-troubleshooting)
10. [FAQ](#10-frequently-asked-questions)
11. [Glossary](#11-glossary)
12. [Tips & Best Practices](#12-tips--best-practices)
13. [Contact & Support](#13-contact--support)

---

## 1. OVERVIEW & INTRODUCTION

### 🎯 What is This Dashboard?

The **TSM Website Structure Analysis Dashboard** is a professional tool designed to:

| Feature | Description |
|---------|-------------|
| 🔍 **Analyze** | Your website's information architecture |
| 🐛 **Identify** | Navigation problems and optimization opportunities |
| 📊 **Visualize** | How pages are organized and connected |
| 📋 **Generate** | Audit reports for decision-makers |
| 📈 **Track** | Changes and improvements over time |

### 👥 Who Should Use This?

| Role | How They Benefit |
|------|------------------|
| **IT Managers** | Maintain website technical health, identify broken links |
| **Content Managers** | Understand content organization, find orphan content |
| **UX/UI Designers** | Optimize navigation and user experience |
| **Website Administrators** | Identify broken links and orphan pages |
| **Executive Leadership** | Understand website performance at a glance |
| **SEO Specialists** | Improve site structure for search engines |
| **Quality Assurance** | Verify website integrity and completeness |

### 🔧 What Problems Does It Solve?

#### Problem 1: "We don't know how our website is organized"
> **Solution:** The dashboard maps your entire website structure visually, showing every page and connection in an interactive network graph.

#### Problem 2: "Some pages are hard to find"
> **Solution:** Identifies orphan pages (no links pointing to them) and navigation bottlenecks (pages requiring too many clicks to reach).

#### Problem 3: "We have broken links scattered around"
> **Solution:** Detects and lists all pages with issues, including HTTP status codes and connection problems.

#### Problem 4: "How do we compare with industry standards?"
> **Solution:** Provides Information Architecture scoring based on best practices, with benchmarking against optimal values.

#### Problem 5: "What should we fix first?"
> **Solution:** Prioritized action plan with impact estimates, effort requirements, and clear recommendations.

### 📊 Key Metrics Quick Reference

| Metric | What It Measures | Optimal Value | Warning Sign |
|--------|------------------|---------------|--------------|
| **Total Pages** | Website size | Depends on site | N/A |
| **Architecture Score** | Organization quality (0-100) | 75+ | Below 50 |
| **Average Depth** | Clicks to reach any page | 2-3 clicks | 5+ clicks |
| **Health Status** | Overall website health | Excellent/Good | Fair/Poor |
| **Orphan Pages** | Pages with no inbound links | 0 | Any |
| **Dead Ends** | Pages with no outbound links | <10% | >20% |
| **Link Density** | Average internal links per page | 5-15 | <3 or >30 |
| **Max Depth** | Deepest page level | ≤4 | >6 |

---

## 2. GETTING STARTED (First-Time Users)

### Step 1: Access the Dashboard

**On Your Computer:**

1. ✅ Open your web browser (Chrome, Firefox, Safari, or Edge recommended)
2. ✅ Navigate to: `http://localhost:5000`
3. ✅ Wait 2-3 seconds for the dashboard to load

**What You'll See First:**

```
┌─────────────────────────────────────────────────────────────────┐
│  🌐 TSM Website Structure    ● Live    Updated: [Date Time]     │
│     Analysis Dashboard                            [Export ▼]    │
├─────────────────────────────────────────────────────────────────┤
│  Overview │ Network │ Statistics │ Audit Report │ Data │ Mind  │
│     ✓     │         │            │              │ Table│  Map  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │  Total  │  │   IA    │  │ Average │  │ Health  │           │
│  │  Pages  │  │  Score  │  │  Depth  │  │ Status  │           │
│  │   115   │  │ 84.9/100│  │   1.9   │  │  Good   │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Step 2: Understand the Basic Layout

The dashboard has **three main areas**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        HEADER BAR                               │
│  Logo │ Title │ Live Status │ Last Updated │ Controls          │
├─────────────────────────────────────────────────────────────────┤
│                      TAB NAVIGATION                             │
│  [Overview] [Network] [Statistics] [Audit] [Data] [Mind Map]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                                                                 │
│                      MAIN CONTENT AREA                          │
│                   (Changes based on tab)                        │
│                                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: Your First Actions (5-Minute Quick Start)

#### Action 1: Review Summary Cards (30 seconds)
Look at the **4 cards at the top** of the Overview tab:

| Card | What to Check | Good Sign | Warning Sign |
|------|---------------|-----------|--------------|
| Total Pages | Website size | Any number | N/A |
| IA Score | Overall health | Green (75+) | Red (<50) |
| Average Depth | Navigation depth | ≤3.0 | >4.0 |
| Health Status | Quick status | "Good" or "Excellent" | "Fair" or "Poor" |

#### Action 2: Explore the Network Tab (2 minutes)
1. Click the **"Network"** tab
2. See your website as a visual map:
   - 🔵 Blue dots = pages near homepage
   - 🟣 Purple dots = pages at medium depth
   - 🔴 Pink dots = deep pages
   - Lines = connections between pages
   - Bigger dots = more important pages
3. **Hover** over any dot to see page details
4. **Drag** to move around the map
5. **Scroll** to zoom in/out

#### Action 3: Check the Audit Report (1 minute)
1. Click the **"Audit Report"** tab
2. Expand **"Executive Summary"** - see your overall score
3. Expand **"Critical Issues"** - see what needs fixing
4. Expand **"Recommendations"** - see prioritized action items

#### Action 4: Browse the Data Table (1 minute)
1. Click the **"Data Table"** tab
2. Use the **search box** to find specific pages
3. Click **column headers** to sort
4. Use **filters** to narrow results
5. Click **"Export CSV"** to download data

#### Action 5: View the Mind Map (30 seconds)
1. Click the **"Mind Map"** tab
2. Toggle between **"Radial View"** and **"Tree View"**
3. See your website hierarchy visually

---

## 3. INSTALLATION & SETUP

### 💻 System Requirements

#### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 2 GB | 4 GB+ |
| Storage | 500 MB | 1 GB+ |
| Processor | Any modern CPU | Multi-core |
| Display | 1280x720 | 1920x1080+ |

#### Software Requirements

| Software | Version | Notes |
|----------|---------|-------|
| Python | 3.8 or newer | Required |
| Web Browser | Chrome, Firefox, Safari, Edge | Any modern browser |
| Operating System | Windows 10+, macOS 10.14+, Linux | Any supported |

### 📥 Installation Steps

#### Step 1: Download or Clone the Project

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/Kamal-1711/tsm-website-crawler.git
cd tsm-website-crawler
```

**Option B: Download ZIP**
1. Go to the GitHub repository
2. Click "Code" → "Download ZIP"
3. Extract to your desired location
4. Open terminal/command prompt in that folder

#### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed Flask-2.3.0 pandas-2.0.0 plotly-5.18.0 ...
```

#### Step 4: Run the Web Crawler (First Time Only)

```bash
python main.py
```

**Expected output:**
```
============================================================
  TSM Website Crawler - Starting...
============================================================
✓ Configuration loaded
✓ Starting crawl of https://tsm.ac.in
✓ Crawled: 115 pages
✓ Data saved to output/tsm_crawl_data.csv
✓ Visualizations generated
============================================================
  Crawl completed successfully!
============================================================
```

#### Step 5: Start the Dashboard

```bash
python run_dashboard_shadcn.py
```

**Expected output:**
```
============================================================
  TSM Website Structure Dashboard
  Modern Edition with shadcn/ui Components
============================================================

  🌐 Dashboard: http://localhost:5000

  ✨ Features:
     • Dark theme with Tailwind CSS
     • shadcn/ui-inspired components
     • Interactive Plotly visualizations
     • Real-time data filtering
     • Export capabilities

============================================================
  Press Ctrl+C to stop

 * Running on http://127.0.0.1:5000
```

#### Step 6: Open in Browser

1. Open your web browser
2. Navigate to: `http://localhost:5000`
3. Dashboard loads automatically

### 🔧 Troubleshooting Installation

| Error | Cause | Solution |
|-------|-------|----------|
| `'python' is not recognized` | Python not installed | Install Python from [python.org](https://python.org) |
| `ModuleNotFoundError: No module named 'flask'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `Address already in use` | Port 5000 occupied | Close other apps or use `python run_dashboard_shadcn.py --port 5001` |
| `FileNotFoundError: tsm_crawl_data.csv` | Crawler not run | Run `python main.py` first |
| Dashboard shows blank page | JavaScript error | Clear browser cache, try different browser |

---

## 4. DASHBOARD INTERFACE TOUR

### 🔝 Header Section

Located at the **top of every page**, the header contains:

```
┌─────────────────────────────────────────────────────────────────┐
│ 🌐 TSM Website Structure  │ ● Live │ Updated: 2025-12-01 14:15 │
│    Analysis Dashboard     │        │                           │
│                           │        │   [🔄] [🌙] [⬇️ Export]   │
└─────────────────────────────────────────────────────────────────┘
```

| Element | Location | Function |
|---------|----------|----------|
| **Logo & Title** | Left | Project identification |
| **Live Indicator** | Center | Shows dashboard is active |
| **Last Updated** | Center | When data was last crawled |
| **Refresh Button** 🔄 | Right | Reload latest data |
| **Theme Toggle** 🌙 | Right | Switch Dark/Light mode |
| **Export Menu** ⬇️ | Right | Download reports and data |

### 📑 Tab Navigation

Six tabs available across the dashboard:

| Tab | Icon | Purpose | Best For |
|-----|------|---------|----------|
| **Overview** | 📊 | Quick summary & key metrics | Daily check-ins |
| **Network** | 🔗 | Interactive site structure map | Understanding relationships |
| **Statistics** | 📈 | Detailed charts & analysis | In-depth analysis |
| **Audit Report** | 📋 | Professional findings | Executive presentations |
| **Data Table** | 📑 | Complete page listing | Finding specific pages |
| **Mind Map** | 🧠 | Hierarchical visualization | Understanding organization |

### 🎨 Color Coding System

Colors are used consistently throughout the dashboard:

| Color | Meaning | Examples |
|-------|---------|----------|
| 🔵 **Blue** | Primary, information, shallow depth | Homepage, main navigation |
| 🟢 **Green** | Good, healthy, optimal | High scores, no issues |
| 🟡 **Amber/Yellow** | Warning, attention needed | Moderate issues, medium depth |
| 🔴 **Red** | Critical, urgent, problem | Low scores, deep pages |
| 🟣 **Purple** | Secondary, medium depth | Subsections, transitions |
| ⚪ **Gray** | Neutral, inactive | Disabled buttons, borders |

### 🌙 Dark Mode vs Light Mode

| Feature | Dark Mode (Default) | Light Mode |
|---------|---------------------|------------|
| Background | Slate gray (#0F172A) | White (#FFFFFF) |
| Text | Light gray (#E2E8F0) | Dark gray (#0F172A) |
| Best for | Extended use, low light | Bright environments |
| Eye strain | Lower | Higher |

**To switch:** Click the moon/sun icon 🌙 in the header.

---

## 5. TAB-BY-TAB FEATURE GUIDE

### 📊 TAB 1: OVERVIEW (Your Starting Point)

The Overview tab provides a **quick snapshot** of your website's health.

#### Section 1: Summary Cards (Top Row)

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Total Pages │  │  IA Score   │  │ Avg Depth   │  │   Health    │
│     115     │  │  84.9/100   │  │    1.9      │  │    Good     │
│ Comprehensive│  │    Good     │  │  Optimal    │  │   ✓ ✓ ✓    │
│   crawl     │  │ ████████░░  │  │             │  │             │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

**Card Details:**

| Card | Shows | Good Value | Action if Bad |
|------|-------|------------|---------------|
| **Total Pages** | Website size | Any | N/A |
| **IA Score** | Organization quality | 75+ (Green) | Review recommendations |
| **Average Depth** | Navigation depth | ≤3.0 | Flatten deep pages |
| **Health Status** | Overall health | Excellent/Good | Address issues |

#### Section 2: Three-Column Layout

**Left Column: Key Metrics**

| Metric | What It Means | Warning Threshold |
|--------|---------------|-------------------|
| Max Depth | Deepest page level | >4 |
| Orphan Pages | No inbound links | Any (should be 0) |
| Dead Ends | No outbound links | >10% of pages |
| Bottlenecks | Hard to reach pages | Any |
| Avg Links/Page | Link density | <3 or >30 |

**Center Column: Network Graph Preview**

- Mini version of the full network visualization
- Shows overall structure at a glance
- Click to expand in Network tab

**Right Column: Issues & Quick Wins**

- **Issues Alert:** Shows count of problems found
- **Issues List:** Categorized by severity
- **Quick Wins:** Easy improvements with high impact

#### Section 3: Top Pages

Shows the **5 most important pages** based on:
- Number of incoming links
- Number of outgoing links
- Position in hierarchy

---

### 🔗 TAB 2: NETWORK VISUALIZATION

The Network tab shows your **entire website as an interactive map**.

#### What You're Looking At

```
                    ┌─────┐
                    │ 🏠  │ ← Homepage (Blue, Large)
                    └──┬──┘
           ┌──────────┼──────────┐
        ┌──┴──┐    ┌──┴──┐    ┌──┴──┐
        │ 📁  │    │ 📁  │    │ 📁  │ ← Main Sections (Green)
        └──┬──┘    └──┬──┘    └──┬──┘
      ┌────┼────┐    │      ┌───┼───┐
    ┌─┴─┐┌─┴─┐┌─┴─┐┌─┴─┐  ┌─┴─┐ ┌─┴─┐
    │📄 ││📄 ││📄 ││📄 │  │📄 │ │📄 │ ← Subsections (Amber)
    └───┘└───┘└───┘└───┘  └───┘ └───┘
```

#### Visual Elements

| Element | Meaning |
|---------|---------|
| **Circle/Node** | A page on your website |
| **Line/Edge** | Link between two pages |
| **Circle Size** | Importance (bigger = more links) |
| **Circle Color** | Depth level (blue→purple→pink) |

#### How to Interact

| Action | How To | Result |
|--------|--------|--------|
| **Hover** | Move mouse over node | See page details tooltip |
| **Click** | Click on node | Select and highlight page |
| **Drag** | Click and drag empty space | Pan around the map |
| **Zoom In** | Scroll up / Click + button | Get closer view |
| **Zoom Out** | Scroll down / Click - button | See more of map |
| **Reset** | Click reset button | Return to default view |
| **Export** | Click "Export PNG" | Download image |

#### Toolbar Controls

```
┌─────────────────────────────────────────────────┐
│ [🔍+] [🔍-] [↺ Reset] [⬇️ Export PNG]          │
└─────────────────────────────────────────────────┘
```

#### Reading the Legend

```
● Depth 0-1 (Homepage/Main)  - Blue
● Depth 2-3 (Section Pages)  - Purple  
● Depth 4+ (Deep Pages)      - Pink
ℹ️ Node size represents link count
```

#### What to Look For

✅ **Good Signs:**
- Balanced tree structure
- Most pages within 3-4 levels
- No isolated nodes
- Dense connections in main areas

❌ **Problem Signs:**
- Long chains of pages (5+ levels deep)
- Isolated/disconnected nodes (orphan pages)
- Very uneven distribution
- Too many deep (pink) nodes

---

### 📈 TAB 3: STATISTICS

The Statistics tab provides **detailed charts and metrics**.

#### Chart 1: Pages by Depth Level (Bar Chart)

```
Pages
  │
50├─ ████████████████████████████████████████  (Depth 2: 52 pages)
  │
30├─ ████████████████████████  (Depth 1: 31 pages)
  │
20├─ ████████████████  (Depth 0: 1 page)
  │
  └────────────────────────────────────────────
       Depth 0    Depth 1    Depth 2    Depth 3
```

**Interpretation:**
- Should look like a **pyramid** (wide base, narrow top)
- Depth 0: Always 1 (homepage)
- Depth 1: Main sections (10-30 typical)
- Depth 2: Subsections (varies)
- Depth 3+: Should decrease

#### Chart 2: Content Distribution (Pie/Donut Chart)

Shows **percentage of pages by main section**:

```
        ┌───────────────┐
       /    Alumni      \
      /      25%         \
     │   ┌─────────┐      │
     │   │ Events  │      │
     │   │  20%    │      │
      \  └─────────┘     /
       \   News 15%    /
        └─────────────┘
         Academics 40%
```

**What to look for:**
- Balanced distribution = Good
- One section >60% = May need reorganization
- Very small sections (<5%) = Consider merging

#### Metrics Cards

| Metric | What It Means | Optimal |
|--------|---------------|---------|
| **Breadth** | Avg pages per depth | Balanced |
| **Depth Range** | Min to max depth | 0-4 |
| **Link Density** | Avg links per page | 5-15 |
| **Connectivity** | % pages reachable | 100% |

#### Detailed Metrics Table

| Metric | Current | Best Practice | Status |
|--------|---------|---------------|--------|
| Max Depth | 2 | ≤4 | ✅ Good |
| Average Depth | 1.9 | ≤3.0 | ✅ Good |
| IA Score | 84.9/100 | ≥75 | ✅ Good |
| Orphan Pages | 0 | 0 | ✅ Good |
| Dead Ends | 3 | <10% | ✅ Good |

---

### 📋 TAB 4: AUDIT REPORT

The Audit Report tab provides a **professional assessment** suitable for presentations.

#### Expandable Sections

Click on any section header to expand/collapse:

```
┌─────────────────────────────────────────────────────────────────┐
│ ▼ Executive Summary                                      [─]    │
├─────────────────────────────────────────────────────────────────┤
│  IA Score: 84.9/100    Total Pages: 115    Max Depth: 2        │
│  Status: Good          Interpretation: Well-organized site      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ▶ Critical Issues (3)                                    [+]    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ▶ Recommendations                                        [+]    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ▶ IA Score Breakdown                                     [+]    │
└─────────────────────────────────────────────────────────────────┘
```

#### Section Details

**1. Executive Summary**
- Overall IA Score with interpretation
- Total pages analyzed
- Maximum depth reached
- Health status badge

**2. Critical Issues**
- 🔴 Orphan Pages: Pages with no inbound links
- 🟡 Dead Ends: Pages with no outbound links
- 🟡 Bottlenecks: Pages hard to reach

**3. Recommendations**
Organized by priority:

| Priority | Timeframe | Example Actions |
|----------|-----------|-----------------|
| **Critical** | This week | Fix broken links, add navigation |
| **Important** | This month | Reorganize deep content |
| **Nice to Have** | Long term | Implement breadcrumbs |

**4. IA Score Breakdown**
- Depth Score: How well-organized depth levels are
- Balance Score: How evenly distributed content is
- Connectivity Score: How well pages are linked

#### Export Options

```
[📄 Export TXT]  [🖨️ Print Report]
```

---

### 📑 TAB 5: DATA TABLE

The Data Table tab shows **every page** with full details.

#### Table Controls

```
┌─────────────────────────────────────────────────────────────────┐
│ [🔍 Search URLs, titles...]  [Depth ▼]  [Status ▼]  [⬇️ CSV]  │
└─────────────────────────────────────────────────────────────────┘
```

| Control | Function |
|---------|----------|
| **Search Box** | Find pages by URL or title |
| **Depth Filter** | Show only specific depth levels |
| **Status Filter** | Show only specific HTTP statuses |
| **Export CSV** | Download all data |

#### Table Columns

| Column | Description | Sortable |
|--------|-------------|----------|
| **URL** | Page address | ✅ |
| **Title** | Page title | ✅ |
| **Depth** | Clicks from homepage | ✅ |
| **Links** | Number of outbound links | ✅ |
| **Status** | HTTP status code | ✅ |

#### How to Use

1. **Search:** Type in search box to filter
2. **Sort:** Click column header to sort
3. **Filter:** Use dropdowns to narrow results
4. **Export:** Click "Export CSV" to download

#### Status Codes Explained

| Code | Meaning | Color |
|------|---------|-------|
| **200** | OK - Page works | 🟢 Green |
| **301/302** | Redirect | 🟡 Amber |
| **404** | Not Found | 🔴 Red |
| **500** | Server Error | 🔴 Red |

---

### 🧠 TAB 6: MIND MAP

The Mind Map tab provides **hierarchical visualization** of your website.

#### View Options

```
┌─────────────────────────────────────────────────────────────────┐
│ [◉ Radial View] [⊞ Tree View]    [All Depths ▼] [↺] [⬇️ PNG]  │
└─────────────────────────────────────────────────────────────────┘
```

#### Radial View (Default)

Shows website as a **circular/radial layout**:

```
                    🟡 🟡
                 🟡       🟡
              🟡     🟢     🟡
           🟡    🟢     🟢    🟡
          🟡   🟢    🔵    🟢   🟡
           🟡    🟢     🟢    🟡
              🟡     🟢     🟡
                 🟡       🟡
                    🟡 🟡
```

- 🔵 **Center:** Homepage
- 🟢 **Inner Ring:** Main sections
- 🟡 **Outer Ring:** Subsections and pages

#### Tree View

Shows website as a **top-down hierarchy**:

```
                    ┌─────┐
                    │ 🔵  │ Homepage
                    └──┬──┘
         ┌─────────────┼─────────────┐
      ┌──┴──┐       ┌──┴──┐       ┌──┴──┐
      │ 🟢  │       │ 🟢  │       │ 🟢  │ Main Sections
      └──┬──┘       └──┬──┘       └──┬──┘
    ┌────┴────┐       │         ┌───┴───┐
  ┌─┴─┐    ┌─┴─┐   ┌─┴─┐     ┌─┴─┐  ┌─┴─┐
  │🟡 │    │🟡 │   │🟡 │     │🟡 │  │🟡 │ Subsections
  └───┘    └───┘   └───┘     └───┘  └───┘
```

#### Controls

| Button | Function |
|--------|----------|
| **Radial View** | Switch to circular layout |
| **Tree View** | Switch to hierarchical layout |
| **All Depths** | Filter by depth level |
| **Reset** | Reset zoom and filters |
| **Export PNG** | Download as image |

#### Side Panel Information

**Structure Summary:**
- Pages count by depth level
- Color-coded indicators

**Content Treemap:**
- Visual breakdown of content distribution
- Size represents page count

**Quick Stats:**
- Total Pages
- Max Depth
- Avg Links/Page
- IA Score

---

## 6. HOW-TO GUIDES

### 📖 How to Find a Specific Page

**Method 1: Using Data Table Search**
1. Go to **Data Table** tab
2. Type page name or URL in search box
3. Results filter automatically
4. Click URL to open page

**Method 2: Using Network Graph**
1. Go to **Network** tab
2. Use browser's Ctrl+F (Cmd+F on Mac)
3. Type page name
4. Hover over highlighted nodes

### 📖 How to Identify Problem Pages

**Step 1: Check Overview**
1. Look at "Issues Found" section
2. Note counts for orphan pages, dead ends, bottlenecks

**Step 2: Review Audit Report**
1. Go to **Audit Report** tab
2. Expand "Critical Issues" section
3. See detailed list with URLs

**Step 3: Verify in Data Table**
1. Go to **Data Table** tab
2. Sort by "Links" column (ascending)
3. Pages with 0 links are dead ends

### 📖 How to Export a Report

**Export Audit Report (TXT):**
1. Go to **Audit Report** tab
2. Click "Export TXT" button
3. File downloads automatically

**Export Data (CSV):**
1. Go to **Data Table** tab
2. Click "Export CSV" button
3. Open in Excel or Google Sheets

**Export Visualization (PNG):**
1. Go to **Network** or **Mind Map** tab
2. Click "Export PNG" button
3. Image downloads automatically

### 📖 How to Refresh Data After Website Changes

**Step 1: Run New Crawl**
```bash
python main.py
```

**Step 2: Refresh Dashboard**
1. Click refresh button 🔄 in header
2. Or add `?refresh=1` to URL
3. Or press F5 to reload page

### 📖 How to Compare Before and After

**Step 1: Save Current Report**
1. Export audit report before changes
2. Name file with date (e.g., `audit_2024_01_15.txt`)

**Step 2: Make Website Changes**
- Implement recommended improvements

**Step 3: Re-crawl and Compare**
1. Run `python main.py` again
2. Export new audit report
3. Compare scores and metrics

### 📖 How to Present Findings to Leadership

**Recommended Approach:**

1. **Start with Executive Summary**
   - Open Audit Report tab
   - Show IA Score and Health Status
   - Highlight key numbers

2. **Show Visual Evidence**
   - Switch to Network tab
   - Point out problem areas
   - Show isolated/deep nodes

3. **Present Action Plan**
   - Return to Audit Report
   - Expand Recommendations
   - Focus on Critical items first

4. **Provide Data Backup**
   - Export CSV for detailed questions
   - Export PNG for documentation

---

## 7. UNDERSTANDING YOUR DATA

### 📊 Data Sources

| File | Location | Contents |
|------|----------|----------|
| `tsm_crawl_data.csv` | `output/` | All crawled page data |
| `tsm_crawl_data.json` | `output/` | Hierarchical structure |
| `TSM_Website_Audit_Report.txt` | `output/` | Generated audit report |

### 📊 CSV Column Reference

| Column | Type | Description |
|--------|------|-------------|
| `url` | String | Full page URL |
| `title` | String | Page title from HTML |
| `depth` | Integer | Clicks from homepage |
| `parent_url` | String | URL of parent page |
| `child_count` | Integer | Number of outbound links |
| `status_code` | Integer | HTTP response code |
| `description` | String | Meta description |
| `heading` | String | Main H1 heading |

### 📊 How Data is Collected

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRAWL PROCESS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Start at Homepage                                          │
│         ↓                                                       │
│  2. Extract all links                                          │
│         ↓                                                       │
│  3. Visit each linked page                                     │
│         ↓                                                       │
│  4. Record: URL, Title, Links, Status                          │
│         ↓                                                       │
│  5. Repeat for new links (up to max depth)                     │
│         ↓                                                       │
│  6. Save to CSV and JSON                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 📊 Data Freshness

- Data represents **point-in-time snapshot**
- Re-run crawler after website changes
- Timestamp shown in dashboard header
- Recommended: Weekly or after major updates

---

## 8. INTERPRETING REPORTS

### 📈 Understanding IA Score

The Information Architecture Score is calculated from three components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    IA SCORE FORMULA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Final Score = (Depth Score × 0.3)                             │
│              + (Balance Score × 0.3)                            │
│              + (Connectivity Score × 0.4)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| **Depth Score** | 30% | How shallow the navigation is |
| **Balance Score** | 30% | How evenly content is distributed |
| **Connectivity Score** | 40% | How well pages are linked |

### 📈 Score Interpretation

| Score Range | Rating | Meaning |
|-------------|--------|---------|
| **90-100** | Excellent | Optimal organization, minimal improvements needed |
| **75-89** | Good | Well-organized, some room for improvement |
| **50-74** | Needs Improvement | Several issues to address |
| **25-49** | Poor | Significant reorganization needed |
| **0-24** | Critical | Major structural problems |

### 📈 Understanding Depth Analysis

**Optimal Structure:**
```
Depth 0: ████ (1 page - Homepage)
Depth 1: ████████████ (10-20 pages - Main sections)
Depth 2: ████████████████████ (30-50 pages - Subsections)
Depth 3: ████████████ (10-20 pages - Detail pages)
Depth 4+: ████ (Few pages - Deep content)
```

**Problematic Structure:**
```
Depth 0: ████ (1 page)
Depth 1: ████ (Few pages)
Depth 2: ████ (Few pages)
Depth 3: ████████████████████████████████████████ (Too many!)
Depth 4+: ████████████████████████ (Way too deep!)
```

### 📈 Reading Recommendations

Recommendations are prioritized by:

| Priority | Timeframe | Effort | Impact |
|----------|-----------|--------|--------|
| **Critical** | This week | 1-4 hours | High |
| **Important** | This month | 1-2 days | Medium |
| **Nice to Have** | Quarter | 1-2 weeks | Low-Medium |

**Example Recommendation:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔴 CRITICAL                                                     │
├─────────────────────────────────────────────────────────────────┤
│ Action: Add internal links to orphan pages                      │
│ Effort: 2 hours                                                 │
│ Impact: +15% navigation improvement                             │
│ Difficulty: Easy                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. TROUBLESHOOTING

### 🔧 Common Issues and Solutions

#### Issue: Dashboard Won't Load

**Symptoms:**
- Browser shows "Connection refused"
- Page stays blank
- Loading spinner never stops

**Solutions:**
1. **Check if server is running:**
   - Look for terminal window with Flask output
   - Should see "Running on http://127.0.0.1:5000"

2. **Restart the server:**
   ```bash
   # Stop with Ctrl+C, then:
   python run_dashboard_shadcn.py
   ```

3. **Check the port:**
   - Try `http://localhost:5000` or `http://127.0.0.1:5000`
   - If port conflict, use different port

4. **Clear browser cache:**
   - Press Ctrl+Shift+Delete
   - Clear cached files
   - Reload page

#### Issue: Charts Not Displaying

**Symptoms:**
- Empty chart areas
- "Loading..." that never completes
- JavaScript errors in console

**Solutions:**
1. **Check browser console:**
   - Press F12 → Console tab
   - Look for red error messages

2. **Try different browser:**
   - Chrome, Firefox, Safari, Edge
   - Avoid Internet Explorer

3. **Disable browser extensions:**
   - Ad blockers may interfere
   - Try incognito/private mode

4. **Check data file:**
   - Verify `output/tsm_crawl_data.csv` exists
   - Run crawler if missing

#### Issue: Data Appears Outdated

**Symptoms:**
- Old page counts
- Missing new pages
- Incorrect structure

**Solutions:**
1. **Re-run the crawler:**
   ```bash
   python main.py
   ```

2. **Force refresh dashboard:**
   - Click refresh button 🔄
   - Or visit `http://localhost:5000/?refresh=1`

3. **Check crawl output:**
   - Look at terminal for crawl results
   - Verify page count matches expectations

#### Issue: Export Not Working

**Symptoms:**
- Download doesn't start
- File is empty or corrupted
- Permission denied error

**Solutions:**
1. **Check download folder:**
   - Default is browser's download location
   - May need to allow downloads

2. **Try different export format:**
   - If CSV fails, try TXT
   - If PNG fails, try screenshot

3. **Check file permissions:**
   - Ensure write access to output folder

#### Issue: Network Graph Too Cluttered

**Symptoms:**
- Too many nodes overlapping
- Can't distinguish pages
- Performance is slow

**Solutions:**
1. **Use zoom controls:**
   - Zoom in to specific areas
   - Use mouse wheel

2. **Use Mind Map instead:**
   - Tree view may be clearer
   - Better for large sites

3. **Filter by depth:**
   - Show only specific depth levels
   - Focus on problem areas

### 🔧 Error Messages Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `FileNotFoundError` | Data file missing | Run `python main.py` |
| `ConnectionRefused` | Server not running | Start server |
| `ModuleNotFoundError` | Missing dependency | Run `pip install -r requirements.txt` |
| `PermissionError` | Can't write file | Check folder permissions |
| `JSONDecodeError` | Corrupted data file | Re-run crawler |

---

## 10. FREQUENTLY ASKED QUESTIONS

### General Questions

**Q: How often should I run the crawler?**
> A: Run after any significant website changes, or at least weekly for active sites. Monthly is sufficient for stable sites.

**Q: Does the crawler affect my website performance?**
> A: The crawler is designed to be polite with configurable delays between requests. Default settings have minimal impact.

**Q: Can I crawl any website?**
> A: The tool is designed for your own websites. Always respect robots.txt and terms of service when crawling.

**Q: How long does a crawl take?**
> A: Depends on site size. Typical: 100 pages ≈ 2-5 minutes, 1000 pages ≈ 20-30 minutes.

### Dashboard Questions

**Q: Why do some pages show as "orphan"?**
> A: Orphan pages have no internal links pointing to them. They're only accessible via direct URL or external links.

**Q: What's a good IA Score?**
> A: 75+ is good, 85+ is excellent. Scores below 50 indicate significant issues.

**Q: Can I customize the dashboard appearance?**
> A: Yes, you can switch between dark and light themes. Further customization requires code changes.

**Q: Is my data stored anywhere else?**
> A: Data is stored locally only. No data is sent to external servers.

### Technical Questions

**Q: What browsers are supported?**
> A: Chrome, Firefox, Safari, and Edge (latest versions). Internet Explorer is not supported.

**Q: Can I run this on a server?**
> A: Yes, change `host='0.0.0.0'` in the Flask app to allow external connections. Use proper security measures.

**Q: How do I update to a new version?**
> A: Pull latest changes from GitHub: `git pull origin main`, then reinstall dependencies.

**Q: Can I integrate this with other tools?**
> A: Yes, the CSV and JSON outputs can be imported into other analysis tools. API endpoints are also available.

---

## 11. GLOSSARY

### A-D

| Term | Definition |
|------|------------|
| **Architecture Score** | A 0-100 rating of how well your website is organized |
| **Breadcrumbs** | Navigation showing the path from homepage to current page |
| **Crawl** | The process of automatically visiting and recording all pages |
| **Dead End** | A page with no links to other pages on the site |
| **Depth** | Number of clicks required to reach a page from the homepage |

### E-I

| Term | Definition |
|------|------------|
| **Edge** | A line connecting two nodes in a graph (represents a link) |
| **Homepage** | The main entry point of a website (depth 0) |
| **HTTP Status** | A code indicating the result of a page request (200=OK, 404=Not Found) |
| **Information Architecture (IA)** | The structural design of information in a website |
| **Internal Link** | A link from one page to another on the same website |

### L-O

| Term | Definition |
|------|------------|
| **Link Density** | Average number of internal links per page |
| **Navigation** | The system of links allowing users to move through a website |
| **Node** | A point in a graph representing a page |
| **Orphan Page** | A page with no internal links pointing to it |

### P-Z

| Term | Definition |
|------|------------|
| **Parent Page** | The page that links to the current page (one level up) |
| **Radial Layout** | A circular visualization with the homepage at center |
| **Sitemap** | A list or diagram of all pages on a website |
| **Tree Layout** | A hierarchical visualization showing parent-child relationships |
| **URL** | Uniform Resource Locator - the address of a web page |

---

## 12. TIPS & BEST PRACTICES

### 🎯 For Best Results

#### Before Running the Crawler

✅ **Do:**
- Ensure website is accessible
- Check robots.txt allows crawling
- Run during low-traffic periods
- Set appropriate depth limits

❌ **Don't:**
- Crawl during peak hours
- Set unlimited depth on large sites
- Ignore rate limiting
- Crawl sites you don't own

#### When Analyzing Results

✅ **Do:**
- Start with Overview tab
- Focus on critical issues first
- Compare against previous crawls
- Export reports for records

❌ **Don't:**
- Ignore orphan pages
- Overlook deep content
- Skip the audit report
- Forget to re-crawl after changes

### 🎯 Optimization Tips

#### Quick Wins (High Impact, Low Effort)

1. **Add links to orphan pages** - 2 hours, +15% improvement
2. **Add "Related Content" sections** - 4 hours, +10% improvement
3. **Fix broken internal links** - 1 hour, +5% improvement
4. **Add breadcrumb navigation** - 4 hours, +10% improvement

#### Long-term Improvements

1. **Flatten deep content** - Move pages closer to homepage
2. **Consolidate similar sections** - Reduce navigation complexity
3. **Implement search functionality** - Alternative navigation path
4. **Create section landing pages** - Better organization

### 🎯 Recommended Workflow

**Weekly:**
1. Run crawler
2. Check IA Score
3. Review new issues
4. Address critical items

**Monthly:**
1. Full audit report review
2. Compare with previous month
3. Plan improvements
4. Update stakeholders

**Quarterly:**
1. Comprehensive analysis
2. Strategic recommendations
3. Executive presentation
4. Set goals for next quarter

### 🎯 Industry Benchmarks

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| IA Score | <50 | 50-74 | 75-89 | 90+ |
| Avg Depth | >4.0 | 3.0-4.0 | 2.0-3.0 | <2.0 |
| Orphan Pages | >10% | 5-10% | 1-5% | 0% |
| Dead Ends | >30% | 15-30% | 5-15% | <5% |
| Max Depth | >6 | 5-6 | 4 | ≤3 |

---

## 13. CONTACT & SUPPORT

### 📞 Getting Help

**Documentation:**
- This user manual
- README.md in project folder
- Code comments

**GitHub Repository:**
- [github.com/Kamal-1711/tsm-website-crawler](https://github.com/Kamal-1711/tsm-website-crawler)
- Open issues for bugs
- Submit feature requests

**Community:**
- GitHub Discussions
- Stack Overflow (tag: website-crawler)

### 📞 Reporting Issues

When reporting issues, please include:

1. **Description:** What happened?
2. **Expected:** What should have happened?
3. **Steps:** How to reproduce?
4. **Environment:** OS, Python version, browser
5. **Screenshots:** If applicable
6. **Error messages:** Full text from console

**Example Issue Report:**
```
Title: Network graph not loading

Description: Network tab shows blank area instead of graph

Expected: Should show interactive network visualization

Steps to reproduce:
1. Start dashboard
2. Click Network tab
3. Wait for loading

Environment:
- Windows 11
- Python 3.10
- Chrome 120

Error in console:
"Uncaught TypeError: Cannot read property 'data' of undefined"
```

### 📞 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2024 | Initial release |

### 📞 License

This project is provided for educational and professional use. See LICENSE file for details.

---

<p align="center">
  <b>TSM Website Structure Analysis Dashboard</b><br>
  User Manual v1.0<br>
  © 2024 TSM Web Crawler Project
</p>

---

*Last updated: December 2024*

*Document version: 1.0*

*For the latest version, visit the GitHub repository.*

