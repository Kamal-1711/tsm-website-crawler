# TSM Madurai Website Crawler & Architecture Visualizer

A production-ready Python web crawler designed to systematically explore and visualize the structure of educational institution websites. This project demonstrates advanced web scraping techniques, data processing, and network visualization using modern Python libraries.

**Purpose:** This is an educational project created to showcase web scraping capabilities, data analysis, and visualization techniques. It provides insights into website architecture and link relationships through interactive network graphs and comprehensive statistics.

---

## ✨ Features

- **Recursive Depth-Limited Crawling**: Systematically explores websites with configurable depth limits
- **Intelligent URL Normalization**: Prevents duplicate crawling by normalizing URLs
- **Domain Filtering**: Restricts crawling to specified domains for focused analysis
- **Comprehensive Logging**: Detailed logs for debugging and monitoring crawl progress
- **Network Graph Visualization**: Creates beautiful hierarchical visualizations using NetworkX and Matplotlib
- **Multiple Export Formats**: Exports data in both CSV (for analysis) and JSON (for hierarchical structure)
- **Statistics Dashboard**: Generates detailed statistics including page counts, depth distribution, and link analysis
- **Respectful Crawling**: Implements request delays and timeout controls to be respectful to servers
- **Extension Filtering**: Automatically skips non-HTML files (PDFs, images, archives)
- **Production-Ready Error Handling**: Comprehensive exception handling with graceful error recovery

---

## 📁 Project Structure

```
tsm-crawler/
├── src/
│   ├── __init__.py          # Package initializer
│   ├── crawler.py           # TSMCrawler class - core crawling logic
│   └── visualize.py         # Visualization functions and statistics
├── output/                  # Generated data files
│   ├── tsm_crawl_data.csv   # Crawl data in CSV format
│   ├── tsm_crawl_data.json  # Hierarchical JSON structure
│   ├── crawler.log          # Crawler execution logs
│   └── crawler_main.log     # Main script logs
├── visualizations/          # Generated visualization images
│   ├── tsm_hierarchy.png    # Network graph visualization
│   └── depth_distribution.png # Depth distribution bar chart
├── .vscode/                 # VS Code workspace settings (optional)
├── main.py                  # Main execution script
├── requirements.txt         # Python dependencies
├── config.json              # Configuration settings
├── README.md                # This file
└── .gitignore               # Git ignore rules
```

### Folder Descriptions

- **`src/`**: Contains all source code modules. The crawler logic and visualization functions are modularized here.
- **`output/`**: Stores all generated data files including CSV exports, JSON hierarchies, and log files.
- **`visualizations/`**: Contains PNG images of network graphs and statistical charts generated from crawl data.
- **`.vscode/`**: Optional VS Code configuration for consistent development environment.

---

## 🔧 Prerequisites

Before installing and running the TSM Web Crawler, ensure you have:

- **Python 3.8+** (Python 3.9 or 3.10 recommended)
- **pip** package manager (usually comes with Python)
- **~50MB** free disk space for dependencies and output files
- **Active internet connection** for crawling websites
- **Command line access** (PowerShell on Windows, Terminal on Mac/Linux)

### Verify Python Installation

```bash
python --version
# or
python3 --version
```

---

## 📦 Installation

### Step 1: Clone or Download the Project

If you have the project in a Git repository:

```bash
git clone <repository-url>
cd tsm-crawler
```

Or simply navigate to the project directory if you've downloaded it:

```bash
cd path/to/tsm-crawler
```

### Step 2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
```

**Mac/Linux:**
```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

If you encounter an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal prompt when activated.

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Verify Installation

```bash
python -c "import requests, bs4, networkx, matplotlib, pandas; print('All dependencies installed successfully!')"
```

---

## 🚀 Quick Start

Once installation is complete, follow these steps:

1. **Navigate to project directory:**
   ```bash
   cd tsm-crawler
   ```

2. **Activate virtual environment:**
   ```powershell
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   ```

3. **Run the crawler:**
   ```bash
   python main.py
   ```

4. **Wait for completion** - The crawler will:
   - Display progress messages
   - Show crawl statistics
   - Generate visualizations
   - Save all output files

