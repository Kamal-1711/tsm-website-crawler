# TSM Website Crawler - Product Analytics Case Study

## 1. Executive Summary

This project developed a production-ready web crawler to systematically analyze the information architecture and digital presence of Thiagarajar School of Management (TSM) website. The solution successfully crawled **115 pages** across **7 main sections**, achieving a **navigation efficiency score of 75.86/100** and generating comprehensive insights into site structure, navigation patterns, and user experience opportunities. The business value lies in providing data-driven recommendations for website optimization, improved user journeys, and enhanced digital accessibility for students, parents, and stakeholders.

**Key Metrics Achieved:**
- ✅ 115 pages crawled with 98.3% success rate
- ✅ 7 main website sections identified and analyzed
- ✅ Navigation efficiency score: 75.86/100
- ✅ Complete site hierarchy visualization generated
- ✅ Comprehensive analytics report with actionable recommendations

---

## 2. Problem Statement

Educational institutions face significant challenges in understanding and optimizing their digital presence:

- **Website Structure Complexity**: Modern educational websites often grow organically, resulting in complex navigation structures that may not align with user needs. Without systematic analysis, institutions cannot identify navigation inefficiencies, orphan pages, or content distribution issues.

- **User Experience Impact**: Website structure directly affects how students, parents, and prospective applicants find information. Poor information architecture leads to increased bounce rates, reduced engagement, and frustrated users who cannot locate critical information like admissions, programs, or faculty details.

- **Manual Analysis Limitations**: Manual website audits are time-consuming, error-prone, and cannot scale. Human reviewers cannot efficiently track link relationships, measure navigation depth, or identify patterns across hundreds of pages. This creates a need for automated, data-driven analysis tools.

---

## 3. Solution Approach

### Web Crawler Architecture

The solution implements a **depth-limited recursive crawler** that systematically explores website structure while respecting server resources:

- **Recursive Depth Control**: Configurable maximum depth (default: 2 levels) prevents infinite crawling
- **Domain Filtering**: Restricts crawling to specified domains to maintain focus
- **URL Normalization**: Prevents duplicate crawling by normalizing URLs (removing fragments, queries, trailing slashes)
- **Respectful Crawling**: Implements request delays (1.5s) and timeout controls to avoid server overload

### Data Collection Methodology

The crawler collects comprehensive metadata for each page:

- **Structural Data**: URL, parent URL, crawl depth, HTTP status codes
- **Content Metadata**: Page titles, meta descriptions, main headings
- **Link Analysis**: Child link counts, parent-child relationships
- **Quality Metrics**: Success/failure rates, missing metadata detection

### Visualization Approach

Multi-dimensional visualization strategy:

- **Network Graph**: Hierarchical visualization using NetworkX showing site structure with nodes colored by depth and sized by link importance
- **Statistical Charts**: Depth distribution bar charts, section size comparisons
- **Analytics Reports**: Text-based comprehensive reports with metrics, recommendations, and insights

---

## 4. Technical Implementation

### Technologies Used

- **Python 3.8+**: Core programming language
- **BeautifulSoup4**: HTML parsing and content extraction
- **Requests**: HTTP library for web page fetching
- **NetworkX**: Graph theory library for network analysis and visualization
- **Matplotlib**: Data visualization and chart generation
- **Pandas**: Data manipulation, analysis, and CSV/JSON export
- **LXML**: Fast XML/HTML parser backend

### Architecture Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN EXECUTION SCRIPT                      │
│                         (main.py)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼────────┐      ┌───────▼────────┐
        │   TSMCrawler   │      │  Configuration │
        │  (crawler.py)  │      │  (config.json) │
        └───────┬────────┘      └────────────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│ Fetch │  │ Parse │  │Extract│
│ Pages │  │ HTML  │  │ Links │
└───┬───┘  └───┬───┘  └───┬───┘
    │           │           │
    └───────────┼───────────┘
                │
        ┌───────▼────────┐
        │  Crawl Data   │
        │  (in-memory)  │
        └───────┬───────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌───▼───┐  ┌───▼────────┐
│  CSV  │  │ JSON  │  │Visualize  │
│ Export│  │Export │  │(visualize)│
└───┬───┘  └───┬───┘  └───┬────────┘
    │           │           │
    │           │      ┌────▼────┐
    │           │      │Analytics│
    │           │      │(analytics)│
    │           │      └────┬────┘
    │           │           │
