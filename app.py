import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import json
from datetime import datetime, timedelta
from fpdf import FPDF
import tempfile
import os
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
    .idx-bar { height: 18px; border-radius: 4px; display: inline-block; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# DATA — Modeled after LandGate + Transect reports
# ══════════════════════════════════════════════════
@st.cache_data
def load_sites():
    sites = [
        {
            "id": 1,
            "name": "Runnels County Solar Site",
            "state": "TX", "county": "Runnels",
            "lat": 31.83, "lon": -99.98,
            "total_acres": 872.76, "buildable_acres": 867,
            "parcel_ids": ["R5254", "R5253", "R6335", "R21930", "R24171"],
            "parcels": [
                {"apn": "R5254", "address": "2059 157 CR", "acres": 624.912, "land_value": 2177},
                {"apn": "R5253", "address": "157 CR", "acres": 14.951, "land_value": 1153},
                {"apn": "R6335", "address": "153 EAST AVE", "acres": 87.371, "land_value": 1722},
                {"apn": "R21930", "address": "164 CR", "acres": 122.916, "land_value": 2315},
                {"apn": "R24171", "address": "157 CR", "acres": 22.607, "land_value": 6378},
            ],
            "total_land_value": 1956990, "land_value_per_acre": 2062,
            # LandGate Value Index
            "value_index": {
                "Land": 37, "Solar Energy": 81, "Wind Energy": 1, "EV Charging": 12,
                "Available Power": 22, "Energy Storage": 29, "Data Center": 33,
                "Green Power": 60, "Carbon Credits": 10, "Carbon Sequestration": 10,
                "Minerals": 20, "Mining": 0, "Water": 79, "Commercial & Industrial": 10,
                "Building Suitability": 47,
            },
            # LandGate Risk Index
            "risk_index": {
                "Oil & Gas Contamination": 0, "Industrial Contamination": 0,
                "Electricity Blackout": 78, "Cost Of Electricity": 90,
                "Electrical Connection": 76, "Drought": 80, "Wildfire": 96,
                "Natural Earthquakes": 19, "Induced Earthquakes": 0,
                "Hurricane": 41, "Tornado": 91, "Straight Line Wind": 99,
                "Hail": 78, "Flood": 47,
            },
            # Land details
            "cropland_irrigation_pct": 19.833, "water_stress": 79.2,
            "annual_precip_in": 26.4, "avg_wind_speed_mph": 17,
            "solar_irradiance_wm2": 245, "avg_high_temp_f": 77.6,
            "avg_low_temp_f": 52.2, "avg_slope_deg": 0.7, "max_slope_deg": 4.2,
            # Elevation
            "avg_elevation_ft": 1874, "min_elevation_ft": 1840, "max_elevation_ft": 1910,
            # Land cover
            "land_cover": [
                {"type": "Shrubland", "acres": 532.8, "value": 0},
                {"type": "Cropland (Winter Wheat)", "acres": 317.7, "value": 426171},
                {"type": "Cropland (Cotton)", "acres": 66.4, "value": 102883},
                {"type": "Developed/Open Space", "acres": 24.6, "value": 1341990},
            ],
            # Soil (from LandGate report)
            "soils": [
                {"type": "VaA", "quality": 2, "group": "C", "acres": 339.8, "desc": "Valera silty clay, 0-1% slopes", "farmland": "Conditionally Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 3.18},
                {"type": "KvA", "quality": 3, "group": "D", "acres": 217, "desc": "Kavett silty clay, 0-1% slopes", "farmland": "Not Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 1.61},
                {"type": "KvB", "quality": 4, "group": "D", "acres": 129.7, "desc": "Kavett silty clay, cool, 1-3% slopes", "farmland": "Not Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 1.57},
                {"type": "Tk", "quality": 7, "group": "D", "acres": 117.2, "desc": "Talpa-Kavett complex", "farmland": "Not Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 0.59},
                {"type": "McA", "quality": 3, "group": "D", "acres": 39.6, "desc": "Mereta clay loam, 0-1% slopes", "farmland": "Not Prime", "suitability": 45, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 6.0},
                {"type": "PoA", "quality": 2, "group": "B", "acres": 14.8, "desc": "Quanah clay loam, 0-1% slopes", "farmland": "Prime", "suitability": 100, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 6.0},
            ],
            # Solar
            "solar_lease_per_acre": 245, "direct_irradiance_wm2": 222,
            "corrected_irradiance_wm2": 245, "solar_panels_possible": 567943,
            "solar_max_capacity_mw": 256, "solar_max_annual_mwh": 296362,
            "nearest_solar_farm": "Hanson Solar, LLC", "nearest_solar_dist_mi": 17.894,
            # Wind
            "wind_lease_per_acre": 34, "avg_wind_speed_ms": 7.6,
            "wind_turbines_possible": 10.83, "wind_max_capacity_mw": 35.748,
            "wind_max_annual_mwh": 112331,
            "nearest_wind_farm": "Horse Hollow Wind Energy Center", "nearest_wind_dist_mi": 22.819,
            # Electrical Infrastructure
            "nearest_sub_name": "TALPA", "nearest_sub_dist_mi": 10.602,
            "nearest_trans_owner": "AEP TEXAS NORTH COMPANY",
            "nearest_trans_dist_mi": 0.72, "nearest_trans_capacity_mw": 1147,
            "wholesale_market": "ERCOT", "state_incentives_per_mwh": 1.32,
            # Wetlands / Property Features
            "federal_wetland_acres": 5, "dwelling_acres": 2, "topo_5pct_acres": 1,
            # Flood
            "flood_risk_score": 47, "flood_zone": "Moderate",
            # Oil & Gas
            "oil_gas_value_per_acre": 275, "wells_on_property": 10,
            "cumulative_oil_bbl": 407806, "cumulative_gas_mcf": 369716,
            # Carbon
            "soil_carbon_stocks_ton_ac": 19.385, "soil_carbon_credits_yr": 567.28,
            # Permits (Transect-style)
            "permits_needed": 8,
            "federal_permits": 4, "state_permits": 4,
            # Species concerns
            "species_concerns": "Low",
            "species_list": [],
            # Community sentiment
            "community_sentiment": "Positive",
            "sentiment_details": ["Pro-development county", "Existing energy infrastructure", "Low population density"],
            # Contamination
            "nearest_superfund": "Main Street Ground Water Plume",
            "superfund_dist_mi": 119.19,
            "abandoned_wells": 8,
        },
        {
            "id": 2,
            "name": "Benton County Solar (BENTON 100MW)",
            "state": "MN", "county": "Benton",
            "lat": 45.592, "lon": -94.028,
            "total_acres": 996.64, "buildable_acres": 0,
            "parcel_ids": ["090016900", "090037900", "090033000", "090037801"],
            "parcels": [
                {"apn": "090016900", "address": "2100 65TH AVE NE", "acres": 245.797, "land_value": 0, "owner": "ALLEN J BAUERLY REV TR"},
                {"apn": "090037900", "address": "928 65TH AVE NE", "acres": 156.303, "land_value": 0, "owner": "PEGGY JO BESSER REV TR"},
                {"apn": "090033000", "address": "6223 HIGHWAY 95 NE", "acres": 127.498, "land_value": 0, "owner": "LORIN E BESSER"},
                {"apn": "090037801", "address": "709 75TH AVE NE", "acres": 121.431, "land_value": 0, "owner": "MCIVER FAMILY TR"},
                {"apn": "090039600", "address": "763 55TH AVE NE", "acres": 81.055, "land_value": 0, "owner": "JOHN J SVIHEL"},
            ],
            "total_land_value": 0, "land_value_per_acre": 0,
            "value_index": {
                "Land": 30, "Solar Energy": 65, "Wind Energy": 40, "EV Charging": 8,
                "Available Power": 35, "Energy Storage": 25, "Data Center": 20,
                "Green Power": 50, "Carbon Credits": 15, "Carbon Sequestration": 20,
                "Minerals": 5, "Mining": 0, "Water": 70, "Commercial & Industrial": 15,
                "Building Suitability": 40,
            },
            "risk_index": {
                "Oil & Gas Contamination": 0, "Industrial Contamination": 5,
                "Electricity Blackout": 45, "Cost Of Electricity": 60,
                "Electrical Connection": 55, "Drought": 30, "Wildfire": 15,
                "Natural Earthquakes": 5, "Induced Earthquakes": 0,
                "Hurricane": 5, "Tornado": 65, "Straight Line Wind": 70,
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
                {"type": "Developed, Low Intensity", "acres": 11.9, "value": 0},
                {"type": "Woody Wetlands", "acres": 8.3, "value": 0},
            ],
            "soils": [
                {"type": "Ronneby loam", "quality": 3, "group": "C/D", "acres": 180, "desc": "0-2% slopes, stony", "farmland": "Not Prime", "suitability": 55, "hydric": 0, "drainage": "Somewhat poorly drained", "bedrock_ft": 6.0},
                {"type": "Hubbard loamy sand", "quality": 2, "group": "A", "acres": 150, "desc": "0-2% slopes", "farmland": "Not Prime", "suitability": 70, "hydric": 0, "drainage": "Excessively drained", "bedrock_ft": 6.0},
                {"type": "Verndale sandy loam", "quality": 2, "group": "A", "acres": 120, "desc": "acid substratum, 0-2% slopes", "farmland": "Prime", "suitability": 80, "hydric": 0, "drainage": "Well drained", "bedrock_ft": 6.0},
                {"type": "St. Francis-Mahtomedi", "quality": 3, "group": "A", "acres": 100, "desc": "6-12% slopes complex", "farmland": "Not Prime", "suitability": 40, "hydric": 0, "drainage": "Somewhat excessively drained", "bedrock_ft": 6.0},
                {"type": "Seelyeville/Markey", "quality": 5, "group": "A/D", "acres": 60, "desc": "depressional, 0-1% slopes", "farmland": "Not Prime", "suitability": 15, "hydric": 1, "drainage": "Very poorly drained", "bedrock_ft": 6.0},
            ],
            "solar_lease_per_acre": 200, "direct_irradiance_wm2": 165,
            "corrected_irradiance_wm2": 180, "solar_panels_possible": 450000,
            "solar_max_capacity_mw": 100, "solar_max_annual_mwh": 175000,
            "nearest_solar_farm": "N/A", "nearest_solar_dist_mi": 0,
            "wind_lease_per_acre": 50, "avg_wind_speed_ms": 5.4,
            "wind_turbines_possible": 8, "wind_max_capacity_mw": 24,
            "wind_max_annual_mwh": 65000,
            "nearest_wind_farm": "N/A", "nearest_wind_dist_mi": 0,
            "nearest_sub_name": "On-site Substation", "nearest_sub_dist_mi": 0.42,
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


# ══════════════════════════════════════════════════
# SCORING ENGINE
# ══════════════════════════════════════════════════
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
    bd = {"Transmission": round(trans_s), "Solar Resource": round(solar_s), "Wetland": round(wet_s),
          "Flood": round(flood_s), "Soil": round(soil_s), "Sentiment": round(sent_s), "Land Cost": round(cost_s)}
    return round(total), bd


def generate_lmp_history(base, days=365):
    np.random.seed(42)
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(days)]
    prices = base + np.cumsum(np.random.randn(days) * 1.2)
    prices = np.clip(prices + 8 * np.sin(np.linspace(0, 2 * np.pi, days)), 5, 120)
    return pd.DataFrame({"Date": dates, "LMP ($/MWh)": np.round(prices, 2)})


# ══════════════════════════════════════════════════
# PDF REPORT GENERATOR
# ══════════════════════════════════════════════════
class SiteIQPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "SiteIQ - Renewable Energy Site Feasibility Report", border=False, ln=True, align="C")
        self.set_draw_color(99, 102, 241)
        self.line(10, 18, 200, 18)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | SiteIQ Platform", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(30, 41, 59)
        self.set_text_color(255)
        self.cell(0, 8, f"  {title}", fill=True, ln=True)
        self.set_text_color(0)
        self.ln(2)

    def kv_row(self, key, value):
        self.set_font("Helvetica", "", 10)
        self.cell(80, 6, key, border=0)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, str(value), border=0, ln=True)

    def table_header(self, cols, widths):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(226, 232, 240)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, col, border=1, fill=True, align="C")
        self.ln()

    def table_row(self, vals, widths):
        self.set_font("Helvetica", "", 8)
        for i, val in enumerate(vals):
            self.cell(widths[i], 6, str(val), border=1, align="C")
        self.ln()


def generate_pdf(s, score, bd):
    pdf = SiteIQPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Page 1 — Cover + Summary
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 15, s["name"], ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"{s['county']} County, {s['state']}", ln=True, align="C")
    pdf.cell(0, 8, f"Report Date: {datetime.now().strftime('%B %d, %Y')}", ln=True, align="C")
    pdf.cell(0, 8, f"Project Type: Renewable Energy Generation (Solar)", ln=True, align="C")
    pdf.ln(10)

    # Key Details
    pdf.section_title("Key Details")
    pdf.kv_row("Total Acreage", f"{s['total_acres']:,.2f}")
    pdf.kv_row("Buildable Acreage", f"{s['buildable_acres']:,}")
    pdf.kv_row("Site Score", f"{score}/100")
    pdf.kv_row("Nearest Transmission Line", f"{s['nearest_trans_dist_mi']} miles ({s['nearest_trans_owner']})")
    pdf.kv_row("Nearest Substation", f"{s['nearest_sub_dist_mi']} miles ({s['nearest_sub_name']})")
    pdf.kv_row("Wholesale Market", s["wholesale_market"])
    pdf.kv_row("Permits Needed", f"{s['permits_needed']} ({s['federal_permits']} Federal, {s['state_permits']} State)")
    pdf.kv_row("Landowners", f"{len(s['parcels'])} landowners")
    pdf.kv_row("Community Sentiment", s["community_sentiment"])
    pdf.kv_row("Species Concern Level", s["species_concerns"])
    pdf.ln(5)

    # Concerns Summary
    pdf.section_title("Concerns Summary")
    concern_map = {"High": "HIGH CONCERN", "Moderate": "MODERATE CONCERN", "Low": "LOW CONCERN"}
    pdf.kv_row("Federally Protected Species", concern_map.get(s["species_concerns"], "Low"))
    pdf.kv_row("Waters / Wetlands", f"{s['federal_wetland_acres']} acres federal wetland")
    pdf.kv_row("Flood Risk", s["flood_zone"])
    pdf.kv_row("Environmental Compliance", f"Abandoned wells: {s['abandoned_wells']}")
    pdf.ln(3)

    # Score Breakdown
    pdf.section_title("Site Score Breakdown")
    for k, v in bd.items():
        pdf.kv_row(k, f"{v}/100")
    pdf.ln(3)

    # Value Index
    pdf.add_page()
    pdf.section_title("Value Index (LandGate-Style)")
    cols = ["Category", "Score /100"]
    widths = [100, 50]
    pdf.table_header(cols, widths)
    for k, v in s["value_index"].items():
        pdf.table_row([k, str(v)], widths)
    pdf.ln(5)

    # Risk Index
    pdf.section_title("Risk Index (LandGate-Style)")
    pdf.table_header(cols, widths)
    for k, v in s["risk_index"].items():
        pdf.table_row([k, str(v)], widths)

    # Land & Topo
    pdf.add_page()
    pdf.section_title("Land & Topography")
    pdf.kv_row("Total Land Value", f"${s['total_land_value']:,} (${s['land_value_per_acre']:,}/ac)")
    pdf.kv_row("Avg Elevation", f"{s['avg_elevation_ft']:,} ft")
    pdf.kv_row("Min / Max Elevation", f"{s['min_elevation_ft']:,} / {s['max_elevation_ft']:,} ft")
    pdf.kv_row("Avg Slope", f"{s['avg_slope_deg']}°")
    pdf.kv_row("Max Slope", f"{s['max_slope_deg']}°")
    pdf.kv_row("Annual Precipitation", f"{s['annual_precip_in']}\"")
    pdf.kv_row("Avg Wind Speed", f"{s['avg_wind_speed_mph']} mph")
    pdf.kv_row("Solar Irradiance", f"{s['solar_irradiance_wm2']} W/m²")
    pdf.kv_row("Avg High / Low Temp", f"{s['avg_high_temp_f']}°F / {s['avg_low_temp_f']}°F")
    pdf.ln(5)

    # Land Cover
    pdf.section_title("Land Cover")
    lc_cols = ["Type", "Acres", "Value ($)"]
    lc_w = [80, 35, 40]
    pdf.table_header(lc_cols, lc_w)
    for lc in s["land_cover"]:
        pdf.table_row([lc["type"], f"{lc['acres']:.1f}", f"${lc['value']:,}"], lc_w)
    pdf.ln(5)

    # Soils
    pdf.section_title("Soil Analysis")
    soil_cols = ["Type", "Acres", "Quality", "Group", "Suit.", "Hydric", "Drainage", "Bedrock"]
    soil_w = [28, 18, 16, 14, 14, 16, 45, 20]
    pdf.table_header(soil_cols, soil_w)
    for soil in s["soils"]:
        pdf.table_row([
            soil["type"], f"{soil['acres']:.0f}", str(soil["quality"]),
            soil["group"], str(soil["suitability"]),
            "Yes" if soil["hydric"] else "No", soil["drainage"],
            f"{soil['bedrock_ft']}ft"
        ], soil_w)
    pdf.ln(5)

    # Solar
    pdf.add_page()
    pdf.section_title("Solar Farm Analysis")
    pdf.kv_row("Est. Solar Lease", f"${s['solar_lease_per_acre']}/ac/yr")
    pdf.kv_row("Direct Solar Irradiance", f"{s['direct_irradiance_wm2']} W/m²")
    pdf.kv_row("Corrected Irradiance", f"{s['corrected_irradiance_wm2']} W/m²")
    pdf.kv_row("Possible Solar Panels", f"{s['solar_panels_possible']:,}")
    pdf.kv_row("Max Capacity", f"{s['solar_max_capacity_mw']} MW")
    pdf.kv_row("Max Annual Output", f"{s['solar_max_annual_mwh']:,} MWh")
    pdf.kv_row("Nearest Solar Farm", f"{s['nearest_solar_farm']} ({s['nearest_solar_dist_mi']} mi)")
    pdf.ln(5)

    # Wind
    pdf.section_title("Wind Analysis")
    pdf.kv_row("Est. Wind Lease", f"${s['wind_lease_per_acre']}/ac/yr")
    pdf.kv_row("Avg Wind Speed", f"{s['avg_wind_speed_ms']} m/s")
    pdf.kv_row("Possible Turbines", str(s["wind_turbines_possible"]))
    pdf.kv_row("Max Capacity", f"{s['wind_max_capacity_mw']} MW")
    pdf.kv_row("Max Annual Output", f"{s['wind_max_annual_mwh']:,} MWh")
    pdf.ln(5)

    # Electrical Infrastructure
    pdf.section_title("Electrical Infrastructure")
    pdf.kv_row("Nearest Substation", f"{s['nearest_sub_name']} — {s['nearest_sub_dist_mi']} mi")
    pdf.kv_row("Nearest Transmission Line", f"{s['nearest_trans_owner']} — {s['nearest_trans_dist_mi']} mi")
    pdf.kv_row("Transmission Capacity", f"{s['nearest_trans_capacity_mw']} MW")
    pdf.kv_row("Wholesale Market", s["wholesale_market"])
    pdf.kv_row("State/Local Incentives", f"{s['state_incentives_per_mwh']} $/MWh")
    pdf.ln(5)

    # Waters & Flood
    pdf.section_title("Waters, Wetlands & Floodplains")
    pdf.kv_row("Federal Wetland Acres", f"{s['federal_wetland_acres']} ac")
    pdf.kv_row("Flood Zone", s["flood_zone"])
    pdf.kv_row("Flood Risk Score", f"{s['flood_risk_score']}/100")
    pdf.ln(5)

    # Species
    if s["species_list"]:
        pdf.section_title("Protected Species")
        sp_cols = ["Name", "Status", "Concern Level"]
        sp_w = [70, 45, 45]
        pdf.table_header(sp_cols, sp_w)
        for sp in s["species_list"]:
            pdf.table_row([sp["name"], sp["status"], sp["concern"]], sp_w)
        pdf.ln(5)

    # Parcels
    pdf.add_page()
    pdf.section_title("Parcel Details")
    p_cols = ["APN", "Address", "Acres", "Land Value"]
    p_w = [35, 65, 30, 35]
    pdf.table_header(p_cols, p_w)
    for p in s["parcels"]:
        pdf.table_row([p["apn"], p["address"], f"{p['acres']:.1f}", f"${p['land_value']:,}"], p_w)
    pdf.ln(5)

    # Community Sentiment
    pdf.section_title("Community Sentiment")
    pdf.kv_row("Overall Sentiment", s["community_sentiment"])
    for detail in s["sentiment_details"]:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, f"  - {detail}", ln=True)
    pdf.ln(5)

    # Oil & Gas (if applicable)
    if s["wells_on_property"] > 0:
        pdf.section_title("Oil & Gas")
        pdf.kv_row("Estimated O&G Value", f"${s['oil_gas_value_per_acre']}/acre")
        pdf.kv_row("Wells on Property", str(s["wells_on_property"]))
        pdf.kv_row("Cumulative Oil", f"{s['cumulative_oil_bbl']:,} bbl")
        pdf.kv_row("Cumulative Gas", f"{s['cumulative_gas_mcf']:,} Mcf")

    # Footer
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 20, "", ln=True)
    pdf.cell(0, 10, "Report generated by SiteIQ Renewable Energy Siting Platform", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "This report combines LandGate property analysis and Transect environmental screening methodologies.", ln=True, align="C")
    pdf.cell(0, 8, "Data sources: USGS, USFWS, FEMA, NRCS, ERCOT, MISO, EPA, LandGate, Transect", ln=True, align="C")

    return pdf.output()


