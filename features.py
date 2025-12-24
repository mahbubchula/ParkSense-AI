"""
ParkSense-AI Advanced Features
==============================
Additional features for enhanced parking intelligence:
- Historical data tracking
- Alert system
- Export reports
- Search & filter
- Nearest parking finder
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import io
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# HISTORICAL DATA TRACKER
# =============================================================================

class HistoricalTracker:
    """
    Tracks parking data over time for trend analysis.
    Stores snapshots in memory (can be extended to database).
    """
    
    def __init__(self, max_snapshots: int = 60):
        """
        Initialize tracker.
        
        Args:
            max_snapshots: Maximum number of snapshots to keep (default 60 = 1 hour at 1-min intervals)
        """
        self.max_snapshots = max_snapshots
        self.snapshots: List[Dict] = []
    
    def add_snapshot(self, df: pd.DataFrame, summary: Dict):
        """Add a new data snapshot."""
        snapshot = {
            "timestamp": datetime.now(),
            "total_carparks": len(df),
            "total_available": int(df["AvailableLots"].sum()),
            "by_agency": {},
            "by_status": {
                "Available": len(df[df["Status"] == "Available"]),
                "Moderate": len(df[df["Status"] == "Moderate"]),
                "Limited": len(df[df["Status"] == "Limited"])
            },
            "stressed_count": len(df[df["AvailableLots"] <= 10]),
            "top_available": df.nlargest(5, "AvailableLots")[["Development", "Agency", "AvailableLots"]].to_dict("records"),
            "most_stressed": df.nsmallest(5, "AvailableLots")[["Development", "Agency", "AvailableLots"]].to_dict("records")
        }
        
        # Agency breakdown
        for agency in df["Agency"].unique():
            agency_df = df[df["Agency"] == agency]
            snapshot["by_agency"][agency] = {
                "available": int(agency_df["AvailableLots"].sum()),
                "carparks": len(agency_df),
                "stressed": len(agency_df[agency_df["AvailableLots"] <= 10])
            }
        
        self.snapshots.append(snapshot)
        
        # Keep only recent snapshots
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]
    
    def get_trend_data(self) -> pd.DataFrame:
        """Get historical trend as DataFrame."""
        if not self.snapshots:
            return pd.DataFrame()
        
        records = []
        for snap in self.snapshots:
            record = {
                "timestamp": snap["timestamp"],
                "total_available": snap["total_available"],
                "stressed_count": snap["stressed_count"]
            }
            # Add agency data
            for agency, data in snap["by_agency"].items():
                record[f"{agency}_available"] = data["available"]
                record[f"{agency}_stressed"] = data["stressed"]
            records.append(record)
        
        return pd.DataFrame(records)
    
    def get_availability_change(self) -> Dict:
        """Calculate change since first snapshot."""
        if len(self.snapshots) < 2:
            return {"change": 0, "percent": 0, "direction": "stable"}
        
        first = self.snapshots[0]["total_available"]
        last = self.snapshots[-1]["total_available"]
        change = last - first
        percent = (change / first * 100) if first > 0 else 0
        
        if change > 0:
            direction = "increasing"
        elif change < 0:
            direction = "decreasing"
        else:
            direction = "stable"
        
        return {
            "change": change,
            "percent": round(percent, 2),
            "direction": direction,
            "time_span_minutes": len(self.snapshots)
        }
    
    def get_agency_trends(self) -> Dict:
        """Get trend analysis by agency."""
        if len(self.snapshots) < 2:
            return {}
        
        trends = {}
        agencies = self.snapshots[-1]["by_agency"].keys()
        
        for agency in agencies:
            first_avail = self.snapshots[0]["by_agency"].get(agency, {}).get("available", 0)
            last_avail = self.snapshots[-1]["by_agency"].get(agency, {}).get("available", 0)
            change = last_avail - first_avail
            
            trends[agency] = {
                "start": first_avail,
                "current": last_avail,
                "change": change,
                "trend": "📈" if change > 0 else "📉" if change < 0 else "➡️"
            }
        
        return trends


# =============================================================================
# ALERT SYSTEM
# =============================================================================

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents a parking alert."""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    agency: Optional[str] = None
    carpark_id: Optional[str] = None
    metric_value: Optional[float] = None


