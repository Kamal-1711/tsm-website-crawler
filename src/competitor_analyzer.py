"""
Competitor Analyzer Module
===========================

Comprehensive multi-competitor comparison matrix with visualizations
and strategic recommendations.

Features:
- Multi-competitor comparison matrix
- Strength gap analysis
- Competitive advantages identification
- Strategic recommendations
- Radar charts and gap visualizations

Author: TSM Web Crawler Project
"""

from __future__ import annotations

import json
import logging
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logger = logging.getLogger("CompetitorAnalyzer")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Gap thresholds
LEADER_THRESHOLD = 0.15  # 15% ahead = leader
LAG_THRESHOLD = -0.15    # 15% behind = lagging

# Metric definitions with higher_is_better flag
METRICS_CONFIG = {
    "domain_authority": {"name": "Domain Authority", "higher_is_better": True, "unit": "", "max": 100},
    "total_backlinks": {"name": "Total Backlinks", "higher_is_better": True, "unit": "", "max": None},
    "keywords_ranked": {"name": "Keywords Ranked", "higher_is_better": True, "unit": "", "max": None},
    "seo_score": {"name": "SEO Score", "higher_is_better": True, "unit": "/100", "max": 100},
    "page_speed": {"name": "Page Speed", "higher_is_better": False, "unit": "s", "max": 10},
    "mobile_score": {"name": "Mobile Score", "higher_is_better": True, "unit": "", "max": 100},
    "top_ranking": {"name": "Top Ranking Position", "higher_is_better": False, "unit": "", "max": 100},
    "content_pages": {"name": "Content Pages", "higher_is_better": True, "unit": "", "max": None},
    "link_density": {"name": "Link Density", "higher_is_better": True, "unit": "", "max": None},
    "orphan_percentage": {"name": "Orphan Page %", "higher_is_better": False, "unit": "%", "max": 100},
    "avg_page_depth": {"name": "Avg Page Depth", "higher_is_better": False, "unit": "", "max": 10},
}


# ---------------------------------------------------------------------------
# Competitor Analyzer Class
# ---------------------------------------------------------------------------