┌───▼───────────▼───────────▼───┐
│      OUTPUT FILES             │
│  • tsm_crawl_data.csv         │
│  • tsm_crawl_data.json        │
│  • tsm_hierarchy.png          │
│  • depth_distribution.png     │
│  • insights_report.txt        │
└───────────────────────────────┘
```

### Data Flow Explanation

1. **Initialization**: Main script loads configuration, creates output directories, and initializes the crawler with parameters (base URL, max depth, delays, domain restrictions)

2. **Crawling Phase**: 
   - Starts from base URL (depth 0)
   - Fetches page content using HTTP requests
   - Parses HTML with BeautifulSoup
   - Extracts links, titles, descriptions, headings
   - Normalizes and validates URLs
   - Recursively crawls child links (depth +1) up to max depth

3. **Data Storage**: 
   - Stores crawl data in memory (list of dictionaries)
   - Exports to CSV for spreadsheet analysis
   - Exports to JSON for hierarchical structure preservation

4. **Visualization Phase**:
   - Creates NetworkX directed graph from crawl data
   - Generates network visualization with depth-based coloring
   - Creates statistical charts (depth distribution)
   - Generates comprehensive analytics report

5. **Analytics Phase**:
   - Calculates site metrics (efficiency scores, depth analysis)
   - Identifies main sections and content distribution
   - Analyzes information architecture
   - Generates actionable recommendations

---

## 5. Key Findings

### Website Structure Overview

The TSM website analysis revealed:

- **Total Pages**: 115 pages organized across 7 main sections
- **Navigation Depth**: 2 levels (optimal for user experience)
- **Page Distribution**: 
  - Level 0 (Homepage): 1 page
  - Level 1 (Main Sections): 9 pages
  - Level 2 (Content Pages): 105 pages

### Navigation Efficiency Assessment

**Overall Score: 75.86/100** - Good, with room for improvement

**Score Breakdown:**
- Depth Score: 15.00/25 (shallow structure is good)
- Link Distribution Score: 14.12/25 (high link count per page)
- Orphan Page Score: 22.39/25 (few orphan pages - excellent)
- Connectivity Score: 24.35/25 (strong internal linking)

**Navigation Pattern**: WIDE - The site has a broad, shallow structure which is generally good for user navigation, though content organization could be improved.

### Top 3 Insights

1. **High-Value Content Pages Identified**: The Alumni Directory (112 links), Full-time Faculty page (96 links), and PhD Scholars page (75 links) are critical navigation hubs. These pages serve as major entry points and should be prominently featured in site navigation.

2. **Excellent Content Connectivity**: With only 3 orphan pages out of 115 (2.6%), the site demonstrates strong internal linking. This improves SEO, user discoverability, and reduces bounce rates.

3. **Wide Navigation Pattern**: The site's broad, shallow structure (2 levels deep) is optimal for user experience. However, the wide navigation (105 pages at depth 2) suggests opportunities for better content categorization and grouping into logical subsections.

---

## 6. Business Impact

This comprehensive website analysis provides actionable data for multiple business objectives:

### Improve Website Navigation
- **Section Identification**: 7 main sections clearly mapped (Programmes, Faculty Research, Life at TSM, Placements, About Us, etc.)
- **Navigation Optimization**: Data shows which pages are most linked (high importance) and should be easily accessible
- **User Journey Mapping**: Clear understanding of how users navigate from homepage to content pages

### Identify Orphan Pages
- **Discovery**: Identified 3 orphan pages (pages with no outgoing links) that may be difficult for users to discover
- **SEO Impact**: Orphan pages may have lower search engine visibility
- **Action**: Recommendations to add internal links to improve discoverability

### Optimize Information Architecture
- **Content Distribution**: Average of 16.43 pages per section helps identify sections that may need reorganization
- **Depth Analysis**: 2-level structure is optimal, but wide navigation suggests need for better categorization
- **Link Analysis**: Understanding which pages serve as navigation hubs helps optimize site structure

### Enhance Student/Parent User Journeys
- **Critical Paths**: Identified most important pages (Alumni Directory, Faculty pages) that should be prominently featured
- **Content Accessibility**: Analysis shows how many clicks it takes to reach important information
- **User Experience**: Navigation efficiency score (75.86/100) provides baseline for improvement tracking

### Additional Business Value
- **Data-Driven Decisions**: Replaces guesswork with quantitative analysis
- **Baseline Metrics**: Establishes metrics for tracking improvements over time
- **Competitive Analysis**: Methodology can be applied to competitor websites for benchmarking
- **Maintenance Planning**: Identifies broken links (2 pages with errors) for immediate attention

---

## 7. Skills Demonstrated

### Technical Skills

- **Python Programming**: 
  - Object-oriented design with custom exception handling
  - Advanced data structures (sets, dictionaries, lists)
  - Recursive algorithms for depth-limited crawling
  - File I/O operations (CSV, JSON, logging)

- **Web Scraping (Ethical, Rate-Limited)**:
  - HTTP request handling with proper headers and timeouts
  - HTML parsing with BeautifulSoup
  - URL normalization and validation
  - Domain filtering and extension exclusion
  - Respectful crawling practices (delays, error handling)

- **Data Visualization**:
  - Network graph generation with NetworkX
  - Statistical chart creation with Matplotlib
  - Custom color mapping and node sizing
  - High-resolution image export (300 DPI)

- **Data Analysis**:
  - Pandas DataFrame manipulation
  - Statistical calculations (averages, distributions, ratios)
  - Information architecture analysis
  - Navigation efficiency scoring algorithms

### Professional Skills

- **Problem-Solving Approach**:
  - Breaking down complex problem (website analysis) into manageable components
  - Designing scalable architecture for different website sizes
  - Implementing error handling and graceful degradation
  - Creating reusable, modular code structure

- **Documentation**:
  - Comprehensive README with setup instructions
  - Inline code comments and docstrings
  - Configuration documentation
  - Case study and analytics reports

- **Project Management**:
  - Structured project organization (src/, output/, visualizations/)
  - Configuration management (config.json)
  - Logging and error tracking
  - Version control best practices (.gitignore)

---

## 8. Future Enhancements

### Real-Time Monitoring Dashboard
- **Web-based Interface**: Create a Flask/Dash dashboard showing live crawl statistics
- **Automated Scheduling**: Daily/weekly automated crawls with change detection
- **Alert System**: Notifications for broken links, new pages, or structural changes
- **Historical Tracking**: Trend analysis showing how site structure evolves over time

### Automated Broken Link Detection
- **Continuous Monitoring**: Regular scans to identify 404 errors, timeouts, or SSL issues
- **Priority Scoring**: Rank broken links by importance (based on link count, depth)
- **Automated Reporting**: Email/Slack notifications for critical broken links
- **Fix Tracking**: Monitor when broken links are resolved

### User Behavior Tracking Integration
- **Google Analytics Integration**: Correlate crawl data with actual user behavior
- **Heatmap Analysis**: Combine site structure with click heatmaps
- **Conversion Path Analysis**: Identify which navigation paths lead to conversions
- **A/B Testing Support**: Use structure data to inform navigation A/B tests

### Multi-Website Comparison Tool
- **Competitive Analysis**: Crawl multiple educational institution websites
- **Benchmarking**: Compare navigation efficiency scores, depth, and structure
- **Best Practice Identification**: Identify common patterns in top-performing sites
- **Industry Reports**: Generate comparative analysis reports

### Additional Enhancements
- **SEO Analysis**: Integrate with SEO tools to analyze meta tags, headings, and content structure
- **Accessibility Audit**: Check for accessibility issues (missing alt text, heading hierarchy)
- **Performance Metrics**: Measure page load times and identify slow pages
- **Content Analysis**: NLP analysis of page content to identify topics and themes
- **Mobile Structure Analysis**: Separate analysis for mobile vs desktop site structures
- **API Development**: RESTful API to access crawl data programmatically
- **Machine Learning**: Predict page importance or user navigation patterns using ML models

---

## Conclusion

This TSM Website Crawler project demonstrates the power of automated web analysis for understanding and optimizing digital presence. By systematically crawling 115 pages and generating comprehensive insights, the solution provides educational institutions with data-driven recommendations for improving user experience, navigation efficiency, and information architecture. The production-ready implementation, comprehensive analytics, and actionable insights make this a valuable tool for digital strategy and website optimization.

**Project Repository**: [GitHub/Portfolio Link]  
**Technologies**: Python, BeautifulSoup, NetworkX, Matplotlib, Pandas  
**Status**: ✅ Production Ready

---

*Generated by TSM Website Crawler Analytics Module*

