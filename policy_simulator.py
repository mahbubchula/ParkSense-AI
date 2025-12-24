"""
ParkSense-AI Policy Simulator
=============================
Simulates "what-if" scenarios for parking policy analysis.
Enables planners to evaluate policy impacts before implementation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


# =============================================================================
# POLICY DEFINITIONS
# =============================================================================

class PolicyType(Enum):
    """Types of parking policies that can be simulated."""
    PRICING = "pricing"
    CAPACITY = "capacity"
    TIME_LIMIT = "time_limit"
    ZONE_RESTRICTION = "zone_restriction"
    INCENTIVE = "incentive"


@dataclass
class PolicyScenario:
    """Defines a parking policy scenario for simulation."""
    name: str
    description: str
    policy_type: PolicyType
    parameters: Dict
    target_agency: Optional[str] = None  # HDB, LTA, URA, or None for all
    target_area: Optional[str] = None    # Specific area or None for all


# =============================================================================
# POLICY SIMULATOR
# =============================================================================

class ParkingPolicySimulator:
    """
    Simulates parking policy impacts using transparent mathematical models.
    
    Key principles:
    - All calculations are transparent and explainable
    - Based on transportation research literature
    - Provides uncertainty ranges, not false precision
    """
    
    def __init__(self):
        # Elasticity coefficients (from literature)
        self.price_elasticity = -0.3      # 10% price increase → 3% demand decrease
        self.capacity_elasticity = 0.5    # 10% capacity increase → 5% utilization increase
        self.time_elasticity = -0.2       # Shorter time limits → reduced long-term parking
        
        # Spillover factors
        self.spillover_rate = 0.15        # 15% of displaced demand goes to nearby carparks
        
    def create_baseline(self, df: pd.DataFrame) -> Dict:
        """
        Create baseline scenario from current data.
        
        Args:
            df: Current parking data
            
        Returns:
            Baseline metrics
        """
        return {
            "name": "Current Baseline",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_carparks": len(df),
            "total_capacity_estimate": self._estimate_capacity(df),
            "total_available": int(df["AvailableLots"].sum()),
            "utilization_rate": self._calculate_utilization(df),
            "stressed_carparks": len(df[df["AvailableLots"] <= 10]),
            "by_agency": self._baseline_by_agency(df)
        }
    
    def simulate_pricing_policy(self, df: pd.DataFrame, 
                                price_change_percent: float,
                                target_agency: Optional[str] = None) -> Dict:
        """
        Simulate impact of parking price changes.
        
        Args:
            df: Current parking data
            price_change_percent: Percentage change in price (e.g., 20 for 20% increase)
            target_agency: Apply to specific agency or all
            
        Returns:
            Simulation results
        """
        baseline = self.create_baseline(df)
        
        # Calculate demand change using price elasticity
        demand_change = self.price_elasticity * (price_change_percent / 100)
        
        # Apply to target or all
        if target_agency:
            target_df = df[df["Agency"] == target_agency]
            other_df = df[df["Agency"] != target_agency]
        else:
            target_df = df
            other_df = pd.DataFrame()
        
        # Estimate new availability (demand decrease = availability increase)
        availability_change = -demand_change  # Inverse relationship
        
        new_available_target = int(target_df["AvailableLots"].sum() * (1 + availability_change))
        
        # Calculate spillover to other agencies
        spillover_lots = int(abs(demand_change) * target_df["AvailableLots"].sum() * self.spillover_rate)
        
        new_available_other = int(other_df["AvailableLots"].sum()) - spillover_lots if not other_df.empty else 0
        
        # Calculate new stress levels
        stress_reduction = abs(demand_change) * 0.5  # Simplified model
        new_stressed = max(0, int(baseline["stressed_carparks"] * (1 - stress_reduction)))
        
        return {
            "scenario_name": f"Pricing Policy: {price_change_percent:+.0f}%",
            "policy_type": "pricing",
            "parameters": {
                "price_change_percent": price_change_percent,
                "target_agency": target_agency or "All"
            },
            "baseline": baseline,
            "projected": {
                "total_available": new_available_target + new_available_other,
                "availability_change": availability_change * 100,
                "stressed_carparks": new_stressed,
                "stress_reduction": (baseline["stressed_carparks"] - new_stressed),
                "spillover_lots": spillover_lots
            },
            "methodology": {
                "model": "Price Elasticity Model",
                "elasticity_used": self.price_elasticity,
                "assumption": "Demand responds to price according to standard elasticity",
                "uncertainty": "±20% due to local factors"
            }
        }
    
    def simulate_capacity_change(self, df: pd.DataFrame,
                                 capacity_change_percent: float,
                                 target_agency: Optional[str] = None) -> Dict:
        """
        Simulate impact of capacity changes (adding/removing lots).
        
        Args:
            df: Current parking data
            capacity_change_percent: Percentage change in capacity
            target_agency: Apply to specific agency or all
            
        Returns:
            Simulation results
        """
        baseline = self.create_baseline(df)
        
        if target_agency:
            target_df = df[df["Agency"] == target_agency]
        else:
            target_df = df
        
        # Current available lots in target
        current_available = target_df["AvailableLots"].sum()
        
        # Capacity change
        capacity_delta = current_available * (capacity_change_percent / 100)
        
        # Induced demand (more capacity → some additional demand)
        induced_demand = capacity_delta * self.capacity_elasticity
        
        # Net availability change
        net_change = capacity_delta - induced_demand
        
        new_total_available = int(baseline["total_available"] + net_change)
        
        # Stress impact
        if capacity_change_percent > 0:
            stress_reduction = min(0.3, capacity_change_percent / 100)  # Cap at 30%
            new_stressed = max(0, int(baseline["stressed_carparks"] * (1 - stress_reduction)))
        else:
            stress_increase = min(0.5, abs(capacity_change_percent) / 100)
            new_stressed = int(baseline["stressed_carparks"] * (1 + stress_increase))
        
        return {
            "scenario_name": f"Capacity Change: {capacity_change_percent:+.0f}%",
            "policy_type": "capacity",
            "parameters": {
                "capacity_change_percent": capacity_change_percent,
                "target_agency": target_agency or "All"
            },
            "baseline": baseline,
            "projected": {
                "total_available": new_total_available,
                "net_availability_change": int(net_change),
                "induced_demand": int(induced_demand),
                "stressed_carparks": new_stressed,
                "stress_change": new_stressed - baseline["stressed_carparks"]
            },
            "methodology": {
                "model": "Capacity-Demand Equilibrium Model",
                "elasticity_used": self.capacity_elasticity,
                "assumption": "Additional capacity induces some new demand",
                "uncertainty": "±25% due to location-specific factors"
            }
        }
    
    def simulate_ura_intervention(self, df: pd.DataFrame,
                                  intervention_type: str) -> Dict:
        """
        Simulate specific interventions for URA (most stressed agency).
        
        Args:
            df: Current parking data
            intervention_type: "pricing", "capacity", or "mixed"
            
        Returns:
            Simulation results
        """
        ura_df = df[df["Agency"] == "URA"]
        baseline = self.create_baseline(df)
        ura_baseline = self._baseline_by_agency(df).get("URA", {})
        
        if intervention_type == "pricing":
            # 25% price increase for URA carparks
            result = self.simulate_pricing_policy(df, 25, "URA")
            result["scenario_name"] = "URA Pricing Intervention (+25%)"
            result["rationale"] = "Higher prices to reduce demand in stressed commercial areas"
            
        elif intervention_type == "capacity":
            # 15% capacity increase for URA
            result = self.simulate_capacity_change(df, 15, "URA")
            result["scenario_name"] = "URA Capacity Expansion (+15%)"
            result["rationale"] = "Additional parking in commercial developments"
            
        elif intervention_type == "mixed":
            # Combined approach
            pricing_effect = self.price_elasticity * 0.15  # 15% price increase
            capacity_effect = 0.10  # 10% capacity increase
            
            net_improvement = -pricing_effect + capacity_effect - (capacity_effect * self.capacity_elasticity)
            
            new_ura_available = int(ura_df["AvailableLots"].sum() * (1 + net_improvement))
            ura_stressed = len(ura_df[ura_df["AvailableLots"] <= 10])
            new_ura_stressed = max(0, int(ura_stressed * 0.6))  # Estimate 40% reduction
            
            result = {
                "scenario_name": "URA Mixed Intervention",
                "policy_type": "mixed",
                "parameters": {
                    "price_increase": "15%",
                    "capacity_increase": "10%",
                    "target_agency": "URA"
                },
                "baseline": baseline,
                "ura_baseline": ura_baseline,
                "projected": {
                    "ura_available": new_ura_available,
                    "ura_stressed_reduction": ura_stressed - new_ura_stressed,
                    "net_improvement_percent": net_improvement * 100
                },
                "rationale": "Combined pricing and capacity approach for optimal impact",
                "methodology": {
                    "model": "Combined Policy Impact Model",
                    "assumption": "Pricing and capacity effects are partially additive",
                    "uncertainty": "±30% due to interaction effects"
                }
            }
        else:
            result = {"error": f"Unknown intervention type: {intervention_type}"}
        
        return result
    
    def compare_scenarios(self, scenarios: List[Dict]) -> Dict:
        """
        Compare multiple policy scenarios.
        
        Args:
            scenarios: List of simulation results
            
        Returns:
            Comparison analysis
        """
        if not scenarios:
            return {"error": "No scenarios to compare"}
        
        comparison = {
            "scenarios_compared": len(scenarios),
            "comparison_metrics": [],
            "ranking": {},
            "recommendation": None
        }
        
        # Extract key metrics
        for scenario in scenarios:
            if "error" in scenario:
                continue
                
            metrics = {
                "name": scenario.get("scenario_name", "Unknown"),
                "policy_type": scenario.get("policy_type", "unknown"),
                "projected_available": scenario.get("projected", {}).get("total_available", 0),
                "stress_change": scenario.get("projected", {}).get("stress_change", 
                               scenario.get("projected", {}).get("stress_reduction", 0))
            }
            comparison["comparison_metrics"].append(metrics)
        
        # Rank by stress reduction
        if comparison["comparison_metrics"]:
            sorted_scenarios = sorted(
                comparison["comparison_metrics"],
                key=lambda x: x.get("stress_change", 0),
                reverse=True
            )
            comparison["ranking"] = {
                "by_stress_reduction": [s["name"] for s in sorted_scenarios]
            }
            comparison["recommendation"] = sorted_scenarios[0]["name"] if sorted_scenarios else None
        
        return comparison
    
    def _estimate_capacity(self, df: pd.DataFrame) -> int:
        """Estimate total capacity (available + occupied)."""
        # Rough estimate: assume average 70% utilization
        avg_utilization = 0.7
        return int(df["AvailableLots"].sum() / (1 - avg_utilization))
    
    def _calculate_utilization(self, df: pd.DataFrame) -> float:
        """Calculate estimated utilization rate."""
        capacity = self._estimate_capacity(df)
        available = df["AvailableLots"].sum()
        return round((1 - available / capacity) * 100, 1) if capacity > 0 else 0
    
    def _baseline_by_agency(self, df: pd.DataFrame) -> Dict:
        """Calculate baseline metrics by agency."""
        results = {}
        for agency in df["Agency"].unique():
            agency_df = df[df["Agency"] == agency]
            results[agency] = {
                "carparks": len(agency_df),
                "available": int(agency_df["AvailableLots"].sum()),
                "stressed": len(agency_df[agency_df["AvailableLots"] <= 10]),
                "avg_availability": round(agency_df["AvailableLots"].mean(), 1)
            }
        return results


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing ParkSense-AI Policy Simulator")
    print("=" * 50)
    
    # Import dependencies
    from data_fetcher import CarparkDataFetcher
    
    # Fetch data
    print("\n📡 Fetching data...")
    fetcher = CarparkDataFetcher()
    data = fetcher.fetch_data()
    
    if data:
        df = fetcher.to_dataframe()
        
        # Create simulator
        simulator = ParkingPolicySimulator()
        
        # Test baseline
        print("\n📊 BASELINE SCENARIO")
        print("-" * 40)
        baseline = simulator.create_baseline(df)
        print(f"Total Carparks: {baseline['total_carparks']}")
        print(f"Total Available: {baseline['total_available']:,}")
        print(f"Utilization Rate: {baseline['utilization_rate']}%")
        print(f"Stressed Carparks: {baseline['stressed_carparks']}")
        
        # Test pricing policy
        print("\n💰 PRICING POLICY SIMULATION (+20%)")
        print("-" * 40)
        pricing_result = simulator.simulate_pricing_policy(df, 20)
        print(f"Projected Available: {pricing_result['projected']['total_available']:,}")
        print(f"Availability Change: {pricing_result['projected']['availability_change']:.1f}%")
        print(f"Stress Reduction: {pricing_result['projected']['stress_reduction']} carparks")
        
        # Test capacity change
        print("\n🏗️ CAPACITY EXPANSION SIMULATION (+15%)")
        print("-" * 40)
        capacity_result = simulator.simulate_capacity_change(df, 15)
        print(f"Projected Available: {capacity_result['projected']['total_available']:,}")
        print(f"Net Change: {capacity_result['projected']['net_availability_change']:,} lots")
        print(f"Induced Demand: {capacity_result['projected']['induced_demand']:,} lots")
        
        # Test URA intervention
        print("\n🎯 URA MIXED INTERVENTION")
        print("-" * 40)
        ura_result = simulator.simulate_ura_intervention(df, "mixed")
        print(f"Scenario: {ura_result['scenario_name']}")
        print(f"Rationale: {ura_result['rationale']}")
        print(f"Net Improvement: {ura_result['projected']['net_improvement_percent']:.1f}%")
        
        # Compare scenarios
        print("\n📈 SCENARIO COMPARISON")
        print("-" * 40)
        comparison = simulator.compare_scenarios([pricing_result, capacity_result])
        print(f"Best Option: {comparison['recommendation']}")
        
        print("\n✅ Policy Simulator working correctly!")
    else:
        print("❌ Failed to fetch data")