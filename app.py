import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import json
from datetime import datetime, timedelta
from io import BytesIO
from fpdf import FPDF
import base64

st.set_page_config(
    page_title="SiteIQ — Renewable Energy Siting Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    .block-container { padding-top: 1rem; }
    div[data-testid="stSidebar"] { background: #0f172a; }
    .concern-high { background: #fee2e2; border-left: 4px solid #ef4444; padding: 12px; border-radius: 6px; margin: 8px 0; }
    .concern-mod { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; border-radius: 6px; margin: 8px 0; }
    .concern-low { background: #dcfce7; border-left: 4px solid #22c55e; padding: 12px; border-radius: 6px; margin: 8px 0; }
    .parcel-card {
        background: #1e293b; border: 1px solid #334155; border-radius: 10px;
        padding: 16px; margin: 8px 0; cursor: pointer;
    }
    .parcel-card:hover { border-color: #6366f1; }
    .selected-card { border-color: #6366f1 !important; background: #1e293b !important; box-shadow: 0 0 12px rgba(99,102,241,0.3); }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# SITE DATA
# ══════════════════════════════════════════════════════════
@st.cache_data
def load_sites():
    sites = [
        {
            "id": 1,
            "name": "Runnels County Solar Site",
            "state": "TX", "county": "Runnels",
            "lat": 31.83, "lon": -99.98,
            "total_acres": 872.76, "buildable_acres": 867,
            "parcels": [
                {"apn": "R5254", "address": "2059 157 CR", "acres": 624.912, "land_value": 2177,
                 "lat": 31.835, "lon": -100.00, "owner": "Claude Brookshier Estate",
                 "poly": [[31.845, -100.02], [31.845, -99.98], [31.825, -99.98], [31.825, -100.02]]},
                {"apn": "R5253", "address": "157 CR", "acres": 14.951, "land_value": 1153,
                 "lat": 31.828, "lon": -99.975, "owner": "J. Smith",
                 "poly": [[31.832, -99.98], [31.832, -99.97], [31.824, -99.97], [31.824, -99.98]]},
                {"apn": "R6335", "address": "153 EAST AVE", "acres": 87.371, "land_value": 1722,
                 "lat": 31.842, "lon": -99.965, "owner": "East Ave Holdings",
                 "poly": [[31.848, -99.975], [31.848, -99.955], [31.836, -99.955], [31.836, -99.975]]},
                {"apn": "R21930", "address": "164 CR", "acres": 122.916, "land_value": 2315,
                 "lat": 31.82, "lon": -100.01, "owner": "Rodgers Ranch",
                 "poly": [[31.828, -100.025], [31.828, -99.995], [31.812, -99.995], [31.812, -100.025]]},
                {"apn": "R24171", "address": "157 CR", "acres": 22.607, "land_value": 6378,
                 "lat": 31.818, "lon": -99.96, "owner": "Clayton Family Trust",
                 "poly": [[31.823, -99.968], [31.823, -99.952], [31.813, -99.952], [31.813, -99.968]]},
            ],
            "total_land_value": 1956990, "land_value_per_acre": 2062,
            "value_index": {
                "Land": 37, "Solar Energy": 81, "Wind Energy": 1, "EV Charging": 12,
                "Available Power": 22, "Energy Storage": 29, "Green Power": 60,
                "Carbon Credits": 10, "Water": 79, "Building Suitability": 47,
            },
            "risk_index": {
                "Oil & Gas Contamination": 0, "Industrial Contamination": 0,
                "Electricity Blackout": 78, "Cost Of Electricity": 90,
                "Electrical Connection": 76, "Drought": 80, "Wildfire": 96,
                "Natural Earthquakes": 19, "Tornado": 91, "Straight Line Wind": 99,
                "Hail": 78, "Flood": 47,
            },
            "cropland_irrigation_pct": 19.833, "water_stress": 79.2,
            "annual_precip_in": 26.4, "avg_wind_speed_mph": 17,
            "solar_irradiance_wm2": 245, "avg_high_temp_f": 77.6,
            "avg_low_temp_f": 52.2, "avg_slope_deg": 0.7, "max_slope_deg": 4.2,
            "avg_elevation_ft": 1874, "min_elevation_ft": 1840, "max_elevation_ft": 1910,
            "land_cover": [
                {"type": "Shrubland", "acres": 532.8, "value": 0},
                {"type": "Cropland (Winter Wheat)", "acres": 317.7, "value": 426171},
                {"type": "Cropland (Cotton)", "acres": 66.4, "value": 102883},
                {"type": "Developed/Open Space", "acres": 24.6, "value": 1341990},
            ],
            "soils": [
                {"type": "VaA", "quality": 2, "group": "C", "acres": 339.8, "desc": "Valera silty clay, 0-1% slopes", "farmland": "Conditionally Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 3.18},
                {"type": "KvA", "quality": 3, "group": "D", "acres": 217, "desc": "Kavett silty clay, 0-1% slopes", "farmland": "Not Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 1.61},
                {"type": "KvB", "quality": 4, "group": "D", "acres": 129.7, "desc": "Kavett silty clay, 1-3% slopes", "farmland": "Not Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 1.57},
                {"type": "Tk", "quality": 7, "group": "D", "acres": 117.2, "desc": "Talpa-Kavett complex", "farmland": "Not Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 0.59},
                {"type": "McA", "quality": 3, "group": "D", "acres": 39.6, "desc": "Mereta clay loam, 0-1% slopes", "farmland": "Not Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 6.0},
                {"type": "PoA", "quality": 2, "group": "B", "acres": 14.8, "desc": "Quanah clay loam, 0-1% slopes", "farmland": "Prime", "suitability": 100, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 6.0},
            ],
            "solar_lease_per_acre": 245, "direct_irradiance_wm2": 222,
            "corrected_irradiance_wm2": 245, "solar_panels_possible": 567943,
            "solar_max_capacity_mw": 256, "solar_max_annual_mwh": 296362,
            "nearest_solar_farm": "Hanson Solar, LLC", "nearest_solar_dist_mi": 17.894,
            "wind_lease_per_acre": 34, "avg_wind_speed_ms": 7.6,
            "wind_turbines_possible": 10.83, "wind_max_capacity_mw": 35.748,
            "wind_max_annual_mwh": 112331,
            "nearest_wind_farm": "Horse Hollow Wind Energy Center", "nearest_wind_dist_mi": 22.819,
            "nearest_sub_name": "TALPA", "nearest_sub_dist_mi": 10.602,
            "nearest_trans_owner": "AEP TEXAS NORTH COMPANY",
            "nearest_trans_dist_mi": 0.72, "nearest_trans_capacity_mw": 1147,
            "wholesale_market": "ERCOT", "state_incentives_per_mwh": 1.32,
            "federal_wetland_acres": 5, "dwelling_acres": 2, "topo_5pct_acres": 1,
            "flood_risk_score": 47, "flood_zone": "Moderate",
            "oil_gas_value_per_acre": 275, "wells_on_property": 10,
            "cumulative_oil_bbl": 407806, "cumulative_gas_mcf": 369716,
            "soil_carbon_stocks_ton_ac": 19.385, "soil_carbon_credits_yr": 567.28,
            "permits_needed": 8, "federal_permits": 4, "state_permits": 4,
            "species_concerns": "Low", "species_list": [],
            "community_sentiment": "Positive",
            "sentiment_details": ["Pro-development county", "Existing energy infrastructure", "Low population density"],
            "nearest_superfund": "Main Street Ground Water Plume", "superfund_dist_mi": 119.19, "abandoned_wells": 8,
        },
        {
            "id": 2,
            "name": "Benton 100MW Solar Project",
            "state": "MN", "county": "Benton",
            "lat": 45.592, "lon": -94.028,
            "total_acres": 996.64, "buildable_acres": 0,
            "parcels": [
                {"apn": "090016900", "address": "2100 65TH AVE NE", "acres": 245.797, "land_value": 0,
                 "lat": 45.600, "lon": -94.022, "owner": "ALLEN J BAUERLY REV TR",
                 "poly": [[45.608, -94.035], [45.608, -94.009], [45.592, -94.009], [45.592, -94.035]]},
                {"apn": "090037900", "address": "928 65TH AVE NE", "acres": 156.303, "land_value": 0,
                 "lat": 45.590, "lon": -94.030, "owner": "PEGGY JO BESSER REV TR",
                 "poly": [[45.596, -94.040], [45.596, -94.020], [45.584, -94.020], [45.584, -94.040]]},
                {"apn": "090033000", "address": "6223 HIGHWAY 95 NE", "acres": 127.498, "land_value": 0,
                 "lat": 45.588, "lon": -94.036, "owner": "LORIN E BESSER",
                 "poly": [[45.594, -94.045], [45.594, -94.027], [45.582, -94.027], [45.582, -94.045]]},
                {"apn": "090037801", "address": "709 75TH AVE NE", "acres": 121.431, "land_value": 0,
                 "lat": 45.582, "lon": -94.025, "owner": "MCIVER FAMILY TR",
                 "poly": [[45.588, -94.035], [45.588, -94.015], [45.576, -94.015], [45.576, -94.035]]},
                {"apn": "090039600", "address": "763 55TH AVE NE", "acres": 81.055, "land_value": 0,
                 "lat": 45.586, "lon": -94.020, "owner": "JOHN J SVIHEL",
                 "poly": [[45.591, -94.028], [45.591, -94.012], [45.581, -94.012], [45.581, -94.028]]},
            ],
            "total_land_value": 0, "land_value_per_acre": 0,
            "value_index": {
                "Land": 30, "Solar Energy": 65, "Wind Energy": 40, "EV Charging": 8,
                "Available Power": 35, "Energy Storage": 25, "Green Power": 50,
                "Carbon Credits": 15, "Water": 70, "Building Suitability": 40,
            },
            "risk_index": {
                "Oil & Gas Contamination": 0, "Industrial Contamination": 5,
                "Electricity Blackout": 45, "Cost Of Electricity": 60,
                "Electrical Connection": 55, "Drought": 30, "Wildfire": 15,
                "Natural Earthquakes": 5, "Tornado": 65, "Straight Line Wind": 70,
                "Hail": 55, "Flood": 35,
            },
            "cropland_irrigation_pct": 5.0, "water_stress": 30.0,
            "annual_precip_in": 32.0, "avg_wind_speed_mph": 12,
            "solar_irradiance_wm2": 180, "avg_high_temp_f": 58.0,
            "avg_low_temp_f": 32.0, "avg_slope_deg": 2.0, "max_slope_deg": 16.0,
            "avg_elevation_ft": 1050, "min_elevation_ft": 1010, "max_elevation_ft": 1100,
            "land_cover": [
                {"type": "Cultivated Crops", "acres": 776.2, "value": 0},
                {"type": "Deciduous Forest", "acres": 136.0, "value": 0},
                {"type": "Pasture/Hay", "acres": 49.6, "value": 0},
                {"type": "Woody Wetlands", "acres": 8.3, "value": 0},
            ],
            "soils": [
                {"type": "Ronneby loam", "quality": 3, "group": "C/D", "acres": 180, "desc": "0-2% slopes, stony", "farmland": "Not Prime", "suitability": 55, "hydric": 0, "drainage": "Somewhat poorly drained", "bedrock_ft": 6.0},
                {"type": "Hubbard loamy sand", "quality": 2, "group": "A", "acres": 150, "desc": "0-2% slopes", "farmland": "Not Prime", "suitability": 70, "hydric": 0, "drainage": "Excessively drained", "bedrock_ft": 6.0},
                {"type": "Verndale sandy loam", "quality": 2, "group": "A", "acres": 120, "desc": "0-2% slopes", "farmland": "Prime", "suitability": 80, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 6.0},
                {"type": "St. Francis complex", "quality": 3, "group": "A", "acres": 100, "desc": "6-12% slopes", "farmland": "Not Prime", "suitability": 40, "hydric": 0, "drainage": "Excessively drained", "bedrock_ft": 6.0},
                {"type": "Seelyeville/Markey", "quality": 5, "group": "A/D", "acres": 60, "desc": "depressional, 0-1%", "farmland": "Not Prime", "suitability": 15, "hydric": 1, "drainage": "Very poorly drained", "bedrock_ft": 6.0},
            ],
            "solar_lease_per_acre": 200, "direct_irradiance_wm2": 165,
            "corrected_irradiance_wm2": 180, "solar_panels_possible": 450000,
            "solar_max_capacity_mw": 100, "solar_max_annual_mwh": 175000,
            "nearest_solar_farm": "N/A", "nearest_solar_dist_mi": 0,
            "wind_lease_per_acre": 50, "avg_wind_speed_ms": 5.4,
            "wind_turbines_possible": 8, "wind_max_capacity_mw": 24,
            "wind_max_annual_mwh": 65000,
            "nearest_wind_farm": "N/A", "nearest_wind_dist_mi": 0,
            "nearest_sub_name": "On-site", "nearest_sub_dist_mi": 0.42,
            "nearest_trans_owner": "On Site", "nearest_trans_dist_mi": 0.0,
            "nearest_trans_capacity_mw": 0,
            "wholesale_market": "MISO", "state_incentives_per_mwh": 0,
            "federal_wetland_acres": 47.64, "dwelling_acres": 0, "topo_5pct_acres": 30,
            "flood_risk_score": 35, "flood_zone": "X / A (64 ac)",
            "oil_gas_value_per_acre": 0, "wells_on_property": 0,
            "cumulative_oil_bbl": 0, "cumulative_gas_mcf": 0,
            "soil_carbon_stocks_ton_ac": 0, "soil_carbon_credits_yr": 0,
            "permits_needed": 13, "federal_permits": 6, "state_permits": 7,
            "species_concerns": "High",
            "species_list": [
                {"name": "Northern Long-Eared Bat", "scientific": "Myotis septentrionalis", "status": "Endangered", "concern": "Species of Concern"},
                {"name": "Monarch butterfly", "scientific": "Danaus plexippus", "status": "Proposed Threatened", "concern": "Species of Concern"},
                {"name": "Bald Eagle", "scientific": "Haliaeetus leucocephalus", "status": "Recovery", "concern": "May Occur"},
                {"name": "Suckley's cuckoo bumble bee", "scientific": "Bombus suckleyi", "status": "Under Review", "concern": "May Occur"},
            ],
            "community_sentiment": "Mixed",
            "sentiment_details": ["Benton County: Positive", "Minden Township: Positive", "St. George Township: Unsure", "In Energy Community: Yes"],
            "nearest_superfund": "N/A", "superfund_dist_mi": 0, "abandoned_wells": 0,
        },
    ]
    return sites


# ══════════════════════════════════════════════════════════
# SCORING
# ══════════════════════════════════════════════════════════
def compute_site_score(s, weights):
    vi = s["value_index"]
    ri = s["risk_index"]
    solar_s = min(100, vi.get("Solar Energy", 0))
    trans_s = max(0, 100 - s["nearest_trans_dist_mi"] * 10)
    wet_s = max(0, 100 - (s["federal_wetland_acres"] / max(s["total_acres"], 1)) * 500)
    flood_s = max(0, 100 - ri.get("Flood", 50))
    soil_s = np.mean([x["suitability"] for x in s["soils"]]) if s["soils"] else 50
    sent_s = {"Positive": 90, "Mixed": 55, "Unsure": 40, "Negative": 15}.get(s["community_sentiment"], 50)
    cost_s = max(0, 100 - (s.get("land_value_per_acre", 0) / 100))
    total = (
        trans_s * weights["Transmission Proximity"] / 100
        + solar_s * weights["Solar Resource"] / 100
        + wet_s * weights["Wetland Risk"] / 100
        + flood_s * weights["Flood Risk"] / 100
        + soil_s * weights["Soil Suitability"] / 100
        + sent_s * weights["Community Sentiment"] / 100
        + cost_s * weights["Land Cost"] / 100
    )
    bd = {
        "Transmission": round(trans_s), "Solar Resource": round(solar_s),
        "Wetland": round(wet_s), "Flood": round(flood_s),
        "Soil": round(soil_s), "Sentiment": round(sent_s), "Land Cost": round(cost_s),
    }
    return round(total), bd


def generate_lmp_history(base, days=365):
    np.random.seed(42)
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(days)]
    prices = base + np.cumsum(np.random.randn(days) * 1.2)
    prices = np.clip(prices + 8 * np.sin(np.linspace(0, 2 * np.pi, days)), 5, 120)
    return pd.DataFrame({"Date": dates, "LMP ($/MWh)": np.round(prices, 2)})


# ══════════════════════════════════════════════════════════
# PDF GENERATOR (fixed)
# ══════════════════════════════════════════════════════════
def build_pdf(s, score, bd):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    def section(title):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, f"  {title}", fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    def kv(key, val):
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(85, 6, str(key), border=0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, str(val), border=0, ln=True)

    def tbl_head(cols, ws):
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(226, 232, 240)
        for i, c in enumerate(cols):
            pdf.cell(ws[i], 6, c, border=1, fill=True, align="C")
        pdf.ln()

    def tbl_row(vals, ws):
        pdf.set_font("Helvetica", "", 7)
        for i, v in enumerate(vals):
            pdf.cell(ws[i], 5, str(v)[:28], border=1, align="C")
        pdf.ln()

    # ── PAGE 1: COVER ──
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, "SiteIQ", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, "Renewable Energy Site Feasibility Report", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, s["name"], ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"{s['county']} County, {s['state']}", ln=True, align="C")
    pdf.cell(0, 8, f"Report Date: {datetime.now().strftime('%B %d, %Y')}", ln=True, align="C")
    pdf.cell(0, 8, "Project Type: Renewable Energy Generation (Solar)", ln=True, align="C")
    pdf.ln(10)

    # ── KEY DETAILS ──
    section("Key Details")
    kv("Total Acreage", f"{s['total_acres']:,.2f}")
    kv("Buildable Acreage", f"{s['buildable_acres']:,}")
    kv("Site Score", f"{score} / 100")
    kv("Nearest Transmission Line", f"{s['nearest_trans_dist_mi']} mi ({s['nearest_trans_owner']})")
    kv("Nearest Substation", f"{s['nearest_sub_dist_mi']} mi ({s['nearest_sub_name']})")
    kv("Wholesale Market", s["wholesale_market"])
    kv("Permits Needed", f"{s['permits_needed']} ({s['federal_permits']} Federal, {s['state_permits']} State)")
    kv("Landowners", f"{len(s['parcels'])}")
    kv("Community Sentiment", s["community_sentiment"])
    kv("Species Concern Level", s["species_concerns"])
    pdf.ln(4)

    # ── CONCERNS ──
    section("Concerns Summary")
    level_map = {"High": "HIGH CONCERN", "Moderate": "MODERATE", "Low": "LOW"}
    kv("Protected Species", level_map.get(s["species_concerns"], "Low"))
    kv("Waters / Wetlands", f"{s['federal_wetland_acres']} ac federal wetland")
    kv("Flood Risk", f"{s['flood_zone']} (Score: {s['flood_risk_score']}/100)")
    kv("Abandoned Wells", str(s["abandoned_wells"]))
    pdf.ln(4)

    # ── SCORE BREAKDOWN ──
    section("Site Score Breakdown")
    for k, v in bd.items():
        kv(k, f"{v} / 100")
    pdf.ln(4)

    # ── PAGE 2: VALUE + RISK INDEX ──
    pdf.add_page()
    section("Value Index")
    cw = [100, 50]
    tbl_head(["Category", "Score /100"], cw)
    for k, v in s["value_index"].items():
        tbl_row([k, str(v)], cw)
    pdf.ln(4)

    section("Risk Index")
    tbl_head(["Category", "Score /100"], cw)
    for k, v in s["risk_index"].items():
        tbl_row([k, str(v)], cw)

    # ── PAGE 3: LAND + TOPO ──
    pdf.add_page()
    section("Land and Topography")
    kv("Total Land Value", f"${s['total_land_value']:,} (${s['land_value_per_acre']:,}/ac)")
    kv("Elevation (Avg / Min / Max)", f"{s['avg_elevation_ft']:,} / {s['min_elevation_ft']:,} / {s['max_elevation_ft']:,} ft")
    kv("Slope (Avg / Max)", f"{s['avg_slope_deg']} deg / {s['max_slope_deg']} deg")
    kv("Annual Precipitation", f"{s['annual_precip_in']} in")
    kv("Avg Wind Speed", f"{s['avg_wind_speed_mph']} mph")
    kv("Solar Irradiance (3D)", f"{s['solar_irradiance_wm2']} W/m2")
    kv("Avg High / Low Temp", f"{s['avg_high_temp_f']} F / {s['avg_low_temp_f']} F")
    pdf.ln(4)

    section("Land Cover")
    lw = [80, 35, 40]
    tbl_head(["Type", "Acres", "Value ($)"], lw)
    for lc in s["land_cover"]:
        tbl_row([lc["type"], f"{lc['acres']:.1f}", f"${lc['value']:,}"], lw)
    pdf.ln(4)

    # ── SOILS ──
    section("Soil Analysis")
    sw = [22, 16, 14, 14, 14, 14, 42, 22]
    tbl_head(["Type", "Acres", "Qual", "Grp", "Suit.", "Hydric", "Drainage", "Bedrock"], sw)
    for soil in s["soils"]:
        tbl_row([soil["type"], f"{soil['acres']:.0f}", str(soil["quality"]), soil["group"],
                 str(soil["suitability"]), "Yes" if soil["hydric"] else "No",
                 soil["drainage"][:18], f"{soil['bedrock_ft']}ft"], sw)
    pdf.ln(4)

    # ── PAGE 4: SOLAR + WIND + INFRA ──
    pdf.add_page()
    section("Solar Farm Analysis")
    kv("Est. Solar Lease", f"${s['solar_lease_per_acre']}/ac/yr")
    kv("Direct Irradiance", f"{s['direct_irradiance_wm2']} W/m2")
    kv("Corrected Irradiance", f"{s['corrected_irradiance_wm2']} W/m2")
    kv("Possible Solar Panels", f"{s['solar_panels_possible']:,}")
    kv("Max Capacity", f"{s['solar_max_capacity_mw']} MW")
    kv("Max Annual Output", f"{s['solar_max_annual_mwh']:,} MWh")
    kv("Nearest Solar Farm", f"{s['nearest_solar_farm']} ({s['nearest_solar_dist_mi']} mi)")
    pdf.ln(4)

    section("Wind Analysis")
    kv("Est. Wind Lease", f"${s['wind_lease_per_acre']}/ac/yr")
    kv("Avg Wind Speed", f"{s['avg_wind_speed_ms']} m/s")
    kv("Possible Turbines", str(s["wind_turbines_possible"]))
    kv("Max Capacity", f"{s['wind_max_capacity_mw']} MW")
    kv("Max Annual Output", f"{s['wind_max_annual_mwh']:,} MWh")
    pdf.ln(4)

    section("Electrical Infrastructure")
    kv("Nearest Substation", f"{s['nearest_sub_name']} - {s['nearest_sub_dist_mi']} mi")
    kv("Nearest Trans Line", f"{s['nearest_trans_owner']} - {s['nearest_trans_dist_mi']} mi")
    kv("Trans Capacity", f"{s['nearest_trans_capacity_mw']} MW")
    kv("Wholesale Market", s["wholesale_market"])
    pdf.ln(4)

    # ── SPECIES ──
    if s["species_list"]:
        section("Protected Species")
        spw = [55, 45, 45]
        tbl_head(["Name", "Status", "Concern"], spw)
        for sp in s["species_list"]:
            tbl_row([sp["name"], sp["status"], sp["concern"]], spw)
        pdf.ln(4)

    # ── PARCELS ──
    pdf.add_page()
    section("Parcel Details")
    pw = [28, 50, 30, 30, 30]
    tbl_head(["APN", "Address", "Owner", "Acres", "Value"], pw)
    for p in s["parcels"]:
        owner = p.get("owner", "N/A")[:20]
        tbl_row([p["apn"], p["address"][:22], owner, f"{p['acres']:.1f}", f"${p['land_value']:,}"], pw)
    pdf.ln(4)

    # ── COMMUNITY ──
    section("Community Sentiment")
    kv("Overall", s["community_sentiment"])
    for d in s["sentiment_details"]:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, f"  - {d}", ln=True)
    pdf.ln(4)

    # ── OIL & GAS ──
    if s["wells_on_property"] > 0:
        section("Oil and Gas")
        kv("Est. O&G Value", f"${s['oil_gas_value_per_acre']}/acre")
        kv("Wells on Property", str(s["wells_on_property"]))
        kv("Cumulative Oil", f"{s['cumulative_oil_bbl']:,} bbl")
        kv("Cumulative Gas", f"{s['cumulative_gas_mcf']:,} Mcf")

    # ── FINAL PAGE ──
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "SiteIQ Renewable Energy Siting Platform", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "Data sources: USGS, USFWS, FEMA, NRCS, ERCOT, MISO, EPA", ln=True, align="C")
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")

    return bytes(pdf.output())


# ══════════════════════════════════════════════════════════
# MAP — Interactive with parcel selection
# ══════════════════════════════════════════════════════════
def build_parcel_map(s, selected_apn=None):
    center_lat = np.mean([p["lat"] for p in s["parcels"]])
    center_lon = np.mean([p["lon"] for p in s["parcels"]])
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles=None)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", control=True,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB", name="Dark", control=True,
    ).add_to(m)

    for p in s["parcels"]:
        is_selected = p["apn"] == selected_apn
        color = "#6366f1" if is_selected else "#22d3ee"
        weight = 4 if is_selected else 2
        fill_opacity = 0.35 if is_selected else 0.15

        if "poly" in p:
            folium.Polygon(
                locations=p["poly"],
                color=color, weight=weight,
                fill=True, fill_color=color, fill_opacity=fill_opacity,
                tooltip=f"{p['apn']} - {p.get('owner', 'N/A')} - {p['acres']:.1f} ac",
                popup=folium.Popup(
                    f"<b>{p['apn']}</b><br>"
                    f"Owner: {p.get('owner', 'N/A')}<br>"
                    f"Address: {p['address']}<br>"
                    f"Acres: {p['acres']:.1f}<br>"
                    f"Value: ${p['land_value']:,}",
                    max_width=250,
                ),
            ).add_to(m)

        folium.Marker(
            [p["lat"], p["lon"]],
            icon=folium.DivIcon(html=f"""
                <div style='font-size:10px;color:{'#fff' if is_selected else '#94a3b8'};
                font-weight:{'bold' if is_selected else 'normal'};
                background:{'#6366f1' if is_selected else '#1e293bcc'};
                padding:2px 6px;border-radius:4px;white-space:nowrap;
                border:1px solid {"#818cf8" if is_selected else "#475569"}'>{p['apn']}</div>
            """),
            tooltip=f"Click to select {p['apn']}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def build_overview_map(sites, scores):
    m = folium.Map(location=[38.5, -96], zoom_start=5, tiles=None)
    folium.TileLayer(tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", attr="CartoDB", name="Dark", control=False).add_to(m)
    for s in sites:
        sc = scores.get(s["id"], 50)
        color = "#22c55e" if sc >= 75 else "#f59e0b" if sc >= 50 else "#ef4444"
        folium.CircleMarker(
            [s["lat"], s["lon"]], radius=16, color=color, fill=True, fill_color=color,
            fill_opacity=0.6, weight=2,
            tooltip=f"{s['name']} - Score: {sc}/100",
            popup=folium.Popup(f"<b>{s['name']}</b><br>Score: {sc}/100<br>{s['total_acres']:,.0f} ac<br>{s['county']} Co, {s['state']}", max_width=250),
        ).add_to(m)
    return m


def index_bar_chart(data, title, color_scale):
    df = pd.DataFrame({"Category": list(data.keys()), "Score": list(data.values())})
    df = df.sort_values("Score", ascending=True)
    fig = px.bar(df, x="Score", y="Category", orientation="h", color="Score",
                 color_continuous_scale=color_scale, range_color=[0, 100])
    fig.update_layout(
        height=max(280, len(data) * 28), showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=11),
        xaxis=dict(range=[0, 100], gridcolor="#334155"),
        yaxis=dict(gridcolor="#334155"),
        coloraxis_showscale=False, title=title,
    )
    return fig


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
def main():
    sites = load_sites()

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("## ⚡ SiteIQ")
        st.caption("Renewable Energy Siting Intelligence")
        st.divider()
        st.markdown("### Scoring Weights")
        weights = {}
        weights["Transmission Proximity"] = st.slider("Transmission Proximity", 0, 40, 20)
        weights["Solar Resource"] = st.slider("Solar Resource", 0, 40, 20)
        weights["Wetland Risk"] = st.slider("Wetland Risk", 0, 40, 15)
        weights["Flood Risk"] = st.slider("Flood Risk", 0, 40, 10)
        weights["Soil Suitability"] = st.slider("Soil Suitability", 0, 40, 15)
        weights["Community Sentiment"] = st.slider("Community Sentiment", 0, 40, 10)
        weights["Land Cost"] = st.slider("Land Cost", 0, 40, 10)
        tw = sum(weights.values())
        if tw != 100:
            st.warning(f"Weights total **{tw}%** - should be 100%")
        else:
            st.success("Weights total 100%")

    scores = {}
    breakdowns = {}
    for s in sites:
        sc, bd = compute_site_score(s, weights)
        scores[s["id"]] = sc
        breakdowns[s["id"]] = bd

    st.markdown("# ⚡ SiteIQ — Renewable Energy Siting Intelligence")

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Sites Analyzed", len(sites))
    with k2: st.metric("Total Acreage", f"{sum(s['total_acres'] for s in sites):,.0f}")
    with k3: st.metric("Avg Score", f"{np.mean(list(scores.values())):.0f}/100")
    with k4: st.metric("Permits Flagged", sum(s["permits_needed"] for s in sites))

    tab_map, tab_parcels, tab_report, tab_env, tab_infra, tab_export = st.tabs([
        "Overview Map", "Parcel Selector", "Site Report",
        "Environmental", "Infrastructure", "Export PDF",
    ])

    # ── OVERVIEW MAP ──
    with tab_map:
        st.markdown("### All Sites Overview")
        om = build_overview_map(sites, scores)
        st_folium(om, width=None, height=500, returned_objects=[])
        rdf = pd.DataFrame([{
            "Site": s["name"], "State": s["state"], "Acres": s["total_acres"],
            "Score": scores[s["id"]], "Species": s["species_concerns"],
            "Permits": s["permits_needed"], "Sentiment": s["community_sentiment"],
        } for s in sites]).sort_values("Score", ascending=False)
        rdf.index = range(1, len(rdf) + 1)
        st.dataframe(rdf, use_container_width=True)

    # ── PARCEL SELECTOR (interactive map) ──
    with tab_parcels:
        st.markdown("### Interactive Parcel Selection")
        st.caption("Select a site, then click a parcel on the map to view its details.")

        site_name = st.selectbox("Choose Site", [s["name"] for s in sites], key="parcel_site")
        s = [x for x in sites if x["name"] == site_name][0]

        # Parcel selector
        apn_list = [p["apn"] for p in s["parcels"]]
        selected_apn = st.selectbox(
            "Select Parcel (or click on map)",
            ["All Parcels"] + apn_list,
            key="parcel_apn",
        )
        sel_apn = None if selected_apn == "All Parcels" else selected_apn

        # Map
        pm = build_parcel_map(s, sel_apn)
        map_data = st_folium(pm, width=None, height=480, returned_objects=["last_object_clicked"])

        # If user clicked a location on the map, find nearest parcel
        if map_data and map_data.get("last_object_clicked"):
            click_lat = map_data["last_object_clicked"].get("lat")
            click_lng = map_data["last_object_clicked"].get("lng")
            if click_lat and click_lng:
                dists = []
                for p in s["parcels"]:
                    d = ((p["lat"] - click_lat) ** 2 + (p["lon"] - click_lng) ** 2) ** 0.5
                    dists.append((d, p))
                dists.sort(key=lambda x: x[0])
                if dists and dists[0][0] < 0.02:
                    sel_apn = dists[0][1]["apn"]

        # Show parcel details
        if sel_apn:
            p = [x for x in s["parcels"] if x["apn"] == sel_apn][0]
            st.markdown(f"### Parcel: {p['apn']}")
            pc1, pc2, pc3, pc4 = st.columns(4)
            with pc1: st.metric("APN", p["apn"])
            with pc2: st.metric("Acres", f"{p['acres']:.1f}")
            with pc3: st.metric("Owner", p.get("owner", "N/A"))
            with pc4: st.metric("Land Value", f"${p['land_value']:,}")
            st.markdown(f"**Address:** {p['address']}")
            st.markdown(f"**Coordinates:** {p['lat']:.4f}, {p['lon']:.4f}")
        else:
            st.markdown("### All Parcels")
            pdf_df = pd.DataFrame(s["parcels"])[["apn", "address", "acres", "land_value", "owner"]]
            pdf_df.columns = ["APN", "Address", "Acres", "Land Value ($)", "Owner"]
            st.dataframe(pdf_df, use_container_width=True, hide_index=True)

        # Acreage summary
        st.markdown("### Acreage Summary")
        ac1, ac2, ac3, ac4 = st.columns(4)
        with ac1: st.metric("Gross Acreage", f"{s['total_acres']:,.1f}")
        with ac2: st.metric("Buildable", f"{s['buildable_acres']:,}")
        with ac3: st.metric("Wetland", f"{s['federal_wetland_acres']} ac")
        with ac4: st.metric("Dwelling", f"{s['dwelling_acres']} ac")

    # ── SITE REPORT ──
    with tab_report:
        sel = st.selectbox("Select Site", [s["name"] for s in sites], key="report_sel")
        s = [x for x in sites if x["name"] == sel][0]
        sc = scores[s["id"]]
        bd = breakdowns[s["id"]]
        color = "#22c55e" if sc >= 75 else "#f59e0b" if sc >= 50 else "#ef4444"

        st.markdown(f"""<div style='display:flex;align-items:center;gap:24px;margin-bottom:16px'>
            <div style='font-size:4rem;font-weight:900;color:{color}'>{sc}</div>
            <div><div style='font-size:1.5rem;font-weight:700'>{s['name']}</div>
            <div style='color:#94a3b8'>{s['county']} County, {s['state']} | {s['total_acres']:,.1f} acres | {s['buildable_acres']:,} buildable</div></div></div>""", unsafe_allow_html=True)

        # Concerns
        st.markdown("### Concerns Summary")
        c1, c2, c3 = st.columns(3)
        with c1:
            cls = {"High": "concern-high", "Moderate": "concern-mod", "Low": "concern-low"}.get(s["species_concerns"], "concern-low")
            st.markdown(f"<div class='{cls}'><b>Protected Species</b><br>{s['species_concerns']} Concern<br>{len(s['species_list'])} species flagged</div>", unsafe_allow_html=True)
        with c2:
            wcls = "concern-high" if s["federal_wetland_acres"] > 30 else "concern-mod" if s["federal_wetland_acres"] > 10 else "concern-low"
            st.markdown(f"<div class='{wcls}'><b>Waters / Wetlands</b><br>{s['federal_wetland_acres']} ac wetlands<br>Flood: {s['flood_zone']}</div>", unsafe_allow_html=True)
        with c3:
            pcls = "concern-high" if s["permits_needed"] > 10 else "concern-mod" if s["permits_needed"] > 5 else "concern-low"
            st.markdown(f"<div class='{pcls}'><b>Permits Required</b><br>{s['permits_needed']} total<br>{s['federal_permits']} Federal, {s['state_permits']} State</div>", unsafe_allow_html=True)

        # Value + Risk Index
        st.markdown("### Value & Risk Indexes")
        vi_col, ri_col = st.columns(2)
        with vi_col:
            st.plotly_chart(index_bar_chart(s["value_index"], "Value Index", ["#ef4444", "#f59e0b", "#22c55e"]), use_container_width=True)
        with ri_col:
            st.plotly_chart(index_bar_chart(s["risk_index"], "Risk Index", ["#22c55e", "#f59e0b", "#ef4444"]), use_container_width=True)

        # Score Radar
        st.markdown("### Score Breakdown")
        cats = list(bd.keys())
        vals = list(bd.values())
        fig_r = go.Figure(go.Scatterpolar(r=vals + [vals[0]], theta=cats + [cats[0]], fill="toself", fillcolor="rgba(99,102,241,0.2)", line=dict(color="#6366f1", width=2)))
        fig_r.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=350, margin=dict(l=60, r=60, t=30, b=30), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
        st.plotly_chart(fig_r, use_container_width=True)

        # Land cover
        st.markdown("### Land Cover")
        lc_df = pd.DataFrame(s["land_cover"])
        fig_lc = px.pie(lc_df, values="acres", names="type", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
        fig_lc.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
        st.plotly_chart(fig_lc, use_container_width=True)

    # ── ENVIRONMENTAL ──
    with tab_env:
        sel2 = st.selectbox("Select Site", [s["name"] for s in sites], key="env_sel")
        s = [x for x in sites if x["name"] == sel2][0]

        st.markdown("### Soil Analysis")
        soil_df = pd.DataFrame(s["soils"])
        soil_df.columns = ["Type", "Quality", "Group", "Acres", "Description", "Farmland", "Suitability", "Hydric", "Drainage", "Bedrock (ft)"]
        soil_df["Hydric"] = soil_df["Hydric"].map({0: "No", 1: "Yes"})
        st.dataframe(soil_df, use_container_width=True, hide_index=True)

        s1, s2 = st.columns(2)
        with s1:
            fig_soil = px.bar(soil_df, x="Type", y="Suitability", color="Suitability", color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"], range_color=[0, 100], title="Soil Suitability")
            fig_soil.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"), coloraxis_showscale=False)
            st.plotly_chart(fig_soil, use_container_width=True)
        with s2:
            fig_bed = px.bar(soil_df, x="Type", y="Bedrock (ft)", title="Depth to Bedrock (ft)", color="Bedrock (ft)", color_continuous_scale=["#fbbf24", "#22c55e"])
            fig_bed.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"), coloraxis_showscale=False)
            st.plotly_chart(fig_bed, use_container_width=True)

        st.markdown("### Protected Species")
        if s["species_list"]:
            for sp in s["species_list"]:
                ccls = "concern-high" if sp["concern"] == "Species of Concern" else "concern-mod"
                st.markdown(f"<div class='{ccls}'><b>{sp['name']}</b> (<i>{sp['scientific']}</i>)<br>Federal Status: <b>{sp['status']}</b> | Assessment: <b>{sp['concern']}</b></div>", unsafe_allow_html=True)
        else:
            st.success("No protected species of concern identified.")

        st.markdown("### Wetlands & Floodplains")
        w1, w2, w3 = st.columns(3)
        with w1: st.metric("Federal Wetland", f"{s['federal_wetland_acres']} ac")
        with w2: st.metric("Flood Zone", s["flood_zone"])
        with w3: st.metric("Flood Risk Score", f"{s['flood_risk_score']}/100")

        st.markdown("### Community Sentiment")
        st.metric("Overall", s["community_sentiment"])
        for d in s["sentiment_details"]:
            st.markdown(f"- {d}")

    # ── INFRASTRUCTURE ──
    with tab_infra:
        sel3 = st.selectbox("Select Site", [s["name"] for s in sites], key="infra_sel")
        s = [x for x in sites if x["name"] == sel3][0]

        st.markdown("### Electrical Infrastructure")
        e1, e2, e3 = st.columns(3)
        with e1:
            st.metric("Nearest Substation", s["nearest_sub_name"])
            st.metric("Distance", f"{s['nearest_sub_dist_mi']} mi")
        with e2:
            st.metric("Nearest Trans. Line", s["nearest_trans_owner"][:25])
            st.metric("Distance", f"{s['nearest_trans_dist_mi']} mi")
        with e3:
            st.metric("Capacity", f"{s['nearest_trans_capacity_mw']} MW")
            st.metric("Market", s["wholesale_market"])

        st.markdown("### Solar Farm Potential")
        so1, so2, so3, so4 = st.columns(4)
        with so1: st.metric("Lease", f"${s['solar_lease_per_acre']}/ac/yr")
        with so2: st.metric("Max Capacity", f"{s['solar_max_capacity_mw']} MW")
        with so3: st.metric("Annual Output", f"{s['solar_max_annual_mwh']:,} MWh")
        with so4: st.metric("Panels", f"{s['solar_panels_possible']:,}")

        st.markdown("### Wind Potential")
        wi1, wi2, wi3, wi4 = st.columns(4)
        with wi1: st.metric("Lease", f"${s['wind_lease_per_acre']}/ac/yr")
        with wi2: st.metric("Max Capacity", f"{s['wind_max_capacity_mw']} MW")
        with wi3: st.metric("Annual Output", f"{s['wind_max_annual_mwh']:,} MWh")
        with wi4: st.metric("Wind Speed", f"{s['avg_wind_speed_ms']} m/s")

        st.markdown("### Historical LMP Pricing")
        base_lmp = 35 if s["wholesale_market"] == "ERCOT" else 28
        lmp_df = generate_lmp_history(base_lmp)
        fig_lmp = px.area(lmp_df, x="Date", y="LMP ($/MWh)", title=f"{s['wholesale_market']} Node - 12 Month LMP")
        fig_lmp.update_traces(fillcolor="rgba(99,102,241,0.2)", line_color="#6366f1")
        fig_lmp.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"), xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155"))
        st.plotly_chart(fig_lmp, use_container_width=True)

        if s["wells_on_property"] > 0:
            st.markdown("### Oil & Gas")
            og1, og2, og3 = st.columns(3)
            with og1: st.metric("Wells", s["wells_on_property"])
            with og2: st.metric("Oil (cum.)", f"{s['cumulative_oil_bbl']:,} bbl")
            with og3: st.metric("Gas (cum.)", f"{s['cumulative_gas_mcf']:,} Mcf")

    # ── EXPORT PDF ──
    with tab_export:
        st.markdown("### Export Feasibility Report")
        sel4 = st.selectbox("Select Site", [s["name"] for s in sites], key="pdf_sel")
        s = [x for x in sites if x["name"] == sel4][0]
        sc = scores[s["id"]]
        bd = breakdowns[s["id"]]

        st.info("Click below to generate a multi-page PDF report with all site data, soil tables, species, infrastructure, and parcel details.")

        pdf_bytes = build_pdf(s, sc, bd)
        safe = s["name"].replace(" ", "_").replace("/", "_")
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"SiteIQ_{safe}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary",
        )

        st.divider()
        st.markdown("### Additional Exports")
        ec1, ec2 = st.columns(2)
        with ec1:
            csv_rows = []
            for s2 in sites:
                csv_rows.append({
                    "name": s2["name"], "state": s2["state"], "county": s2["county"],
                    "acres": s2["total_acres"], "score": scores[s2["id"]],
                    "species_concern": s2["species_concerns"], "permits": s2["permits_needed"],
                    "sentiment": s2["community_sentiment"],
                    "trans_dist_mi": s2["nearest_trans_dist_mi"],
                    "solar_mw": s2["solar_max_capacity_mw"],
                    "wetland_acres": s2["federal_wetland_acres"],
                })
            st.download_button("Download All Sites CSV", pd.DataFrame(csv_rows).to_csv(index=False), file_name="SiteIQ_Sites.csv", mime="text/csv")
        with ec2:
            geojson = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [s2["lon"], s2["lat"]]},
                    "properties": {"name": s2["name"], "score": scores[s2["id"]], "acres": s2["total_acres"]},
                } for s2 in sites],
            }
            st.download_button("Download GeoJSON", json.dumps(geojson, indent=2), file_name="SiteIQ_Sites.geojson", mime="application/json")


if __name__ == "__main__":
    main()
