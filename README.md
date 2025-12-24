# 🅿️ ParkSense-AI

**Intelligent Real-Time Parking Analysis System for Singapore**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://parksense-ai.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Overview

ParkSense-AI is a comprehensive parking intelligence platform that provides real-time analysis of **2,500+ carparks** across Singapore. It integrates data from three major agencies (HDB, LTA, URA) and uses **LLM-powered AI** to generate actionable insights for drivers, urban planners, and researchers.

![Dashboard Preview]([https://via.placeholder.com/800x400?text=ParkSense-AI+Dashboard](https://parksenseai.streamlit.app/))

---

## ✨ Features

### 🏠 Real-Time Dashboard
- Live parking availability across Singapore
- System health monitoring
- Agency performance comparison
- Interactive charts and metrics

### 🗺️ Interactive Maps
- Color-coded markers by agency (HDB/LTA/URA)
- Status-based visualization (Available/Moderate/Limited)
- Heatmap view for availability density
- Clustered markers for better performance

### 🔍 Search & Find
- Search carparks by name
- Advanced filtering (agency, status, availability)
- **Find Nearest Parking** to any location
- 15+ popular Singapore locations pre-configured

### 🔔 Alert System
- Real-time stress monitoring
- Critical, Warning, and Info alerts
- Agency-specific health tracking
- Automated anomaly detection

### 🤖 AI-Powered Insights
- Natural language analysis using **Llama 3.3 70B**
- Overall system assessment
- Stress point explanation
- Agency comparison
- Driver recommendations
- Custom policy questions

### 🎯 Policy Simulator
- **Pricing Policy** simulation
- **Capacity Change** simulation
- **URA Intervention** scenarios
- AI-generated policy analysis
- Transparent methodology

### 📄 Export Reports
- CSV data export
- Text summary reports
- JSON full export
- Publication-ready outputs

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit |
| **Maps** | Folium, Streamlit-Folium |
| **Charts** | Plotly |
| **Data** | Pandas, NumPy |
| **LLM** | Groq API (Llama 3.3 70B) |
| **Data Source** | LTA DataMall API |

---

## 📊 Data Sources

ParkSense-AI uses real-time data from:

| Agency | Description | Carparks |
|--------|-------------|----------|
| **HDB** | Public housing carparks | ~2,400 |
| **LTA** | Transport hub carparks (Orchard, Marina, etc.) | ~40 |
| **URA** | Commercial/private developments | ~150 |

**Update Frequency:** Every 1 minute

---

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- LTA DataMall API Key ([Get here](https://datamall.lta.gov.sg/))
- Groq API Key ([Get here](https://console.groq.com/))

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ParkSense-AI.git
cd ParkSense-AI
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file:
```env
LTA_API_KEY=your_lta_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

5. **Run the application**
```bash
streamlit run app.py
```

---

## 📁 Project Structure
```
ParkSense-AI/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration and settings
├── data_fetcher.py        # LTA API integration
├── analyzer.py            # Data analysis engine
├── visualizations.py      # Maps and charts
├── llm_agent.py           # AI/LLM integration
├── policy_simulator.py    # Policy simulation
├── features.py            # Advanced features
├── requirements.txt       # Dependencies
├── .env                   # API keys (not in repo)
├── .gitignore            # Git ignore file
└── README.md             # Documentation
```

---

## 🔬 Research Applications

ParkSense-AI is designed for academic research in:

- **Urban Mobility** - Parking pattern analysis
- **Smart Cities** - Real-time urban intelligence
- **Transportation Planning** - Policy impact assessment
- **Explainable AI** - LLM-based decision support

### Novel Contributions

1. **Multi-agency integration** - First tool combining HDB, LTA, URA real-time data
2. **LLM as reasoning layer** - AI explains patterns, not just predicts
3. **Transparent methodology** - All calculations are inspectable
4. **Policy simulation** - What-if analysis for planners

### Target Journals
- Transportation Research Part C
- IEEE Transactions on ITS
- Cities
- Sustainable Cities and Society

---

## 📈 Sample Insights
```
📊 System Health: 66.3% (Good)
🅿️ Total Carparks: 2,581
🚗 Available Lots: 465,000+

Agency Performance:
- LTA: 90% health (Best performer)
- HDB: 79% health (Stable)
- URA: 52% health (Needs attention)
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**MAHBUB**  
Chulalongkorn University  
Transportation Research

---

## 🙏 Acknowledgments

- [LTA DataMall](https://datamall.lta.gov.sg/) for real-time parking data
- [Groq](https://groq.com/) for fast LLM inference
- [Streamlit](https://streamlit.io/) for the web framework

---

## 📞 Contact

For questions or collaborations, please open an issue or contact via GitHub.

---

<p align="center">
  Made with ❤️ for Smart Urban Mobility
</p>
