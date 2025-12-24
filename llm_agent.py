"""
ParkSense-AI LLM Agent
======================
Uses Groq LLM to generate intelligent explanations,
insights, and recommendations from parking data analysis.
"""

import json
from typing import Dict, List, Optional
from groq import Groq
from config import GROQ_API_KEY, LLM_MODELS


# =============================================================================
# LLM AGENT
# =============================================================================

class ParkingLLMAgent:
    """
    LLM-powered agent for generating natural language explanations
    and insights from parking data analysis.
    
    Uses Groq API with Llama models (free, open-source).
    """
    
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found. Check your .env file.")
        
        self.client = Groq(api_key=GROQ_API_KEY)
        self.main_model = LLM_MODELS["main"]
        self.fast_model = LLM_MODELS["fast"]
        
        # System prompt for parking analysis
        self.system_prompt = """You are ParkSense-AI, an intelligent parking analysis assistant for Singapore.

Your role is to:
1. Analyze real-time parking data from HDB, LTA, and URA carparks
2. Explain parking patterns in clear, understandable language
3. Identify stress points and their likely causes
4. Provide actionable recommendations for drivers and planners
5. Compare performance across agencies objectively

Key context:
- HDB: Public housing carparks (residential areas)
- LTA: Transport hub carparks (Orchard, Marina, Harbourfront, Jurong Lake District)
- URA: Commercial/private development carparks

Always be:
- Clear and concise
- Data-driven (cite specific numbers)
- Helpful with practical recommendations
- Objective in comparisons

Format your responses with clear sections using markdown headers."""
    
    def generate_overall_analysis(self, analysis_report: Dict) -> str:
        """
        Generate comprehensive analysis explanation.
        
        Args:
            analysis_report: Complete analysis from ParkingAnalyzer
            
        Returns:
            Natural language analysis
        """
        prompt = f"""Based on the following real-time parking data analysis for Singapore, provide a comprehensive overview:

## Current Data Summary
- Timestamp: {analysis_report.get('timestamp', 'N/A')}
- Total Carparks: {analysis_report['overall_health']['total_carparks']}
- Total Available Lots: {analysis_report['overall_health']['total_available_lots']:,}
- System Health Score: {analysis_report['overall_health']['health_score']}%
- Status: {analysis_report['overall_health']['status']}

## Agency Breakdown
{self._format_agency_stats(analysis_report['agency_analysis'])}

## Stress Points
- Stressed Carparks: {analysis_report['overall_health']['stressed_carparks']}
- Stress Percentage: {analysis_report['overall_health']['stress_percentage']}%

## Spatial Clusters
{len(analysis_report.get('spatial_clusters', []))} stress clusters detected

Please provide:
1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (bullet points)
3. **Agency Performance Analysis**
4. **Areas of Concern**
5. **Recommendations**

Keep the response concise but insightful."""

        return self._call_llm(prompt, use_main_model=True)
    
    def explain_stress_points(self, stress_points: List[Dict], 
                              agency_stats: Dict) -> str:
        """
        Generate explanation for stressed carparks.
        
        Args:
            stress_points: List of stressed carpark data
            agency_stats: Agency-level statistics
            
        Returns:
            Natural language explanation
        """
        # Summarize stress points
        stress_summary = []
        for point in stress_points[:10]:  # Top 10
            stress_summary.append(
                f"- {point['Development']} ({point['Agency']}): {point['AvailableLots']} lots"
            )
        
        prompt = f"""Analyze these stressed carparks in Singapore and explain the likely causes:

## Most Stressed Carparks (Lowest Availability)
{chr(10).join(stress_summary)}

## Agency Context
{self._format_agency_stats(agency_stats)}

Please provide:
1. **Pattern Analysis**: What patterns do you see in the stressed carparks?
2. **Likely Causes**: Why might these specific locations be stressed?
3. **Agency Insights**: Which agency shows most stress and why?
4. **Recommendations**: What can drivers do? What can planners consider?

Be specific and practical in your analysis."""

        return self._call_llm(prompt, use_main_model=True)
    
    def compare_agencies(self, agency_stats: Dict, comparison: Dict) -> str:
        """
        Generate agency comparison analysis.
        
        Args:
            agency_stats: Detailed agency statistics
            comparison: Comparison insights
            
        Returns:
            Natural language comparison
        """
        prompt = f"""Compare the parking performance of Singapore's three carpark agencies:

## Agency Statistics
{self._format_agency_stats(agency_stats)}

## Comparison Summary
- Best Performer: {comparison.get('best_performer', 'N/A')}
- Needs Attention: {comparison.get('worst_performer', 'N/A')}

## Auto-Generated Insights
{chr(10).join(comparison.get('insights', ['No insights available']))}

Please provide:
1. **Performance Ranking** with justification
2. **Strengths and Weaknesses** for each agency
3. **Key Differences** in availability patterns
4. **Possible Explanations** for performance differences
5. **Policy Recommendations** for improvement

Be balanced and objective in your analysis."""

        return self._call_llm(prompt, use_main_model=True)
    
    def generate_driver_recommendations(self, analysis_report: Dict,
                                        user_location: Optional[str] = None) -> str:
        """
        Generate practical recommendations for drivers.
        
        Args:
            analysis_report: Complete analysis data
            user_location: Optional user location/area
            
        Returns:
            Driver-friendly recommendations
        """
        high_avail = analysis_report.get('high_availability', [])[:5]
        high_avail_text = []
        for cp in high_avail:
            high_avail_text.append(
                f"- {cp['Development']} ({cp['Agency']}): {cp['AvailableLots']} lots available"
            )
        
        prompt = f"""Based on current real-time parking data, provide recommendations for drivers in Singapore:

## Current System Status
- Overall Health: {analysis_report['overall_health']['health_score']}% ({analysis_report['overall_health']['status']})
- Total Available Lots: {analysis_report['overall_health']['total_available_lots']:,}

## Top Available Carparks Right Now
{chr(10).join(high_avail_text)}

## Stressed Areas
- {analysis_report['overall_health']['stressed_carparks']} carparks with limited availability
- {len(analysis_report.get('spatial_clusters', []))} stress clusters detected

{f"User is looking for parking near: {user_location}" if user_location else ""}

Please provide:
1. **Quick Summary** (current parking situation in 1-2 sentences)
2. **Best Bets** (where to find parking easily)
3. **Areas to Avoid** (where parking is difficult)
4. **Pro Tips** (timing, alternatives, strategies)

Keep it practical and driver-friendly!"""

        return self._call_llm(prompt, use_main_model=False)  # Fast model for quick tips
    
    def analyze_area(self, area_name: str, area_data: Dict, 
                     df_subset: Optional[List[Dict]] = None) -> str:
        """
        Generate analysis for specific area.
        
        Args:
            area_name: Name of area (Orchard, Marina, etc.)
            area_data: Statistics for the area
            df_subset: Optional list of carparks in area
            
        Returns:
            Area-specific analysis
        """
        carparks_text = ""
        if df_subset:
            carparks_text = "Carparks in this area:\n"
            for cp in df_subset[:10]:
                carparks_text += f"- {cp.get('Development', 'Unknown')}: {cp.get('AvailableLots', 0)} lots\n"
        
        prompt = f"""Analyze the parking situation in {area_name}, Singapore:

## Area Statistics
- Total Carparks: {area_data.get('total_carparks', 'N/A')}
- Total Available Lots: {area_data.get('total_lots', 'N/A'):,}
- Average Availability: {area_data.get('average_availability', 'N/A')}

{carparks_text}

Please provide:
1. **Area Overview** (what kind of area is this?)
2. **Current Status** (good/moderate/stressed?)
3. **Typical Patterns** (when is parking easier/harder?)
4. **Recommendations** for visitors to this area"""

        return self._call_llm(prompt, use_main_model=False)
    
    def generate_policy_insight(self, analysis_report: Dict, 
                                policy_question: str) -> str:
        """
        Generate policy-level insights for planners.
        
        Args:
            analysis_report: Complete analysis data
            policy_question: Specific policy question
            
        Returns:
            Policy analysis and recommendations
        """
        prompt = f"""As a parking policy analyst, address this question:

**Policy Question**: {policy_question}

## Current Data Context
- Total Carparks: {analysis_report['overall_health']['total_carparks']}
- System Health: {analysis_report['overall_health']['health_score']}%
- Stressed Carparks: {analysis_report['overall_health']['stressed_carparks']} ({analysis_report['overall_health']['stress_percentage']}%)

## Agency Performance
{self._format_agency_stats(analysis_report['agency_analysis'])}

## Stress Clusters
{len(analysis_report.get('spatial_clusters', []))} high-density stress areas detected

Please provide:
1. **Direct Answer** to the policy question
2. **Data Evidence** supporting your answer
3. **Potential Implications** of current patterns
4. **Policy Recommendations** with rationale
5. **Monitoring Suggestions** for tracking improvement

Be analytical and evidence-based."""

        return self._call_llm(prompt, use_main_model=True)
    
    def _format_agency_stats(self, agency_stats: Dict) -> str:
        """Format agency statistics for prompt."""
        lines = []
        for agency, stats in agency_stats.items():
            lines.append(
                f"**{agency}**: {stats['total_carparks']} carparks, "
                f"{stats['total_lots']:,} lots, "
                f"Avg {stats['average_availability']} lots/carpark, "
                f"Health {stats['health_score']}%, "
                f"Stressed {stats['stress_percentage']}%"
            )
        return "\n".join(lines)
    
    def _call_llm(self, prompt: str, use_main_model: bool = True) -> str:
        """
        Call Groq LLM API.
        
        Args:
            prompt: User prompt
            use_main_model: Use main (70B) or fast (8B) model
            
        Returns:
            LLM response text
        """
        model = self.main_model if use_main_model else self.fast_model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error generating analysis: {str(e)}"


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("Testing ParkSense-AI LLM Agent")
    print("=" * 50)
    
    # Import dependencies
    from data_fetcher import CarparkDataFetcher
    from analyzer import ParkingAnalyzer
    
    # Fetch and analyze data
    print("\n📡 Fetching data...")
    fetcher = CarparkDataFetcher()
    data = fetcher.fetch_data()
    
    if data:
        df = fetcher.to_dataframe()
        
        print("🔍 Analyzing data...")
        analyzer = ParkingAnalyzer()
        report = analyzer.generate_analysis_report(df)
        
        print("🤖 Initializing LLM Agent...")
        agent = ParkingLLMAgent()
        
        # Test overall analysis
        print("\n" + "=" * 50)
        print("📊 OVERALL ANALYSIS")
        print("=" * 50)
        analysis = agent.generate_overall_analysis(report)
        print(analysis)
        
        # Test driver recommendations
        print("\n" + "=" * 50)
        print("🚗 DRIVER RECOMMENDATIONS")
        print("=" * 50)
        recommendations = agent.generate_driver_recommendations(report)
        print(recommendations)
        
        print("\n✅ LLM Agent working correctly!")
    else:
        print("❌ Failed to fetch data")