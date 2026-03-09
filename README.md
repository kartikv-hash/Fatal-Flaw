# Fatal-Flaw
A fatal flaw platform. 
# ⚡ SiteIQ — Renewable Energy Siting Intelligence Platform

A full-featured, interactive Streamlit application that helps renewable energy developers evaluate land parcels across the United States by combining environmental constraints, soil analysis, transmission grid proximity, wholesale electricity pricing, congestion analytics, and community sentiment scoring.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 What It Does

SiteIQ answers the key questions every renewable energy developer faces:

- **Is this land developable?** — Soil analysis, flood zone detection, wetland coverage
- **How far is the grid?** — Transmission line distance, voltage, substation proximity
- **What will the power sell for?** — Hub/node LMP pricing, basis risk analysis
- **What's the congestion risk?** — Historical curtailment data, revenue volatility
- **Will the community support it?** — NLP-derived sentiment scoring, opposition risk

---

## 🖥️ Features

### 🗺️ Interactive GIS Map
- Dark-themed Folium map with 8 sample parcels across the US
- Toggle layers: transmission lines, substations, wetland zones, flood zones
- Click markers for instant parcel summaries
- Color-coded by site score (green ≥ 80, amber 60–79, red < 60)

### 🔍 Developer Query Engine
- Filter parcels by acreage, transmission distance, node price, wetland coverage, flood zone, and site score
- Real-time results with ranked output

### 📊 Site Deep Dive
- Radar chart + horizontal bar chart for score factor breakdown
- Full environmental, soil, grid, pricing, and sentiment analysis
- Per-factor weighted scoring with adjustable weights

### ⚖️ Side-by-Side Comparison
- Compare any two sites with overlaid radar charts
- Metric-by-metric table showing which site wins each category

### 💲 Market Analytics
- Synthetic 12-month LMP price history (area chart)
- Monthly congestion event tracking (bar chart)
- Curtailment rate trends (line chart)

### 📄 Export & Reporting
- Full-text feasibility report preview and download (.txt)
- All-sites CSV export
- GeoJSON export for integration with external GIS tools

### ⚖️ Adjustable Scoring Weights
- Sidebar sliders for all 7 scoring factors
- Real-time score recalculation across all parcels
- Weight validation (must total 100%)

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/siteiq-platform.git
cd siteiq-platform
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 📁 Project Structure

```
siteiq-platform/
├── app.py               # Main Streamlit application
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── LICENSE              # MIT License
└── .streamlit/
    └── config.toml      # Streamlit theme configuration
```

---

## 🎨 Theme Configuration

Create `.streamlit/config.toml` for the dark theme:

```toml
[theme]
primaryColor = "#6366f1"
backgroundColor = "#0a0e1a"
secondaryBackgroundColor = "#1e293b"
textColor = "#e2e8f0"
font = "sans serif"
```

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Streamlit   │────▶│  Scoring     │────▶│  Folium Map    │
│  Frontend    │     │  Engine      │     │  Renderer      │
└──────┬──────┘     └──────┬───────┘     └────────────────┘
       │                   │
       ▼                   ▼
┌──────────────┐   ┌──────────────────┐
│  Plotly       │   │  Data Layer      │
│  Charts       │   │  (Parcels, LMP,  │
│               │   │   Congestion)    │
└──────────────┘   └──────────────────┘
```

### Scoring Engine

Multi-factor weighted scoring with 7 dimensions:

| Factor                 | Default Weight |
|------------------------|---------------|
| Transmission Proximity | 25%           |
| Node Pricing           | 15%           |
| Wetland Risk           | 15%           |
| Soil Suitability       | 15%           |
| Flood Risk             | 10%           |
| Community Sentiment    | 10%           |
| Land Cost              | 10%           |

Each factor is normalized to 0–100, then combined via weighted average.

---

## 🔌 Data Sources (Production Roadmap)

| Dataset               | Source                              |
|-----------------------|-------------------------------------|
| Wetlands (NWI)        | US Fish & Wildlife Service          |
| Floodplains (NFHL)    | FEMA                                |
| Soils (WSS)           | NRCS Web Soil Survey                |
| Transmission Lines     | OpenInfraMap / HIFLD                |
| LMP Pricing           | ERCOT, PJM, MISO, CAISO, SPP, NYISO|
| Parcel Data           | County GIS / State Land Records     |
| Community Sentiment   | News APIs + NLP pipeline            |

---

## 🛣️ Roadmap

- [ ] **Live data integration** — Connect to real NWI, FEMA, and NRCS APIs
- [ ] **Real-time LMP** — Pull live pricing from ISO APIs
- [ ] **User authentication** — Login, saved searches, project portfolios
- [ ] **AI recommendations** — ML model for optimal county/site suggestions
- [ ] **PDF report generation** — Formatted reports with charts
- [ ] **Parcel drawing tool** — Draw custom boundaries on the map
- [ ] **Bulk analysis** — Upload parcel CSVs for batch scoring
- [ ] **Deployment** — Streamlit Cloud / AWS / GCP hosting

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a PR.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) — App framework
- [Folium](https://python-visualization.github.io/folium/) — Interactive maps
- [Plotly](https://plotly.com/python/) — Charts and visualizations
- [USGS](https://www.usgs.gov/), [FEMA](https://www.fema.gov/), [NRCS](https://www.nrcs.usda.gov/) — Federal geospatial datasets

---

<p align="center">Built with ⚡ by SiteIQ</p>
