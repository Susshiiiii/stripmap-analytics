# Stripmap Analytics

Streamlit dashboard for semiconductor strip defect analysis on VEGA, SPARROW, SQUID and SOLARIS devices.
Every physical unit on a strip is drawn as its own tile, numbered in the strip's serpentine order.

## Features
- **Dashboard & Stations**: KPI cards (rejects, lots, affected units, estimated yield), severity mix, daily yield-loss trend,
  2D unit map, top 10 hotspots, raw data stream, and per-station analytics (Die Attach, Wire Bond, Strip AOI, Lid AOI).
- **Mapping Painter**: click units to mark rejects, then export the list as CSV.
- **Unit Finder**: convert X/Y coordinates to a unit number and back.
- Sidebar navigation, collapsible filters with Latest Date / Latest Week presets, data editor, light and dark mode.

## Run locally
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then upload the master workbook (`Rejects` + `Average` sheets) in the sidebar under **Data**.
Production data files are not stored in this repository.
