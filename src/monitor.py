"""
Website Monitoring Service
===========================

Runs scheduled crawls and tracks changes over time with alerting capabilities.

Features:
- Scheduled crawls (daily, weekly, monthly)
- Change detection and comparison
- Alert system (email, Slack)
- Trend tracking and visualization
- Dashboard integration

Author: TSM Web Crawler Project
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import hashlib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

import pandas as pd

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("Warning: APScheduler not installed. Run: pip install apscheduler")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Import crawler
from src.crawler import TSMCrawler

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("WebsiteMonitor")
if not logger.handlers:
    handler = logging.StreamHandler()
    file_handler = logging.FileHandler("output/monitor.log")
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Alert Levels
# ---------------------------------------------------------------------------

class AlertLevel:
    """Alert severity levels."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


# ---------------------------------------------------------------------------
# Change Types
# ---------------------------------------------------------------------------

class ChangeType:
    """Types of changes detected."""
    NEW_PAGE = "new_page"
    REMOVED_PAGE = "removed_page"
    BROKEN_LINK = "broken_link"
    FIXED_LINK = "fixed_link"
    URL_CHANGE = "url_change"
    TITLE_CHANGE = "title_change"
    DEPTH_CHANGE = "depth_change"
    LINK_COUNT_CHANGE = "link_count_change"


# ---------------------------------------------------------------------------
# Website Monitor Class
# ---------------------------------------------------------------------------

