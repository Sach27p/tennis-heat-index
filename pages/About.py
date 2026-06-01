import streamlit as st

st.set_page_config(page_title="About — Tennis Heat Index", layout="centered")

st.title("About")

st.divider()

st.markdown("""
This tool came out of a LinkedIn post I wrote about Jakub Menšík collapsing at Roland Garros 2026 after 
nearly five hours in 32°C heat on an unshaded outer court. I wanted to build something that made the 
data behind that argument visible.

I work in the energy sector where I focus on sustainable fuels and chemicals within the wider climate change space. 
Tennis is something I've played since I was 11. This sits at the intersection of both.

**Still a work in progress.** The methodology is improving and there's more to build.
""")

st.divider()

st.subheader("How it works")
st.markdown("""
Live and historical weather data is pulled from [Open-Meteo](https://open-meteo.com) for each Grand Slam venue.

WBGT (Wet Bulb Globe Temperature) is calculated from air temperature, humidity, solar radiation and wind speed 
using the standard ISO 7243 outdoor formula. This is the same metric the ATP uses in their official Heat Policy.

Historical peak WBGT is the highest hourly value recorded during each tournament window.
""")

st.divider()

st.subheader("Limitations")
st.markdown("""
- WBGT is approximated from met station data, not physical on-court instrumentation
- Daily peak conditions may not align exactly with when matches were played
- Tournament window dates are fixed — actual dates shift slightly year to year
""")

st.divider()

st.subheader("ATP policy thresholds")
st.markdown("""
| WBGT | Status |
|------|--------|
| < 29.0°C | Normal |
| 29.0–30.0°C | Heat advisory |
| 30.1–32.1°C | Extreme heat level 1 — cooling break available |
| ≥ 32.2°C | Extreme heat level 2 — play suspended |
""")

st.divider()

st.caption("Built by Sach · Data: Open-Meteo · Policy: ATP 2026 · Work in progress · Not affiliated with the ATP.")