class AlertSystem:
    """
    Monitors parking data and generates alerts for critical conditions.
    """
    
    def __init__(self):
        # Thresholds
        self.critical_stress_percent = 30  # >30% stressed = critical
        self.warning_stress_percent = 20   # >20% stressed = warning
        self.critical_availability = 5     # <5 lots = critical for individual carpark
        self.warning_availability = 10     # <10 lots = warning
        
        self.alerts: List[Alert] = []
    
    def analyze_and_alert(self, df: pd.DataFrame, summary: Dict) -> List[Alert]:
        """
        Analyze data and generate alerts.
        
        Args:
            df: Current parking data
            summary: Summary statistics
            
        Returns:
            List of generated alerts
        """
        self.alerts = []
        
        # System-wide alerts
        self._check_system_health(df, summary)
        
        # Agency-specific alerts
        self._check_agency_health(df)
        
        # Individual carpark alerts
        self._check_critical_carparks(df)
        
        # Sort by severity (critical first)
        severity_order = {AlertLevel.CRITICAL: 0, AlertLevel.WARNING: 1, AlertLevel.INFO: 2}
        self.alerts.sort(key=lambda x: severity_order[x.level])
        
        return self.alerts
    
    def _check_system_health(self, df: pd.DataFrame, summary: Dict):
        """Check overall system health."""
        total = len(df)
        stressed = len(df[df["AvailableLots"] <= 10])
        stress_percent = (stressed / total * 100) if total > 0 else 0
        
        if stress_percent >= self.critical_stress_percent:
            self.alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                title="🚨 System Under Critical Stress",
                message=f"{stress_percent:.1f}% of carparks ({stressed}) have critically low availability. "
                        f"Immediate attention required.",
                timestamp=datetime.now(),
                metric_value=stress_percent
            ))
        elif stress_percent >= self.warning_stress_percent:
            self.alerts.append(Alert(
                level=AlertLevel.WARNING,
                title="⚠️ Elevated System Stress",
                message=f"{stress_percent:.1f}% of carparks ({stressed}) showing stress. "
                        f"Monitor closely.",
                timestamp=datetime.now(),
                metric_value=stress_percent
            ))
    
    def _check_agency_health(self, df: pd.DataFrame):
        """Check health by agency."""
        for agency in df["Agency"].unique():
            agency_df = df[df["Agency"] == agency]
            total = len(agency_df)
            stressed = len(agency_df[agency_df["AvailableLots"] <= 10])
            stress_percent = (stressed / total * 100) if total > 0 else 0
            
            if stress_percent >= 40:  # Agency-specific critical threshold
                self.alerts.append(Alert(
                    level=AlertLevel.CRITICAL,
                    title=f"🚨 {agency} Critical",
                    message=f"{agency} has {stress_percent:.1f}% stressed carparks ({stressed}/{total}). "
                            f"Agency requires immediate attention.",
                    timestamp=datetime.now(),
                    agency=agency,
                    metric_value=stress_percent
                ))
            elif stress_percent >= 25:
                self.alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    title=f"⚠️ {agency} Warning",
                    message=f"{agency} showing elevated stress: {stress_percent:.1f}% ({stressed}/{total}).",
                    timestamp=datetime.now(),
                    agency=agency,
                    metric_value=stress_percent
                ))
    
    def _check_critical_carparks(self, df: pd.DataFrame):
        """Check individual carparks with critical availability."""
        critical_carparks = df[df["AvailableLots"] <= self.critical_availability]
        
        if len(critical_carparks) > 10:
            # Too many to list individually, summarize
            self.alerts.append(Alert(
                level=AlertLevel.WARNING,
                title="⚠️ Multiple Carparks Near Capacity",
                message=f"{len(critical_carparks)} carparks have ≤{self.critical_availability} lots available.",
                timestamp=datetime.now(),
                metric_value=len(critical_carparks)
            ))
        else:
            # List individual critical carparks
            for _, row in critical_carparks.iterrows():
                if row["AvailableLots"] == 0:
                    self.alerts.append(Alert(
                        level=AlertLevel.CRITICAL,
                        title=f"🚨 {row['Development'][:30]} FULL",
                        message=f"Carpark is completely full (0 lots). Agency: {row['Agency']}",
                        timestamp=datetime.now(),
                        agency=row["Agency"],
                        carpark_id=row["CarParkID"],
                        metric_value=0
                    ))
    
    def get_alert_summary(self) -> Dict:
        """Get summary of current alerts."""
        return {
            "total": len(self.alerts),
            "critical": len([a for a in self.alerts if a.level == AlertLevel.CRITICAL]),
            "warning": len([a for a in self.alerts if a.level == AlertLevel.WARNING]),
            "info": len([a for a in self.alerts if a.level == AlertLevel.INFO])
        }


