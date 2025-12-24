"""
ParkSense-AI Analyzer
=====================
Analyzes parking data patterns, detects stress points,
and generates insights for LLM explanation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from config import COLORS


# =============================================================================
# PARKING ANALYZER
# =============================================================================

class ParkingAnalyzer:
    """
    Analyzes real-time parking data to detect patterns,
    stress points, and generate actionable insights.
    """
    
    def __init__(self):
        self.stress_threshold_low = 10      # Less than 10 lots = stressed
        self.stress_threshold_moderate = 50  # Less than 50 lots = moderate
    
    def analyze_overall_health(self, df: pd.DataFrame) -> Dict:
        """
        Calculate overall parking system health metrics.
        
        Returns:
            Dictionary with health indicators
        """
        total_carparks = len(df)
        total_lots = df["AvailableLots"].sum()
        
        # Calculate stress levels
        stressed = len(df[df["AvailableLots"] <= self.stress_threshold_low])
        moderate = len(df[(df["AvailableLots"] > self.stress_threshold_low) & 
                         (df["AvailableLots"] <= self.stress_threshold_moderate)])
        healthy = len(df[df["AvailableLots"] > self.stress_threshold_moderate])
        
        # Health score (0-100)
        health_score = round((healthy / total_carparks) * 100, 1) if total_carparks > 0 else 0
        
        return {
            "health_score": health_score,
            "total_carparks": total_carparks,
            "total_available_lots": int(total_lots),
            "average_availability": round(df["AvailableLots"].mean(), 1),
            "median_availability": round(df["AvailableLots"].median(), 1),
            "stressed_carparks": stressed,
            "moderate_carparks": moderate,
            "healthy_carparks": healthy,
            "stress_percentage": round((stressed / total_carparks) * 100, 1) if total_carparks > 0 else 0,
            "status": self._get_health_status(health_score)
        }
    
    def analyze_by_agency(self, df: pd.DataFrame) -> Dict:
        """
        Analyze parking patterns by agency (HDB, LTA, URA).
        
        Returns:
            Dictionary with agency-level analysis
        """
        results = {}
        
        for agency in df["Agency"].unique():
            agency_df = df[df["Agency"] == agency]
            
            stressed = len(agency_df[agency_df["AvailableLots"] <= self.stress_threshold_low])
            total = len(agency_df)
            
            results[agency] = {
                "total_carparks": total,
                "total_lots": int(agency_df["AvailableLots"].sum()),
                "average_availability": round(agency_df["AvailableLots"].mean(), 1),
                "median_availability": round(agency_df["AvailableLots"].median(), 1),
                "min_availability": int(agency_df["AvailableLots"].min()),
                "max_availability": int(agency_df["AvailableLots"].max()),
                "stressed_carparks": stressed,
                "stress_percentage": round((stressed / total) * 100, 1) if total > 0 else 0,
                "health_score": round(((total - stressed) / total) * 100, 1) if total > 0 else 0
            }
        
        # Rank agencies by health
        ranked = sorted(results.items(), key=lambda x: x[1]["health_score"], reverse=True)
        for i, (agency, data) in enumerate(ranked):
            results[agency]["rank"] = i + 1
        
        return results
    
    def analyze_by_area(self, df: pd.DataFrame) -> Dict:
        """
        Analyze parking patterns by area (for LTA carparks).
        
        Returns:
            Dictionary with area-level analysis
        """
        # Filter for records with Area data (mainly LTA)
        df_with_area = df[df["Area"].notna() & (df["Area"] != "")]
        
        if df_with_area.empty:
            return {}
        
        results = {}
        
        for area in df_with_area["Area"].unique():
            area_df = df_with_area[df_with_area["Area"] == area]
            
            results[area] = {
                "total_carparks": len(area_df),
                "total_lots": int(area_df["AvailableLots"].sum()),
                "average_availability": round(area_df["AvailableLots"].mean(), 1),
                "carpark_names": area_df["Development"].tolist()
            }
        
        return results
    
    def identify_stress_points(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        Identify most stressed carparks (lowest availability).
        
        Returns:
            DataFrame of stressed carparks
        """
        stressed_df = df[df["AvailableLots"] <= self.stress_threshold_low].copy()
        stressed_df = stressed_df.nlargest(top_n, "AvailableLots") if len(stressed_df) > top_n else stressed_df
        stressed_df = stressed_df.sort_values("AvailableLots")
        
        return stressed_df[["CarParkID", "Development", "Agency", "Area", 
                           "AvailableLots", "LotType", "Latitude", "Longitude"]]
    
    def identify_high_availability(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        Identify carparks with highest availability.
        
        Returns:
            DataFrame of high-availability carparks
        """
        high_df = df.nlargest(top_n, "AvailableLots")
        
        return high_df[["CarParkID", "Development", "Agency", "Area",
                       "AvailableLots", "LotType", "Latitude", "Longitude"]]
    
    def analyze_lot_types(self, df: pd.DataFrame) -> Dict:
        """
        Analyze availability by lot type (Cars, Heavy Vehicles, Motorcycles).
        
        Returns:
            Dictionary with lot type analysis
        """
        lot_type_names = {
            "C": "Cars",
            "H": "Heavy Vehicles", 
            "Y": "Motorcycles"
        }
        
        results = {}
        
        for lot_type in df["LotType"].unique():
            lot_df = df[df["LotType"] == lot_type]
            
            results[lot_type] = {
                "name": lot_type_names.get(lot_type, lot_type),
                "total_carparks": len(lot_df),
                "total_lots": int(lot_df["AvailableLots"].sum()),
                "average_availability": round(lot_df["AvailableLots"].mean(), 1),
                "stressed_count": len(lot_df[lot_df["AvailableLots"] <= self.stress_threshold_low])
            }
        
        return results
    
    def detect_spatial_clusters(self, df: pd.DataFrame, 
                                grid_size: float = 0.01) -> List[Dict]:
        """
        Detect spatial clusters of stressed carparks.
        
        Args:
            df: DataFrame with parking data
            grid_size: Size of grid cells in degrees (~1km)
            
        Returns:
            List of cluster information
        """
        df_valid = df.dropna(subset=["Latitude", "Longitude"])
        
        # Create grid cells
        df_valid = df_valid.copy()
        df_valid["grid_lat"] = (df_valid["Latitude"] / grid_size).astype(int)
        df_valid["grid_lon"] = (df_valid["Longitude"] / grid_size).astype(int)
        df_valid["grid_cell"] = df_valid["grid_lat"].astype(str) + "_" + df_valid["grid_lon"].astype(str)
        
        clusters = []
        
        for cell in df_valid["grid_cell"].unique():
            cell_df = df_valid[df_valid["grid_cell"] == cell]
            
            stressed_in_cell = len(cell_df[cell_df["AvailableLots"] <= self.stress_threshold_low])
            
            if stressed_in_cell >= 3:  # At least 3 stressed carparks = cluster
                clusters.append({
                    "center_lat": cell_df["Latitude"].mean(),
                    "center_lon": cell_df["Longitude"].mean(),
                    "total_carparks": len(cell_df),
                    "stressed_carparks": stressed_in_cell,
                    "total_lots": int(cell_df["AvailableLots"].sum()),
                    "carpark_names": cell_df["Development"].head(5).tolist(),
                    "severity": "High" if stressed_in_cell >= 5 else "Moderate"
                })
        
        # Sort by severity
        clusters.sort(key=lambda x: x["stressed_carparks"], reverse=True)
        
        return clusters
    
    def compare_agencies(self, df: pd.DataFrame) -> Dict:
        """
        Generate comparative analysis between agencies.
        
        Returns:
            Dictionary with comparison insights
        """
        agency_stats = self.analyze_by_agency(df)
        
        comparison = {
            "best_performer": None,
            "worst_performer": None,
            "insights": []
        }
        
        if not agency_stats:
            return comparison
        
        # Find best and worst
        sorted_agencies = sorted(agency_stats.items(), 
                                key=lambda x: x[1]["health_score"], 
                                reverse=True)
        
        comparison["best_performer"] = sorted_agencies[0][0]
        comparison["worst_performer"] = sorted_agencies[-1][0]
        
        # Generate insights
        for agency, stats in agency_stats.items():
            if stats["stress_percentage"] > 30:
                comparison["insights"].append(
                    f"{agency} shows high stress with {stats['stress_percentage']}% of carparks under pressure"
                )
            elif stats["stress_percentage"] < 10:
                comparison["insights"].append(
                    f"{agency} is performing well with only {stats['stress_percentage']}% stressed carparks"
                )
        
        return comparison
    
    def generate_analysis_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate comprehensive analysis report for LLM processing.
        
        Returns:
            Complete analysis dictionary
        """
        report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_health": self.analyze_overall_health(df),
            "agency_analysis": self.analyze_by_agency(df),
            "area_analysis": self.analyze_by_area(df),
            "lot_type_analysis": self.analyze_lot_types(df),
            "stress_points": self.identify_stress_points(df).to_dict("records"),
            "high_availability": self.identify_high_availability(df).to_dict("records"),
            "spatial_clusters": self.detect_spatial_clusters(df),
            "agency_comparison": self.compare_agencies(df)
        }
        
        return report
    
    def _get_health_status(self, score: float) -> str:
        """Convert health score to status text."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Moderate"
        elif score >= 20:
            return "Stressed"
        else:
            return "Critical"


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing ParkSense-AI Analyzer")
    print("=" * 50)
    
    # Import data fetcher
    from data_fetcher import CarparkDataFetcher
    
    # Fetch data
    fetcher = CarparkDataFetcher()
    data = fetcher.fetch_data()
    
    if data:
        df = fetcher.to_dataframe()
        
        # Create analyzer
        analyzer = ParkingAnalyzer()
        
        # Test overall health
        print("\n🏥 Overall System Health:")
        health = analyzer.analyze_overall_health(df)
        print(f"   Health Score: {health['health_score']}% ({health['status']})")
        print(f"   Total Carparks: {health['total_carparks']}")
        print(f"   Stressed Carparks: {health['stressed_carparks']} ({health['stress_percentage']}%)")
        
        # Test agency analysis
        print("\n🏢 Agency Analysis:")
        agency_stats = analyzer.analyze_by_agency(df)
        for agency, stats in agency_stats.items():
            print(f"   {agency}: Score {stats['health_score']}%, "
                  f"Avg {stats['average_availability']} lots, "
                  f"Stressed {stats['stress_percentage']}%")
        
        # Test stress points
        print("\n⚠️ Top 5 Stressed Carparks:")
        stress_df = analyzer.identify_stress_points(df, top_n=5)
        for _, row in stress_df.iterrows():
            print(f"   {row['Development']} ({row['Agency']}): {row['AvailableLots']} lots")
        
        # Test high availability
        print("\n✅ Top 5 High Availability Carparks:")
        high_df = analyzer.identify_high_availability(df, top_n=5)
        for _, row in high_df.iterrows():
            print(f"   {row['Development']} ({row['Agency']}): {row['AvailableLots']} lots")
        
        # Test spatial clusters
        print("\n📍 Stress Clusters Detected:")
        clusters = analyzer.detect_spatial_clusters(df)
        if clusters:
            for i, cluster in enumerate(clusters[:3]):
                print(f"   Cluster {i+1}: {cluster['stressed_carparks']} stressed carparks "
                      f"({cluster['severity']} severity)")
        else:
            print("   No significant stress clusters detected")
        
        # Test comparison
        print("\n📊 Agency Comparison:")
        comparison = analyzer.compare_agencies(df)
        print(f"   Best Performer: {comparison['best_performer']}")
        print(f"   Needs Attention: {comparison['worst_performer']}")
        
        print("\n✅ Analyzer working correctly!")
    else:
        print("❌ Failed to fetch data")