class CompetitorAnalyzer:
    """
    Comprehensive multi-competitor comparison analyzer.
    
    Provides detailed comparison matrices, gap analysis, and strategic
    recommendations for competitive SEO analysis.
    """
    
    def __init__(self, our_data: Dict[str, Any] = None):
        """
        Initialize the competitor analyzer.
        
        Args:
            our_data: Dictionary containing our website's metrics.
        """
        self.our_data = our_data or {}
        self.competitors = []
        self.comparison_results = {}
        self.gap_analysis = {}
        self.recommendations = []
        
        logger.info("CompetitorAnalyzer initialized")
    
    def set_our_metrics(self, metrics: Dict[str, Any]) -> None:
        """Set our website's metrics."""
        self.our_data = metrics
    
    def add_competitor(self, name: str, metrics: Dict[str, Any]) -> None:
        """Add a competitor with their metrics."""
        self.competitors.append({
            "name": name,
            "metrics": metrics,
        })
    
    # -----------------------------------------------------------------------
    # Multi-Competitor Comparison
    # -----------------------------------------------------------------------
    
    def compare_multiple_competitors(
        self, 
        our_data: Dict[str, Any] = None, 
        competitor_list: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare metrics across multiple competitors.
        
        Args:
            our_data: Our website's metrics (uses self.our_data if not provided).
            competitor_list: List of competitor data dicts with 'name' and 'metrics'.
        
        Returns:
            Comprehensive comparison matrix with all metrics.
        """
        if our_data:
            self.our_data = our_data
        if competitor_list:
            self.competitors = competitor_list
        
        if not self.our_data:
            raise ValueError("Our data not provided")
        
        logger.info(f"Comparing against {len(self.competitors)} competitors")
        
        our_name = self.our_data.get("name", "Our Site")
        our_metrics = self.our_data.get("metrics", self.our_data)
        
        # Build comparison matrix
        comparison_matrix = {
            "our_name": our_name,
            "our_metrics": our_metrics,
            "competitors": [],
            "metrics_comparison": {},
            "summary": {},
        }
        
        # Compare each metric
        for metric_key, config in METRICS_CONFIG.items():
            our_value = our_metrics.get(metric_key, 0)
            
            metric_comparison = {
                "name": config["name"],
                "our_value": our_value,
                "competitors": [],
                "our_rank": 1,
                "best_value": our_value,
                "best_performer": our_name,
            }
            
            all_values = [(our_name, our_value)]
            
            for comp in self.competitors:
                comp_name = comp.get("name", "Unknown")
                comp_metrics = comp.get("metrics", {})
                comp_value = comp_metrics.get(metric_key, 0)
                
                # Calculate gap
                gap_info = self._calculate_single_gap(
                    our_value, comp_value, config["higher_is_better"]
                )
                
                metric_comparison["competitors"].append({
                    "name": comp_name,
                    "value": comp_value,
                    "gap": gap_info["gap"],
                    "gap_percentage": gap_info["gap_percentage"],
                    "gap_level": gap_info["gap_level"],
                    "gap_emoji": gap_info["gap_emoji"],
                })
                
                all_values.append((comp_name, comp_value))
            
            # Determine rankings
            if config["higher_is_better"]:
                sorted_values = sorted(all_values, key=lambda x: x[1], reverse=True)
            else:
                sorted_values = sorted(all_values, key=lambda x: x[1] if x[1] > 0 else float('inf'))
            
            metric_comparison["our_rank"] = next(
                (i + 1 for i, (name, _) in enumerate(sorted_values) if name == our_name),
                len(sorted_values)
            )
            metric_comparison["best_performer"] = sorted_values[0][0]
            metric_comparison["best_value"] = sorted_values[0][1]
            
            comparison_matrix["metrics_comparison"][metric_key] = metric_comparison
        
        # Generate summary
        comparison_matrix["summary"] = self._generate_comparison_summary(comparison_matrix)
        
        self.comparison_results = comparison_matrix
        
        return comparison_matrix
    
    def _calculate_single_gap(
        self, our_value: float, comp_value: float, higher_is_better: bool
    ) -> Dict[str, Any]:
        """Calculate gap between our value and competitor value."""
        if comp_value == 0:
            return {
                "gap": our_value,
                "gap_percentage": 100.0 if our_value > 0 else 0,
                "gap_level": "leader" if our_value > 0 else "neutral",
                "gap_emoji": "🟢" if our_value > 0 else "⚪",
            }
        
        if higher_is_better:
            gap = our_value - comp_value
            gap_percentage = (gap / comp_value) * 100 if comp_value != 0 else 0
        else:
            gap = comp_value - our_value  # Reversed for lower-is-better
            gap_percentage = (gap / our_value) * 100 if our_value != 0 else 0
        
        # Determine gap level
        if gap_percentage >= LEADER_THRESHOLD * 100:
            gap_level = "leader"
            gap_emoji = "🟢"
        elif gap_percentage <= LAG_THRESHOLD * 100:
            gap_level = "behind"
            gap_emoji = "🔴"
        else:
            gap_level = "competitive"
            gap_emoji = "🟡"
        
        return {
            "gap": round(gap, 2),
            "gap_percentage": round(gap_percentage, 1),
            "gap_level": gap_level,
            "gap_emoji": gap_emoji,
        }
    
    def _generate_comparison_summary(self, matrix: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of comparison results."""
        leading_count = 0
        competitive_count = 0
        behind_count = 0
        
        for metric_key, metric_data in matrix["metrics_comparison"].items():
            if metric_data["our_rank"] == 1:
                leading_count += 1
            elif metric_data["our_rank"] <= 2:
                competitive_count += 1
            else:
                behind_count += 1
        
        total_metrics = len(matrix["metrics_comparison"])
        
        return {
            "total_metrics": total_metrics,
            "leading_in": leading_count,
            "competitive_in": competitive_count,
            "behind_in": behind_count,
            "overall_position": self._determine_overall_position(
                leading_count, competitive_count, behind_count, total_metrics
            ),
        }
    
    def _determine_overall_position(
        self, leading: int, competitive: int, behind: int, total: int
    ) -> str:
        """Determine overall competitive position."""
        if leading > total / 2:
            return "Market Leader"
        elif leading + competitive > total / 2:
            return "Strong Competitor"
        elif behind > total / 2:
            return "Needs Improvement"
        else:
            return "Moderate Position"
    
    # -----------------------------------------------------------------------
    # Strength Gap Analysis
    # -----------------------------------------------------------------------
    
    def calculate_strength_gaps(
        self, 
        our_metrics: Dict[str, Any] = None, 
        competitor_metrics: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate detailed strength gaps for each metric.
        
        Args:
            our_metrics: Our website's metrics.
            competitor_metrics: List of competitor metrics.
        
        Returns:
            Gap matrix with visual coding.
        """
        if our_metrics:
            self.our_data = {"metrics": our_metrics}
        if competitor_metrics:
            self.competitors = competitor_metrics
        
        our_metrics = self.our_data.get("metrics", self.our_data)
        
        gap_matrix = {
            "gaps": {},
            "summary": {
                "strengths": [],
                "weaknesses": [],
                "neutral": [],
            },
            "visual_matrix": [],
        }
        
        for metric_key, config in METRICS_CONFIG.items():
            our_value = our_metrics.get(metric_key, 0)
            
            gaps_for_metric = []
            
            for comp in self.competitors:
                comp_name = comp.get("name", "Unknown")
                comp_metrics = comp.get("metrics", {})
                comp_value = comp_metrics.get(metric_key, 0)
                
                gap_info = self._calculate_detailed_gap(
                    our_value, comp_value, config
                )
                gap_info["competitor"] = comp_name
                gaps_for_metric.append(gap_info)
            
            # Aggregate gap status
            gap_levels = [g["gap_level"] for g in gaps_for_metric]
            
            if all(level == "leader" for level in gap_levels):
                overall_status = "strength"
                gap_matrix["summary"]["strengths"].append({
                    "metric": config["name"],
                    "our_value": our_value,
                    "description": f"Leading in {config['name']}",
                })
            elif all(level == "behind" for level in gap_levels):
                overall_status = "weakness"
                avg_gap = statistics.mean([g["gap"] for g in gaps_for_metric])
                gap_matrix["summary"]["weaknesses"].append({
                    "metric": config["name"],
                    "our_value": our_value,
                    "avg_gap": avg_gap,
                    "description": f"Behind by {abs(avg_gap):.1f} on average",
                })
            else:
                overall_status = "neutral"
                gap_matrix["summary"]["neutral"].append({
                    "metric": config["name"],
                    "our_value": our_value,
                })
            
            gap_matrix["gaps"][metric_key] = {
                "metric_name": config["name"],
                "our_value": our_value,
                "competitors": gaps_for_metric,
                "overall_status": overall_status,
            }
            
            # Build visual matrix row
            row = {
                "metric": config["name"],
                "our_value": f"{our_value}{config['unit']}",
                "comparisons": [],
            }
            
            for gap in gaps_for_metric:
                row["comparisons"].append({
                    "competitor": gap["competitor"],
                    "value": f"{gap['competitor_value']}{config['unit']}",
                    "gap_display": f"{gap['gap_emoji']} {gap['gap']:+.1f}" if gap['gap'] != 0 else "=",
                })
            
            gap_matrix["visual_matrix"].append(row)
        
        self.gap_analysis = gap_matrix
        
        return gap_matrix
    
    def _calculate_detailed_gap(
        self, our_value: float, comp_value: float, config: Dict
    ) -> Dict[str, Any]:
        """Calculate detailed gap information."""
        higher_is_better = config["higher_is_better"]
        
        if comp_value == 0 and our_value == 0:
            return {
                "gap": 0,
                "gap_percentage": 0,
                "gap_level": "neutral",
                "gap_emoji": "⚪",
                "our_value": our_value,
                "competitor_value": comp_value,
                "action_needed": None,
            }
        
        if higher_is_better:
            gap = our_value - comp_value
            reference = comp_value if comp_value != 0 else 1
        else:
            gap = comp_value - our_value
            reference = our_value if our_value != 0 else 1
        
        gap_percentage = (gap / reference) * 100
        
        # Determine gap level and action
        if gap_percentage >= LEADER_THRESHOLD * 100:
            gap_level = "leader"
            gap_emoji = "🟢"
            action_needed = None
        elif gap_percentage <= LAG_THRESHOLD * 100:
            gap_level = "behind"
            gap_emoji = "🔴"
            if higher_is_better:
                action_needed = f"Need +{abs(gap):.0f} to catch up"
            else:
                action_needed = f"Need to reduce by {abs(gap):.1f}"
        else:
            gap_level = "competitive"
            gap_emoji = "🟡"
            action_needed = "Maintain current position"
        
        return {
            "gap": round(gap, 2),
            "gap_percentage": round(gap_percentage, 1),
            "gap_level": gap_level,
            "gap_emoji": gap_emoji,
            "our_value": our_value,
            "competitor_value": comp_value,
            "action_needed": action_needed,
        }
    
    # -----------------------------------------------------------------------
    # Competitive Advantages
    # -----------------------------------------------------------------------
    
    def identify_competitive_advantages(
        self, 
        our_data: Dict[str, Any] = None, 
        all_competitors: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Identify where we lead and where we lag.
        
        Args:
            our_data: Our website's data.
            all_competitors: List of all competitor data.
        
        Returns:
            Dictionary with advantages, disadvantages, and suggestions.
        """
        if our_data:
            self.our_data = our_data
        if all_competitors:
            self.competitors = all_competitors
        
        # Ensure gap analysis is done
        if not self.gap_analysis:
            self.calculate_strength_gaps()
        
        our_metrics = self.our_data.get("metrics", self.our_data)
        
        advantages = []
        disadvantages = []
        
        for metric_key, config in METRICS_CONFIG.items():
            our_value = our_metrics.get(metric_key, 0)
            
            comp_values = []
            for comp in self.competitors:
                comp_metrics = comp.get("metrics", {})
                comp_values.append(comp_metrics.get(metric_key, 0))
            
            if not comp_values:
                continue
            
            avg_competitor = statistics.mean(comp_values)
            best_competitor = max(comp_values) if config["higher_is_better"] else min(comp_values)
            
            # Check if we're leading
            if config["higher_is_better"]:
                if our_value > best_competitor:
                    lead_amount = our_value - best_competitor
                    lead_ratio = our_value / best_competitor if best_competitor > 0 else float('inf')
                    advantages.append({
                        "metric": config["name"],
                        "metric_key": metric_key,
                        "our_value": our_value,
                        "best_competitor": best_competitor,
                        "lead_amount": lead_amount,
                        "lead_ratio": lead_ratio,
                        "description": self._format_lead_description(
                            config["name"], lead_amount, lead_ratio, config
                        ),
                        "suggestion": self._get_advantage_suggestion(metric_key),
                    })
                elif our_value < avg_competitor:
                    gap_amount = avg_competitor - our_value
                    gap_ratio = avg_competitor / our_value if our_value > 0 else float('inf')
                    disadvantages.append({
                        "metric": config["name"],
                        "metric_key": metric_key,
                        "our_value": our_value,
                        "avg_competitor": avg_competitor,
                        "gap_amount": gap_amount,
                        "gap_ratio": gap_ratio,
                        "description": self._format_gap_description(
                            config["name"], gap_amount, config
                        ),
                        "suggestion": self._get_improvement_suggestion(metric_key, gap_amount),
                    })
            else:
                # Lower is better
                if our_value < best_competitor and our_value > 0:
                    lead_amount = best_competitor - our_value
                    lead_ratio = best_competitor / our_value if our_value > 0 else float('inf')
                    advantages.append({
                        "metric": config["name"],
                        "metric_key": metric_key,
                        "our_value": our_value,
                        "best_competitor": best_competitor,
                        "lead_amount": lead_amount,
                        "lead_ratio": lead_ratio,
                        "description": self._format_lead_description(
                            config["name"], lead_amount, lead_ratio, config, lower_is_better=True
                        ),
                        "suggestion": self._get_advantage_suggestion(metric_key),
                    })
                elif our_value > avg_competitor:
                    gap_amount = our_value - avg_competitor
                    disadvantages.append({
                        "metric": config["name"],
                        "metric_key": metric_key,
                        "our_value": our_value,
                        "avg_competitor": avg_competitor,
                        "gap_amount": gap_amount,
                        "description": self._format_gap_description(
                            config["name"], gap_amount, config, lower_is_better=True
                        ),
                        "suggestion": self._get_improvement_suggestion(metric_key, gap_amount),
                    })
        
        # Sort by impact
        advantages.sort(key=lambda x: x.get("lead_ratio", 0), reverse=True)
        disadvantages.sort(key=lambda x: x.get("gap_amount", 0), reverse=True)
        
        return {
            "advantages": advantages[:5],  # Top 5
            "disadvantages": disadvantages[:5],  # Top 5
            "top_3_advantages": advantages[:3],
            "top_3_weaknesses": disadvantages[:3],
            "summary": {
                "total_advantages": len(advantages),
                "total_disadvantages": len(disadvantages),
                "net_position": len(advantages) - len(disadvantages),
            },
        }
    
    def _format_lead_description(
        self, metric_name: str, lead_amount: float, lead_ratio: float, 
        config: Dict, lower_is_better: bool = False
    ) -> str:
        """Format description for a competitive advantage."""
        if lead_ratio >= 2:
            return f"{lead_ratio:.1f}x better {metric_name.lower()}"
        elif lead_ratio >= 1.5:
            return f"50%+ better {metric_name.lower()}"
        else:
            unit = config.get("unit", "")
            if lower_is_better:
                return f"{lead_amount:.1f}{unit} faster/lower {metric_name.lower()}"
            return f"+{lead_amount:.0f}{unit} ahead in {metric_name.lower()}"
    
    def _format_gap_description(
        self, metric_name: str, gap_amount: float, config: Dict,
        lower_is_better: bool = False
    ) -> str:
        """Format description for a competitive disadvantage."""
        unit = config.get("unit", "")
        if lower_is_better:
            return f"Need to improve {metric_name.lower()} by {gap_amount:.1f}{unit}"
        return f"Need +{gap_amount:.0f}{unit} more in {metric_name.lower()}"
    
    def _get_advantage_suggestion(self, metric_key: str) -> str:
        """Get suggestion for leveraging an advantage."""
        suggestions = {
            "domain_authority": "Highlight authority in marketing materials",
            "total_backlinks": "Leverage backlink profile for partnerships",
            "keywords_ranked": "Expand to related keywords",
            "seo_score": "Showcase SEO excellence in case studies",
            "page_speed": "Promote fast user experience in messaging",
            "mobile_score": "Emphasize mobile-first approach",
            "top_ranking": "Maintain and build on top positions",
            "content_pages": "Use content breadth as competitive advantage",
            "link_density": "Promote comprehensive internal linking",
            "orphan_percentage": "Highlight well-connected content structure",
            "avg_page_depth": "Emphasize easy navigation and accessibility",
        }
        return suggestions.get(metric_key, "Leverage this advantage in marketing")
    
    def _get_improvement_suggestion(self, metric_key: str, gap_amount: float) -> str:
        """Get suggestion for improving a weakness."""
        suggestions = {
            "domain_authority": f"Build {int(gap_amount * 10)} quality backlinks over 6 months",
            "total_backlinks": f"Acquire {int(gap_amount)} backlinks through outreach",
            "keywords_ranked": f"Create {int(gap_amount)} new keyword-targeted pages",
            "seo_score": "Improve metadata, fix technical issues, optimize content",
            "page_speed": "Optimize images, enable caching, minimize code",
            "mobile_score": "Implement responsive design, optimize touch targets",
            "top_ranking": "Focus on content quality and backlink building",
            "content_pages": f"Create {int(gap_amount)} new quality content pages",
            "link_density": "Add relevant internal links throughout site",
            "orphan_percentage": "Connect orphan pages with internal links",
            "avg_page_depth": "Restructure navigation to reduce depth",
        }
        return suggestions.get(metric_key, f"Improve by {gap_amount:.0f} to match competitors")
    
    # -----------------------------------------------------------------------
    # Strategic Recommendations
    # -----------------------------------------------------------------------
    
    def generate_strategic_recommendations(
        self, gap_analysis: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized strategic recommendations.
        
        Args:
            gap_analysis: Gap analysis results.
        
        Returns:
            List of prioritized recommendations.
        """
        if gap_analysis:
            self.gap_analysis = gap_analysis
        
        if not self.gap_analysis:
            self.calculate_strength_gaps()
        
        advantages = self.identify_competitive_advantages()
        
        recommendations = []
        
        # Priority 1: Biggest impact opportunities
        for weakness in advantages.get("top_3_weaknesses", []):
            recommendations.append({
                "priority": 1,
                "category": "High Impact",
                "metric": weakness["metric"],
                "action": weakness["suggestion"],
                "current_value": weakness["our_value"],
                "target_value": weakness.get("avg_competitor", weakness["our_value"] * 1.5),
                "gap_to_close": weakness["gap_amount"],
                "effort": self._estimate_effort(weakness["metric_key"], weakness["gap_amount"]),
                "timeline": self._estimate_timeline(weakness["metric_key"], weakness["gap_amount"]),
                "expected_impact": self._estimate_impact(weakness["metric_key"]),
            })
        
        # Priority 2: Medium impact opportunities
        weaknesses = advantages.get("disadvantages", [])[3:6]  # Next 3
        for weakness in weaknesses:
            recommendations.append({
                "priority": 2,
                "category": "Medium Impact",
                "metric": weakness["metric"],
                "action": weakness["suggestion"],
                "current_value": weakness["our_value"],
                "gap_to_close": weakness["gap_amount"],
                "effort": self._estimate_effort(weakness["metric_key"], weakness["gap_amount"]),
                "timeline": self._estimate_timeline(weakness["metric_key"], weakness["gap_amount"]),
                "expected_impact": self._estimate_impact(weakness["metric_key"]),
            })
        
        # Priority 3: Quick wins (leverage advantages)
        for advantage in advantages.get("top_3_advantages", []):
            recommendations.append({
                "priority": 3,
                "category": "Quick Win / Leverage",
                "metric": advantage["metric"],
                "action": advantage["suggestion"],
                "current_value": advantage["our_value"],
                "lead_amount": advantage["lead_amount"],
                "effort": "Low",
                "timeline": "Immediate",
                "expected_impact": "Maintain competitive advantage",
            })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"])
        
        self.recommendations = recommendations
        
        return recommendations
    
    def _estimate_effort(self, metric_key: str, gap_amount: float) -> str:
        """Estimate effort required to close gap."""
        high_effort_metrics = ["domain_authority", "total_backlinks", "keywords_ranked"]
        medium_effort_metrics = ["content_pages", "seo_score"]
        
        if metric_key in high_effort_metrics:
            if gap_amount > 100:
                return "High (6+ months)"
            return "Medium-High (3-6 months)"
        elif metric_key in medium_effort_metrics:
            return "Medium (1-3 months)"
        else:
            return "Low (2-4 weeks)"
    
    def _estimate_timeline(self, metric_key: str, gap_amount: float) -> str:
        """Estimate timeline to close gap."""
        timelines = {
            "domain_authority": f"{int(gap_amount / 5)} months" if gap_amount > 10 else "3 months",
            "total_backlinks": f"{int(gap_amount / 50)} months",
            "keywords_ranked": f"{int(gap_amount / 30)} months",
            "seo_score": "1-2 months",
            "page_speed": "2-4 weeks",
            "mobile_score": "1 month",
            "content_pages": f"{int(gap_amount / 20)} months",
        }
        return timelines.get(metric_key, "2-3 months")
    
    def _estimate_impact(self, metric_key: str) -> str:
        """Estimate impact of improvement."""
        impacts = {
            "domain_authority": "+20-30% organic traffic",
            "total_backlinks": "+15-25% rankings improvement",
            "keywords_ranked": "+30-50% search visibility",
            "seo_score": "+10-20% overall performance",
            "page_speed": "+5-15% conversion rate",
            "mobile_score": "+10-20% mobile traffic",
            "content_pages": "+25-40% keyword coverage",
            "top_ranking": "+50-100% click-through rate",
        }
        return impacts.get(metric_key, "Significant improvement expected")
    
    # -----------------------------------------------------------------------
    # Visualizations
    # -----------------------------------------------------------------------
    
    def create_competitor_radar_chart(
        self, 
        metrics_to_show: List[str] = None,
        normalize: bool = True
    ) -> Dict[str, Any]:
        """
        Create radar/spider chart for visual comparison.
        
        Args:
            metrics_to_show: List of metric keys to include.
            normalize: Whether to normalize values to 0-100 scale.
        
        Returns:
            Plotly figure data for radar chart.
        """
        if not self.comparison_results:
            self.compare_multiple_competitors()
        
        if not metrics_to_show:
            metrics_to_show = list(METRICS_CONFIG.keys())[:8]  # Top 8 metrics
        
        our_metrics = self.our_data.get("metrics", self.our_data)
        our_name = self.our_data.get("name", "Our Site")
        
        categories = [METRICS_CONFIG[m]["name"] for m in metrics_to_show]
        
        # Prepare data traces
        traces = []
        
        # Our data
        our_values = []
        for metric_key in metrics_to_show:
            value = our_metrics.get(metric_key, 0)
            if normalize:
                value = self._normalize_value(metric_key, value)
            our_values.append(value)
        
        # Close the radar chart
        our_values.append(our_values[0])
        categories_closed = categories + [categories[0]]
        
        traces.append({
            "type": "scatterpolar",
            "r": our_values,
            "theta": categories_closed,
            "fill": "toself",
            "name": our_name,
            "line": {"color": "#3B82F6", "width": 2},
            "fillcolor": "rgba(59, 130, 246, 0.2)",
        })
        
        # Competitor data
        colors = ["#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899"]
        
        for idx, comp in enumerate(self.competitors[:5]):  # Max 5 competitors
            comp_name = comp.get("name", f"Competitor {idx + 1}")
            comp_metrics = comp.get("metrics", {})
            
            comp_values = []
            for metric_key in metrics_to_show:
                value = comp_metrics.get(metric_key, 0)
                if normalize:
                    value = self._normalize_value(metric_key, value)
                comp_values.append(value)
            
            comp_values.append(comp_values[0])
            
            traces.append({
                "type": "scatterpolar",
                "r": comp_values,
                "theta": categories_closed,
                "fill": "toself",
                "name": comp_name,
                "line": {"color": colors[idx % len(colors)], "width": 2},
                "fillcolor": f"rgba({self._hex_to_rgb(colors[idx % len(colors)])}, 0.1)",
            })
        
        layout = {
            "polar": {
                "radialaxis": {
                    "visible": True,
                    "range": [0, 100] if normalize else None,
                    "gridcolor": "#334155",
                    "linecolor": "#334155",
                },
                "angularaxis": {
                    "gridcolor": "#334155",
                    "linecolor": "#334155",
                },
                "bgcolor": "transparent",
            },
            "showlegend": True,
            "legend": {
                "x": 1.1,
                "y": 0.5,
                "font": {"color": "#E2E8F0"},
            },
            "paper_bgcolor": "transparent",
            "plot_bgcolor": "transparent",
            "font": {"color": "#E2E8F0"},
            "title": {
                "text": "Competitive Comparison Radar",
                "font": {"size": 16, "color": "#E2E8F0"},
            },
        }
        
        return {
            "data": traces,
            "layout": layout,
        }
    
    def _normalize_value(self, metric_key: str, value: float) -> float:
        """Normalize value to 0-100 scale."""
        config = METRICS_CONFIG.get(metric_key, {})
        max_val = config.get("max")
        
        if max_val:
            normalized = (value / max_val) * 100
            # Invert for lower-is-better metrics
            if not config.get("higher_is_better", True):
                normalized = 100 - normalized
            return min(100, max(0, normalized))
        
        # For unbounded metrics, use relative scaling
        return min(100, value / 10)  # Rough scaling
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB string."""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))
    
    def create_gap_visualization(self) -> Dict[str, Any]:
        """
        Create horizontal bar chart showing gaps.
        
        Returns:
            Plotly figure data for gap visualization.
        """
        if not self.gap_analysis:
            self.calculate_strength_gaps()
        
        our_metrics = self.our_data.get("metrics", self.our_data)
        
        # Prepare data for visualization
        metrics = []
        our_values = []
        gap_values = []
        gap_colors = []
        annotations = []
        
        for metric_key, config in METRICS_CONFIG.items():
            gap_data = self.gap_analysis.get("gaps", {}).get(metric_key, {})
            our_value = our_metrics.get(metric_key, 0)
            
            # Get best competitor value
            comp_data = gap_data.get("competitors", [])
            if comp_data:
                if config["higher_is_better"]:
                    best_comp = max(comp_data, key=lambda x: x.get("competitor_value", 0))
                else:
                    best_comp = min(comp_data, key=lambda x: x.get("competitor_value", float('inf')))
                
                best_comp_value = best_comp.get("competitor_value", 0)
                gap = best_comp.get("gap", 0)
                gap_level = best_comp.get("gap_level", "neutral")
            else:
                best_comp_value = our_value
                gap = 0
                gap_level = "neutral"
            
            metrics.append(config["name"])
            our_values.append(our_value)
            
            # Normalize for display
            max_val = max(our_value, best_comp_value, 1)
            normalized_gap = (best_comp_value - our_value) / max_val * 100
            gap_values.append(normalized_gap)
            
            # Color based on gap level
            if gap_level == "leader":
                gap_colors.append("#10B981")  # Green
            elif gap_level == "behind":
                gap_colors.append("#EF4444")  # Red
            else:
                gap_colors.append("#F59E0B")  # Yellow
        
        # Create horizontal bar chart
        traces = [
            {
                "type": "bar",
                "y": metrics,
                "x": gap_values,
                "orientation": "h",
                "marker": {"color": gap_colors},
                "text": [f"{v:+.1f}%" for v in gap_values],
                "textposition": "outside",
                "textfont": {"color": "#E2E8F0"},
                "name": "Gap",
            }
        ]
        
        layout = {
            "title": {
                "text": "Competitive Gap Analysis",
                "font": {"size": 16, "color": "#E2E8F0"},
            },
            "xaxis": {
                "title": "Gap (%) - Negative = We're behind",
                "gridcolor": "#334155",
                "zerolinecolor": "#64748B",
                "tickfont": {"color": "#94A3B8"},
            },
            "yaxis": {
                "tickfont": {"color": "#E2E8F0"},
            },
            "paper_bgcolor": "transparent",
            "plot_bgcolor": "transparent",
            "font": {"color": "#E2E8F0"},
            "shapes": [{
                "type": "line",
                "x0": 0, "x1": 0,
                "y0": -0.5, "y1": len(metrics) - 0.5,
                "line": {"color": "#64748B", "width": 2, "dash": "dash"},
            }],
            "margin": {"l": 150, "r": 50, "t": 50, "b": 50},
        }
        
        return {
            "data": traces,
            "layout": layout,
        }
    
    # -----------------------------------------------------------------------
    # Report Generation
    # -----------------------------------------------------------------------
    
    def generate_comparison_report(
        self, output_file: str = "output/Competitor_Comparison_Report.txt"
    ) -> str:
        """
        Generate comprehensive competitor comparison report.
        
        Args:
            output_file: Path to save the report.
        
        Returns:
            Path to generated report.
        """
        # Ensure all analyses are done
        if not self.comparison_results:
            self.compare_multiple_competitors()
        if not self.gap_analysis:
            self.calculate_strength_gaps()
        
        advantages = self.identify_competitive_advantages()
        recommendations = self.generate_strategic_recommendations()
        
        our_name = self.our_data.get("name", "Our Site")
        
        lines = [
            "═" * 70,
            "COMPETITOR COMPARISON REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "═" * 70,
            "",
            "=" * 70,
            "COMPETITOR COMPARISON MATRIX",
            "=" * 70,
            "",
        ]
        
        # Build comparison matrix header
        comp_names = [c.get("name", "Unknown") for c in self.competitors]
        header = f"{'Metric':<25} | {our_name:<15}"
        for name in comp_names[:3]:
            header += f" | {name[:15]:<20}"
        lines.append(header)
        lines.append("-" * len(header))
        
        # Add metric rows
        for metric_key, config in METRICS_CONFIG.items():
            comparison = self.comparison_results.get("metrics_comparison", {}).get(metric_key, {})
            our_value = comparison.get("our_value", 0)
            
            row = f"{config['name']:<25} | {our_value:<15}"
            
            for comp in comparison.get("competitors", [])[:3]:
                comp_value = comp.get("value", 0)
                gap_emoji = comp.get("gap_emoji", "")
                gap = comp.get("gap", 0)
                
                if gap != 0:
                    display = f"{comp_value} ({gap_emoji} {gap:+.0f})"
                else:
                    display = f"{comp_value}"
                
                row += f" | {display:<20}"
            
            lines.append(row)
        
        lines.extend([
            "",
            "=" * 70,
            "WHERE WE LEAD ✅",
            "=" * 70,
        ])
        
        for adv in advantages.get("top_3_advantages", []):
            lines.append(f"• {adv['metric']}: {adv['description']}")
            lines.append(f"  Suggestion: {adv['suggestion']}")
            lines.append("")
        
        lines.extend([
            "=" * 70,
            "WHERE WE LAG 🔴",
            "=" * 70,
        ])
        
        for weakness in advantages.get("top_3_weaknesses", []):
            lines.append(f"• {weakness['metric']}: {weakness['description']}")
            lines.append(f"  Action: {weakness['suggestion']}")
            lines.append("")
        
        lines.extend([
            "=" * 70,
            "STRATEGY TO COMPETE",
            "=" * 70,
            "",
        ])
        
        for i, rec in enumerate(recommendations[:6], 1):
            lines.append(f"{i}. [{rec['category']}] {rec['metric']}")
            lines.append(f"   Action: {rec['action']}")
            lines.append(f"   Effort: {rec['effort']}")
            lines.append(f"   Timeline: {rec['timeline']}")
            lines.append(f"   Expected Impact: {rec.get('expected_impact', 'TBD')}")
            lines.append("")
        
        lines.extend([
            "=" * 70,
            "End of Report",
            "=" * 70,
        ])
        
        report = "\n".join(lines)
        
        # Save report
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info(f"Competitor comparison report saved to {output_path}")
        
        return str(output_path)
    
    # -----------------------------------------------------------------------
    # Dashboard Data
    # -----------------------------------------------------------------------
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get all data formatted for dashboard display.
        
        Returns:
            Dictionary with all comparison data for dashboard.
        """
        if not self.comparison_results:
            self.compare_multiple_competitors()
        if not self.gap_analysis:
            self.calculate_strength_gaps()
        
        advantages = self.identify_competitive_advantages()
        recommendations = self.generate_strategic_recommendations()
        
        radar_chart = self.create_competitor_radar_chart()
        gap_chart = self.create_gap_visualization()
        
        return {
            "comparison_matrix": self.comparison_results,
            "gap_analysis": self.gap_analysis,
            "advantages": advantages,
            "recommendations": recommendations,
            "radar_chart": radar_chart,
            "gap_chart": gap_chart,
            "visual_matrix": self._format_visual_matrix(),
        }
    
    def _format_visual_matrix(self) -> str:
        """Format visual comparison matrix as text."""
        if not self.comparison_results:
            return ""
        
        our_name = self.our_data.get("name", "Our Site")
        comp_names = [c.get("name", "Unknown")[:15] for c in self.competitors[:2]]
        
        lines = [
            "╔" + "═" * 60 + "╗",
            f"║ {our_name:^15} vs {' vs '.join(comp_names):^40} ║",
            "╠" + "═" * 60 + "╣",
        ]
        
        for metric_key, config in list(METRICS_CONFIG.items())[:8]:
            comparison = self.comparison_results.get("metrics_comparison", {}).get(metric_key, {})
            our_value = comparison.get("our_value", 0)
            
            row = f"║ {config['name'][:20]:<20}: {our_value:<6}"
            
            for comp in comparison.get("competitors", [])[:2]:
                comp_value = comp.get("value", 0)
                gap_emoji = comp.get("gap_emoji", "")
                gap = comp.get("gap", 0)
                row += f" vs {comp_value} ({gap_emoji}{gap:+.0f})"
            
            row = row[:58].ljust(58) + " ║"
            lines.append(row)
        
        lines.append("╚" + "═" * 60 + "╝")
        
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standalone Functions
# ---------------------------------------------------------------------------

def create_sample_metrics(
    domain_authority: int = 50,
    total_backlinks: int = 500,
    keywords_ranked: int = 100,
    seo_score: float = 70,
    page_speed: float = 2.0,
    mobile_score: int = 80,
    top_ranking: int = 10,
    content_pages: int = 500,
    link_density: float = 5.0,
    orphan_percentage: float = 5.0,
    avg_page_depth: float = 2.5,
) -> Dict[str, Any]:
    """Create a sample metrics dictionary."""
    return {
        "domain_authority": domain_authority,
        "total_backlinks": total_backlinks,
        "keywords_ranked": keywords_ranked,
        "seo_score": seo_score,
        "page_speed": page_speed,
        "mobile_score": mobile_score,
        "top_ranking": top_ranking,
        "content_pages": content_pages,
        "link_density": link_density,
        "orphan_percentage": orphan_percentage,
        "avg_page_depth": avg_page_depth,
    }


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("COMPETITOR ANALYZER - Demo")
    print("=" * 60)
    
    # Create sample data
    our_data = {
        "name": "TSM",
        "metrics": create_sample_metrics(
            domain_authority=42,
            total_backlinks=245,
            keywords_ranked=45,
            seo_score=65,
            page_speed=2.3,
            mobile_score=78,
            top_ranking=8,
            content_pages=1245,
        ),
    }
    
    competitors = [
        {
            "name": "IIT Madras",
            "metrics": create_sample_metrics(
                domain_authority=68,
                total_backlinks=1200,
                keywords_ranked=320,
                seo_score=82,
                page_speed=1.8,
                mobile_score=92,
                top_ranking=3,
                content_pages=2100,
            ),
        },
        {
            "name": "Anna University",
            "metrics": create_sample_metrics(
                domain_authority=55,
                total_backlinks=680,
                keywords_ranked=180,
                seo_score=75,
                page_speed=2.1,
                mobile_score=88,
                top_ranking=5,
                content_pages=1800,
            ),
        },
    ]
    
    # Initialize analyzer
    analyzer = CompetitorAnalyzer(our_data)
    analyzer.competitors = competitors
    
    # Run comparison
    print("\nRunning multi-competitor comparison...")
    comparison = analyzer.compare_multiple_competitors()
    
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"Overall Position: {comparison['summary']['overall_position']}")
    print(f"Leading in: {comparison['summary']['leading_in']} metrics")
    print(f"Competitive in: {comparison['summary']['competitive_in']} metrics")
    print(f"Behind in: {comparison['summary']['behind_in']} metrics")
    
    # Get advantages
    print("\n" + "=" * 60)
    print("COMPETITIVE ADVANTAGES")
    print("=" * 60)
    advantages = analyzer.identify_competitive_advantages()
    
    print("\n✅ Where We Lead:")
    for adv in advantages.get("top_3_advantages", []):
        print(f"  • {adv['metric']}: {adv['description']}")
    
    print("\n🔴 Where We Lag:")
    for weakness in advantages.get("top_3_weaknesses", []):
        print(f"  • {weakness['metric']}: {weakness['description']}")
    
    # Get recommendations
    print("\n" + "=" * 60)
    print("STRATEGIC RECOMMENDATIONS")
    print("=" * 60)
    
