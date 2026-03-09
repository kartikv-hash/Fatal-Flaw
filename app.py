import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import json
import io
from datetime import datetime, timedelta
import random

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="SiteIQ — Renewable Energy Siting Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    .block-container { padding-top: 1rem; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value { font-size: 2.2rem; font-weight: 900; }
    .metric-label { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
    .score-high { color: #22c55e; }
    .score-mid { color: #f59e0b; }
    .score-low { color: #ef4444; }
    .risk-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-low { background: #22c55e22; color: #22c55e; border: 1px solid #22c55e44; }
    .badge-med { background: #f59e0b22; color: #f59e0b; border: 1px solid #f59e0b44; }
    .badge-high { background: #ef444422; color: #ef4444; border: 1px solid #ef444444; }
    div[data-testid="stSidebar"] { background: #0f172a; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SEED DATA — PARCELS
# ──────────────────────────────────────────────
@st.cache_data
def load_parcel_data():
    parcels = [
        {
            "id": 1, "name": "Reeves County Solar Site", "state": "TX", "county": "Reeves",
            "lat": 31.39, "lon": -103.69, "acres": 482, "owner": "Bar-T Ranch LLC",
            "zoning": "Agricultural", "land_use": "Rangeland",
            "wetland_pct": 3, "wetland_type": "None significant",
            "flood_zone": "X (Minimal)", "flood_coverage": 2,
            "soil_score": 91, "drainage": "Well drained", "hydric": False,
            "erosion_factor": 0.15, "pile_suitability": "High", "bedrock_depth": 42,
            "trans_dist": 1.8, "voltage": "345 kV", "sub_dist": 1.2, "interconnection": "High",
            "hub": "ERCOT North Hub", "hub_lmp": 44, "node": "REEVES_345_WIND",
            "node_lmp": 41, "basis": -3, "congestion": "Low",
            "cong_freq": 6, "curtail_risk": "Low", "rev_risk": "Low",
            "sentiment": 0.32, "opp_risk": "Low",
            "issues": ["Minimal opposition", "Pro-development county"],
            "project_type": "Utility Solar", "permit_risk": "Low", "revenue_potential": "High",
            "land_cost_acre": 850,
        },
        {
            "id": 2, "name": "Kern County Solar Farm", "state": "CA", "county": "Kern",
            "lat": 35.15, "lon": -118.75, "acres": 310, "owner": "Sunland Holdings",
            "zoning": "Agricultural", "land_use": "Farmland",
            "wetland_pct": 8, "wetland_type": "Freshwater Emergent",
            "flood_zone": "AE", "flood_coverage": 10,
            "soil_score": 78, "drainage": "Moderately drained", "hydric": False,
            "erosion_factor": 0.28, "pile_suitability": "Moderate", "bedrock_depth": 28,
            "trans_dist": 4.1, "voltage": "230 kV", "sub_dist": 3.5, "interconnection": "Moderate",
            "hub": "CAISO SP15", "hub_lmp": 52, "node": "KERN_230_SOLAR",
            "node_lmp": 46, "basis": -6, "congestion": "Medium",
            "cong_freq": 14, "curtail_risk": "Moderate", "rev_risk": "Moderate",
            "sentiment": -0.18, "opp_risk": "Moderate",
            "issues": ["Wildlife corridor concerns", "Visual impact on ridgeline", "Active environmental groups"],
            "project_type": "Utility Solar", "permit_risk": "Moderate", "revenue_potential": "High",
            "land_cost_acre": 3200,
        },
        {
            "id": 3, "name": "Logan County Wind Prospect", "state": "IL", "county": "Logan",
            "lat": 40.12, "lon": -89.37, "acres": 520, "owner": "Heartland Ag Corp",
            "zoning": "Agricultural", "land_use": "Cropland",
            "wetland_pct": 18, "wetland_type": "Freshwater Forested/Shrub",
            "flood_zone": "A", "flood_coverage": 15,
            "soil_score": 62, "drainage": "Poorly drained", "hydric": True,
            "erosion_factor": 0.42, "pile_suitability": "Low", "bedrock_depth": 15,
            "trans_dist": 6.8, "voltage": "138 kV", "sub_dist": 5.4, "interconnection": "Low",
            "hub": "MISO Indiana Hub", "hub_lmp": 36, "node": "LOGAN_138_WIND",
            "node_lmp": 31, "basis": -5, "congestion": "High",
            "cong_freq": 22, "curtail_risk": "High", "rev_risk": "High",
            "sentiment": -0.45, "opp_risk": "High",
            "issues": ["Strong local opposition", "Wetland advocacy groups", "Township moratorium pending"],
            "project_type": "Not Recommended", "permit_risk": "High", "revenue_potential": "Low",
            "land_cost_acre": 7800,
        },
        {
            "id": 4, "name": "Custer County Wind Farm", "state": "OK", "county": "Custer",
            "lat": 35.63, "lon": -99.00, "acres": 640, "owner": "Prairie Wind LLC",
            "zoning": "Rural", "land_use": "Rangeland",
            "wetland_pct": 1, "wetland_type": "None significant",
            "flood_zone": "X (Minimal)", "flood_coverage": 0,
            "soil_score": 88, "drainage": "Well drained", "hydric": False,
            "erosion_factor": 0.18, "pile_suitability": "High", "bedrock_depth": 55,
            "trans_dist": 2.4, "voltage": "345 kV", "sub_dist": 1.9, "interconnection": "High",
            "hub": "SPP South Hub", "hub_lmp": 38, "node": "CUSTER_345_WIND",
            "node_lmp": 35, "basis": -3, "congestion": "Low",
            "cong_freq": 8, "curtail_risk": "Low", "rev_risk": "Low",
            "sentiment": 0.55, "opp_risk": "Low",
            "issues": ["Community supportive", "Existing wind development nearby", "County incentives available"],
            "project_type": "Wind Farm", "permit_risk": "Low", "revenue_potential": "High",
            "land_cost_acre": 620,
        },
        {
            "id": 5, "name": "Chautauqua Community Solar", "state": "NY", "county": "Chautauqua",
            "lat": 42.21, "lon": -79.43, "acres": 275, "owner": "Lake Erie Land Trust",
            "zoning": "Mixed Use", "land_use": "Idle Farmland",
            "wetland_pct": 12, "wetland_type": "Freshwater Emergent",
            "flood_zone": "AE", "flood_coverage": 8,
            "soil_score": 70, "drainage": "Moderately drained", "hydric": False,
            "erosion_factor": 0.32, "pile_suitability": "Moderate", "bedrock_depth": 20,
            "trans_dist": 5.5, "voltage": "230 kV", "sub_dist": 4.2, "interconnection": "Moderate",
            "hub": "NYISO Zone A", "hub_lmp": 48, "node": "CHAUT_230_SOLAR",
            "node_lmp": 42, "basis": -6, "congestion": "Medium",
            "cong_freq": 16, "curtail_risk": "Moderate", "rev_risk": "Moderate",
            "sentiment": -0.30, "opp_risk": "Moderate",
            "issues": ["Lakeshore viewshed concerns", "Active environmental groups", "Supportive town board"],
            "project_type": "Community Solar", "permit_risk": "Moderate", "revenue_potential": "Moderate",
            "land_cost_acre": 4500,
        },
        {
            "id": 6, "name": "Pecos County Solar Mega", "state": "TX", "county": "Pecos",
            "lat": 30.94, "lon": -102.41, "acres": 1200, "owner": "TransPecos Energy LP",
            "zoning": "Agricultural", "land_use": "Rangeland",
            "wetland_pct": 1, "wetland_type": "None significant",
            "flood_zone": "X (Minimal)", "flood_coverage": 1,
            "soil_score": 89, "drainage": "Well drained", "hydric": False,
            "erosion_factor": 0.12, "pile_suitability": "High", "bedrock_depth": 60,
            "trans_dist": 2.1, "voltage": "345 kV", "sub_dist": 1.5, "interconnection": "High",
            "hub": "ERCOT West Hub", "hub_lmp": 42, "node": "PECOS_345_SOLAR",
            "node_lmp": 39, "basis": -3, "congestion": "Low",
            "cong_freq": 7, "curtail_risk": "Low", "rev_risk": "Low",
            "sentiment": 0.41, "opp_risk": "Low",
            "issues": ["Strong local support", "Existing solar infrastructure", "Tax abatement available"],
            "project_type": "Utility Solar", "permit_risk": "Low", "revenue_potential": "High",
            "land_cost_acre": 450,
        },
        {
            "id": 7, "name": "Sumner County Wind", "state": "KS", "county": "Sumner",
            "lat": 37.18, "lon": -97.47, "acres": 890, "owner": "Great Plains Wind Co.",
            "zoning": "Agricultural", "land_use": "Cropland",
            "wetland_pct": 4, "wetland_type": "Riverine",
            "flood_zone": "X (Minimal)", "flood_coverage": 3,
            "soil_score": 84, "drainage": "Well drained", "hydric": False,
            "erosion_factor": 0.21, "pile_suitability": "High", "bedrock_depth": 48,
            "trans_dist": 3.0, "voltage": "345 kV", "sub_dist": 2.3, "interconnection": "High",
            "hub": "SPP North Hub", "hub_lmp": 35, "node": "SUMNER_345_WIND",
            "node_lmp": 33, "basis": -2, "congestion": "Low",
            "cong_freq": 9, "curtail_risk": "Low", "rev_risk": "Low",
            "sentiment": 0.48, "opp_risk": "Low",
            "issues": ["Supportive county commission", "Wind energy heritage area"],
            "project_type": "Wind Farm", "permit_risk": "Low", "revenue_potential": "High",
            "land_cost_acre": 1100,
        },
        {
            "id": 8, "name": "Imperial Valley Solar", "state": "CA", "county": "Imperial",
            "lat": 32.85, "lon": -115.57, "acres": 750, "owner": "Desert Sun Ventures",
            "zoning": "Agricultural", "land_use": "Desert Scrub",
            "wetland_pct": 2, "wetland_type": "None significant",
            "flood_zone": "X (Minimal)", "flood_coverage": 1,
            "soil_score": 82, "drainage": "Excessively drained", "hydric": False,
            "erosion_factor": 0.35, "pile_suitability": "Moderate", "bedrock_depth": 35,
            "trans_dist": 3.8, "voltage": "500 kV", "sub_dist": 2.8, "interconnection": "High",
            "hub": "CAISO SP15", "hub_lmp": 55, "node": "IMPERIAL_500_SOLAR",
            "node_lmp": 50, "basis": -5, "congestion": "Medium",
            "cong_freq": 12, "curtail_risk": "Moderate", "rev_risk": "Moderate",
            "sentiment": 0.10, "opp_risk": "Low",
            "issues": ["Some dust concerns", "Generally supportive", "Existing solar neighbors"],
            "project_type": "Utility Solar", "permit_risk": "Low", "revenue_potential": "High",
            "land_cost_acre": 1800,
        },
    ]
    return pd.DataFrame(parcels)


# ──────────────────────────────────────────────
# SCORING ENGINE
# ──────────────────────────────────────────────
def compute_site_score(row, weights):
    trans_score = max(0, 100 - (row["trans_dist"] / 10) * 100)
    price_score = min(100, (row["node_lmp"] / 60) * 100)
    wet_score = max(0, 100 - row["wetland_pct"] * 5)
    flood_map = {"X (Minimal)": 100, "AE": 55, "A": 25}
    flood_score = flood_map.get(row["flood_zone"], 50)
    soil_score = row["soil_score"]
    sent_score = (row["sentiment"] + 1) / 2 * 100
    cost_score = max(0, 100 - (row["land_cost_acre"] / 10000) * 100)

    total = (
        trans_score * weights["Transmission Proximity"] / 100
        + price_score * weights["Node Pricing"] / 100
        + wet_score * weights["Wetland Risk"] / 100
        + flood_score * weights["Flood Risk"] / 100
        + soil_score * weights["Soil Suitability"] / 100
        + sent_score * weights["Community Sentiment"] / 100
        + cost_score * weights["Land Cost"] / 100
    )
    return round(total), {
        "Transmission": round(trans_score),
        "Pricing": round(price_score),
        "Wetland": round(wet_score),
        "Flood": round(flood_score),
        "Soil": round(soil_score),
        "Sentiment": round(sent_score),
        "Land Cost": round(cost_score),
    }


def generate_lmp_history(base, days=365):
    np.random.seed(42)
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(days)]
    prices = base + np.cumsum(np.random.randn(days) * 1.5)
    prices = np.clip(prices, 5, 150)
    seasonal = 8 * np.sin(np.linspace(0, 2 * np.pi, days))
    prices = prices + seasonal
    return pd.DataFrame({"Date": dates, "LMP ($/MWh)": np.round(prices, 2)})


def generate_congestion_data():
    months = pd.date_range("2024-01", periods=12, freq="MS").strftime("%b %Y").tolist()
    return pd.DataFrame({
        "Month": months,
        "Congestion Events": np.random.randint(2, 30, 12),
        "Avg Curtailment %": np.round(np.random.uniform(1, 18, 12), 1),
        "Revenue Impact ($k)": np.round(np.random.uniform(-50, -2, 12), 1),
    })


# ──────────────────────────────────────────────
# MAP BUILDER
# ──────────────────────────────────────────────
def build_map(df, show_layers):
    m = folium.Map(location=[37.5, -96], zoom_start=5, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB", name="Dark Basemap", control=False,
    ).add_to(m)

    if show_layers.get("transmission"):
        trans_group = folium.FeatureGroup(name="Transmission Lines")
        lines = [
            [[31.0, -104.0], [32.5, -101.0], [34.0, -99.0]],
            [[35.0, -119.0], [36.0, -117.5], [37.0, -116.0]],
            [[39.0, -90.0], [40.5, -89.0], [42.0, -88.0]],
            [[35.0, -99.5], [36.5, -98.0], [37.5, -97.0]],
            [[41.0, -80.0], [42.0, -79.5], [43.0, -78.5]],
            [[32.5, -116.0], [33.5, -115.0], [34.5, -114.0]],
        ]
        for line in lines:
            folium.PolyLine(line, color="#f59e0b", weight=3, opacity=0.7,
                            dash_array="8 4").add_to(trans_group)
        trans_group.add_to(m)

    if show_layers.get("substations"):
        sub_group = folium.FeatureGroup(name="Substations")
        subs = [
            (31.5, -103.0, "Pecos Sub 345kV"), (35.5, -118.0, "Kern Sub 230kV"),
            (40.0, -89.5, "Lincoln Sub 138kV"), (35.8, -99.2, "Custer Sub 345kV"),
            (42.3, -79.5, "Erie Sub 230kV"), (33.0, -115.5, "Imperial Sub 500kV"),
            (37.2, -97.5, "Sumner Sub 345kV"),
        ]
        for lat, lon, name in subs:
            folium.CircleMarker(
                [lat, lon], radius=8, color="#f97316", fill=True,
                fill_color="#f97316", fill_opacity=0.8,
                popup=folium.Popup(f"<b>{name}</b>", max_width=200), tooltip=name,
            ).add_to(sub_group)
        sub_group.add_to(m)

    if show_layers.get("wetlands"):
        wet_group = folium.FeatureGroup(name="Wetland Zones")
        for _, row in df[df["wetland_pct"] > 5].iterrows():
            folium.Circle(
                [row["lat"], row["lon"]], radius=8000,
                color="#22d3ee", fill=True, fill_color="#22d3ee",
                fill_opacity=0.15, weight=1,
                tooltip=f"Wetland area near {row['name']} ({row['wetland_pct']}%)",
            ).add_to(wet_group)
        wet_group.add_to(m)

    if show_layers.get("floodplains"):
        flood_group = folium.FeatureGroup(name="Flood Zones")
        for _, row in df[df["flood_coverage"] > 5].iterrows():
            folium.Circle(
                [row["lat"], row["lon"]], radius=6000,
                color="#60a5fa", fill=True, fill_color="#60a5fa",
                fill_opacity=0.15, weight=1,
                tooltip=f"Flood Zone {row['flood_zone']} - {row['flood_coverage']}% coverage",
            ).add_to(flood_group)
        flood_group.add_to(m)

    for _, row in df.iterrows():
        score = row.get("score", 50)
        if score >= 80:
            color = "#22c55e"
        elif score >= 60:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        popup_html = f"""
        <div style="font-family:Inter,sans-serif;min-width:220px">
            <h4 style="margin:0 0 8px;color:{color}">{row['name']}</h4>
            <table style="font-size:12px;width:100%">
                <tr><td><b>Score</b></td><td style="color:{color};font-weight:900;font-size:18px">{score}/100</td></tr>
                <tr><td><b>Acres</b></td><td>{row['acres']}</td></tr>
                <tr><td><b>Type</b></td><td>{row['project_type']}</td></tr>
                <tr><td><b>Trans. Dist</b></td><td>{row['trans_dist']} mi</td></tr>
                <tr><td><b>Node LMP</b></td><td>${row['node_lmp']}/MWh</td></tr>
                <tr><td><b>Wetlands</b></td><td>{row['wetland_pct']}%</td></tr>
                <tr><td><b>Sentiment</b></td><td>{row['sentiment']}</td></tr>
            </table>
        </div>
        """
        folium.CircleMarker(
            [row["lat"], row["lon"]], radius=12 + score / 10,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.6, weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{row['name']} - Score: {score}",
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ──────────────────────────────────────────────
# MAIN APP
# ──────────────────────────────────────────────
def main():
    df = load_parcel_data()

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown("## ⚡ SiteIQ")
        st.caption("Renewable Energy Siting Intelligence Platform")
        st.divider()

        st.markdown("### Scoring Weights")
        st.caption("Adjust weights for the multi-factor scoring engine (must total 100%)")

        weights = {}
        weights["Transmission Proximity"] = st.slider("Transmission Proximity", 0, 50, 25, key="w_trans")
        weights["Node Pricing"] = st.slider("Node Pricing", 0, 50, 15, key="w_price")
        weights["Wetland Risk"] = st.slider("Wetland Risk", 0, 50, 15, key="w_wet")
        weights["Flood Risk"] = st.slider("Flood Risk", 0, 50, 10, key="w_flood")
        weights["Soil Suitability"] = st.slider("Soil Suitability", 0, 50, 15, key="w_soil")
        weights["Community Sentiment"] = st.slider("Community Sentiment", 0, 50, 10, key="w_sent")
        weights["Land Cost"] = st.slider("Land Cost", 0, 50, 10, key="w_cost")

        total_weight = sum(weights.values())
        if total_weight != 100:
            st.warning(f"Weights total **{total_weight}%** — should be 100%")
        else:
            st.success("Weights total 100%")

        st.divider()

        st.markdown("### Map Layers")
        show_layers = {
            "transmission": st.checkbox("Transmission Lines", True),
            "substations": st.checkbox("Substations", True),
            "wetlands": st.checkbox("Wetland Zones", True),
            "floodplains": st.checkbox("Flood Zones", True),
        }

    # Apply scoring
    scores_data = []
    breakdowns = {}
    for idx, row in df.iterrows():
        score, bd = compute_site_score(row, weights)
        scores_data.append(score)
        breakdowns[row["id"]] = bd
    df["score"] = scores_data

    # ── HEADER ──
    st.markdown("# ⚡ SiteIQ — Renewable Energy Siting Intelligence")
    st.markdown("> Evaluate land parcels for solar and wind development using environmental, grid, pricing, and community data layers.")

    # ── KPI ROW ──
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Total Parcels", len(df))
    with k2:
        st.metric("Avg Site Score", f"{df['score'].mean():.0f}/100")
    with k3:
        st.metric("Total Acreage", f"{df['acres'].sum():,}")
    with k4:
        st.metric("Avg Node LMP", f"${df['node_lmp'].mean():.0f}/MWh")
    with k5:
        viable = len(df[df["score"] >= 75])
        st.metric("Viable Sites (75+)", viable)

    # ── TABS ──
    tab_map, tab_query, tab_detail, tab_compare, tab_market, tab_report = st.tabs([
        "Interactive Map",
        "Developer Query",
        "Site Deep Dive",
        "Compare Sites",
        "Market Analytics",
        "Export Report",
    ])

    # ━━━━━━━━━━━━━ TAB: MAP ━━━━━━━━━━━━━
    with tab_map:
        st.markdown("### Interactive Siting Map")
        st.caption("Click any parcel marker to see details. Toggle layers in the sidebar.")
        m = build_map(df, show_layers)
        st_folium(m, width=None, height=550, returned_objects=[])

        st.markdown("### Parcel Rankings")
        display_df = df[["name", "state", "county", "acres", "score", "project_type",
                         "trans_dist", "node_lmp", "wetland_pct", "sentiment", "opp_risk"]].copy()
        display_df.columns = ["Site", "State", "County", "Acres", "Score", "Project Type",
                              "Trans. Dist (mi)", "Node LMP", "Wetland %", "Sentiment", "Opposition"]
        display_df = display_df.sort_values("Score", ascending=False).reset_index(drop=True)
        display_df.index += 1
        st.dataframe(display_df, use_container_width=True, height=340)

    # ━━━━━━━━━━━━━ TAB: QUERY ━━━━━━━━━━━━━
    with tab_query:
        st.markdown("### Developer Query Engine")
        st.caption("Filter parcels by your development criteria.")

        q1, q2, q3 = st.columns(3)
        with q1:
            min_acres = st.number_input("Min Acreage", 0, 5000, 200, step=50)
            max_trans = st.number_input("Max Transmission Distance (mi)", 0.0, 20.0, 5.0, step=0.5)
        with q2:
            min_node = st.number_input("Min Node Price ($/MWh)", 0, 100, 35, step=5)
            max_wetland = st.number_input("Max Wetland Coverage (%)", 0, 50, 10, step=1)
        with q3:
            min_score = st.number_input("Min Site Score", 0, 100, 70, step=5)
            flood_ok = st.multiselect("Acceptable Flood Zones", ["X (Minimal)", "AE", "A"], default=["X (Minimal)", "AE"])

        results = df[
            (df["acres"] >= min_acres) &
            (df["trans_dist"] <= max_trans) &
            (df["node_lmp"] >= min_node) &
            (df["wetland_pct"] <= max_wetland) &
            (df["score"] >= min_score) &
            (df["flood_zone"].isin(flood_ok))
        ].sort_values("score", ascending=False)

        st.markdown(f"### Results: **{len(results)}** parcels match")

        if len(results) > 0:
            for _, row in results.iterrows():
                sc = row["score"]
                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
                    with c1:
                        st.markdown(f"**{row['name']}** — {row['county']} Co., {row['state']}")
                        st.caption(f"Owner: {row['owner']} | {row['zoning']} | {row['project_type']}")
                    with c2:
                        st.metric("Score", f"{sc}/100")
                    with c3:
                        st.metric("Acres", row["acres"])
                    with c4:
                        st.metric("Trans. Dist", f"{row['trans_dist']} mi")
                    with c5:
                        st.metric("Node LMP", f"${row['node_lmp']}")
        else:
            st.info("No parcels match your criteria. Try relaxing your filters.")

    # ━━━━━━━━━━━━━ TAB: DETAIL ━━━━━━━━━━━━━
    with tab_detail:
        st.markdown("### Site Deep Dive")
        selected_site = st.selectbox("Select a parcel", df["name"].tolist(), key="detail_site")
        p = df[df["name"] == selected_site].iloc[0]
        bd = breakdowns[p["id"]]

        sc = p["score"]
        if sc >= 80:
            color = "#22c55e"
        elif sc >= 60:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:24px;margin-bottom:16px">
            <div style="font-size:4rem;font-weight:900;color:{color}">{sc}</div>
            <div>
                <div style="font-size:1.5rem;font-weight:700">{p['name']}</div>
                <div style="color:#94a3b8">{p['county']} County, {p['state']} | {p['acres']} acres | {p['project_type']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        s1, s2 = st.columns([1, 1])
        with s1:
            st.markdown("#### Score Breakdown")
            cats = list(bd.keys())
            vals = list(bd.values())
            fig_radar = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]], theta=cats + [cats[0]],
                fill="toself", fillcolor="rgba(99,102,241,0.2)",
                line=dict(color="#6366f1", width=2),
            ))
            fig_radar.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
                ),
                showlegend=False, height=350,
                margin=dict(l=60, r=60, t=30, b=30),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with s2:
            st.markdown("#### Factor Scores")
            score_df = pd.DataFrame({"Factor": cats, "Score": vals})
            score_df = score_df.sort_values("Score", ascending=True)
            fig_bar = px.bar(
                score_df, x="Score", y="Factor", orientation="h",
                color="Score", color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
                range_color=[0, 100],
            )
            fig_bar.update_layout(
                height=350, showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"),
                xaxis=dict(range=[0, 100], gridcolor="#334155"),
                yaxis=dict(gridcolor="#334155"),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            st.markdown("#### Environmental")
            st.metric("Wetland Coverage", f"{p['wetland_pct']}%")
            st.metric("Wetland Type", p["wetland_type"])
            st.metric("Flood Zone", p["flood_zone"])
            st.metric("Flood Coverage", f"{p['flood_coverage']}%")

        with d2:
            st.markdown("#### Soil & Land")
            st.metric("Soil Score", f"{p['soil_score']}/100")
            st.metric("Drainage", p["drainage"])
            st.metric("Hydric Soil", "Yes" if p["hydric"] else "No")
            st.metric("Pile Suitability", p["pile_suitability"])
            st.metric("Bedrock Depth", f"{p['bedrock_depth']} ft")

        with d3:
            st.markdown("#### Grid Access")
            st.metric("Nearest Line", f"{p['trans_dist']} mi")
            st.metric("Voltage", p["voltage"])
            st.metric("Nearest Substation", f"{p['sub_dist']} mi")
            st.metric("Interconnection", p["interconnection"])

        st.divider()

        p1, p2 = st.columns(2)
        with p1:
            st.markdown("#### Hub / Node Pricing")
            st.metric("Hub", p["hub"])
            st.metric("Hub LMP", f"${p['hub_lmp']}/MWh")
            st.metric("Node", p["node"])
            st.metric("Node LMP", f"${p['node_lmp']}/MWh")
            st.metric("Basis Difference", f"${p['basis']}/MWh")
            st.metric("Congestion Risk", p["congestion"])

        with p2:
            st.markdown("#### Community Sentiment")
            if p["sentiment"] > 0:
                sent_color = "#22c55e"
            elif p["sentiment"] > -0.3:
                sent_color = "#f59e0b"
            else:
                sent_color = "#ef4444"
            sent_prefix = "+" if p["sentiment"] > 0 else ""
            st.markdown(
                f"<h2 style='color:{sent_color};margin:0'>{sent_prefix}{p['sentiment']:.2f}</h2>",
                unsafe_allow_html=True,
            )
            st.metric("Opposition Risk", p["opp_risk"])
            st.markdown("**Key Issues:**")
            for issue in p["issues"]:
                st.markdown(f"- {issue}")

    # ━━━━━━━━━━━━━ TAB: COMPARE ━━━━━━━━━━━━━
    with tab_compare:
        st.markdown("### Compare Sites Side-by-Side")
        cc1, cc2 = st.columns(2)
        with cc1:
            site_a = st.selectbox("Site A", df["name"].tolist(), index=0, key="cmp_a")
        with cc2:
            site_b = st.selectbox("Site B", df["name"].tolist(), index=3, key="cmp_b")

        pa = df[df["name"] == site_a].iloc[0]
        pb = df[df["name"] == site_b].iloc[0]
        bda = breakdowns[pa["id"]]
        bdb = breakdowns[pb["id"]]

        cats = list(bda.keys())
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Scatterpolar(
            r=list(bda.values()) + [list(bda.values())[0]],
            theta=cats + [cats[0]], fill="toself",
            fillcolor="rgba(99,102,241,0.15)", line=dict(color="#6366f1", width=2),
            name=pa["name"],
        ))
        fig_cmp.add_trace(go.Scatterpolar(
            r=list(bdb.values()) + [list(bdb.values())[0]],
            theta=cats + [cats[0]], fill="toself",
            fillcolor="rgba(34,211,238,0.15)", line=dict(color="#22d3ee", width=2),
            name=pb["name"],
        ))
        fig_cmp.update_layout(
            polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 100])),
            height=420, margin=dict(l=80, r=80, t=40, b=40),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"), legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        metrics = [
            ("Score", "score", "/100", False),
            ("Acres", "acres", "", False),
            ("Transmission Dist.", "trans_dist", " mi", True),
            ("Node LMP", "node_lmp", " $/MWh", False),
            ("Wetland %", "wetland_pct", "%", True),
            ("Soil Score", "soil_score", "/100", False),
            ("Congestion Freq.", "cong_freq", "%", True),
            ("Sentiment", "sentiment", "", False),
            ("Land Cost/Acre", "land_cost_acre", "", True),
        ]
        cmp_data = []
        for label, key, unit, lower_better in metrics:
            va = pa[key]
            vb = pb[key]
            if lower_better:
                winner = "A" if va < vb else "B" if vb < va else "Tie"
            else:
                winner = "A" if va > vb else "B" if vb < va else "Tie"
            cmp_data.append({
                "Metric": label,
                site_a: f"{va}{unit}",
                site_b: f"{vb}{unit}",
                "Better": winner,
            })

        cmp_df = pd.DataFrame(cmp_data)
        st.dataframe(cmp_df, use_container_width=True, hide_index=True, height=370)

    # ━━━━━━━━━━━━━ TAB: MARKET ━━━━━━━━━━━━━
    with tab_market:
        st.markdown("### Market & Congestion Analytics")
        market_site = st.selectbox("Select site for market analysis", df["name"].tolist(), key="mkt_site")
        pm = df[df["name"] == market_site].iloc[0]

        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.metric("Hub", pm["hub"])
        with mc2:
            st.metric("Hub LMP", f"${pm['hub_lmp']}/MWh")
        with mc3:
            st.metric("Node LMP", f"${pm['node_lmp']}/MWh")
        with mc4:
            st.metric("Basis", f"${pm['basis']}/MWh")

        lmp_df = generate_lmp_history(pm["node_lmp"])
        fig_lmp = px.area(lmp_df, x="Date", y="LMP ($/MWh)", title="Historical LMP — 12-Month Trend")
        fig_lmp.update_traces(fillcolor="rgba(99,102,241,0.2)", line_color="#6366f1")
        fig_lmp.update_layout(
            height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"), xaxis=dict(gridcolor="#334155"),
            yaxis=dict(gridcolor="#334155"),
        )
        st.plotly_chart(fig_lmp, use_container_width=True)

        st.markdown("#### Congestion & Curtailment Analysis")
        cong_df = generate_congestion_data()
        cg1, cg2 = st.columns(2)

        with cg1:
            fig_cong = px.bar(
                cong_df, x="Month", y="Congestion Events",
                title="Monthly Congestion Events",
                color="Congestion Events",
                color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"],
            )
            fig_cong.update_layout(
                height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"), xaxis=dict(gridcolor="#334155"),
                yaxis=dict(gridcolor="#334155"), coloraxis_showscale=False,
            )
            st.plotly_chart(fig_cong, use_container_width=True)

        with cg2:
            fig_curt = px.line(
                cong_df, x="Month", y="Avg Curtailment %",
                title="Average Curtailment Rate",
                markers=True,
            )
            fig_curt.update_traces(line_color="#f59e0b", marker_color="#f59e0b")
            fig_curt.update_layout(
                height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e2e8f0"), xaxis=dict(gridcolor="#334155"),
                yaxis=dict(gridcolor="#334155"),
            )
            st.plotly_chart(fig_curt, use_container_width=True)

    # ━━━━━━━━━━━━━ TAB: REPORT ━━━━━━━━━━━━━
    with tab_report:
        st.markdown("### Export Feasibility Report")
        report_site = st.selectbox("Select site for report", df["name"].tolist(), key="rpt_site")
        pr = df[df["name"] == report_site].iloc[0]
        bdr = breakdowns[pr["id"]]

        breakdown_lines = "\n".join(
            [f"  {k:.<25} {v}/100" for k, v in bdr.items()]
        )
        issue_lines = "\n".join([f"    - {i}" for i in pr["issues"]])
        sent_prefix = "+" if pr["sentiment"] > 0 else ""

        report_text = f"""
================================================================
  SITEIQ — RENEWABLE ENERGY SITE FEASIBILITY REPORT
  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
================================================================

SITE: {pr['name']}
LOCATION: {pr['county']} County, {pr['state']}
COORDINATES: {pr['lat']}, {pr['lon']}
ACREAGE: {pr['acres']}
OWNER: {pr['owner']}
ZONING: {pr['zoning']}
LAND USE: {pr['land_use']}

----------------------------------------------------------------
OVERALL SITE SCORE: {pr['score']} / 100
RECOMMENDED PROJECT TYPE: {pr['project_type']}
PERMITTING RISK: {pr['permit_risk']}
REVENUE POTENTIAL: {pr['revenue_potential']}
----------------------------------------------------------------

SCORE BREAKDOWN:
{breakdown_lines}

----------------------------------------------------------------
ENVIRONMENTAL ANALYSIS
----------------------------------------------------------------
  Wetland Coverage:        {pr['wetland_pct']}%
  Wetland Type:            {pr['wetland_type']}
  Flood Zone:              {pr['flood_zone']}
  Flood Coverage:          {pr['flood_coverage']}%

----------------------------------------------------------------
SOIL ANALYSIS
----------------------------------------------------------------
  Soil Score:              {pr['soil_score']}/100
  Drainage Class:          {pr['drainage']}
  Hydric Soil:             {'Yes' if pr['hydric'] else 'No'}
  Erosion Factor:          {pr['erosion_factor']}
  Pile Suitability:        {pr['pile_suitability']}
  Depth to Bedrock:        {pr['bedrock_depth']} ft

----------------------------------------------------------------
TRANSMISSION & GRID ACCESS
----------------------------------------------------------------
  Nearest Trans. Line:     {pr['trans_dist']} miles
  Line Voltage:            {pr['voltage']}
  Nearest Substation:      {pr['sub_dist']} miles
  Interconnection:         {pr['interconnection']}

----------------------------------------------------------------
HUB / NODE PRICING
----------------------------------------------------------------
  Trading Hub:             {pr['hub']}
  Hub LMP:                 ${pr['hub_lmp']}/MWh
  Pricing Node:            {pr['node']}
  Node LMP:                ${pr['node_lmp']}/MWh
  Basis Difference:        ${pr['basis']}/MWh
  Congestion Risk:         {pr['congestion']}

----------------------------------------------------------------
CONGESTION ANALYTICS
----------------------------------------------------------------
  Congestion Frequency:    {pr['cong_freq']}%
  Curtailment Risk:        {pr['curtail_risk']}
  Revenue Risk:            {pr['rev_risk']}

----------------------------------------------------------------
COMMUNITY SENTIMENT
----------------------------------------------------------------
  Sentiment Score:         {sent_prefix}{pr['sentiment']:.2f}
  Opposition Risk:         {pr['opp_risk']}
  Key Issues:
{issue_lines}

----------------------------------------------------------------
LAND ECONOMICS
----------------------------------------------------------------
  Land Cost (per acre):    ${pr['land_cost_acre']:,}
  Total Land Cost Est.:    ${pr['land_cost_acre'] * pr['acres']:,}

================================================================
  Report generated by SiteIQ Renewable Energy Siting Platform
================================================================
"""
        st.text_area("Report Preview", report_text, height=500)

        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            safe_name = pr["name"].replace(" ", "_")
            st.download_button(
                "Download Report (.txt)", report_text,
                file_name=f"SiteIQ_Report_{safe_name}.txt",
                mime="text/plain",
            )
        with rc2:
            csv_data = df.to_csv(index=False)
            st.download_button(
                "Download All Sites (.csv)", csv_data,
                file_name="SiteIQ_All_Parcels.csv", mime="text/csv",
            )
        with rc3:
            geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(r["lon"]), float(r["lat"])],
                        },
                        "properties": {
                            k: (v if not isinstance(v, (np.integer, np.floating)) else int(v) if isinstance(v, np.integer) else float(v))
                            for k, v in r.items()
                            if k not in ["lat", "lon", "issues"]
                        },
                    }
                    for _, r in df.iterrows()
                ],
            }
            st.download_button(
                "Download GeoJSON", json.dumps(geojson, indent=2),
                file_name="SiteIQ_Parcels.geojson", mime="application/json",
            )


if __name__ == "__main__":
    main()