# ══════════════════════════════════════════════════
# MAP
# ══════════════════════════════════════════════════
def build_map(sites, scores, show_layers):
    m = folium.Map(location=[38.5, -96], zoom_start=5, tiles=None)
    folium.TileLayer(tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", attr="CartoDB", name="Dark", control=False).add_to(m)

    if show_layers.get("transmission"):
        tg = folium.FeatureGroup(name="Transmission Lines")
        for s in sites:
            if s["nearest_trans_dist_mi"] < 50:
                folium.PolyLine([[s["lat"], s["lon"] - 0.15], [s["lat"] + 0.1, s["lon"] + 0.15]], color="#f59e0b", weight=3, opacity=0.7, dash_array="8 4").add_to(tg)
        tg.add_to(m)

    if show_layers.get("substations"):
        sg = folium.FeatureGroup(name="Substations")
        for s in sites:
            folium.CircleMarker([s["lat"] + 0.05, s["lon"] + 0.05], radius=7, color="#f97316", fill=True, fill_color="#f97316", fill_opacity=0.8, tooltip=s["nearest_sub_name"]).add_to(sg)
        sg.add_to(m)

    if show_layers.get("wetlands"):
        wg = folium.FeatureGroup(name="Wetlands")
        for s in sites:
            if s["federal_wetland_acres"] > 3:
                folium.Circle([s["lat"], s["lon"]], radius=s["federal_wetland_acres"] * 20, color="#22d3ee", fill=True, fill_color="#22d3ee", fill_opacity=0.15, tooltip=f"{s['federal_wetland_acres']} ac wetlands").add_to(wg)
        wg.add_to(m)

    for s in sites:
        sc = scores.get(s["id"], 50)
        color = "#22c55e" if sc >= 75 else "#f59e0b" if sc >= 50 else "#ef4444"
        popup = f"""<div style='min-width:240px;font-family:sans-serif'>
            <h4 style='color:{color};margin:0'>{s['name']}</h4>
            <table style='font-size:12px'>
            <tr><td><b>Score</b></td><td style='color:{color};font-size:16px;font-weight:900'>{sc}/100</td></tr>
            <tr><td><b>Acres</b></td><td>{s['total_acres']:,.1f}</td></tr>
            <tr><td><b>Trans Dist</b></td><td>{s['nearest_trans_dist_mi']} mi</td></tr>
            <tr><td><b>Wetlands</b></td><td>{s['federal_wetland_acres']} ac</td></tr>
            <tr><td><b>Species</b></td><td>{s['species_concerns']}</td></tr>
            <tr><td><b>Sentiment</b></td><td>{s['community_sentiment']}</td></tr>
            </table></div>"""
        folium.CircleMarker([s["lat"], s["lon"]], radius=14, color=color, fill=True, fill_color=color, fill_opacity=0.6, weight=2, popup=folium.Popup(popup, max_width=300), tooltip=f"{s['name']} — {sc}/100").add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ══════════════════════════════════════════════════
# INDEX BAR CHART helper
# ══════════════════════════════════════════════════
def index_bar_chart(data, title, color_scale):
    df = pd.DataFrame({"Category": list(data.keys()), "Score": list(data.values())})
    df = df.sort_values("Score", ascending=True)
    fig = px.bar(df, x="Score", y="Category", orientation="h", color="Score", color_continuous_scale=color_scale, range_color=[0, 100])
    fig.update_layout(height=max(300, len(data) * 28), showlegend=False, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0", size=11), xaxis=dict(range=[0, 100], gridcolor="#334155"), yaxis=dict(gridcolor="#334155"), coloraxis_showscale=False, title=title)
    return fig


# ══════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════
def main():
    sites = load_sites()

    with st.sidebar:
        st.markdown("## ⚡ SiteIQ")
        st.caption("Renewable Energy Siting Intelligence Platform")
        st.caption("Powered by LandGate + Transect Methodology")
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
            st.warning(f"Weights total **{tw}%** — should be 100%")
        else:
            st.success("Weights total 100%")
        st.divider()
        st.markdown("### Map Layers")
        show_layers = {"transmission": st.checkbox("Transmission Lines", True), "substations": st.checkbox("Substations", True), "wetlands": st.checkbox("Wetlands", True)}

    scores = {}
    breakdowns = {}
    for s in sites:
        sc, bd = compute_site_score(s, weights)
        scores[s["id"]] = sc
        breakdowns[s["id"]] = bd

    st.markdown("# ⚡ SiteIQ — Renewable Energy Siting Intelligence")
    st.markdown("> Modeled after **LandGate Property Reports** and **Transect Environmental Screening**")

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Sites Analyzed", len(sites))
    with k2: st.metric("Total Acreage", f"{sum(s['total_acres'] for s in sites):,.0f}")
    with k3: st.metric("Avg Score", f"{np.mean(list(scores.values())):.0f}/100")
    with k4: st.metric("Permits Flagged", sum(s["permits_needed"] for s in sites))

    tab_map, tab_site, tab_env, tab_infra, tab_compare, tab_export = st.tabs(["Map", "Site Report", "Environmental", "Infrastructure", "Compare", "Export PDF"])

    # ── MAP ──
    with tab_map:
        st.markdown("### Interactive Siting Map")
        m = build_map(sites, scores, show_layers)
        st_folium(m, width=None, height=520, returned_objects=[])
        rdf = pd.DataFrame([{"Site": s["name"], "State": s["state"], "Acres": s["total_acres"], "Score": scores[s["id"]], "Species": s["species_concerns"], "Permits": s["permits_needed"], "Sentiment": s["community_sentiment"]} for s in sites]).sort_values("Score", ascending=False)
        rdf.index = range(1, len(rdf) + 1)
        st.dataframe(rdf, use_container_width=True)

    # ── SITE REPORT ──
    with tab_site:
        sel = st.selectbox("Select Site", [s["name"] for s in sites], key="site_sel")
        s = [x for x in sites if x["name"] == sel][0]
        sc = scores[s["id"]]
        bd = breakdowns[s["id"]]
        color = "#22c55e" if sc >= 75 else "#f59e0b" if sc >= 50 else "#ef4444"

        st.markdown(f"""<div style='display:flex;align-items:center;gap:24px;margin-bottom:16px'>
            <div style='font-size:4rem;font-weight:900;color:{color}'>{sc}</div>
            <div><div style='font-size:1.5rem;font-weight:700'>{s['name']}</div>
            <div style='color:#94a3b8'>{s['county']} County, {s['state']} | {s['total_acres']:,.1f} acres | {s['buildable_acres']:,} buildable</div></div></div>""", unsafe_allow_html=True)

        # Concerns summary (Transect style)
        st.markdown("### Concerns Summary")
        cmap = {"High": "concern-high", "Moderate": "concern-mod", "Low": "concern-low"}
        c1, c2, c3 = st.columns(3)
        with c1:
            cls = cmap.get(s["species_concerns"], "concern-low")
            st.markdown(f"<div class='{cls}'><b>Protected Species</b><br>{s['species_concerns']} Concern<br>{len(s['species_list'])} species flagged</div>", unsafe_allow_html=True)
        with c2:
            wcls = "concern-high" if s["federal_wetland_acres"] > 30 else "concern-mod" if s["federal_wetland_acres"] > 10 else "concern-low"
            st.markdown(f"<div class='{wcls}'><b>Waters / Wetlands</b><br>{s['federal_wetland_acres']} ac wetlands<br>Flood: {s['flood_zone']}</div>", unsafe_allow_html=True)
        with c3:
            pcls = "concern-high" if s["permits_needed"] > 10 else "concern-mod" if s["permits_needed"] > 5 else "concern-low"
            st.markdown(f"<div class='{pcls}'><b>Permits Required</b><br>{s['permits_needed']} total<br>{s['federal_permits']} Federal, {s['state_permits']} State</div>", unsafe_allow_html=True)

        # Value + Risk Indexes side by side
        st.markdown("### Value & Risk Indexes")
        vi_col, ri_col = st.columns(2)
        with vi_col:
            st.plotly_chart(index_bar_chart(s["value_index"], "Value Index", ["#ef4444", "#f59e0b", "#22c55e"]), use_container_width=True)
        with ri_col:
            st.plotly_chart(index_bar_chart(s["risk_index"], "Risk Index", ["#22c55e", "#f59e0b", "#ef4444"]), use_container_width=True)

        # Parcels
        st.markdown("### Parcel Details")
        pdf_data = s["parcels"]
        pdf_df = pd.DataFrame(pdf_data)
        st.dataframe(pdf_df, use_container_width=True, hide_index=True)

        # Land & Topo
        st.markdown("### Land & Topography")
        l1, l2, l3, l4 = st.columns(4)
        with l1: st.metric("Avg Elevation", f"{s['avg_elevation_ft']:,} ft")
        with l2: st.metric("Avg Slope", f"{s['avg_slope_deg']}°")
        with l3: st.metric("Solar Irradiance", f"{s['solar_irradiance_wm2']} W/m²")
        with l4: st.metric("Avg Wind", f"{s['avg_wind_speed_mph']} mph")

        lc_df = pd.DataFrame(s["land_cover"])
        fig_lc = px.pie(lc_df, values="acres", names="type", title="Land Cover", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
        fig_lc.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
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
            fig_soil = px.bar(soil_df, x="Type", y="Suitability", color="Suitability", color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"], range_color=[0, 100], title="Soil Suitability Score")
            fig_soil.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"), coloraxis_showscale=False)
            st.plotly_chart(fig_soil, use_container_width=True)
        with s2:
            fig_bed = px.bar(soil_df, x="Type", y="Bedrock (ft)", title="Depth to Bedrock (ft)", color="Bedrock (ft)", color_continuous_scale=["#fbbf24", "#22c55e"])
            fig_bed.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"), coloraxis_showscale=False)
            st.plotly_chart(fig_bed, use_container_width=True)

        # Species
        st.markdown("### Protected Species (Transect-Style)")
        if s["species_list"]:
            for sp in s["species_list"]:
                concern_cls = "concern-high" if sp["concern"] == "Species of Concern" else "concern-mod"
                st.markdown(f"""<div class='{concern_cls}'>
                    <b>{sp['name']}</b> (<i>{sp['scientific']}</i>)<br>
                    Federal Status: <b>{sp['status']}</b> | Transect Assessment: <b>{sp['concern']}</b>
                </div>""", unsafe_allow_html=True)
        else:
            st.success("No protected species of concern identified.")

        # Wetlands + Flood
        st.markdown("### Wetlands & Floodplains")
        w1, w2, w3 = st.columns(3)
        with w1: st.metric("Federal Wetland", f"{s['federal_wetland_acres']} ac")
        with w2: st.metric("Flood Zone", s["flood_zone"])
        with w3: st.metric("Flood Risk Score", f"{s['flood_risk_score']}/100")

        # Community
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
            st.metric("Nearest Trans. Line", s["nearest_trans_owner"])
            st.metric("Distance", f"{s['nearest_trans_dist_mi']} mi")
        with e3:
            st.metric("Capacity", f"{s['nearest_trans_capacity_mw']} MW")
            st.metric("Market", s["wholesale_market"])

        st.markdown("### Solar Farm Potential")
        so1, so2, so3, so4 = st.columns(4)
        with so1: st.metric("Lease Rate", f"${s['solar_lease_per_acre']}/ac/yr")
        with so2: st.metric("Max Capacity", f"{s['solar_max_capacity_mw']} MW")
        with so3: st.metric("Annual Output", f"{s['solar_max_annual_mwh']:,} MWh")
        with so4: st.metric("Solar Panels", f"{s['solar_panels_possible']:,}")

        st.markdown("### Wind Potential")
        wi1, wi2, wi3, wi4 = st.columns(4)
        with wi1: st.metric("Lease Rate", f"${s['wind_lease_per_acre']}/ac/yr")
        with wi2: st.metric("Max Capacity", f"{s['wind_max_capacity_mw']} MW")
        with wi3: st.metric("Annual Output", f"{s['wind_max_annual_mwh']:,} MWh")
        with wi4: st.metric("Wind Speed", f"{s['avg_wind_speed_ms']} m/s")

        # LMP Chart
        st.markdown("### Historical LMP Pricing")
        base_lmp = 35 if s["wholesale_market"] == "ERCOT" else 28
        lmp_df = generate_lmp_history(base_lmp)
        fig_lmp = px.area(lmp_df, x="Date", y="LMP ($/MWh)", title=f"{s['wholesale_market']} Node — 12-Month LMP")
        fig_lmp.update_traces(fillcolor="rgba(99,102,241,0.2)", line_color="#6366f1")
        fig_lmp.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"), xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155"))
        st.plotly_chart(fig_lmp, use_container_width=True)

        if s["wells_on_property"] > 0:
            st.markdown("### Oil & Gas")
            st.metric("Wells on Property", s["wells_on_property"])
            st.metric("Cumulative Oil", f"{s['cumulative_oil_bbl']:,} bbl")
            st.metric("Cumulative Gas", f"{s['cumulative_gas_mcf']:,} Mcf")

    # ── COMPARE ──
    with tab_compare:
        st.markdown("### Side-by-Side Comparison")
        cc1, cc2 = st.columns(2)
        with cc1: sa_name = st.selectbox("Site A", [s["name"] for s in sites], index=0, key="cmp_a")
        with cc2: sb_name = st.selectbox("Site B", [s["name"] for s in sites], index=min(1, len(sites) - 1), key="cmp_b")
        sa = [x for x in sites if x["name"] == sa_name][0]
        sb = [x for x in sites if x["name"] == sb_name][0]
        bda = breakdowns[sa["id"]]
        bdb = breakdowns[sb["id"]]
        cats = list(bda.keys())

        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Scatterpolar(r=list(bda.values()) + [list(bda.values())[0]], theta=cats + [cats[0]], fill="toself", fillcolor="rgba(99,102,241,0.15)", line=dict(color="#6366f1", width=2), name=sa["name"]))
        fig_cmp.add_trace(go.Scatterpolar(r=list(bdb.values()) + [list(bdb.values())[0]], theta=cats + [cats[0]], fill="toself", fillcolor="rgba(34,211,238,0.15)", line=dict(color="#22d3ee", width=2), name=sb["name"]))
        fig_cmp.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 100])), height=420, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"), legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_cmp, use_container_width=True)

        cmp_metrics = [
            ("Site Score", scores[sa["id"]], scores[sb["id"]], False),
            ("Total Acres", sa["total_acres"], sb["total_acres"], False),
            ("Buildable Acres", sa["buildable_acres"], sb["buildable_acres"], False),
            ("Trans. Distance (mi)", sa["nearest_trans_dist_mi"], sb["nearest_trans_dist_mi"], True),
            ("Wetland Acres", sa["federal_wetland_acres"], sb["federal_wetland_acres"], True),
            ("Solar Capacity (MW)", sa["solar_max_capacity_mw"], sb["solar_max_capacity_mw"], False),
            ("Permits Needed", sa["permits_needed"], sb["permits_needed"], True),
            ("Flood Risk Score", sa["flood_risk_score"], sb["flood_risk_score"], True),
        ]
        cmp_data = []
        for label, va, vb, lower_better in cmp_metrics:
            winner = "A" if (va < vb if lower_better else va > vb) else "B" if (vb < va if lower_better else vb > va) else "Tie"
            cmp_data.append({"Metric": label, sa_name: va, sb_name: vb, "Better": winner})
        st.dataframe(pd.DataFrame(cmp_data), use_container_width=True, hide_index=True)

    # ── EXPORT PDF ──
    with tab_export:
        st.markdown("### Export Feasibility Report (PDF)")
        st.caption("Generate a professional PDF report modeled after LandGate Property Reports and Transect Environmental Screening.")
        sel4 = st.selectbox("Select Site", [s["name"] for s in sites], key="pdf_sel")
        s = [x for x in sites if x["name"] == sel4][0]
        sc = scores[s["id"]]
        bd = breakdowns[s["id"]]

        if st.button("Generate PDF Report", type="primary"):
            with st.spinner("Generating report..."):
                pdf_bytes = generate_pdf(s, sc, bd)
                safe = s["name"].replace(" ", "_")
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"SiteIQ_Report_{safe}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                )
            st.success("Report generated successfully!")

        # Also offer CSV + GeoJSON
        st.divider()
        st.markdown("### Additional Exports")
        ec1, ec2 = st.columns(2)
        with ec1:
            csv_rows = []
            for s2 in sites:
                row = {"name": s2["name"], "state": s2["state"], "county": s2["county"], "acres": s2["total_acres"], "score": scores[s2["id"]], "species_concern": s2["species_concerns"], "permits": s2["permits_needed"], "sentiment": s2["community_sentiment"], "trans_dist_mi": s2["nearest_trans_dist_mi"], "solar_mw": s2["solar_max_capacity_mw"], "wetland_acres": s2["federal_wetland_acres"]}
                csv_rows.append(row)
            st.download_button("Download All Sites CSV", pd.DataFrame(csv_rows).to_csv(index=False), file_name="SiteIQ_Sites.csv", mime="text/csv")
        with ec2:
            geojson = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [s2["lon"], s2["lat"]]}, "properties": {"name": s2["name"], "score": scores[s2["id"]], "acres": s2["total_acres"], "species": s2["species_concerns"]}} for s2 in sites]}
            st.download_button("Download GeoJSON", json.dumps(geojson, indent=2), file_name="SiteIQ_Sites.geojson", mime="application/json")


if __name__ == "__main__":
    main()
