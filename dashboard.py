import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
from app import get_all_venues, get_historical_trends, get_tournament_state, TOURNAMENT_STATUS

st.set_page_config(page_title="Tennis Heat Index", layout="centered")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 780px; }
    h1 { font-size: 24px !important; font-weight: 500 !important; }
    .risk-bar-bg { background: #2a2a2a; border-radius: 4px; height: 10px; position: relative; }
    .risk-bar-fill { height: 10px; border-radius: 4px; position: absolute; left: 0; top: 0; }
    .risk-bar-marker { position: absolute; top: -4px; width: 3px; height: 18px; background: #E24B4A; border-radius: 2px; }
    .risk-bar-labels { display: flex; justify-content: space-between; font-size: 11px; color: #888; margin-top: 5px; }
    .risk-bar-header { display: flex; justify-content: space-between; font-size: 13px; color: #ccc; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

st.title("Tennis heat index")
st.caption("This dashboard tracks real-time and historical heat stress conditions at all four majors, measured against the ATP's official 2026 Heat Policy thresholds.")
st.caption("Live court conditions at the Grand Slams")

with st.spinner("Fetching live conditions..."):
    data = get_all_venues()

with st.spinner("Loading historical data..."):
    hist = get_historical_trends()

selected = st.radio(
    "Select venue",
    options=list(data.keys()),
    horizontal=True
)

venue = data[selected]
state = get_tournament_state(selected)
ATP_THRESHOLD = 32.2
wb = venue["wet_bulb"]
venue_hist = hist[selected]

st.divider()

# --- STATUS LABEL ---
status_labels = {"active": "🟢 Live", "completed": "⚪ Recently completed", "upcoming": "🔵 Upcoming"}
st.caption(status_labels[state])

# --- METRICS ---
col1, col2, col3 = st.columns(3)

if state == "active":
    with col1:
        st.metric("Air temperature", f"{venue['air_temp']}°C")
    with col2:
        st.metric("WBGT", f"{venue['wet_bulb']}°C", help="Wet Bulb Globe Temperature — composite heat stress metric used in ATP policy.")
    with col3:
        st.metric("Court surface", f"{venue['surface_temp']}°C", help="Estimated from solar radiation and surface albedo")

elif state == "completed":
    last_year = max(d["year"] for d in venue_hist["data"] if d["peak_wet_bulb"] is not None)
    last_peak = next(d["peak_wet_bulb"] for d in venue_hist["data"] if d["year"] == last_year)
    with col1:
        st.metric("Peak WBGT", f"{last_peak}°C", help=f"Peak during {last_year} tournament")
    with col2:
        st.metric("ATP threshold", "32.2°C")
    with col3:
        st.metric("% of limit", f"{round((last_peak / 32.2) * 100)}%")
    st.caption(f"Showing peak conditions from {last_year} tournament — live conditions not relevant outside tournament window.")

else:
    with col1:
        st.metric("Next tournament", TOURNAMENT_STATUS[selected]['start'].strftime("%d %b %Y"))
    with col2:
        st.metric("ATP threshold", "32.2°C")
    with col3:
        st.metric("Surface", venue['surface'].capitalize())
    st.caption("Tournament not yet started — historical data shown below.")

# --- WBGT BAR + RISK (active only) ---
if state == "active":
    pct = min((wb / 42) * 100, 100)
    bar_color = "#E24B4A" if wb >= ATP_THRESHOLD else "#EF9F27" if wb >= 29 else "#639922"
    pct_label = f"{round((wb / ATP_THRESHOLD) * 100)}% of limit"

    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div class="risk-bar-header">
            <span>WBGT vs ATP threshold</span><span>{pct_label}</span>
        </div>
        <div class="risk-bar-bg">
            <div class="risk-bar-fill" style="width:{pct:.1f}%; background:{bar_color};"></div>
            <div class="risk-bar-marker" style="left:{((29.0/42)*100):.1f}%;background:#EF9F27;"></div>
            <div class="risk-bar-marker" style="left:{((32.2/42)*100):.1f}%;background:#E24B4A;"></div>
        </div>
        <div style="position:relative;height:16px;margin-top:4px;">
            <span style="position:absolute;left:0;font-size:11px;color:#888;">0°C</span>
            <span style="position:absolute;left:{((29.0/42)*100):.1f}%;transform:translateX(-80%);font-size:11px;color:#EF9F27;">29°C advisory</span>
            <span style="position:absolute;left:{((32.2/42)*100):.1f}%;transform:translateX(-50%);font-size:11px;color:#E24B4A;">32.2°C suspension</span>
            <span style="position:absolute;right:0;font-size:11px;color:#888;">42°C</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if wb >= 32.2:
        st.error("Extreme heat level 2 — outdoor play suspended after 15 consecutive minutes.")
    elif wb >= 30.1:
        st.warning("Extreme heat level 1 — players may request a 10-minute cooling break before set 3.")
    elif wb >= 29.0:
        st.info("Heat advisory — conditions elevated, players and officials on alert.")
    else:
        st.success("Normal conditions — standard protocols apply.")

    if venue['surface_temp'] >= 45:
        st.warning(f"Court surface temperature {venue['surface_temp']}°C — roof closure trigger reached (≥ 45°C).")

# --- ATP POLICY TABLE ---
st.divider()
st.subheader("ATP heat policy — current status")

atp_rows = [
    {"band": "Below 29.0°C", "outer": "Play on", "outer_cls": "pill-green", "show": "Play on", "show_cls": "pill-green", "protection": "Standard", "prot_cls": "pill-blue"},
    {"band": "29.0–30.0°C", "outer": "Advisory", "outer_cls": "pill-amber", "show": "Play on", "show_cls": "pill-green", "protection": "Advisory", "prot_cls": "pill-amber"},
    {"band": "30.1–32.1°C", "outer": "Cooling break available", "outer_cls": "pill-amber", "show": "Cooling break available", "show_cls": "pill-amber", "protection": "Player-requested break", "prot_cls": "pill-amber"},
    {"band": "≥ 32.2°C (15 mins)", "outer": "Suspended", "outer_cls": "pill-red", "show": "Roof closed", "show_cls": "pill-blue", "protection": "Inequitable", "prot_cls": "pill-red"},
]

pill_styles = {
    "pill-green": "background:#1a3a1a;color:#6dbf6d;",
    "pill-amber": "background:#3a2a0a;color:#EF9F27;",
    "pill-red": "background:#3a1a1a;color:#E24B4A;",
    "pill-blue": "background:#0a2a3a;color:#378ADD;",
}

def get_band(wb):
    if wb >= 32.2:
        return 3
    elif wb >= 30.1:
        return 2
    elif wb >= 29.0:
        return 1
    else:
        return 0

current_band = get_band(wb) if state == "active" else -1

rows_html = ""
for i, row in enumerate(atp_rows):
    active = i == current_band
    bg = "#2a2a2a" if active else "transparent"
    color = "#ffffff" if active else "#aaaaaa"
    weight = "600" if active else "400"
    marker = " <span style='color:#EF9F27;font-size:11px;'>← current</span>" if active else ""
    rows_html += f"""
    <div style="background:{bg};border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;width:100%;box-sizing:border-box;">
        <span style="font-size:13px;font-weight:{weight};color:{color};">{row['band']}{marker}</span>
        <div style="display:flex;gap:6px;flex-shrink:0;">
            <span style="font-size:11px;padding:3px 10px;border-radius:20px;{pill_styles[row['outer_cls']]}">Outer: {row['outer']}</span>
            <span style="font-size:11px;padding:3px 10px;border-radius:20px;{pill_styles[row['show_cls']]}">Show: {row['show']}</span>
            <span style="font-size:11px;padding:3px 10px;border-radius:20px;{pill_styles[row['prot_cls']]}">{row['protection']}</span>
        </div>
    </div>"""

st.components.v1.html(f"""
<div style="font-family:sans-serif;width:100%;">
{rows_html}
</div>
""", height=185)

st.divider()
st.caption(f"Humidity: {venue['humidity']}% · Wind: {venue['wind_speed']} km/h · Solar radiation: {venue['solar_radiation']} W/m² · Surface: {venue['surface']}")

# --- HISTORICAL CHART ---
st.divider()
st.subheader("Peak WBGT during tournament")

years = [d["year"] for d in venue_hist["data"] if d["peak_wet_bulb"] is not None]
values = [d["peak_wet_bulb"] for d in venue_hist["data"] if d["peak_wet_bulb"] is not None]
incidents = venue_hist["incidents"]

incident_years = [y for y in years if y in incidents]
incident_values = [values[years.index(y)] for y in incident_years]
incident_labels = [incidents[y] for y in incident_years]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=years, y=values,
    mode="lines+markers",
    name="Peak WBGT",
    line=dict(color="#378ADD", width=2),
    marker=dict(size=5, color="#378ADD"),
    hovertemplate="%{x}: %{y}°C<extra></extra>"
))

fig.add_hline(
    y=32.2,
    line_dash="dash",
    line_color="#E24B4A",
    annotation_text="ATP suspension threshold 32.2°C",
    annotation_position="top right"
)

fig.add_trace(go.Scatter(
    x=incident_years, y=incident_values,
    mode="markers",
    name="Heat incident",
    marker=dict(size=10, color="#E24B4A", symbol="circle"),
    text=incident_labels,
    hovertemplate="%{x}: %{y}°C<br>%{text}<extra></extra>"
))

fig.update_layout(
    height=300,
    margin=dict(l=0, r=0, t=10, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(title="°C", gridcolor="rgba(128,128,128,0.1)", color="#888"),
    xaxis=dict(gridcolor="rgba(0,0,0,0)", color="#888"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(color="#888")),
    hovermode="closest",
    font=dict(color="#888")
)

st.plotly_chart(fig, width="stretch")