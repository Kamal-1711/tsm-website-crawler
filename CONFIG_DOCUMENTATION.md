# Configuration File Documentation

## Overview

The `config.json` file contains all settings for the TSM web crawler. This document explains each configuration option in detail.

## Configuration Sections

### 1. crawl_settings

Core crawling behavior and HTTP request parameters.

#### base_url
- **Type:** String (URL)
- **Default:** `"https://tsm.ac.in/"`
- **Description:** The starting URL for the crawler. All crawling begins from this URL and follows links from there.
- **Example:** `"https://tsm.ac.in/"`

#### max_depth
- **Type:** Integer
- **Default:** `2`
- **Description:** Maximum depth to crawl from the base URL.
  - Depth 0: Only the base URL
  - Depth 1: Base URL + all pages directly linked from it
  - Depth 2: Base URL + direct links + links from those pages
- **Note:** Set to 2 for initial testing to avoid overwhelming the server. Increase gradually as needed.
- **Example:** `2`

#### request_delay
- **Type:** Float (seconds)
- **Default:** `1.5`
- **Description:** Delay in seconds between HTTP requests. This prevents server overload and reduces the risk of being blocked or rate-limited.
- **Best Practice:** 1.5 seconds is a reasonable balance between speed and politeness. Increase if you encounter rate limiting.
- **Example:** `1.5`

#### timeout
- **Type:** Integer (seconds)
- **Default:** `10`
- **Description:** Timeout in seconds for each HTTP request. If a page takes longer than this to respond, the request will be abandoned and the URL will be marked as failed.
- **Note:** Adjust based on typical response times of the target website.
- **Example:** `10`

#### user_agent
- **Type:** String
- **Default:** `"TSM-Crawler/1.0 (Educational Project for Portfolio)"`
- **Description:** User-Agent string sent with each HTTP request. This identifies the crawler to the web server and helps with logging and access control.
- **Best Practice:** Always identify your crawler clearly, especially for educational projects.
- **Example:** `"TSM-Crawler/1.0 (Educational Project for Portfolio)"`

---

### 2. output_settings

File paths and formats for saving crawled data.

#### csv_output_path
- **Type:** String (file path)
- **Default:** `"output/tsm_crawl_data.csv"`
- **Description:** Path where crawled data will be saved in CSV format. CSV files are useful for spreadsheet analysis and data manipulation.
- **Note:** The directory will be created automatically if it doesn't exist.
- **Example:** `"output/tsm_crawl_data.csv"`

#### json_output_path
- **Type:** String (file path)
- **Default:** `"output/tsm_crawl_data.json"`
- **Description:** Path where crawled data will be saved in JSON format. JSON preserves hierarchical structure and is easy to parse programmatically.
- **Note:** The directory will be created automatically if it doesn't exist.
- **Example:** `"output/tsm_crawl_data.json"`

---

### 3. visualization_settings

Settings for generating site structure visualizations using NetworkX and Matplotlib.

#### output_path
- **Type:** String (file path)
- **Default:** `"visualizations/tsm_hierarchy.png"`
- **Description:** File path where the site hierarchy visualization will be saved as a PNG image.
- **Note:** The directory will be created automatically if it doesn't exist.
- **Example:** `"visualizations/tsm_hierarchy.png"`

#### figure_size
- **Type:** Array of two integers `[width, height]`
- **Default:** `[20, 12]`
- **Description:** Figure dimensions in inches. Larger sizes provide more detail but take longer to render.
- **Note:** `[20, 12]` is recommended for complex site structures. Reduce for simpler sites or faster rendering.
- **Example:** `[20, 12]`

#### dpi
- **Type:** Integer
- **Default:** `300`
- **Description:** Resolution in dots per inch (DPI). Higher DPI produces sharper images but larger file sizes.
- **Note:** 300 DPI is print-quality resolution. Use 150-200 for web display, 300+ for printing.
- **Example:** `300`

#### node_size
- **Type:** Integer
- **Default:** `500`
- **Description:** Size of nodes (pages) in the network graph visualization. Larger nodes are more visible but may cause overlap in dense graphs.
- **Note:** Adjust based on the number of pages. More pages = smaller nodes recommended.
- **Example:** `500`

#### colormap
- **Type:** String
- **Default:** `"Blues"`
- **Description:** Color scheme for the visualization. Provides a professional, clean appearance.
- **Options:** 
  - Sequential: `"Blues"`, `"Reds"`, `"Greens"`, `"Oranges"`, `"Purples"`
  - Perceptually uniform: `"viridis"`, `"plasma"`, `"inferno"`, `"magma"`
  - Diverging: `"RdBu"`, `"RdYlBu"`, `"Spectral"`
- **Example:** `"Blues"`

---

### 4. filtering

Rules for filtering which URLs to crawl and which to exclude.

#### allowed_domains
- **Type:** Array of strings
- **Default:** `["tsm.ac.in"]`
- **Description:** List of domains the crawler is allowed to visit. Only URLs from these domains will be crawled. This prevents the crawler from following external links and keeps the crawl focused.
- **Note:** Include all variations (with/without www) if needed: `["tsm.ac.in", "www.tsm.ac.in"]`
- **Example:** `["tsm.ac.in"]`

#### exclude_extensions
- **Type:** Array of strings
- **Default:** `[".pdf", ".jpg", ".png", ".gif", ".zip"]`
- **Description:** File extensions to skip during crawling. These file types are typically not HTML pages and don't contain crawlable links. Excluding them saves time and bandwidth.
- **Common Extensions to Exclude:**
  - Documents: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`
  - Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.svg`, `.webp`
  - Archives: `.zip`, `.rar`, `.tar`, `.gz`
  - Media: `.mp4`, `.mp3`, `.avi`, `.mov`
- **Example:** `[".pdf", ".jpg", ".png", ".gif", ".zip"]`

---

## Usage Tips

1. **Start Conservative:** Begin with `max_depth: 2` and `request_delay: 1.5` to test the crawler safely.

2. **Monitor Server Response:** If you encounter rate limiting or blocking, increase `request_delay` to 2-3 seconds.

3. **Adjust Visualization:** For large sites, reduce `figure_size` and `node_size` to prevent overcrowded visualizations.

4. **Domain Filtering:** Always set `allowed_domains` to prevent accidentally crawling external sites.

5. **Extension Filtering:** Add more extensions to `exclude_extensions` if you notice the crawler attempting to download non-HTML files.

## Example Configuration

See `config.json` for the current configuration. For a commented version with explanations, see `config.example.json` (note: JSON doesn't natively support comments, so `config.example.json` uses underscore-prefixed keys for documentation).