# =============================================================================
# SEARCH & FILTER
# =============================================================================

class CarparkSearch:
    """
    Advanced search and filter functionality for carparks.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def search_by_name(self, query: str) -> pd.DataFrame:
        """Search carparks by name/development."""
        if not query:
            return self.df
        
        query = query.lower()
        mask = self.df["Development"].str.lower().str.contains(query, na=False)
        return self.df[mask]
    
    def filter_by_agency(self, agencies: List[str]) -> pd.DataFrame:
        """Filter by agency."""
        if not agencies or "All" in agencies:
            return self.df
        return self.df[self.df["Agency"].isin(agencies)]
    
    def filter_by_availability(self, min_lots: int = 0, max_lots: int = None) -> pd.DataFrame:
        """Filter by availability range."""
        result = self.df[self.df["AvailableLots"] >= min_lots]
        if max_lots is not None:
            result = result[result["AvailableLots"] <= max_lots]
        return result
    
    def filter_by_status(self, statuses: List[str]) -> pd.DataFrame:
        """Filter by status."""
        if not statuses:
            return self.df
        return self.df[self.df["Status"].isin(statuses)]
    
    def filter_by_lot_type(self, lot_types: List[str]) -> pd.DataFrame:
        """Filter by lot type."""
        if not lot_types:
            return self.df
        return self.df[self.df["LotType"].isin(lot_types)]
    
    def filter_by_area(self, areas: List[str]) -> pd.DataFrame:
        """Filter by area (for LTA carparks)."""
        if not areas:
            return self.df
        return self.df[self.df["Area"].isin(areas)]
    
    def advanced_filter(self, 
                       query: str = None,
                       agencies: List[str] = None,
                       statuses: List[str] = None,
                       min_lots: int = 0,
                       lot_types: List[str] = None) -> pd.DataFrame:
        """Apply multiple filters."""
        result = self.df.copy()
        
        if query:
            result = result[result["Development"].str.lower().str.contains(query.lower(), na=False)]
        
        if agencies and "All" not in agencies:
            result = result[result["Agency"].isin(agencies)]
        
        if statuses:
            result = result[result["Status"].isin(statuses)]
        
        result = result[result["AvailableLots"] >= min_lots]
        
        if lot_types:
            result = result[result["LotType"].isin(lot_types)]
        
        return result


# =============================================================================
# NEAREST PARKING FINDER
# =============================================================================

class NearestParkingFinder:
    """
    Finds nearest carparks to a given location.
    Uses Haversine formula for distance calculation.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.dropna(subset=["Latitude", "Longitude"])
    
    def haversine_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
    
    def find_nearest(self, lat: float, lon: float, 
                    n: int = 10, 
                    min_availability: int = 1,
                    agency: str = None) -> pd.DataFrame:
        """
        Find nearest carparks to a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            n: Number of results
            min_availability: Minimum available lots
            agency: Filter by agency (optional)
            
        Returns:
            DataFrame of nearest carparks with distances
        """
        df = self.df.copy()
        
        # Filter by availability
        df = df[df["AvailableLots"] >= min_availability]
        
        # Filter by agency
        if agency and agency != "All":
            df = df[df["Agency"] == agency]
        
        if df.empty:
            return pd.DataFrame()
        
        # Calculate distances
        df["Distance_km"] = df.apply(
            lambda row: self.haversine_distance(lat, lon, row["Latitude"], row["Longitude"]),
            axis=1
        )
        
        # Sort by distance and get top n
        result = df.nsmallest(n, "Distance_km")
        result["Distance_km"] = result["Distance_km"].round(2)
        
        return result[["Development", "Agency", "AvailableLots", "Status", 
                      "Distance_km", "Latitude", "Longitude", "LotType"]]
    
    def find_in_radius(self, lat: float, lon: float,
                      radius_km: float = 1.0,
                      min_availability: int = 1) -> pd.DataFrame:
        """
        Find all carparks within a radius.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers
            min_availability: Minimum available lots
            
        Returns:
            DataFrame of carparks within radius
        """
        df = self.df.copy()
        df = df[df["AvailableLots"] >= min_availability]
        
        if df.empty:
            return pd.DataFrame()
        
        # Calculate distances
        df["Distance_km"] = df.apply(
            lambda row: self.haversine_distance(lat, lon, row["Latitude"], row["Longitude"]),
            axis=1
        )
        
        # Filter by radius
        result = df[df["Distance_km"] <= radius_km]
        result = result.sort_values("Distance_km")
        result["Distance_km"] = result["Distance_km"].round(2)
        
        return result[["Development", "Agency", "AvailableLots", "Status",
                      "Distance_km", "Latitude", "Longitude"]]