5. **Check results:**
   - **CSV Data**: `output/tsm_crawl_data.csv`
   - **JSON Data**: `output/tsm_crawl_data.json`
   - **Hierarchy Graph**: `visualizations/tsm_hierarchy.png`
   - **Depth Chart**: `visualizations/depth_distribution.png`

The entire process typically takes 5-15 minutes depending on website size and configured depth.

---

## ⚙️ Configuration

The crawler behavior is controlled through `config.json`. Here are the key parameters:

### Crawl Settings

```json
"crawl_settings": {
  "base_url": "https://tsm.ac.in/",      // Starting URL
  "max_depth": 2,                         // How deep to crawl (0-5 recommended)
  "request_delay": 1.5,                   // Seconds between requests
  "timeout": 10,                          // Request timeout in seconds
  "user_agent": "TSM-Crawler/1.0..."     // Browser identification
}
```

**Adjusting `max_depth`:**
- `0`: Only the homepage
- `1`: Homepage + direct links
- `2`: Homepage + direct links + links from those pages (recommended for testing)
- `3+`: Deeper exploration (use cautiously)

**Adjusting `request_delay`:**
- `0.5-1.0`: Faster but may trigger rate limiting
- `1.5-2.0`: Balanced (recommended)
- `2.0+`: Slower but more respectful to servers

### Output Settings

```json
"output_settings": {
  "csv_output_path": "output/tsm_crawl_data.csv",
  "json_output_path": "output/tsm_crawl_data.json"
}
```

Change these paths to save output files in different locations.

### Filtering Settings

```json
"filtering": {
  "allowed_domains": ["tsm.ac.in"],      // Only crawl these domains
  "exclude_extensions": [".pdf", ".jpg"] // Skip these file types
}
```

---

## 📊 Output Files

### `tsm_crawl_data.csv`

Comma-separated values file containing all crawled pages with the following columns:

| Column | Description |
|--------|-------------|
| `url` | Full URL of the page |
| `parent_url` | URL that linked to this page (None for homepage) |
| `depth` | Crawl depth (0 = homepage, 1 = first level, etc.) |
| `status_code` | HTTP status code (200 = success) |
| `title` | Page title from `<title>` tag |
| `description` | Meta description if available |
| `heading` | First `<h1>` heading on the page |
| `child_count` | Number of links found on this page |

**Usage:** Open in Excel, Google Sheets, or any spreadsheet application for analysis.

### `tsm_crawl_data.json`

Hierarchical JSON structure showing parent-child relationships:

```json
{
  "url": "https://tsm.ac.in/",
  "depth": 0,
  "title": "Homepage",
  "children": [
    {
      "url": "https://tsm.ac.in/about",
      "depth": 1,
      "title": "About Us",
      "children": [...]
    }
  ]
}
```

**Usage:** Perfect for programmatic analysis or building interactive tree views.

### `tsm_hierarchy.png`

High-resolution network graph visualization (300 DPI) showing:
- **Nodes**: Each page as a colored circle
- **Edges**: Links between pages as arrows
- **Colors**: Depth levels (lighter = shallow, darker = deep)
- **Sizes**: Larger nodes have more child links

**Usage:** View in any image viewer or include in reports/presentations.

### `crawler.log` & `crawler_main.log`

Detailed execution logs with timestamps, including:
- Crawl progress
- Errors and warnings
- Statistics
- Execution flow

**Usage:** Debug issues or track crawl progress.

---

## 📈 Understanding the Results

### Reading the CSV

1. **Open in Excel/Sheets**: The CSV is formatted for easy spreadsheet analysis
2. **Filter by depth**: See how many pages exist at each level
3. **Sort by child_count**: Identify pages with the most links
4. **Analyze parent_url**: Understand the site's link structure

### Interpreting the Hierarchy Visualization

- **Node Color (Blue gradient)**: 
  - Light blue = Shallow pages (depth 0-1)
  - Dark blue = Deep pages (depth 2+)
- **Node Size**: 
  - Larger nodes = More child links
  - Smaller nodes = Fewer or no links