class WebsiteMonitor:
    """
    Website monitoring service that runs scheduled crawls and tracks changes.
    
    Features:
    - Scheduled crawling at configurable intervals
    - Change detection between crawls
    - Alert notifications (email, Slack)
    - Historical trend tracking
    - Dashboard integration
    """
    
    def __init__(
        self,
        website_url: str,
        crawl_interval_hours: int = 24,
        config_path: str = "config.json",
        history_dir: str = "output/history",
    ):
        """
        Initialize the website monitor.
        
        Args:
            website_url: Base URL of the website to monitor.
            crawl_interval_hours: Hours between crawls (default: 24).
            config_path: Path to crawler configuration file.
            history_dir: Directory to store historical crawl data.
        """
        self.website_url = website_url
        self.crawl_interval_hours = crawl_interval_hours
        self.config_path = config_path
        self.history_dir = Path(history_dir)
        
        # Create history directory
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize scheduler
        self.scheduler: Optional[BackgroundScheduler] = None
        if SCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()
        
        # Alert configuration
        self.alert_config: Dict[str, Any] = {
            "email": {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_address": "",
                "to_addresses": [],
            },
            "slack": {
                "enabled": False,
                "webhook_url": "",
            },
            "thresholds": {
                "critical_broken_links": 5,
                "critical_removed_pages": 10,
                "warning_new_pages": 20,
                "warning_depth_increase": 2,
            },
        }
        
        # Monitoring state
        self.last_crawl_time: Optional[datetime] = None
        self.next_crawl_time: Optional[datetime] = None
        self.is_running: bool = False
        self.crawl_history: List[Dict[str, Any]] = []
        
        # Load existing history
        self._load_history()
        
        logger.info(f"WebsiteMonitor initialized for {website_url}")
    
    # -----------------------------------------------------------------------
    # Configuration Methods
    # -----------------------------------------------------------------------
    
    def configure_email_alerts(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_address: str,
        to_addresses: List[str],
    ) -> None:
        """Configure email alert settings."""
        self.alert_config["email"].update({
            "enabled": True,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "username": username,
            "password": password,
            "from_address": from_address,
            "to_addresses": to_addresses,
        })
        logger.info("Email alerts configured")
    
    def configure_slack_alerts(self, webhook_url: str) -> None:
        """Configure Slack webhook for alerts."""
        self.alert_config["slack"].update({
            "enabled": True,
            "webhook_url": webhook_url,
        })
        logger.info("Slack alerts configured")
    
    def set_alert_thresholds(
        self,
        critical_broken_links: int = 5,
        critical_removed_pages: int = 10,
        warning_new_pages: int = 20,
        warning_depth_increase: int = 2,
    ) -> None:
        """Set thresholds for alert levels."""
        self.alert_config["thresholds"].update({
            "critical_broken_links": critical_broken_links,
            "critical_removed_pages": critical_removed_pages,
            "warning_new_pages": warning_new_pages,
            "warning_depth_increase": warning_depth_increase,
        })
        logger.info("Alert thresholds updated")
    
    # -----------------------------------------------------------------------
    # Scheduling Methods
    # -----------------------------------------------------------------------
    
    def schedule_crawl(
        self,
        interval_type: str = "hours",
        interval_value: int = 24,
        start_immediately: bool = True,
    ) -> bool:
        """
        Schedule recurring crawls.
        
        Args:
            interval_type: 'hours', 'days', 'weeks', or 'cron'
            interval_value: Interval value (ignored for cron)
            start_immediately: Whether to run first crawl immediately
            
        Returns:
            True if scheduling successful, False otherwise.
        """
        if not SCHEDULER_AVAILABLE:
            logger.error("APScheduler not available. Cannot schedule crawls.")
            return False
        
        if self.scheduler is None:
            self.scheduler = BackgroundScheduler()
        
        # Remove existing jobs
        self.scheduler.remove_all_jobs()
        
        # Create trigger based on interval type
        if interval_type == "hours":
            trigger = IntervalTrigger(hours=interval_value)
            self.next_crawl_time = datetime.now() + timedelta(hours=interval_value)
        elif interval_type == "days":
            trigger = IntervalTrigger(days=interval_value)
            self.next_crawl_time = datetime.now() + timedelta(days=interval_value)
        elif interval_type == "weeks":
            trigger = IntervalTrigger(weeks=interval_value)
            self.next_crawl_time = datetime.now() + timedelta(weeks=interval_value)
        elif interval_type == "daily":
            # Run daily at 2 AM
            trigger = CronTrigger(hour=2, minute=0)
            self.next_crawl_time = datetime.now().replace(hour=2, minute=0) + timedelta(days=1)
        elif interval_type == "weekly":
            # Run weekly on Sunday at 2 AM
            trigger = CronTrigger(day_of_week="sun", hour=2, minute=0)
            self.next_crawl_time = datetime.now() + timedelta(days=7)
        elif interval_type == "monthly":
            # Run on 1st of each month at 2 AM
            trigger = CronTrigger(day=1, hour=2, minute=0)
            self.next_crawl_time = datetime.now().replace(day=1) + timedelta(days=32)
        else:
            logger.error(f"Unknown interval type: {interval_type}")
            return False
        
        # Add job
        self.scheduler.add_job(
            self._run_scheduled_crawl,
            trigger=trigger,
            id="website_crawl",
            name=f"Crawl {self.website_url}",
            replace_existing=True,
        )
        
        # Start scheduler
        if not self.scheduler.running:
            self.scheduler.start()
        
        self.is_running = True
        logger.info(f"Crawl scheduled: {interval_type} every {interval_value}")
        
        # Run immediately if requested
        if start_immediately:
            self._run_scheduled_crawl()
        
        return True
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
        self.is_running = False
        logger.info("Monitoring stopped")
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """Get current scheduling status."""
        return {
            "is_running": self.is_running,
            "last_crawl": self.last_crawl_time.isoformat() if self.last_crawl_time else None,
            "next_crawl": self.next_crawl_time.isoformat() if self.next_crawl_time else None,
            "total_crawls": len(self.crawl_history),
            "website_url": self.website_url,
        }
    
    # -----------------------------------------------------------------------
    # Crawling Methods
    # -----------------------------------------------------------------------
    
    def _run_scheduled_crawl(self) -> Dict[str, Any]:
        """Execute a scheduled crawl and process results."""
        logger.info(f"Starting scheduled crawl of {self.website_url}")
        
        crawl_start = datetime.now()
        
        try:
            # Load previous data for comparison
            previous_data = self._load_latest_crawl_data()
            
            # Run crawler
            crawler = TSMCrawler(config_path=self.config_path)
            crawler.crawl(self.website_url)
            
            # Get current data
            current_data = crawler.get_crawl_data()
            
            # Save crawl data with timestamp
            crawl_id = self._save_crawl_data(current_data, crawl_start)
            
            # Compare if we have previous data
            changes = {}
            if previous_data is not None:
                changes = self.compare_crawls(previous_data, current_data)
                
                # Generate change report
                report = self.generate_change_report(changes, crawl_start)
                
                # Check for critical changes and send alerts
                self._process_alerts(changes, report)
            
            # Update state
            self.last_crawl_time = crawl_start
            self.next_crawl_time = datetime.now() + timedelta(hours=self.crawl_interval_hours)
            
            # Record in history
            crawl_record = {
                "crawl_id": crawl_id,
                "timestamp": crawl_start.isoformat(),
                "total_pages": len(current_data) if current_data is not None else 0,
                "changes": changes,
                "status": "success",
            }
            self.crawl_history.append(crawl_record)
            self._save_history()
            
            logger.info(f"Crawl completed: {len(current_data) if current_data is not None else 0} pages")
            
            return crawl_record
            
        except Exception as e:
            logger.error(f"Crawl failed: {e}")
            
            crawl_record = {
                "crawl_id": None,
                "timestamp": crawl_start.isoformat(),
                "total_pages": 0,
                "changes": {},
                "status": "failed",
                "error": str(e),
            }
            self.crawl_history.append(crawl_record)
            self._save_history()
            
            # Send alert for failed crawl
            self._send_alert(
                AlertLevel.CRITICAL,
                "Crawl Failed",
                f"Scheduled crawl of {self.website_url} failed: {e}",
            )
            
            return crawl_record
    
    def run_manual_crawl(self) -> Dict[str, Any]:
        """Run a manual crawl outside of schedule."""
        logger.info("Running manual crawl")
        return self._run_scheduled_crawl()
    
    # -----------------------------------------------------------------------
    # Comparison Methods
    # -----------------------------------------------------------------------
    
    def compare_crawls(
        self,
        previous_data: pd.DataFrame,
        current_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Compare two crawl datasets and detect changes.
        
        Args:
            previous_data: DataFrame from previous crawl.
            current_data: DataFrame from current crawl.
            
        Returns:
            Dictionary containing all detected changes.
        """
        changes: Dict[str, Any] = {
            "new_pages": [],
            "removed_pages": [],
            "broken_links": [],
            "fixed_links": [],
            "title_changes": [],
            "depth_changes": [],
            "link_count_changes": [],
            "summary": {},
        }
        
        # Get URL sets
        prev_urls = set(previous_data["url"].tolist())
        curr_urls = set(current_data["url"].tolist())
        
        # Detect new pages
        new_urls = curr_urls - prev_urls
        for url in new_urls:
            row = current_data[current_data["url"] == url].iloc[0]
            changes["new_pages"].append({
                "url": url,
                "title": row.get("title", ""),
                "depth": int(row.get("depth", 0)),
            })
        
        # Detect removed pages
        removed_urls = prev_urls - curr_urls
        for url in removed_urls:
            row = previous_data[previous_data["url"] == url].iloc[0]
            changes["removed_pages"].append({
                "url": url,
                "title": row.get("title", ""),
                "depth": int(row.get("depth", 0)),
            })
        
        # Detect broken links (new 404s)
        prev_broken = set(
            previous_data[previous_data["status_code"] != 200]["url"].tolist()
        ) if "status_code" in previous_data.columns else set()
        
        curr_broken = set(
            current_data[current_data["status_code"] != 200]["url"].tolist()
        ) if "status_code" in current_data.columns else set()
        
        new_broken = curr_broken - prev_broken
        for url in new_broken:
            row = current_data[current_data["url"] == url].iloc[0]
            changes["broken_links"].append({
                "url": url,
                "status_code": int(row.get("status_code", 0)),
                "title": row.get("title", ""),
            })
        
        # Detect fixed links
        fixed_links = prev_broken - curr_broken
        for url in fixed_links:
            if url in curr_urls:
                changes["fixed_links"].append({"url": url})
        
        # Compare common pages for changes
        common_urls = prev_urls & curr_urls
        for url in common_urls:
            prev_row = previous_data[previous_data["url"] == url].iloc[0]
            curr_row = current_data[current_data["url"] == url].iloc[0]
            
            # Title changes
            prev_title = prev_row.get("title", "")
            curr_title = curr_row.get("title", "")
            if prev_title != curr_title:
                changes["title_changes"].append({
                    "url": url,
                    "old_title": prev_title,
                    "new_title": curr_title,
                })
            
            # Depth changes
            prev_depth = int(prev_row.get("depth", 0))
            curr_depth = int(curr_row.get("depth", 0))
            if prev_depth != curr_depth:
                changes["depth_changes"].append({
                    "url": url,
                    "old_depth": prev_depth,
                    "new_depth": curr_depth,
                    "change": curr_depth - prev_depth,
                })
            
            # Link count changes
            prev_links = int(prev_row.get("child_count", 0))
            curr_links = int(curr_row.get("child_count", 0))
            if abs(prev_links - curr_links) >= 5:  # Significant change threshold
                changes["link_count_changes"].append({
                    "url": url,
                    "old_count": prev_links,
                    "new_count": curr_links,
                    "change": curr_links - prev_links,
                })
        
        # Calculate summary statistics
        prev_total = len(prev_urls)
        curr_total = len(curr_urls)
        
        changes["summary"] = {
            "previous_total_pages": prev_total,
            "current_total_pages": curr_total,
            "pages_added": len(changes["new_pages"]),
            "pages_removed": len(changes["removed_pages"]),
            "new_broken_links": len(changes["broken_links"]),
            "fixed_links": len(changes["fixed_links"]),
            "title_changes": len(changes["title_changes"]),
            "depth_changes": len(changes["depth_changes"]),
            "percent_change": round(
                ((curr_total - prev_total) / prev_total * 100) if prev_total > 0 else 0, 2
            ),
            "net_change": curr_total - prev_total,
        }
        
        return changes
    
    # -----------------------------------------------------------------------
    # Report Generation
    # -----------------------------------------------------------------------
    
    def generate_change_report(
        self,
        changes: Dict[str, Any],
        crawl_time: datetime,
    ) -> str:
        """
        Generate a human-readable change report.
        
        Args:
            changes: Dictionary of detected changes.
            crawl_time: Timestamp of the crawl.
            
        Returns:
            Formatted report string.
        """
        summary = changes.get("summary", {})
        
        report_lines = [
            "=" * 60,
            "WEBSITE CHANGE REPORT",
            f"Generated: {crawl_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Website: {self.website_url}",
            "=" * 60,
            "",
            "📊 SUMMARY",
            "-" * 40,
            f"Previous Total Pages: {summary.get('previous_total_pages', 0)}",
            f"Current Total Pages:  {summary.get('current_total_pages', 0)}",
            f"Net Change:           {summary.get('net_change', 0):+d} ({summary.get('percent_change', 0):+.1f}%)",
            "",
        ]
        
        # New pages section
        new_pages = changes.get("new_pages", [])
        if new_pages:
            report_lines.extend([
                f"✅ NEW PAGES ADDED ({len(new_pages)})",
                "-" * 40,
            ])
            for page in new_pages[:10]:  # Limit to 10
                report_lines.append(f"  + {page['title'][:50]} (Depth: {page['depth']})")
                report_lines.append(f"    {page['url'][:70]}")
            if len(new_pages) > 10:
                report_lines.append(f"  ... and {len(new_pages) - 10} more")
            report_lines.append("")
        
        # Removed pages section
        removed_pages = changes.get("removed_pages", [])
        if removed_pages:
            report_lines.extend([
                f"❌ PAGES REMOVED ({len(removed_pages)})",
                "-" * 40,
            ])
            for page in removed_pages[:10]:
                report_lines.append(f"  - {page['title'][:50]} (Depth: {page['depth']})")
                report_lines.append(f"    {page['url'][:70]}")
            if len(removed_pages) > 10:
                report_lines.append(f"  ... and {len(removed_pages) - 10} more")
            report_lines.append("")
        
        # Broken links section
        broken_links = changes.get("broken_links", [])
        if broken_links:
            report_lines.extend([
                f"🔴 NEW BROKEN LINKS ({len(broken_links)})",
                "-" * 40,
            ])
            for link in broken_links[:10]:
                report_lines.append(f"  ⚠ [{link['status_code']}] {link['url'][:60]}")
            if len(broken_links) > 10:
                report_lines.append(f"  ... and {len(broken_links) - 10} more")
            report_lines.append("")
        
        # Fixed links section
        fixed_links = changes.get("fixed_links", [])
        if fixed_links:
            report_lines.extend([
                f"🟢 FIXED LINKS ({len(fixed_links)})",
                "-" * 40,
            ])
            for link in fixed_links[:5]:
                report_lines.append(f"  ✓ {link['url'][:60]}")
            if len(fixed_links) > 5:
                report_lines.append(f"  ... and {len(fixed_links) - 5} more")
            report_lines.append("")
        
        # Depth changes section
        depth_changes = changes.get("depth_changes", [])
        if depth_changes:
            report_lines.extend([
                f"📊 DEPTH CHANGES ({len(depth_changes)})",
                "-" * 40,
            ])
            for change in depth_changes[:5]:
                direction = "↑" if change["change"] > 0 else "↓"
                report_lines.append(
                    f"  {direction} {change['old_depth']} → {change['new_depth']}: {change['url'][:50]}"
                )
            if len(depth_changes) > 5:
                report_lines.append(f"  ... and {len(depth_changes) - 5} more")
            report_lines.append("")
        
        # Assessment
        report_lines.extend([
            "📈 ASSESSMENT",
            "-" * 40,
        ])
        
        # Determine overall status
        critical_issues = len(broken_links) + len(removed_pages)
        if critical_issues > 10:
            status = "⚠️ CRITICAL - Immediate attention required"
        elif critical_issues > 5:
            status = "🟡 WARNING - Review recommended"
        elif len(new_pages) > 0 or len(fixed_links) > 0:
            status = "🟢 IMPROVED - Positive changes detected"
        else:
            status = "✅ STABLE - No significant changes"
        
        report_lines.append(f"Status: {status}")
        report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "💡 RECOMMENDATIONS",
            "-" * 40,
        ])
        
        if broken_links:
            report_lines.append(f"  • Fix {len(broken_links)} broken links")
        if removed_pages:
            report_lines.append(f"  • Review {len(removed_pages)} removed pages for redirects")
        if depth_changes:
            deeper = [c for c in depth_changes if c["change"] > 0]
            if deeper:
                report_lines.append(f"  • {len(deeper)} pages moved deeper - consider flattening")
        if not (broken_links or removed_pages or depth_changes):
            report_lines.append("  • No immediate actions required")
        
        report_lines.extend([
            "",
            "=" * 60,
            "End of Report",
            "=" * 60,
        ])
        
        report = "\n".join(report_lines)
        
        # Save report to file
        report_path = self.history_dir / f"report_{crawl_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info(f"Change report saved to {report_path}")
        
        return report
    
    # -----------------------------------------------------------------------
    # Alert Methods
    # -----------------------------------------------------------------------
    
    def _process_alerts(self, changes: Dict[str, Any], report: str) -> None:
        """Process changes and send appropriate alerts."""
        summary = changes.get("summary", {})
        thresholds = self.alert_config["thresholds"]
        
        # Check for critical conditions
        broken_count = summary.get("new_broken_links", 0)
        removed_count = summary.get("pages_removed", 0)
        
        if broken_count >= thresholds["critical_broken_links"]:
            self._send_alert(
                AlertLevel.CRITICAL,
                f"{broken_count} New Broken Links Detected",
                self._format_alert_message(changes, "broken_links"),
            )
        
        if removed_count >= thresholds["critical_removed_pages"]:
            self._send_alert(
                AlertLevel.CRITICAL,
                f"{removed_count} Pages Removed",
                self._format_alert_message(changes, "removed_pages"),
            )
        
        # Check for warning conditions
        new_count = summary.get("pages_added", 0)
        if new_count >= thresholds["warning_new_pages"]:
            self._send_alert(
                AlertLevel.WARNING,
                f"{new_count} New Pages Added",
                self._format_alert_message(changes, "new_pages"),
            )
        
        # Check depth increases
        depth_changes = changes.get("depth_changes", [])
        significant_depth_increases = [
            c for c in depth_changes 
            if c["change"] >= thresholds["warning_depth_increase"]
        ]
        if significant_depth_increases:
            self._send_alert(
                AlertLevel.WARNING,
                f"{len(significant_depth_increases)} Pages Moved Significantly Deeper",
                self._format_alert_message(changes, "depth_changes"),
            )
    
    def _format_alert_message(self, changes: Dict[str, Any], change_type: str) -> str:
        """Format alert message for specific change type."""
        summary = changes.get("summary", {})
        
        message_lines = [
            f"🌐 Website: {self.website_url}",
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "📊 Summary:",
            f"  • Total Pages: {summary.get('current_total_pages', 0)}",
            f"  • Net Change: {summary.get('net_change', 0):+d}",
            "",
        ]
        
        if change_type == "broken_links":
            broken = changes.get("broken_links", [])
            message_lines.append("🔴 Broken Links:")
            for link in broken[:5]:
                message_lines.append(f"  • [{link['status_code']}] {link['url'][:50]}")
            if len(broken) > 5:
                message_lines.append(f"  ... and {len(broken) - 5} more")
        
        elif change_type == "removed_pages":
            removed = changes.get("removed_pages", [])
            message_lines.append("❌ Removed Pages:")
            for page in removed[:5]:
                message_lines.append(f"  • {page['title'][:40]}")
            if len(removed) > 5:
                message_lines.append(f"  ... and {len(removed) - 5} more")
        
        elif change_type == "new_pages":
            new = changes.get("new_pages", [])
            message_lines.append("✅ New Pages:")
            for page in new[:5]:
                message_lines.append(f"  • {page['title'][:40]}")
            if len(new) > 5:
                message_lines.append(f"  ... and {len(new) - 5} more")
        
        elif change_type == "depth_changes":
            depth = changes.get("depth_changes", [])
            message_lines.append("📊 Depth Changes:")
            for change in depth[:5]:
                message_lines.append(
                    f"  • {change['old_depth']} → {change['new_depth']}: {change['url'][:40]}"
                )
        
        message_lines.extend([
            "",
            "🔗 Action Required: Review changes in dashboard",
        ])
        
        return "\n".join(message_lines)
    
    def _send_alert(self, level: str, subject: str, message: str) -> None:
        """Send alert via configured channels."""
        logger.info(f"Sending {level} alert: {subject}")
        
        # Add level prefix to subject
        full_subject = f"[{level}] {subject} - {self.website_url}"
        
        # Send email if configured
        if self.alert_config["email"]["enabled"]:
            self._send_email_alert(full_subject, message, level)
        
        # Send Slack if configured
        if self.alert_config["slack"]["enabled"]:
            self._send_slack_alert(full_subject, message, level)
        
        # Log alert
        logger.warning(f"ALERT [{level}]: {subject}")
    
    def _send_email_alert(self, subject: str, message: str, level: str) -> bool:
        """Send email alert."""
        config = self.alert_config["email"]
        
        try:
            msg = MIMEMultipart()
            msg["From"] = config["from_address"]
            msg["To"] = ", ".join(config["to_addresses"])
            msg["Subject"] = subject
            
            # Add level-specific styling
            level_colors = {
                AlertLevel.CRITICAL: "#EF4444",
                AlertLevel.WARNING: "#F59E0B",
                AlertLevel.INFO: "#3B82F6",
            }
            
            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: {level_colors.get(level, '#3B82F6')}; 
                            color: white; padding: 10px; border-radius: 5px;">
                    <h2>⚠️ {level} ALERT</h2>
                </div>
                <pre style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
{message}
                </pre>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(message, "plain"))
            msg.attach(MIMEText(html_message, "html"))
            
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                server.starttls()
                server.login(config["username"], config["password"])
                server.send_message(msg)
            
            logger.info("Email alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _send_slack_alert(self, subject: str, message: str, level: str) -> bool:
        """Send Slack webhook alert."""
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests library not available for Slack alerts")
            return False
        
        config = self.alert_config["slack"]
        
        try:
            # Format for Slack
            level_emojis = {
                AlertLevel.CRITICAL: "🚨",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.INFO: "ℹ️",
            }
            
            slack_message = {
                "text": f"{level_emojis.get(level, '📢')} {subject}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{level_emojis.get(level, '📢')} {level} ALERT",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{subject}*",
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{message[:2000]}```",  # Slack limit
                        }
                    },
                ]
            }
            
            response = requests.post(
                config["webhook_url"],
                json=slack_message,
                timeout=10,
            )
            
            if response.status_code == 200:
                logger.info("Slack alert sent successfully")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def send_test_alert(self) -> bool:
        """Send a test alert to verify configuration."""
        return self._send_alert(
            AlertLevel.INFO,
            "Test Alert",
            "This is a test alert from the Website Monitor.\n\n"
            f"Website: {self.website_url}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "If you received this, alerts are working correctly!"
        ) or True  # Return True even if no alerts configured
    
    # -----------------------------------------------------------------------
    # History Management
    # -----------------------------------------------------------------------
    
    def _save_crawl_data(self, data: pd.DataFrame, crawl_time: datetime) -> str:
        """Save crawl data with timestamp."""
        crawl_id = crawl_time.strftime("%Y%m%d_%H%M%S")
        
        # Save CSV
        csv_path = self.history_dir / f"crawl_{crawl_id}.csv"
        data.to_csv(csv_path, index=False)
        
        # Save JSON summary
        summary = {
            "crawl_id": crawl_id,
            "timestamp": crawl_time.isoformat(),
            "total_pages": len(data),
            "max_depth": int(data["depth"].max()) if "depth" in data.columns else 0,
            "avg_depth": round(data["depth"].mean(), 2) if "depth" in data.columns else 0,
        }
        
        json_path = self.history_dir / f"crawl_{crawl_id}_summary.json"
        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Crawl data saved: {crawl_id}")
        
        return crawl_id
    
    def _load_latest_crawl_data(self) -> Optional[pd.DataFrame]:
        """Load the most recent crawl data."""
        csv_files = sorted(self.history_dir.glob("crawl_*.csv"), reverse=True)
        
        if not csv_files:
            # Try loading from main output
            main_csv = Path("output/tsm_crawl_data.csv")
            if main_csv.exists():
                return pd.read_csv(main_csv)
            return None
        
        latest = csv_files[0]
        return pd.read_csv(latest)
    
    def _load_history(self) -> None:
        """Load crawl history from file."""
        history_file = self.history_dir / "crawl_history.json"
        
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    self.crawl_history = json.load(f)
                logger.info(f"Loaded {len(self.crawl_history)} historical crawls")
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
                self.crawl_history = []
    
    def _save_history(self) -> None:
        """Save crawl history to file."""
        history_file = self.history_dir / "crawl_history.json"
        
        try:
            with open(history_file, "w") as f:
                json.dump(self.crawl_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent crawl history."""
        return self.crawl_history[-limit:]
    
    def get_trend_data(self, days: int = 30) -> Dict[str, Any]:
        """Get trend data for the specified period."""
        cutoff = datetime.now() - timedelta(days=days)
        
        trend_data = {
            "dates": [],
            "total_pages": [],
            "broken_links": [],
            "new_pages": [],
            "removed_pages": [],
        }
        
        for record in self.crawl_history:
            try:
                record_time = datetime.fromisoformat(record["timestamp"])
                if record_time >= cutoff:
                    trend_data["dates"].append(record_time.strftime("%Y-%m-%d"))
                    trend_data["total_pages"].append(record.get("total_pages", 0))
                    
                    changes = record.get("changes", {})
                    summary = changes.get("summary", {})
                    trend_data["broken_links"].append(summary.get("new_broken_links", 0))
                    trend_data["new_pages"].append(summary.get("pages_added", 0))
                    trend_data["removed_pages"].append(summary.get("pages_removed", 0))
            except Exception:
                continue
        
        return trend_data


# ---------------------------------------------------------------------------
# Dashboard Integration Functions
# ---------------------------------------------------------------------------

def get_monitor_status() -> Dict[str, Any]:
    """Get current monitor status for dashboard display."""
    history_file = Path("output/history/crawl_history.json")
    
    if not history_file.exists():
        return {
            "last_crawl": None,
            "next_crawl": None,
            "total_crawls": 0,
            "is_running": False,
            "recent_changes": [],
        }
    
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
        
        last_record = history[-1] if history else None
        
        return {
            "last_crawl": last_record["timestamp"] if last_record else None,
            "next_crawl": None,  # Would need active monitor instance
            "total_crawls": len(history),
            "is_running": False,  # Would need active monitor instance
            "recent_changes": history[-5:] if history else [],
        }
    except Exception as e:
        logger.error(f"Failed to get monitor status: {e}")
        return {
            "last_crawl": None,
            "next_crawl": None,
            "total_crawls": 0,
            "is_running": False,
            "recent_changes": [],
            "error": str(e),
        }


def get_trend_chart_data(days: int = 30) -> Dict[str, Any]:
    """Get trend data for dashboard charts."""
    history_file = Path("output/history/crawl_history.json")
    
    if not history_file.exists():
        return {"dates": [], "total_pages": [], "changes": []}
    
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
        
        cutoff = datetime.now() - timedelta(days=days)
        
        data = {
            "dates": [],
            "total_pages": [],
            "net_changes": [],
        }
        
        for record in history:
            try:
                record_time = datetime.fromisoformat(record["timestamp"])
                if record_time >= cutoff:
                    data["dates"].append(record_time.strftime("%m/%d"))
                    data["total_pages"].append(record.get("total_pages", 0))
                    
                    changes = record.get("changes", {})
                    summary = changes.get("summary", {})
                    data["net_changes"].append(summary.get("net_change", 0))
            except Exception:
                continue
        
        return data
    except Exception as e:
        logger.error(f"Failed to get trend data: {e}")
        return {"dates": [], "total_pages": [], "net_changes": []}


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Website Monitor - Scheduled Crawling Service")
    print("=" * 60)
    
    # Example usage
    monitor = WebsiteMonitor(
        website_url="https://tsm.ac.in",
        crawl_interval_hours=24,
    )
    
    # Configure alerts (example - replace with actual values)
    # monitor.configure_slack_alerts("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
    # monitor.configure_email_alerts(
    #     smtp_server="smtp.gmail.com",
    #     smtp_port=587,
    #     username="your-email@gmail.com",
    #     password="your-app-password",
    #     from_address="your-email@gmail.com",
    #     to_addresses=["recipient@example.com"],
    # )
    
    print("\nOptions:")
    print("  1. Run manual crawl")
    print("  2. Start scheduled monitoring (every 24 hours)")
    print("  3. View crawl history")
    print("  4. Send test alert")
    print("  5. Exit")
    
    try:
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            print("\nRunning manual crawl...")
            result = monitor.run_manual_crawl()
            print(f"\nCrawl completed: {result['total_pages']} pages")
            
        elif choice == "2":
            print("\nStarting scheduled monitoring...")
            monitor.schedule_crawl(interval_type="hours", interval_value=24)
            print("Monitoring started. Press Ctrl+C to stop.")
            
            try:
                while True:
                    import time
                    time.sleep(60)
            except KeyboardInterrupt:
                monitor.stop_monitoring()
                print("\nMonitoring stopped.")
                
        elif choice == "3":
            history = monitor.get_history(10)
            print(f"\nRecent crawl history ({len(history)} records):")
            for record in history:
                print(f"  - {record['timestamp']}: {record['total_pages']} pages ({record['status']})")
                
        elif choice == "4":
            print("\nSending test alert...")
            monitor.send_test_alert()
            print("Test alert sent (if alerts configured)")
            
        elif choice == "5":
            print("\nExiting...")
            
        else:
            print("\nInvalid option")
            
    except KeyboardInterrupt:
        print("\n\nExiting...")