# =============================================================================
# REPORT EXPORTER
# =============================================================================

class ReportExporter:
    """
    Exports parking data and analysis to various formats.
    """
    
    def __init__(self, df: pd.DataFrame, summary: Dict, analysis: Dict = None):
        self.df = df
        self.summary = summary
        self.analysis = analysis or {}
    
    def to_csv(self) -> str:
        """Export data to CSV string."""
        return self.df.to_csv(index=False)
    
    def to_excel_buffer(self) -> io.BytesIO:
        """Export to Excel buffer for download."""
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Main data
            self.df.to_excel(writer, sheet_name='Carpark Data', index=False)
            
            # Summary
            summary_df = pd.DataFrame([
                {"Metric": "Total Carparks", "Value": self.summary.get("total_carparks", 0)},
                {"Metric": "Total Available Lots", "Value": self.summary.get("total_available_lots", 0)},
                {"Metric": "Fetch Time", "Value": str(self.summary.get("fetch_time", ""))}
            ])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Agency breakdown
            if "by_agency" in self.summary:
                agency_data = []
                for agency, stats in self.summary["by_agency"].items():
                    agency_data.append({
                        "Agency": agency,
                        "Carparks": stats.get("carparks", 0),
                        "Available Lots": stats.get("available_lots", 0),
                        "Avg Availability": stats.get("avg_availability", 0)
                    })
                agency_df = pd.DataFrame(agency_data)
                agency_df.to_excel(writer, sheet_name='By Agency', index=False)
        
        buffer.seek(0)
        return buffer
    
    def generate_text_report(self) -> str:
        """Generate a text-based report."""
        report = []
        report.append("=" * 60)
        report.append("PARKSENSE-AI PARKING REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Carparks: {self.summary.get('total_carparks', 0):,}")
        report.append(f"Total Available Lots: {self.summary.get('total_available_lots', 0):,}")
        report.append("")
        
        # By Agency
        report.append("BY AGENCY")
        report.append("-" * 40)
        if "by_agency" in self.summary:
            for agency, stats in self.summary["by_agency"].items():
                report.append(f"{agency}:")
                report.append(f"  - Carparks: {stats.get('carparks', 0)}")
                report.append(f"  - Available: {stats.get('available_lots', 0):,}")
                report.append(f"  - Avg: {stats.get('avg_availability', 0)}")
        report.append("")
        
        # Status
        report.append("BY STATUS")
        report.append("-" * 40)
        if "by_status" in self.summary:
            for status, count in self.summary["by_status"].items():
                report.append(f"{status}: {count}")
        
        report.append("")
        report.append("=" * 60)
        report.append("END OF REPORT")
        
        return "\n".join(report)
    
    def generate_json_report(self) -> str:
        """Generate JSON report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": self.summary,
            "analysis": self.analysis,
            "data_sample": self.df.head(100).to_dict("records")
        }
        return json.dumps(report, indent=2, default=str)


# =============================================================================
# POPULAR LOCATIONS (Singapore)
# =============================================================================

POPULAR_LOCATIONS = {
    "Orchard Road": {"lat": 1.3048, "lon": 103.8318},
    "Marina Bay": {"lat": 1.2814, "lon": 103.8636},
    "Sentosa": {"lat": 1.2494, "lon": 103.8303},
    "Changi Airport": {"lat": 1.3644, "lon": 103.9915},
    "Jurong East": {"lat": 1.3329, "lon": 103.7436},
    "Tampines": {"lat": 1.3496, "lon": 103.9568},
    "Woodlands": {"lat": 1.4382, "lon": 103.7890},
    "Ang Mo Kio": {"lat": 1.3691, "lon": 103.8454},
    "Bugis": {"lat": 1.3008, "lon": 103.8553},
    "Harbourfront": {"lat": 1.2644, "lon": 103.8223},
    "Raffles Place": {"lat": 1.2830, "lon": 103.8513},
    "Chinatown": {"lat": 1.2836, "lon": 103.8440},
    "Little India": {"lat": 1.3066, "lon": 103.8518},
    "Clarke Quay": {"lat": 1.2906, "lon": 103.8465},
    "Dhoby Ghaut": {"lat": 1.2988, "lon": 103.8456}
}


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing ParkSense-AI Advanced Features")
    print("=" * 50)
    
    # Import data fetcher
    from data_fetcher import CarparkDataFetcher
    
    # Fetch data
    fetcher = CarparkDataFetcher()
    data = fetcher.fetch_data()
    
    if data:
        df = fetcher.to_dataframe()
        summary = fetcher.get_summary(df)
        
        # Test Historical Tracker
        print("\n📈 Testing Historical Tracker...")
        tracker = HistoricalTracker()
        tracker.add_snapshot(df, summary)
        print(f"   Snapshots: {len(tracker.snapshots)}")
        print("   ✅ Historical Tracker working!")
        
        # Test Alert System
        print("\n🔔 Testing Alert System...")
        alert_system = AlertSystem()
        alerts = alert_system.analyze_and_alert(df, summary)
        alert_summary = alert_system.get_alert_summary()
        print(f"   Total Alerts: {alert_summary['total']}")
        print(f"   Critical: {alert_summary['critical']}")
        print(f"   Warning: {alert_summary['warning']}")
        print("   ✅ Alert System working!")
        
        # Test Search
        print("\n🔍 Testing Search...")
        search = CarparkSearch(df)
        results = search.search_by_name("marina")
        print(f"   Found {len(results)} carparks matching 'marina'")
        print("   ✅ Search working!")
        
        # Test Nearest Finder
        print("\n📍 Testing Nearest Parking Finder...")
        finder = NearestParkingFinder(df)
        nearest = finder.find_nearest(1.2814, 103.8636, n=5)  # Marina Bay
        print(f"   Found {len(nearest)} nearest carparks to Marina Bay")
        if not nearest.empty:
            print(f"   Closest: {nearest.iloc[0]['Development']} ({nearest.iloc[0]['Distance_km']} km)")
        print("   ✅ Nearest Finder working!")
        
        # Test Export
        print("\n📄 Testing Report Exporter...")
        exporter = ReportExporter(df, summary)
        text_report = exporter.generate_text_report()
        print(f"   Generated text report: {len(text_report)} characters")
        print("   ✅ Report Exporter working!")
        
        print("\n" + "=" * 50)
        print("✅ All advanced features working correctly!")
    else:
        print("❌ Failed to fetch data")