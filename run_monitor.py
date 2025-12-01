#!/usr/bin/env python3
"""
Run Website Monitor Service
============================

Starts the website monitoring service with scheduled crawls.

Usage:
    python run_monitor.py [options]

Options:
    --interval HOURS    Crawl interval in hours (default: 24)
    --daily             Run daily at 2 AM
    --weekly            Run weekly on Sunday at 2 AM
    --monthly           Run monthly on 1st at 2 AM
    --immediate         Run first crawl immediately
    --no-immediate      Skip first crawl, wait for schedule
"""

import argparse
import sys
import time
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.monitor import WebsiteMonitor, AlertLevel


def main():
    """Main entry point for the monitoring service."""
    parser = argparse.ArgumentParser(
        description="Website Monitoring Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=24,
        help="Crawl interval in hours (default: 24)",
    )
    
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Run daily at 2 AM",
    )
    
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="Run weekly on Sunday at 2 AM",
    )
    
    parser.add_argument(
        "--monthly",
        action="store_true",
        help="Run monthly on 1st at 2 AM",
    )
    
    parser.add_argument(
        "--immediate",
        action="store_true",
        default=True,
        help="Run first crawl immediately (default)",
    )
    
    parser.add_argument(
        "--no-immediate",
        action="store_true",
        help="Skip first crawl, wait for schedule",
    )
    
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Website URL to monitor (overrides config)",
    )
    
    parser.add_argument(
        "--slack-webhook",
        type=str,
        default=None,
        help="Slack webhook URL for alerts",
    )
    
    parser.add_argument(
        "--test-alert",
        action="store_true",
        help="Send a test alert and exit",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Website Monitor - Scheduled Crawling Service")
    print("=" * 60)
    print()
    
    # Load config
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        website_url = args.url or config.get("crawl_settings", {}).get("base_url", "https://tsm.ac.in")
    else:
        website_url = args.url or "https://tsm.ac.in"
    
    print(f"  📍 Website: {website_url}")
    
    # Determine interval type
    if args.daily:
        interval_type = "daily"
        interval_value = 1
        print("  ⏰ Schedule: Daily at 2 AM")
    elif args.weekly:
        interval_type = "weekly"
        interval_value = 1
        print("  ⏰ Schedule: Weekly on Sunday at 2 AM")
    elif args.monthly:
        interval_type = "monthly"
        interval_value = 1
        print("  ⏰ Schedule: Monthly on 1st at 2 AM")
    else:
        interval_type = "hours"
        interval_value = args.interval
        print(f"  ⏰ Schedule: Every {interval_value} hours")
    
    print()
    
    # Initialize monitor
    monitor = WebsiteMonitor(
        website_url=website_url,
        crawl_interval_hours=args.interval,
    )
    
    # Configure Slack if provided
    if args.slack_webhook:
        monitor.configure_slack_alerts(args.slack_webhook)
        print("  🔔 Slack alerts configured")
    
    # Test alert mode
    if args.test_alert:
        print("\n  Sending test alert...")
        monitor.send_test_alert()
        print("  ✓ Test alert sent (check your configured channels)")
        return
    
    # Start monitoring
    start_immediately = args.immediate and not args.no_immediate
    
    print("=" * 60)
    print()
    
    success = monitor.schedule_crawl(
        interval_type=interval_type,
        interval_value=interval_value,
        start_immediately=start_immediately,
    )
    
    if not success:
        print("  ❌ Failed to start monitoring")
        print("  Make sure APScheduler is installed: pip install apscheduler")
        return
    
    print("  ✓ Monitoring started successfully")
    print()
    print("  Press Ctrl+C to stop monitoring")
    print()
    
    try:
        while True:
            status = monitor.get_schedule_status()
            
            # Print status update every minute
            print(f"\r  Status: Running | Last crawl: {status['last_crawl'] or 'N/A'} | "
                  f"Next crawl: {status['next_crawl'] or 'N/A'} | "
                  f"Total crawls: {status['total_crawls']}    ", end="", flush=True)
            
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\n  Stopping monitoring...")
        monitor.stop_monitoring()
        print("  ✓ Monitoring stopped")
        print()


if __name__ == "__main__":
    main()

