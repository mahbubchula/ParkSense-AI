"""
ParkSense-AI Data Fetcher
=========================
Connects to LTA DataMall API and retrieves real-time carpark availability.
Handles HDB, LTA, and URA carpark data.
"""

import requests
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from config import LTA_API_KEY, CARPARK_ENDPOINT, COLORS


# =============================================================================
# LTA API CLIENT
# =============================================================================

class CarparkDataFetcher:
    """
    Fetches real-time carpark availability from LTA DataMall API.
    
    Data includes:
    - HDB: Public housing carparks
    - LTA: Transport hub carparks (Orchard, Marina, Harbourfront, Jurong Lake)
    - URA: Commercial/private development carparks
    """
    
    def __init__(self):
        self.api_key = LTA_API_KEY
        self.endpoint = CARPARK_ENDPOINT
        self.headers = {
            "AccountKey": self.api_key,
            "accept": "application/json"
        }
        self.last_fetch_time = None
        self.raw_data = None
        
    def fetch_data(self) -> Optional[List[Dict]]:
        """
        Fetch carpark availability data from LTA API.
        
        Returns:
            List of carpark records or None if error
        """
        all_records = []
        skip = 0
        
        print("🚗 Fetching carpark data from LTA API...")
        
        try:
            while True:
                # LTA API uses pagination with $skip parameter
                url = f"{self.endpoint}?$skip={skip}"
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"❌ API Error: Status {response.status_code}")
                    print(f"   Response: {response.text}")
                    return None
                
                data = response.json()
                records = data.get("value", [])
                
                if not records:
                    break
                    
                all_records.extend(records)
                skip += 500  # LTA API returns max 500 per request
                
                print(f"   Retrieved {len(all_records)} records...")
                
            self.raw_data = all_records
            self.last_fetch_time = datetime.now()
            
            print(f"✅ Successfully fetched {len(all_records)} carparks!")
            return all_records
            
        except requests.exceptions.Timeout:
            print("❌ API Error: Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return None
    
    def to_dataframe(self, data: Optional[List[Dict]] = None) -> pd.DataFrame:
        """
        Convert raw API data to pandas DataFrame with processed columns.
        
        Returns:
            DataFrame with carpark data
        """
        if data is None:
            data = self.raw_data
            
        if not data:
            print("⚠️ No data available. Call fetch_data() first.")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Parse Location into Latitude and Longitude
        if "Location" in df.columns:
            df["Latitude"] = df["Location"].apply(self._parse_latitude)
            df["Longitude"] = df["Location"].apply(self._parse_longitude)
        
        # Convert AvailableLots to numeric
        if "AvailableLots" in df.columns:
            df["AvailableLots"] = pd.to_numeric(df["AvailableLots"], errors="coerce").fillna(0).astype(int)
        
        # Add agency color for visualization
        df["AgencyColor"] = df["Agency"].map(COLORS)
        
        # Add availability status
        df["Status"] = df["AvailableLots"].apply(self._get_availability_status)
        df["StatusColor"] = df["Status"].map({
            "Available": COLORS["available"],
            "Moderate": COLORS["moderate"],
            "Limited": COLORS["limited"]
        })
        
        # Add fetch timestamp
        df["FetchTime"] = self.last_fetch_time
        
        return df
    
    def _parse_latitude(self, location: str) -> Optional[float]:
        """Extract latitude from location string."""
        try:
            if location and " " in location:
                return float(location.split(" ")[0])
            return None
        except:
            return None
    
    def _parse_longitude(self, location: str) -> Optional[float]:
        """Extract longitude from location string."""
        try:
            if location and " " in location:
                return float(location.split(" ")[1])
            return None
        except:
            return None
    
    def _get_availability_status(self, lots: int) -> str:
        """Categorize availability status."""
        if lots > 50:
            return "Available"
        elif lots > 10:
            return "Moderate"
        else:
            return "Limited"
    
    def get_summary(self, df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Generate summary statistics from carpark data.
        
        Returns:
            Dictionary with summary stats
        """
        if df is None:
            df = self.to_dataframe()
            
        if df.empty:
            return {}
        
        summary = {
            "total_carparks": len(df),
            "total_available_lots": int(df["AvailableLots"].sum()),
            "by_agency": {},
            "by_lot_type": {},
            "by_status": {},
            "fetch_time": self.last_fetch_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_fetch_time else None
        }
        
        # By Agency
        for agency in df["Agency"].unique():
            agency_df = df[df["Agency"] == agency]
            summary["by_agency"][agency] = {
                "carparks": len(agency_df),
                "available_lots": int(agency_df["AvailableLots"].sum()),
                "avg_availability": round(agency_df["AvailableLots"].mean(), 1)
            }
        
        # By Lot Type
        for lot_type in df["LotType"].unique():
            lot_df = df[df["LotType"] == lot_type]
            summary["by_lot_type"][lot_type] = {
                "carparks": len(lot_df),
                "available_lots": int(lot_df["AvailableLots"].sum())
            }
        
        # By Status
        for status in ["Available", "Moderate", "Limited"]:
            status_df = df[df["Status"] == status]
            summary["by_status"][status] = len(status_df)
        
        return summary
    
    def get_agency_data(self, agency: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Filter data by agency (HDB, LTA, or URA)."""
        if df is None:
            df = self.to_dataframe()
        return df[df["Agency"] == agency]
    
    def get_area_data(self, area: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Filter data by area (for LTA carparks)."""
        if df is None:
            df = self.to_dataframe()
        return df[df["Area"] == area]


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing ParkSense-AI Data Fetcher")
    print("=" * 50)
    
    # Create fetcher
    fetcher = CarparkDataFetcher()
    
    # Fetch data
    data = fetcher.fetch_data()
    
    if data:
        # Convert to DataFrame
        df = fetcher.to_dataframe()
        print(f"\n📊 DataFrame Shape: {df.shape}")
        print(f"\n📋 Columns: {list(df.columns)}")
        
        # Show sample
        print(f"\n🔍 Sample Data (first 5 rows):")
        print(df[["CarParkID", "Development", "Agency", "LotType", "AvailableLots", "Status"]].head())
        
        # Show summary
        print(f"\n📈 Summary Statistics:")
        summary = fetcher.get_summary(df)
        print(f"   Total Carparks: {summary['total_carparks']}")
        print(f"   Total Available Lots: {summary['total_available_lots']:,}")
        print(f"\n   By Agency:")
        for agency, stats in summary["by_agency"].items():
            print(f"      {agency}: {stats['carparks']} carparks, {stats['available_lots']:,} lots")
        
        print(f"\n   By Status:")
        for status, count in summary["by_status"].items():
            print(f"      {status}: {count} carparks")
        
        print("\n✅ Data fetcher working correctly!")
    else:
        print("\n❌ Failed to fetch data. Check your API key.")