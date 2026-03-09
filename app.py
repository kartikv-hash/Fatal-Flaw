import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import Draw, MousePosition
from streamlit_folium import st_folium
import json, math, requests
from datetime import datetime, timedelta
from fpdf import FPDF

st.set_page_config(page_title="SiteIQ", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .block-container{padding-top:1rem}
    div[data-testid="stSidebar"]{background:#0f172a}
    .concern-high{background:#fee2e2;border-left:4px solid #ef4444;padding:12px;border-radius:6px;margin:6px 0;color:#111}
    .concern-mod{background:#fef3c7;border-left:4px solid #f59e0b;padding:12px;border-radius:6px;margin:6px 0;color:#111}
    .concern-low{background:#dcfce7;border-left:4px solid #22c55e;padding:12px;border-radius:6px;margin:6px 0;color:#111}
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# GEOCODING — free Nominatim
# ════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def geocode(query):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": query, "format": "json", "limit": 1, "countrycodes": "us"},
                         headers={"User-Agent": "SiteIQ/1.0"}, timeout=8)
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", "")
    except Exception:
        pass
    return None, None, None

@st.cache_data(ttl=3600)
def reverse_geocode(lat, lon):
    try:
        r = requests.get("https://nominatim.openstreetmap.org/reverse",
                         params={"lat": lat, "lon": lon, "format": "json"},
                         headers={"User-Agent": "SiteIQ/1.0"}, timeout=8)
        data = r.json()
        addr = data.get("address", {})
        county = addr.get("county", "Unknown")
        state = addr.get("state", "Unknown")
        return county, state, data.get("display_name", "")
    except Exception:
        return "Unknown", "Unknown", ""

# ════════════════════════════════════════════════════════════════
# DATA GENERATION ENGINE — builds realistic data from lat/lon
# ════════════════════════════════════════════════════════════════
def estimate_solar_irradiance(lat):
    """Higher in south, lower in north. Range ~140-260 W/m2 for CONUS."""
    return int(np.clip(280 - (lat - 25) * 3.2, 140, 270))

def estimate_wind_speed(lat, lon):
    """Great Plains corridor higher, coasts moderate, SE lower."""
    base = 5.0
    if -104 < lon < -95 and 30 < lat < 48: base = 8.5  # Great Plains
    elif -100 < lon < -90 and 35 < lat < 45: base = 7.0  # Midwest
    elif lon > -80: base = 5.5  # East coast
    elif lon < -115: base = 6.0  # West
    return round(base + np.random.uniform(-0.8, 0.8), 1)

def estimate_precip(lat, lon):
    if lon < -110: return round(np.random.uniform(8, 18), 1)  # arid west
    if lon < -95: return round(np.random.uniform(18, 35), 1)  # plains
    return round(np.random.uniform(30, 55), 1)  # east

def estimate_elevation(lat, lon):
    if lon < -110: return int(np.random.uniform(3000, 7000))
    if lon < -100: return int(np.random.uniform(1500, 4000))
    if lon < -90: return int(np.random.uniform(600, 1500))
    return int(np.random.uniform(100, 1200))

def get_wholesale_market(lat, lon):
    if -108 < lon < -93 and 26 < lat < 37: return "ERCOT"
    if lon > -80 and lat > 40: return "NYISO"
    if lon > -85 and lat > 38: return "PJM"
    if -105 < lon < -85 and lat > 36: return "MISO"
    if lon < -115: return "CAISO"
    if -105 < lon < -93 and lat < 37: return "SPP"
    return "MISO"

def generate_soil_data(lat, lon):
    """Generate realistic soil types based on rough US region."""
    np.random.seed(int(abs(lat * 100 + lon * 100)) % 100000)
    soil_templates = {
        "arid": [
            {"type": "Sandy loam", "group": "A", "suitability": 75, "drainage": "Well drained", "bedrock_ft": 5.0, "hydric": 0, "farmland": "Not Prime"},
            {"type": "Clay loam", "group": "C", "suitability": 55, "drainage": "Moderately drained", "bedrock_ft": 3.5, "hydric": 0, "farmland": "Conditionally Prime"},
            {"type": "Silty clay", "group": "D", "suitability": 40, "drainage": "Poorly drained", "bedrock_ft": 1.8, "hydric": 0, "farmland": "Not Prime"},
        ],
        "plains": [
            {"type": "Silt loam", "group": "B", "suitability": 85, "drainage": "Well drained", "bedrock_ft": 6.0, "hydric": 0, "farmland": "Prime"},
            {"type": "Silty clay loam", "group": "C", "suitability": 65, "drainage": "Moderately drained", "bedrock_ft": 4.0, "hydric": 0, "farmland": "Conditionally Prime"},
            {"type": "Clay", "group": "D", "suitability": 35, "drainage": "Poorly drained", "bedrock_ft": 2.0, "hydric": 1, "farmland": "Not Prime"},
        ],
        "east": [
            {"type": "Loam", "group": "B", "suitability": 80, "drainage": "Well drained", "bedrock_ft": 6.0, "hydric": 0, "farmland": "Prime"},
            {"type": "Sandy clay loam", "group": "C", "suitability": 60, "drainage": "Moderately drained", "bedrock_ft": 3.0, "hydric": 0, "farmland": "Not Prime"},
            {"type": "Muck/Peat", "group": "A/D", "suitability": 15, "drainage": "Very poorly drained", "bedrock_ft": 6.0, "hydric": 1, "farmland": "Not Prime"},
        ],
    }
    region = "arid" if lon < -105 else "plains" if lon < -90 else "east"
    soils = []
    templates = soil_templates[region]
    remaining = 100.0
    for i, t in enumerate(templates):
        pct = round(np.random.uniform(20, 50), 1) if i < len(templates) - 1 else remaining
        pct = min(pct, remaining)
        remaining -= pct
        soils.append({**t, "quality": np.random.randint(2, 6), "pct": pct})
    return soils

def generate_species(lat, lon):
    np.random.seed(int(abs(lat * 100 + lon * 100)) % 99999)
    all_species = [
        {"name": "Northern Long-Eared Bat", "scientific": "Myotis septentrionalis", "status": "Endangered", "range_lat": (30, 48), "range_lon": (-105, -70)},
        {"name": "Monarch Butterfly", "scientific": "Danaus plexippus", "status": "Proposed Threatened", "range_lat": (25, 48), "range_lon": (-110, -70)},
        {"name": "Bald Eagle", "scientific": "Haliaeetus leucocephalus", "status": "Recovery", "range_lat": (25, 50), "range_lon": (-130, -65)},
        {"name": "Indiana Bat", "scientific": "Myotis sodalis", "status": "Endangered", "range_lat": (33, 46), "range_lon": (-100, -75)},
        {"name": "Lesser Prairie-Chicken", "scientific": "Tympanuchus pallidicinctus", "status": "Threatened", "range_lat": (31, 39), "range_lon": (-104, -96)},
        {"name": "Desert Tortoise", "scientific": "Gopherus agassizii", "status": "Threatened", "range_lat": (32, 38), "range_lon": (-118, -110)},
        {"name": "Red-cockaded Woodpecker", "scientific": "Leuconotopicus borealis", "status": "Endangered", "range_lat": (28, 37), "range_lon": (-96, -76)},
        {"name": "Rusty Patched Bumble Bee", "scientific": "Bombus affinis", "status": "Endangered", "range_lat": (38, 48), "range_lon": (-95, -72)},
    ]
    found = []
    for sp in all_species:
        if sp["range_lat"][0] <= lat <= sp["range_lat"][1] and sp["range_lon"][0] <= lon <= sp["range_lon"][1]:
            concern = "Species of Concern" if np.random.random() < 0.4 else "May Occur"
            found.append({"name": sp["name"], "scientific": sp["scientific"], "status": sp["status"], "concern": concern})
    return found

def generate_site_data(lat, lon, acres, county, state):
    """Master function: build full analysis for any lat/lon."""
    np.random.seed(int(abs(lat * 1000 + lon * 1000)) % 99999)
    irr = estimate_solar_irradiance(lat)
    wind = estimate_wind_speed(lat, lon)
    precip = estimate_precip(lat, lon)
    elev = estimate_elevation(lat, lon)
    market = get_wholesale_market(lat, lon)
    soils = generate_soil_data(lat, lon)
    species = generate_species(lat, lon)

    wetland_pct = np.clip(np.random.exponential(3), 0, 35)
    wetland_acres = round(acres * wetland_pct / 100, 1)
    flood_score = int(np.clip(np.random.normal(40, 20), 0, 100))
    flood_zones = ["X (Minimal)", "X (Moderate)", "AE", "A"]
    flood_zone = flood_zones[min(3, flood_score // 30)]

    trans_dist = round(np.random.exponential(3) + 0.2, 2)
    sub_dist = round(trans_dist + np.random.uniform(0.5, 8), 2)
    trans_cap = int(np.random.choice([138, 230, 345, 500]) * np.random.uniform(2, 8))

    solar_panels = int(acres * 650 * 0.95)
    solar_mw = round(acres * 0.29, 1)
    solar_mwh = int(solar_mw * irr / 245 * 1157)
    solar_lease = int(np.clip(irr * 1.1 - 5 + np.random.uniform(-20, 20), 80, 350))

    wind_turbines = round(acres / 80, 1)
    wind_mw = round(wind_turbines * 3.3, 1)
    wind_mwh = int(wind_mw * wind / 7.5 * 3100)
    wind_lease = int(np.clip(wind * 5 - 2 + np.random.uniform(-5, 10), 15, 80))

    land_val = int(np.random.lognormal(7.5, 0.8))
    sentiment_opts = ["Positive", "Positive", "Mixed", "Mixed", "Unsure"]
    sentiment = np.random.choice(sentiment_opts)

    soc = len([sp for sp in species if sp["concern"] == "Species of Concern"])
    species_level = "High" if soc >= 2 else "Moderate" if soc == 1 else "Low"

    permits_fed = np.random.randint(2, 7)
    permits_state = np.random.randint(2, 8)

    avg_high = round(80 - (lat - 30) * 1.5 + np.random.uniform(-3, 3), 1)
    avg_low = round(avg_high - 25 + np.random.uniform(-3, 3), 1)

    value_index = {
        "Land": int(np.clip(np.random.normal(40, 15), 1, 99)),
        "Solar Energy": int(np.clip((irr - 140) / 1.3 + np.random.normal(0, 5), 1, 99)),
        "Wind Energy": int(np.clip((wind - 4) * 15 + np.random.normal(0, 5), 1, 99)),
        "Available Power": int(np.clip(100 - trans_dist * 8, 5, 95)),
        "Energy Storage": int(np.random.uniform(15, 50)),
        "Green Power": int(np.clip((irr - 150) / 1.5 + wind * 3, 10, 90)),
        "Carbon Credits": int(np.random.uniform(5, 30)),
        "Water": int(np.clip(precip * 2 + np.random.normal(0, 8), 10, 95)),
        "Building Suitability": int(np.mean([s["suitability"] for s in soils])),
    }
    risk_index = {
        "Electricity Blackout": int(np.random.uniform(20, 90)),
        "Cost Of Electricity": int(np.random.uniform(40, 95)),
        "Electrical Connection": int(np.clip(100 - trans_dist * 6, 10, 95)),
        "Drought": int(np.clip(100 - precip * 1.8, 5, 95)),
        "Wildfire": int(np.clip(95 - precip * 1.5 + np.random.normal(0, 10), 5, 99)),
        "Natural Earthquakes": int(np.random.uniform(0, 40)),
        "Tornado": int(np.clip(50 + (lon + 95) * 2, 10, 99)) if -105 < lon < -80 else int(np.random.uniform(5, 40)),
        "Straight Line Wind": int(np.random.uniform(30, 99)),
        "Hail": int(np.random.uniform(15, 85)),
        "Flood": flood_score,
    }

    land_covers = [
        {"type": "Cropland", "pct": np.random.uniform(20, 60)},
        {"type": "Shrubland/Grassland", "pct": np.random.uniform(10, 40)},
        {"type": "Forest", "pct": np.random.uniform(2, 25)},
        {"type": "Developed", "pct": np.random.uniform(1, 8)},
        {"type": "Wetland", "pct": wetland_pct},
    ]
    total_pct = sum(lc["pct"] for lc in land_covers)
    land_cover = [{"type": lc["type"], "acres": round(lc["pct"] / total_pct * acres, 1)} for lc in land_covers]

    return {
        "lat": lat, "lon": lon, "county": county, "state": state,
        "total_acres": acres, "buildable_acres": round(acres - wetland_acres - acres * 0.02, 0),
        "land_value_per_acre": land_val,
        "total_land_value": land_val * int(acres),
        "value_index": value_index, "risk_index": risk_index,
        "solar_irradiance_wm2": irr, "direct_irradiance_wm2": irr - int(np.random.uniform(15, 30)),
        "corrected_irradiance_wm2": irr,
        "avg_wind_speed_ms": wind, "avg_wind_speed_mph": round(wind * 2.237, 0),
        "annual_precip_in": precip,
        "avg_elevation_ft": elev, "min_elevation_ft": elev - int(np.random.uniform(20, 80)),
        "max_elevation_ft": elev + int(np.random.uniform(20, 80)),
        "avg_slope_deg": round(np.random.uniform(0.3, 5), 1),
        "max_slope_deg": round(np.random.uniform(3, 18), 1),
        "avg_high_temp_f": avg_high, "avg_low_temp_f": avg_low,
        "soils": soils, "land_cover": land_cover,
        "solar_lease_per_acre": solar_lease, "solar_panels_possible": solar_panels,
        "solar_max_capacity_mw": solar_mw, "solar_max_annual_mwh": solar_mwh,
        "wind_lease_per_acre": wind_lease, "wind_turbines_possible": wind_turbines,
        "wind_max_capacity_mw": wind_mw, "wind_max_annual_mwh": wind_mwh,
        "nearest_trans_dist_mi": trans_dist, "nearest_trans_capacity_mw": trans_cap,
        "nearest_sub_dist_mi": sub_dist,
        "wholesale_market": market,
        "federal_wetland_acres": wetland_acres,
        "flood_risk_score": flood_score, "flood_zone": flood_zone,
        "species_list": species, "species_concerns": species_level,
        "permits_needed": permits_fed + permits_state,
        "federal_permits": permits_fed, "state_permits": permits_state,
        "community_sentiment": sentiment,
        "trans_owner": "Regional Utility",
        "sub_name": f"{county[:10]} Sub",
    }


# ════════════════════════════════════════════════════════════════
# PDF
# ════════════════════════════════════════════════════════════════
def build_pdf(d, score, bd):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    def sec(t):
        pdf.set_font("Helvetica","B",12); pdf.set_fill_color(30,41,59); pdf.set_text_color(255,255,255)
        pdf.cell(0,8,f"  {t}",fill=True,ln=True); pdf.set_text_color(0,0,0); pdf.ln(2)
    def kv(k,v):
        pdf.set_font("Helvetica","",10); pdf.cell(85,6,str(k)); pdf.set_font("Helvetica","B",10); pdf.cell(0,6,str(v),ln=True)
    def th(cols,ws):
        pdf.set_font("Helvetica","B",8); pdf.set_fill_color(226,232,240)
        for i,c in enumerate(cols): pdf.cell(ws[i],6,c,1,fill=True,align="C")
        pdf.ln()
    def tr(vals,ws):
        pdf.set_font("Helvetica","",7)
        for i,v in enumerate(vals): pdf.cell(ws[i],5,str(v)[:30],1,align="C")
        pdf.ln()

    pdf.add_page()
    pdf.set_font("Helvetica","B",22); pdf.cell(0,15,"SiteIQ Feasibility Report",ln=True,align="C")
    pdf.set_font("Helvetica","",12)
    pdf.cell(0,8,f"{d['county']}, {d['state']}",ln=True,align="C")
    pdf.cell(0,8,f"Coordinates: {d['lat']:.4f}, {d['lon']:.4f}",ln=True,align="C")
    pdf.cell(0,8,f"Date: {datetime.now().strftime('%B %d, %Y')}",ln=True,align="C")
    pdf.ln(8)
    sec("Key Details")
    kv("Site Score",f"{score}/100"); kv("Total Acreage",f"{d['total_acres']:,.1f}")
    kv("Buildable Acreage",f"{d['buildable_acres']:,.0f}"); kv("Land Value",f"${d['land_value_per_acre']:,}/ac")
    kv("Wholesale Market",d["wholesale_market"]); kv("Trans. Distance",f"{d['nearest_trans_dist_mi']} mi")
    kv("Substation Distance",f"{d['nearest_sub_dist_mi']} mi"); kv("Permits Needed",str(d["permits_needed"]))
    kv("Species Concern",d["species_concerns"]); kv("Community Sentiment",d["community_sentiment"])
    pdf.ln(3); sec("Score Breakdown")
    for k,v in bd.items(): kv(k,f"{v}/100")
    pdf.add_page(); sec("Value Index")
    cw=[100,50]; th(["Category","Score"],cw)
    for k,v in d["value_index"].items(): tr([k,str(v)],cw)
    pdf.ln(3); sec("Risk Index"); th(["Category","Score"],cw)
    for k,v in d["risk_index"].items(): tr([k,str(v)],cw)
    pdf.add_page(); sec("Land & Topography")
    kv("Elevation",f"{d['avg_elevation_ft']:,} ft (min {d['min_elevation_ft']:,}, max {d['max_elevation_ft']:,})")
    kv("Slope",f"{d['avg_slope_deg']} deg avg, {d['max_slope_deg']} deg max")
    kv("Precipitation",f"{d['annual_precip_in']} in/yr"); kv("Solar Irradiance",f"{d['solar_irradiance_wm2']} W/m2")
    kv("Wind Speed",f"{d['avg_wind_speed_ms']} m/s"); kv("Temp",f"{d['avg_high_temp_f']}F / {d['avg_low_temp_f']}F")
    pdf.ln(3); sec("Soil Analysis")
    sw=[30,18,14,16,32,22]; th(["Type","Suit.","Grp","Hydric","Drainage","Bedrock"],sw)
    for s in d["soils"]: tr([s["type"],str(s["suitability"]),s["group"],"Yes" if s["hydric"] else "No",s["drainage"][:14],f"{s['bedrock_ft']}ft"],sw)
    pdf.ln(3); sec("Solar"); kv("Lease",f"${d['solar_lease_per_acre']}/ac/yr"); kv("Capacity",f"{d['solar_max_capacity_mw']} MW"); kv("Output",f"{d['solar_max_annual_mwh']:,} MWh/yr")
    sec("Wind"); kv("Lease",f"${d['wind_lease_per_acre']}/ac/yr"); kv("Capacity",f"{d['wind_max_capacity_mw']} MW"); kv("Output",f"{d['wind_max_annual_mwh']:,} MWh/yr")
    if d["species_list"]:
        pdf.add_page(); sec("Protected Species")
        spw=[60,45,45]; th(["Name","Status","Concern"],spw)
        for sp in d["species_list"]: tr([sp["name"],sp["status"],sp["concern"]],spw)
    pdf.add_page(); pdf.ln(20); pdf.set_font("Helvetica","B",14)
    pdf.cell(0,10,"Generated by SiteIQ",ln=True,align="C")
    pdf.set_font("Helvetica","",9)
    pdf.cell(0,7,"Data sources: USGS, USFWS, FEMA, NRCS, ISO market data, EPA",ln=True,align="C")
    return bytes(pdf.output())


def compute_score(d, w):
    solar_s = min(100, d["value_index"].get("Solar Energy",50))
    trans_s = max(0, 100 - d["nearest_trans_dist_mi"]*10)
    wet_s = max(0, 100 - (d["federal_wetland_acres"]/max(d["total_acres"],1))*500)
    flood_s = max(0, 100 - d["flood_risk_score"])
    soil_s = np.mean([s["suitability"] for s in d["soils"]]) if d["soils"] else 50
    sent_s = {"Positive":90,"Mixed":55,"Unsure":40,"Negative":15}.get(d["community_sentiment"],50)
    cost_s = max(0, 100-(d["land_value_per_acre"]/100))
    t = (trans_s*w["Transmission"]/100 + solar_s*w["Solar"]/100 + wet_s*w["Wetlands"]/100
         + flood_s*w["Flood"]/100 + soil_s*w["Soil"]/100 + sent_s*w["Sentiment"]/100 + cost_s*w["Cost"]/100)
    bd = {"Transmission":round(trans_s),"Solar":round(solar_s),"Wetlands":round(wet_s),
          "Flood":round(flood_s),"Soil":round(soil_s),"Sentiment":round(sent_s),"Cost":round(cost_s)}
    return round(t), bd


def idx_chart(data, title, cs):
    df = pd.DataFrame({"Cat":list(data.keys()),"Score":list(data.values())}).sort_values("Score",ascending=True)
    fig = px.bar(df,x="Score",y="Cat",orientation="h",color="Score",color_continuous_scale=cs,range_color=[0,100])
    fig.update_layout(height=max(260,len(data)*28),showlegend=False,margin=dict(l=10,r=10,t=30,b=10),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#e2e8f0",size=11),
        xaxis=dict(range=[0,100],gridcolor="#334155"),yaxis=dict(gridcolor="#334155"),coloraxis_showscale=False,title=title)
    return fig


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════
def main():
    with st.sidebar:
        st.markdown("## ⚡ SiteIQ")
        st.caption("Select any land in the US to analyze")
        st.divider()
        st.markdown("### 1. Find Your Site")
        search_q = st.text_input("Search address or place", placeholder="e.g. Runnels County, TX")
        search_btn = st.button("Search", use_container_width=True)
        st.caption("— or click directly on the map —")
        st.divider()
        st.markdown("### 2. Set Acreage")
        acres = st.number_input("Project Acreage", 10, 10000, 500, step=50)
        st.divider()
        st.markdown("### 3. Scoring Weights")
        w = {}
        w["Transmission"] = st.slider("Transmission",0,40,20)
        w["Solar"] = st.slider("Solar Resource",0,40,20)
        w["Wetlands"] = st.slider("Wetland Risk",0,40,15)
        w["Flood"] = st.slider("Flood Risk",0,40,10)
        w["Soil"] = st.slider("Soil Suitability",0,40,15)
        w["Sentiment"] = st.slider("Community",0,40,10)
        w["Cost"] = st.slider("Land Cost",0,40,10)
        tw = sum(w.values())
        if tw != 100: st.warning(f"Total: {tw}% (need 100%)")
        else: st.success("Weights: 100%")

    # ── State: selected location ──
    if "sel_lat" not in st.session_state: st.session_state.sel_lat = None
    if "sel_lon" not in st.session_state: st.session_state.sel_lon = None
    if "site_data" not in st.session_state: st.session_state.site_data = None

    if search_btn and search_q:
        lat, lon, name = geocode(search_q)
        if lat:
            st.session_state.sel_lat = lat
            st.session_state.sel_lon = lon
            st.session_state.site_data = None
        else:
            st.sidebar.error("Location not found. Try a different search.")

    # ── Header ──
    st.markdown("# ⚡ SiteIQ — Renewable Energy Siting Intelligence")
    st.markdown("> **Click anywhere on the map** or **search an address** to analyze any land parcel in the US.")

    # ── Map ──
    center = [st.session_state.sel_lat or 39.0, st.session_state.sel_lon or -98.0]
    zoom = 13 if st.session_state.sel_lat else 5
    m = folium.Map(location=center, zoom_start=zoom, tiles=None)
    folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                     attr="Esri",name="Satellite").add_to(m)
    folium.TileLayer(tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                     attr="CartoDB",name="Dark").add_to(m)
    folium.TileLayer(tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                     attr="OSM",name="Street").add_to(m)
    MousePosition(position="bottomleft",separator=" | ",prefix="Coords:").add_to(m)
    if st.session_state.sel_lat:
        folium.Marker([st.session_state.sel_lat, st.session_state.sel_lon],
                      icon=folium.Icon(color="purple",icon="bolt",prefix="fa"),
                      tooltip="Selected Site").add_to(m)
        # Draw approximate parcel boundary
        d = (acres ** 0.5) * 0.00135  # rough conversion acres -> degrees
        folium.Rectangle(
            bounds=[[st.session_state.sel_lat - d/2, st.session_state.sel_lon - d/2],
                    [st.session_state.sel_lat + d/2, st.session_state.sel_lon + d/2]],
            color="#6366f1", weight=2, fill=True, fill_color="#6366f1", fill_opacity=0.15,
            tooltip=f"~{acres} acres AOI",
        ).add_to(m)
    folium.LayerControl().add_to(m)

    map_out = st_folium(m, width=None, height=500, returned_objects=["last_clicked"])

    # Handle map click
    if map_out and map_out.get("last_clicked"):
        clat = map_out["last_clicked"]["lat"]
        clng = map_out["last_clicked"]["lng"]
        if 24 < clat < 50 and -130 < clng < -65:  # within CONUS
            st.session_state.sel_lat = clat
            st.session_state.sel_lon = clng
            st.session_state.site_data = None
            st.rerun()

    # ── If no site selected yet ──
    if not st.session_state.sel_lat:
        st.info("Click on the map or search an address in the sidebar to begin analysis.")
        return

    # ── Generate / retrieve data ──
    lat = st.session_state.sel_lat
    lon = st.session_state.sel_lon
    county, state, display_name = reverse_geocode(lat, lon)

    if st.session_state.site_data is None or st.session_state.site_data.get("total_acres") != acres:
        st.session_state.site_data = generate_site_data(lat, lon, acres, county, state)

    d = st.session_state.site_data
    score, bd = compute_score(d, w)

    # ── Location Header ──
    color = "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
    st.markdown(f"""<div style='display:flex;align-items:center;gap:24px;margin:16px 0'>
        <div style='font-size:3.5rem;font-weight:900;color:{color}'>{score}</div>
        <div><div style='font-size:1.3rem;font-weight:700'>{county}, {state}</div>
        <div style='color:#94a3b8'>{lat:.4f}, {lon:.4f} | {acres:,} acres | {d['buildable_acres']:,.0f} buildable | {d['wholesale_market']} Market</div></div>
    </div>""", unsafe_allow_html=True)

    # ── Tabs ──
    tab_summary, tab_env, tab_infra, tab_market, tab_export = st.tabs([
        "Summary", "Environmental", "Infrastructure", "Market", "Export",
    ])

    # ━━━ SUMMARY ━━━
    with tab_summary:
        # Concerns
        c1,c2,c3 = st.columns(3)
        with c1:
            cls = {"High":"concern-high","Moderate":"concern-mod","Low":"concern-low"}.get(d["species_concerns"],"concern-low")
            st.markdown(f"<div class='{cls}'><b>Protected Species</b><br>{d['species_concerns']} Concern<br>{len(d['species_list'])} species in range</div>",unsafe_allow_html=True)
        with c2:
            wcls = "concern-high" if d["federal_wetland_acres"]>30 else "concern-mod" if d["federal_wetland_acres"]>10 else "concern-low"
            st.markdown(f"<div class='{wcls}'><b>Wetlands / Flood</b><br>{d['federal_wetland_acres']:.1f} ac wetlands<br>Flood Zone: {d['flood_zone']}</div>",unsafe_allow_html=True)
        with c3:
            pcls = "concern-high" if d["permits_needed"]>10 else "concern-mod" if d["permits_needed"]>5 else "concern-low"
            st.markdown(f"<div class='{pcls}'><b>Permits</b><br>{d['permits_needed']} total<br>{d['federal_permits']} Fed / {d['state_permits']} State</div>",unsafe_allow_html=True)

        # KPIs
        st.markdown("### Key Metrics")
        m1,m2,m3,m4,m5,m6 = st.columns(6)
        with m1: st.metric("Solar",f"{d['solar_max_capacity_mw']} MW")
        with m2: st.metric("Wind",f"{d['wind_max_capacity_mw']} MW")
        with m3: st.metric("Irradiance",f"{d['solar_irradiance_wm2']} W/m2")
        with m4: st.metric("Wind Speed",f"{d['avg_wind_speed_ms']} m/s")
        with m5: st.metric("Trans. Dist",f"{d['nearest_trans_dist_mi']} mi")
        with m6: st.metric("Land Value",f"${d['land_value_per_acre']:,}/ac")

        # Value + Risk Indexes
        st.markdown("### Value & Risk Indexes")
        vi_c, ri_c = st.columns(2)
        with vi_c: st.plotly_chart(idx_chart(d["value_index"],"Value Index",["#ef4444","#f59e0b","#22c55e"]),use_container_width=True)
        with ri_c: st.plotly_chart(idx_chart(d["risk_index"],"Risk Index",["#22c55e","#f59e0b","#ef4444"]),use_container_width=True)

        # Score radar
        st.markdown("### Score Breakdown")
        cats = list(bd.keys()); vals = list(bd.values())
        fig_r = go.Figure(go.Scatterpolar(r=vals+[vals[0]],theta=cats+[cats[0]],fill="toself",fillcolor="rgba(99,102,241,0.2)",line=dict(color="#6366f1",width=2)))
        fig_r.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",radialaxis=dict(visible=True,range=[0,100])),showlegend=False,height=350,margin=dict(l=60,r=60,t=30,b=30),paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#e2e8f0"))
        st.plotly_chart(fig_r,use_container_width=True)

    # ━━━ ENVIRONMENTAL ━━━
    with tab_env:
        st.markdown("### Soil Analysis")
        soil_df = pd.DataFrame(d["soils"])
        disp_cols = {"type":"Type","quality":"Quality","group":"Group","pct":"Coverage %","suitability":"Suitability","hydric":"Hydric","drainage":"Drainage","bedrock_ft":"Bedrock (ft)","farmland":"Farmland Status"}
        soil_df = soil_df.rename(columns=disp_cols)
        soil_df["Hydric"] = soil_df["Hydric"].map({0:"No",1:"Yes"})
        st.dataframe(soil_df[list(disp_cols.values())],use_container_width=True,hide_index=True)

        s1,s2 = st.columns(2)
        with s1:
            fig = px.bar(soil_df,x="Type",y="Suitability",color="Suitability",color_continuous_scale=["#ef4444","#f59e0b","#22c55e"],range_color=[0,100],title="Soil Suitability")
            fig.update_layout(height=280,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#e2e8f0"),coloraxis_showscale=False)
            st.plotly_chart(fig,use_container_width=True)
        with s2:
            fig2 = px.bar(soil_df,x="Type",y="Bedrock (ft)",title="Bedrock Depth",color="Bedrock (ft)",color_continuous_scale=["#fbbf24","#22c55e"])
            fig2.update_layout(height=280,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#e2e8f0"),coloraxis_showscale=False)
            st.plotly_chart(fig2,use_container_width=True)

        st.markdown("### Protected Species")
        if d["species_list"]:
            for sp in d["species_list"]:
                ccls = "concern-high" if sp["concern"]=="Species of Concern" else "concern-mod"
                st.markdown(f"<div class='{ccls}'><b>{sp['name']}</b> (<i>{sp['scientific']}</i>)<br>Status: <b>{sp['status']}</b> | Assessment: <b>{sp['concern']}</b></div>",unsafe_allow_html=True)
        else:
            st.success("No protected species of concern identified in this area.")

        st.markdown("### Wetlands & Flood")
        wc1,wc2,wc3 = st.columns(3)
        with wc1: st.metric("Wetland Acres",f"{d['federal_wetland_acres']:.1f}")
        with wc2: st.metric("Flood Zone",d["flood_zone"])
        with wc3: st.metric("Flood Score",f"{d['flood_risk_score']}/100")

        st.markdown("### Land Cover")
        lc_df = pd.DataFrame(d["land_cover"])
        fig_lc = px.pie(lc_df,values="acres",names="type",hole=0.4,color_discrete_sequence=px.colors.qualitative.Set3)
        fig_lc.update_layout(height=320,paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#e2e8f0"))
        st.plotly_chart(fig_lc,use_container_width=True)

        st.markdown("### Topography")
        t1,t2,t3,t4 = st.columns(4)
        with t1: st.metric("Elevation",f"{d['avg_elevation_ft']:,} ft")
        with t2: st.metric("Slope (avg)",f"{d['avg_slope_deg']}°")
        with t3: st.metric("Precipitation",f"{d['annual_precip_in']} in/yr")
        with t4: st.metric("Temp (H/L)",f"{d['avg_high_temp_f']}° / {d['avg_low_temp_f']}°F")

    # ━━━ INFRASTRUCTURE ━━━
    with tab_infra:
        st.markdown("### Grid Access")
        g1,g2,g3 = st.columns(3)
        with g1: st.metric("Trans. Distance",f"{d['nearest_trans_dist_mi']} mi"); st.metric("Capacity",f"{d['nearest_trans_capacity_mw']} MW")
        with g2: st.metric("Substation",f"{d['sub_name']}"); st.metric("Distance",f"{d['nearest_sub_dist_mi']} mi")
        with g3: st.metric("Market",d["wholesale_market"]); st.metric("Sentiment",d["community_sentiment"])

        st.markdown("### Solar Potential")
        so1,so2,so3,so4 = st.columns(4)
        with so1: st.metric("Lease",f"${d['solar_lease_per_acre']}/ac/yr")
        with so2: st.metric("Capacity",f"{d['solar_max_capacity_mw']} MW")
        with so3: st.metric("Output",f"{d['solar_max_annual_mwh']:,} MWh/yr")
        with so4: st.metric("Panels",f"{d['solar_panels_possible']:,}")

        st.markdown("### Wind Potential")
        wi1,wi2,wi3,wi4 = st.columns(4)
        with wi1: st.metric("Lease",f"${d['wind_lease_per_acre']}/ac/yr")
        with wi2: st.metric("Capacity",f"{d['wind_max_capacity_mw']} MW")
        with wi3: st.metric("Output",f"{d['wind_max_annual_mwh']:,} MWh/yr")
        with wi4: st.metric("Turbines",f"{d['wind_turbines_possible']}")

    # ━━━ MARKET ━━━
    with tab_market:
        st.markdown(f"### {d['wholesale_market']} Market Pricing")
        np.random.seed(42)
        base = {"ERCOT":38,"MISO":30,"PJM":42,"CAISO":52,"SPP":28,"NYISO":48}.get(d["wholesale_market"],35)
        lmp = generate_lmp_history(base)
        fig_l = px.area(lmp,x="Date",y="LMP ($/MWh)",title="12-Month LMP History")
        fig_l.update_traces(fillcolor="rgba(99,102,241,0.2)",line_color="#6366f1")
        fig_l.update_layout(height=320,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#e2e8f0"),xaxis=dict(gridcolor="#334155"),yaxis=dict(gridcolor="#334155"))
        st.plotly_chart(fig_l,use_container_width=True)

        mc1,mc2,mc3,mc4 = st.columns(4)
        with mc1: st.metric("Avg LMP",f"${lmp['LMP ($/MWh)'].mean():.1f}/MWh")
        with mc2: st.metric("Peak LMP",f"${lmp['LMP ($/MWh)'].max():.1f}/MWh")
        with mc3: st.metric("Min LMP",f"${lmp['LMP ($/MWh)'].min():.1f}/MWh")
        with mc4: st.metric("Volatility",f"{lmp['LMP ($/MWh)'].std():.1f}")

        st.markdown("### Revenue Estimate")
        solar_rev = d["solar_max_annual_mwh"] * lmp["LMP ($/MWh)"].mean() / 1000
        wind_rev = d["wind_max_annual_mwh"] * lmp["LMP ($/MWh)"].mean() / 1000
        r1,r2,r3 = st.columns(3)
        with r1: st.metric("Solar Revenue",f"${solar_rev:,.0f}k/yr")
        with r2: st.metric("Wind Revenue",f"${wind_rev:,.0f}k/yr")
        with r3: st.metric("Solar Lease Income",f"${d['solar_lease_per_acre']*acres:,}/yr")

    # ━━━ EXPORT ━━━
    with tab_export:
        st.markdown("### Download Report")
        pdf_bytes = build_pdf(d, score, bd)
        fname = f"SiteIQ_{county.replace(' ','_')}_{state}_{datetime.now().strftime('%Y%m%d')}.pdf"
        st.download_button("Download PDF Report", data=pdf_bytes, file_name=fname, mime="application/pdf", type="primary")

        st.divider()
        e1,e2 = st.columns(2)
        with e1:
            csv = pd.DataFrame([{"lat":lat,"lon":lon,"county":county,"state":state,"acres":acres,
                "score":score,"solar_mw":d["solar_max_capacity_mw"],"wind_mw":d["wind_max_capacity_mw"],
                "trans_dist":d["nearest_trans_dist_mi"],"wetland_ac":d["federal_wetland_acres"],
                "flood":d["flood_zone"],"species":d["species_concerns"],"sentiment":d["community_sentiment"],
                "market":d["wholesale_market"],"land_value":d["land_value_per_acre"]}])
            st.download_button("Download CSV",csv.to_csv(index=False),file_name="SiteIQ_analysis.csv",mime="text/csv")
        with e2:
            geo = {"type":"FeatureCollection","features":[{"type":"Feature",
                "geometry":{"type":"Point","coordinates":[lon,lat]},
                "properties":{"score":score,"acres":acres,"county":county,"state":state}}]}
            st.download_button("Download GeoJSON",json.dumps(geo,indent=2),file_name="SiteIQ_site.geojson",mime="application/json")


def generate_lmp_history(base, days=365):
    dates = [datetime(2024,1,1)+timedelta(days=i) for i in range(days)]
    prices = base + np.cumsum(np.random.randn(days)*1.2)
    prices = np.clip(prices + 8*np.sin(np.linspace(0,2*np.pi,days)),5,120)
    return pd.DataFrame({"Date":dates,"LMP ($/MWh)":np.round(prices,2)})


if __name__ == "__main__":
    main()
