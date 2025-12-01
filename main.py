"""
TSM Website Crawler - Main Execution Script
Orchestrates the complete web crawling and visualization pipeline.
"""

import sys
import os
import json
import logging
import traceback
from pathlib import Path
from src.crawler import TSMCrawler
from src.visualize import main as visualize_main


def setup_logging() -> logging.Logger:
    """
    Setup and configure logging for the main script.
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("TSMCrawlerMain")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = Path("output/crawler_main.log")
    log_file.parent.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def load_config(config_path: str = "config.json") -> dict:
    """
    Load configuration settings from config.json file.
    
    If file not found, returns default configuration values.
    
    Args:
        config_path: Path to configuration file (default: config.json)
        
    Returns:
        Dictionary containing configuration settings
    """
    default_config = {
        "crawl_settings": {
            "base_url": "https://tsm.ac.in/",
            "max_depth": 2,
            "request_delay": 1.5,
            "timeout": 10,
            "user_agent": "TSM-Crawler/1.0 (Educational Project for Portfolio)"
        },
        "output_settings": {
            "csv_output_path": "output/tsm_crawl_data.csv",
            "json_output_path": "output/tsm_crawl_data.json"
        },
        "visualization_settings": {
            "output_path": "visualizations/tsm_hierarchy.png",
            "figure_size": [20, 12],
            "dpi": 300,
            "node_size": 500,
            "colormap": "Blues"
        },
        "filtering": {
            "allowed_domains": ["tsm.ac.in"],
            "exclude_extensions": [".pdf", ".jpg", ".png", ".gif", ".zip"]
        }
    }
    
    try:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger = logging.getLogger("TSMCrawlerMain")
                logger.info(f"Configuration loaded from {config_path}")
                return config
        else:
            logger = logging.getLogger("TSMCrawlerMain")
            logger.warning(f"Config file not found: {config_path}. Using default values.")
            return default_config
    except json.JSONDecodeError as e:
        logger = logging.getLogger("TSMCrawlerMain")
        logger.error(f"Invalid JSON in {config_path}: {e}. Using default values.")
        return default_config
    except Exception as e:
        logger = logging.getLogger("TSMCrawlerMain")
        logger.error(f"Error loading config: {e}. Using default values.")
        return default_config


def create_directories() -> None:
    """
    Ensure all required output directories exist.
    
    Creates output/ and visualizations/ directories if they don't exist.
    """
    logger = logging.getLogger("TSMCrawlerMain")
    
    directories = ["output", "visualizations"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}/")
        else:
            logger.debug(f"Directory already exists: {directory}/")
    
    logger.info("Directories created/verified")


def main() -> None:
    """
    Main execution flow for the TSM Website Crawler.
    
    Orchestrates:
    1. Directory creation
    2. Configuration loading
    3. Crawler instantiation and execution
    4. Data export (CSV and JSON)
    5. Statistics display
    6. Visualization generation
    """
    logger = setup_logging()
    
    try:
        # Log startup
        logger.info("="*60)
        logger.info("Starting TSM Website Crawler...")
        logger.info("="*60)
        
        # Create directories
        logger.info("Step 1/6: Creating required directories...")
        create_directories()
        
        # Load configuration
        logger.info("Step 2/6: Loading configuration...")
        config = load_config()
        
        # Extract configuration values
        crawl_settings = config.get("crawl_settings", {})
        filtering = config.get("filtering", {})
        
        base_url = crawl_settings.get("base_url", "https://tsm.ac.in/")
        max_depth = crawl_settings.get("max_depth", 2)
        request_delay = crawl_settings.get("request_delay", 1.5)
        timeout = crawl_settings.get("timeout", 10)
        user_agent = crawl_settings.get("user_agent", "TSM-Crawler/1.0 (Educational Project for Portfolio)")
        allowed_domains = filtering.get("allowed_domains", ["tsm.ac.in"])
        exclude_extensions = filtering.get("exclude_extensions", [".pdf", ".jpg", ".png", ".gif", ".zip"])
        
        # Instantiate TSMCrawler with config values
        logger.info("Step 3/6: Initializing crawler...")
        logger.info(f"  Base URL: {base_url}")
        logger.info(f"  Max Depth: {max_depth}")
        logger.info(f"  Request Delay: {request_delay}s")
        logger.info(f"  Allowed Domains: {', '.join(allowed_domains)}")
        
        crawler = TSMCrawler(
            base_url=base_url,
            max_depth=max_depth,
            request_delay=request_delay,
            allowed_domains=allowed_domains,
            timeout=timeout,
            user_agent=user_agent,
            exclude_extensions=exclude_extensions
        )
        
        # Start crawling
        logger.info("Step 4/6: Beginning crawl...")
        logger.info(f"Beginning crawl of {base_url}")
        logger.info(f"This may take several minutes depending on site size and depth...")
        
        crawler.crawl(crawler.base_url)
        
        # Save data
        logger.info("Step 5/6: Saving crawl data...")
        output_settings = config.get("output_settings", {})
        csv_path = output_settings.get("csv_output_path", "output/tsm_crawl_data.csv")
        json_path = output_settings.get("json_output_path", "output/tsm_crawl_data.json")
        
        crawler.save_to_csv(csv_path)
        crawler.save_to_json(json_path)
        
        # Print crawl statistics
        logger.info("Crawl Statistics:")
        stats = crawler.get_crawl_statistics()
        
        print("\n" + "="*60)
        print("CRAWL STATISTICS")
        print("="*60)
        print(f"Total Pages Crawled: {stats['total_pages']}")
        print(f"Max Depth Reached: {stats['max_depth_reached']}")
        print(f"Unique Domains: {stats['unique_domains']}")
        print(f"Average Children per Page: {stats['average_children_per_page']}")
        print("\nPages by Depth:")
        for depth, count in sorted(stats['pages_by_depth'].items()):
            print(f"  Depth {depth}: {count} pages")
        print("="*60 + "\n")
        
        logger.info(f"Total pages crawled: {stats['total_pages']}")
        logger.info(f"Max depth reached: {stats['max_depth_reached']}")
        logger.info("Crawl completed. Starting visualizations...")
        
        # Generate visualizations
        logger.info("Step 6/6: Generating visualizations...")
        visualize_main()
        
        # Success message
        logger.info("="*60)
        logger.info("All tasks completed successfully!")
        logger.info("="*60)
        
        print("\n" + "="*60)
        print("SUCCESS - All Tasks Completed!")
        print("="*60)
        print("\nOutput Files Generated:")
        print(f"  ✓ CSV Data: {csv_path}")
        print(f"  ✓ JSON Data: {json_path}")
        print(f"  ✓ Hierarchy Visualization: visualizations/tsm_hierarchy.png")
        print(f"  ✓ Depth Distribution: visualizations/depth_distribution.png")
        print(f"  ✓ Crawler Log: output/crawler.log")
        print(f"  ✓ Main Log: output/crawler_main.log")
        print("\n" + "="*60 + "\n")
    
    except KeyboardInterrupt:
        logger.info("Crawler interrupted by user (Ctrl+C)")
        print("\n\nCrawler interrupted by user. Partial data may be available in output/ directory.")
        sys.exit(0)
    
    except Exception as e:
        logger.error("="*60)
        logger.error("FATAL ERROR - Crawler execution failed")
        logger.error("="*60)
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Error Message: {str(e)}")
        logger.error("\nFull Traceback:")
        logger.error(traceback.format_exc())
        
        print("\n" + "="*60)
        print("ERROR - Crawler execution failed")
        print("="*60)
        print(f"Error: {str(e)}")
        print("\nCheck logs in output/crawler_main.log for details.")
        print("="*60 + "\n")
        
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt gracefully
        try:
            logger = logging.getLogger("TSMCrawlerMain")
            logger.info("Graceful shutdown initiated by user")
        except:
            pass
        print("\n\nGraceful shutdown completed.")
        sys.exit(0)
    except Exception as e:
        # Final catch-all for any unhandled exceptions
        try:
            logger = logging.getLogger("TSMCrawlerMain")
            logger.error(f"Unhandled exception: {e}")
            logger.error(traceback.format_exc())
        except:
            pass
        print(f"\nUnexpected error: {e}")
        print("Check logs for more details.")
        sys.exit(1)
