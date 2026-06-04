# KRBL Inventory Replenishment Engine | AIonOS

Streamlit demo adapted from the original Inventory Replenishment Engine for the AIonOS × KRBL narrative.

## What changed for KRBL

The demo metrics are aligned to the KRBL 2-pager and KRBL supply-chain deck:

- 45-day harvest window, down from 90 days
- 324-day average inventory holding period
- ₹3,000 Cr+ inventory / working-capital exposure
- 13 CNFs and 850+ dealers
- 90+ export countries and 61% Middle East export exposure
- 90-day pilot outcomes:
  - Procurement cost reduction: 10–15%
  - Inventory holding-period reduction: 20–30 days
  - Order accuracy: 99%
  - Service level: 98%
  - Exception resolution: <10 minutes

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud

1. Upload this folder to a GitHub repository.
2. Ensure `app.py`, `requirements.txt`, `README.md`, and the `videos/` folder are in the repo root.
3. In Streamlit Cloud, create a new app.
4. Select the repository and set the main file path to:

```text
app.py
```

5. Deploy.

## Optional video replacement

Replace `videos/warehouse1.mp4` with any KRBL-aligned plant, warehouse, inventory, or supply-chain video. Keep the file under `videos/`.

## Notes

This is an offline/rule-based demo with synthetic telemetry. It is intended for sales storytelling and can be connected later to ERP, WMS, mandi data feeds, dealer-management systems, export order data, and AIonOS MCP connectors.