- **Arrows**: Show link direction (parent → child)
- **Layout**: Spring layout groups related pages together

### Understanding Statistics

- **Total Pages Crawled**: Total number of unique pages discovered
- **Max Depth Reached**: How deep the crawler went
- **Pages by Depth**: Distribution showing how pages are organized
- **Average Children per Page**: Average number of links per page
- **Orphan Pages**: Pages with no outgoing links

### Color Coding

The visualization uses a **Blues** colormap where:
- **Lightest blue**: Depth 0 (homepage)
- **Medium blue**: Depth 1-2 (main sections)
- **Darkest blue**: Depth 3+ (deep pages)

---

## 🔧 Troubleshooting

### ModuleNotFoundError

**Error:** `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
# Ensure virtual environment is activated
pip install -r requirements.txt
```

### Connection Errors

**Error:** `Connection timeout` or `Connection refused`

**Solutions:**
- Check your internet connection
- Verify the target website is accessible
- Increase `timeout` in `config.json`
- Check if the website blocks automated requests

### Permission Errors

**Error:** `Permission denied` when creating files

**Solution:**
- Ensure you have write permissions in the project directory
- On Windows, run PowerShell as Administrator if needed
- Check that `output/` and `visualizations/` directories are writable

### Empty CSV/No Data

**Possible Causes:**
- Website blocks crawlers (check robots.txt)
- Allowed domains misconfigured
- Network issues during crawl
- Website requires authentication

**Solution:** Check `output/crawler.log` for detailed error messages.

### PowerShell Execution Policy Error

**Error:** `cannot be loaded because running scripts is disabled`

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Graph Visualization Empty

**Error:** Visualization file created but appears empty

**Solution:**
- Ensure CSV file contains data
- Check that `output/tsm_crawl_data.csv` exists and has rows
- Verify matplotlib is properly installed: `pip install matplotlib --upgrade`

---

## 🤝 Ethical Considerations

This crawler is designed with ethical web scraping practices:

- **Respects robots.txt**: Always check a website's `robots.txt` before crawling
- **Request Delays**: Implements delays between requests to avoid overloading servers
- **Educational Purpose**: Designed for learning and portfolio demonstration
- **No Sensitive Data**: Only collects publicly available page structure and metadata
- **User-Agent Identification**: Clearly identifies itself as an educational crawler
- **Domain Restrictions**: Only crawls specified domains to avoid unintended exploration

**Important:** Always obtain permission before crawling websites, especially for production use. This tool is intended for educational purposes and personal portfolio projects.

---

## 🚀 Future Improvements

Potential enhancements for future versions:

- **Multi-Website Support**: Configure and crawl multiple websites in one session
- **Parallel Crawling**: Implement multi-threaded crawling for faster execution
- **Authentication Handling**: Support for websites requiring login
- **Interactive Visualization**: Web-based interactive graph using D3.js or Plotly
- **Export Formats**: Support for Excel, PDF reports, and database exports
- **Robots.txt Parser**: Automatic robots.txt compliance checking
- **Sitemap Integration**: Use XML sitemaps for more efficient crawling
- **Real-time Progress**: Web dashboard showing live crawl progress
- **Custom Extractors**: Allow users to define custom data extraction rules
- **Scheduled Crawling**: Automatic periodic crawls with cron-like scheduling

---

## 👤 Author & License

**Author:** [Your Name]

**Created:** 2024

**License:** MIT License

This project is open source and available for educational use. Feel free to modify and extend it for your own projects.

---

## 📧 Contact & Support

For questions, issues, or contributions:

- **Email:** [your.email@example.com]
- **GitHub Issues:** [repository-url]/issues
- **Documentation:** See `CONFIG_DOCUMENTATION.md` for detailed configuration options

---

## 🙏 Acknowledgments

Built with:
- [Requests](https://requests.readthedocs.io/) - HTTP library
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [NetworkX](https://networkx.org/) - Network analysis
- [Matplotlib](https://matplotlib.org/) - Visualization
- [Pandas](https://pandas.pydata.org/) - Data processing

---

**Happy Crawling! 🕷️**
