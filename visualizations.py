"""
ParkSense-AI Visualizations
===========================
Creates beautiful interactive maps and charts for parking data.
Uses Folium for maps and Plotly for charts.
"""

import folium
from folium.plugins import MarkerCluster, HeatMap
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Optional
from config import COLORS, SINGAPORE_CENTER, DEFAULT_ZOOM


# =============================================================================
# MAP VISUALIZATIONS
# =============================================================================

class ParkingMapVisualizer:
    """
    Creates interactive maps showing carpark locations and availability.
    """
    
    def __init__(self):
        self.colors = COLORS
        self.center = SINGAPORE_CENTER
        self.zoom = DEFAULT_ZOOM
    
    def create_base_map(self, style: str = "dark") -> folium.Map:
        """
        Create base Singapore map with selected style.
        
        Args:
            style: "dark", "light", or "satellite"
        """
        tiles_map = {
            "dark": "cartodbdark_matter",
            "light": "cartodbpositron",
            "satellite": "Esri.WorldImagery"
        }
        
        m = folium.Map(
            location=self.center,
            zoom_start=self.zoom,
            tiles=tiles_map.get(style, "cartodbdark_matter"),
            control_scale=True
        )
        
        return m
    
    def create_availability_map(self, df: pd.DataFrame, cluster: bool = True) -> folium.Map:
        """
        Create map with carpark markers colored by agency.
        
        Args:
            df: DataFrame with carpark data
            cluster: Whether to cluster markers
        """
        m = self.create_base_map("dark")
        
        # Filter out records without valid coordinates
        df_valid = df.dropna(subset=["Latitude", "Longitude"])
        
        if cluster:
            # Create marker clusters for each agency
            for agency in ["HDB", "LTA", "URA"]:
                agency_df = df_valid[df_valid["Agency"] == agency]
                
                if agency_df.empty:
                    continue
                
                cluster_group = MarkerCluster(
                    name=f"{agency} Carparks",
                    show=True
                )
                
                for _, row in agency_df.iterrows():
                    popup_html = self._create_popup(row)
                    
                    folium.CircleMarker(
                        location=[row["Latitude"], row["Longitude"]],
                        radius=8,
                        popup=folium.Popup(popup_html, max_width=300),
                        color=self.colors.get(agency, "#666666"),
                        fill=True,
                        fill_color=self.colors.get(agency, "#666666"),
                        fill_opacity=0.7,
                        weight=2
                    ).add_to(cluster_group)
                
                cluster_group.add_to(m)
        else:
            # Add individual markers
            for _, row in df_valid.iterrows():
                popup_html = self._create_popup(row)
                
                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=6,
                    popup=folium.Popup(popup_html, max_width=300),
                    color=self.colors.get(row["Agency"], "#666666"),
                    fill=True,
                    fill_color=self.colors.get(row["Agency"], "#666666"),
                    fill_opacity=0.7,
                    weight=2
                ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        return m
    
    def create_heatmap(self, df: pd.DataFrame, weight_col: str = "AvailableLots") -> folium.Map:
        """
        Create heatmap showing parking availability intensity.
        
        Args:
            df: DataFrame with carpark data
            weight_col: Column to use for heat intensity
        """
        m = self.create_base_map("dark")
        
        # Filter valid coordinates
        df_valid = df.dropna(subset=["Latitude", "Longitude"])
        
        # Prepare heatmap data: [lat, lng, weight]
        heat_data = df_valid[["Latitude", "Longitude", weight_col]].values.tolist()
        
        # Add heatmap layer
        HeatMap(
            heat_data,
            name="Availability Heatmap",
            min_opacity=0.3,
            max_zoom=18,
            radius=15,
            blur=10,
            gradient={
                0.2: "#22C55E",  # Green - high availability
                0.5: "#EAB308",  # Yellow - moderate
                0.8: "#EF4444"   # Red - limited
            }
        ).add_to(m)
        
        folium.LayerControl().add_to(m)
        
        return m
    
    def create_status_map(self, df: pd.DataFrame) -> folium.Map:
        """
        Create map with markers colored by availability status.
        """
        m = self.create_base_map("dark")
        
        df_valid = df.dropna(subset=["Latitude", "Longitude"])
        
        status_colors = {
            "Available": "#22C55E",
            "Moderate": "#EAB308", 
            "Limited": "#EF4444"
        }
        
        for status, color in status_colors.items():
            status_df = df_valid[df_valid["Status"] == status]
            
            cluster_group = MarkerCluster(name=f"{status} ({len(status_df)})")
            
            for _, row in status_df.iterrows():
                popup_html = self._create_popup(row)
                
                folium.CircleMarker(
                    location=[row["Latitude"], row["Longitude"]],
                    radius=7,
                    popup=folium.Popup(popup_html, max_width=300),
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    weight=2
                ).add_to(cluster_group)
            
            cluster_group.add_to(m)
        
        folium.LayerControl().add_to(m)
        
        return m
    
    def _create_popup(self, row: pd.Series) -> str:
        """Create HTML popup content for marker."""
        status_color = {
            "Available": "#22C55E",
            "Moderate": "#EAB308",
            "Limited": "#EF4444"
        }.get(row.get("Status", ""), "#666666")
        
        return f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; min-width: 200px;">
            <h4 style="margin: 0 0 8px 0; color: #1E3A8A; border-bottom: 2px solid {self.colors.get(row['Agency'], '#666')}; padding-bottom: 5px;">
                {row.get('Development', 'Unknown')}
            </h4>
            <table style="width: 100%;">
                <tr>
                    <td><strong>Agency:</strong></td>
                    <td style="color: {self.colors.get(row['Agency'], '#666')};">{row.get('Agency', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>Available:</strong></td>
                    <td style="color: {status_color}; font-weight: bold;">{row.get('AvailableLots', 0)} lots</td>
                </tr>
                <tr>
                    <td><strong>Lot Type:</strong></td>
                    <td>{self._get_lot_type_name(row.get('LotType', ''))}</td>
                </tr>
                <tr>
                    <td><strong>Status:</strong></td>
                    <td style="color: {status_color};">{row.get('Status', 'Unknown')}</td>
                </tr>
                <tr>
                    <td><strong>ID:</strong></td>
                    <td>{row.get('CarParkID', 'N/A')}</td>
                </tr>
            </table>
        </div>
        """
    
    def _get_lot_type_name(self, lot_type: str) -> str:
        """Convert lot type code to readable name."""
        types = {
            "C": "Cars",
            "H": "Heavy Vehicles",
            "Y": "Motorcycles"
        }
        return types.get(lot_type, lot_type)


# =============================================================================
# CHART VISUALIZATIONS
# =============================================================================

class ParkingChartVisualizer:
    """
    Creates interactive charts for parking data analysis.
    """
    
    def __init__(self):
        self.colors = COLORS
        self.template = "plotly_dark"
    
    def create_agency_comparison(self, summary: Dict) -> go.Figure:
        """
        Create bar chart comparing agencies.
        """
        agencies = list(summary["by_agency"].keys())
        carparks = [summary["by_agency"][a]["carparks"] for a in agencies]
        lots = [summary["by_agency"][a]["available_lots"] for a in agencies]
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Number of Carparks", "Available Lots"),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        colors = [self.colors.get(a, "#666666") for a in agencies]
        
        # Carparks count
        fig.add_trace(
            go.Bar(
                x=agencies,
                y=carparks,
                marker_color=colors,
                text=carparks,
                textposition="outside",
                name="Carparks"
            ),
            row=1, col=1
        )
        
        # Available lots
        fig.add_trace(
            go.Bar(
                x=agencies,
                y=lots,
                marker_color=colors,
                text=[f"{l:,}" for l in lots],
                textposition="outside",
                name="Lots"
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            template=self.template,
            showlegend=False,
            height=400,
            title_text="Agency Comparison",
            title_x=0.5,
            paper_bgcolor=self.colors["background"],
            plot_bgcolor=self.colors["surface"],
            font=dict(color=self.colors["text"])
        )
        
        return fig
    
    def create_status_donut(self, summary: Dict) -> go.Figure:
        """
        Create donut chart showing availability status distribution.
        """
        statuses = list(summary["by_status"].keys())
        values = list(summary["by_status"].values())
        
        colors = [
            self.colors["available"],
            self.colors["moderate"],
            self.colors["limited"]
        ]
        
        fig = go.Figure(data=[go.Pie(
            labels=statuses,
            values=values,
            hole=0.5,
            marker_colors=colors,
            textinfo="label+percent",
            textposition="outside"
        )])
        
        fig.update_layout(
            template=self.template,
            title_text="Availability Status Distribution",
            title_x=0.5,
            height=400,
            paper_bgcolor=self.colors["background"],
            plot_bgcolor=self.colors["surface"],
            font=dict(color=self.colors["text"]),
            annotations=[dict(
                text=f"{sum(values):,}<br>Carparks",
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False,
                font_color=self.colors["text"]
            )]
        )
        
        return fig
    
    def create_lot_type_chart(self, summary: Dict) -> go.Figure:
        """
        Create bar chart showing lot type distribution.
        """
        lot_types = list(summary["by_lot_type"].keys())
        lot_names = [self._get_lot_type_name(lt) for lt in lot_types]
        values = [summary["by_lot_type"][lt]["available_lots"] for lt in lot_types]
        
        fig = go.Figure(data=[go.Bar(
            x=lot_names,
            y=values,
            marker_color=[self.colors["primary"], self.colors["secondary"], self.colors["accent"]][:len(lot_types)],
            text=[f"{v:,}" for v in values],
            textposition="outside"
        )])
        
        fig.update_layout(
            template=self.template,
            title_text="Available Lots by Type",
            title_x=0.5,
            height=400,
            xaxis_title="Lot Type",
            yaxis_title="Available Lots",
            paper_bgcolor=self.colors["background"],
            plot_bgcolor=self.colors["surface"],
            font=dict(color=self.colors["text"])
        )
        
        return fig
    
    def create_top_carparks_chart(self, df: pd.DataFrame, n: int = 10) -> go.Figure:
        """
        Create horizontal bar chart of top carparks by availability.
        """
        top_df = df.nlargest(n, "AvailableLots")[["Development", "AvailableLots", "Agency"]]
        
        colors = [self.colors.get(a, "#666666") for a in top_df["Agency"]]
        
        fig = go.Figure(data=[go.Bar(
            y=top_df["Development"],
            x=top_df["AvailableLots"],
            orientation="h",
            marker_color=colors,
            text=top_df["AvailableLots"],
            textposition="outside"
        )])
        
        fig.update_layout(
            template=self.template,
            title_text=f"Top {n} Carparks by Availability",
            title_x=0.5,
            height=500,
            xaxis_title="Available Lots",
            yaxis_title="",
            paper_bgcolor=self.colors["background"],
            plot_bgcolor=self.colors["surface"],
            font=dict(color=self.colors["text"]),
            yaxis=dict(autorange="reversed")
        )
        
        return fig
    
    def create_gauge_chart(self, value: int, max_value: int, title: str) -> go.Figure:
        """
        Create gauge chart for single metric.
        """
        percentage = (value / max_value * 100) if max_value > 0 else 0
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=percentage,
            number={"suffix": "%", "font": {"size": 40, "color": self.colors["text"]}},
            title={"text": title, "font": {"size": 16, "color": self.colors["text"]}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": self.colors["text"]},
                "bar": {"color": self.colors["secondary"]},
                "bgcolor": self.colors["surface"],
                "bordercolor": self.colors["text"],
                "steps": [
                    {"range": [0, 30], "color": self.colors["limited"]},
                    {"range": [30, 70], "color": self.colors["moderate"]},
                    {"range": [70, 100], "color": self.colors["available"]}
                ],
                "threshold": {
                    "line": {"color": self.colors["text"], "width": 4},
                    "thickness": 0.75,
                    "value": percentage
                }
            }
        ))
        
        fig.update_layout(
            height=250,
            paper_bgcolor=self.colors["background"],
            font=dict(color=self.colors["text"])
        )
        
        return fig
    
    def _get_lot_type_name(self, lot_type: str) -> str:
        """Convert lot type code to readable name."""
        types = {"C": "Cars", "H": "Heavy Vehicles", "Y": "Motorcycles"}
        return types.get(lot_type, lot_type)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing ParkSense-AI Visualizations")
    print("=" * 50)
    
    # Import data fetcher
    from data_fetcher import CarparkDataFetcher
    
    # Fetch data
    fetcher = CarparkDataFetcher()
    data = fetcher.fetch_data()
    
    if data:
        df = fetcher.to_dataframe()
        summary = fetcher.get_summary(df)
        
        # Test Map
        print("\n🗺️ Creating map...")
        map_viz = ParkingMapVisualizer()
        m = map_viz.create_availability_map(df)
        m.save("test_map.html")
        print("   ✅ Map saved to test_map.html")
        
        # Test Charts
        print("\n📊 Creating charts...")
        chart_viz = ParkingChartVisualizer()
        
        fig1 = chart_viz.create_agency_comparison(summary)
        fig1.write_html("test_agency_chart.html")
        print("   ✅ Agency chart saved to test_agency_chart.html")
        
        fig2 = chart_viz.create_status_donut(summary)
        fig2.write_html("test_status_chart.html")
        print("   ✅ Status chart saved to test_status_chart.html")
        
        fig3 = chart_viz.create_top_carparks_chart(df)
        fig3.write_html("test_top_carparks.html")
        print("   ✅ Top carparks chart saved to test_top_carparks.html")
        
        print("\n✅ All visualizations created successfully!")
        print("   Open the HTML files in your browser to see them!")
    else:
        print("❌ Failed to fetch data")