# Interactive Web Dashboard

## Quick Start

1. **Install Dependencies** (if not already installed):
   ```bash
   pip install flask plotly
   ```

2. **Run the Dashboard**:
   ```bash
   python dashboard.py
   ```

3. **Access the Dashboard**:
   - Open your browser and navigate to: `http://localhost:5000`
   - The dashboard will automatically load your crawl data from `output/tsm_crawl_data.csv`

## Features

- ✅ **Summary Cards**: Key metrics at a glance
- ✅ **Interactive Network Graph**: Visualize site structure with hover details
- ✅ **Charts**: Depth distribution, section pie chart, treemap
- ✅ **Data Table**: Sortable, filterable table with search
- ✅ **Statistics Panel**: Navigation efficiency and analysis
- ✅ **Dark Mode**: Toggle between light and dark themes
- ✅ **Responsive Design**: Works on desktop, tablet, and mobile
- ✅ **Data Refresh**: Reload data without restarting the server

## Routes

- `/` - Main dashboard
- `/data` - JSON API endpoint for crawl data
- `/about` - Project information
- `/api/network-graph` - Network graph JSON
- `/api/depth-chart` - Depth bar chart JSON
- `/api/section-chart` - Section pie chart JSON
- `/api/treemap` - Treemap JSON
- `/api/refresh` - Refresh data endpoint

## Requirements

- Python 3.8+
- Flask 3.0+
- Plotly 5.18+
- Crawl data CSV file (`output/tsm_crawl_data.csv`)

## Troubleshooting

**Dashboard shows "No crawl data found"**:
- Make sure you've run the crawler first: `python main.py`
- Verify that `output/tsm_crawl_data.csv` exists

**Charts not loading**:
- Check browser console for errors
- Verify Plotly CDN is accessible
- Check Flask server logs for errors

**Port 5000 already in use**:
- Change the port in `dashboard.py`: `app.run(port=5001)`

