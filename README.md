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


## Render the MP3 narration and MP4 video demo

The repo includes a two-step renderer for a shareable Streamlit walkthrough:

1. Render the narration MP3 first.
2. Capture the Streamlit end-to-end flow and mux it with the narration into an MP4.

Install the Python dependencies, install a Chromium browser for Playwright, and make sure `ffmpeg` is available on your PATH:

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

Then run the one-command renderer:

```bash
python scripts/render_demo.py
```

Or run each stage explicitly:

```bash
python scripts/render_narration.py --output rendered_demo/krbl_narration.mp3
python scripts/render_video_demo.py --narration rendered_demo/krbl_narration.mp3 --output rendered_demo/krbl_streamlit_demo.mp4
```

Outputs are written to `rendered_demo/` by default. The video renderer starts Streamlit locally, disables autoplay, walks through the scope, changes the replenishment-flow choices, opens the live timeline, agent recommendation, and KRBL GenBI tabs, captures multiple GenBI questions, and combines the screens with the narration. The renderer probes the MP3 duration and stretches the storyboard durations so the complete narration plays through instead of being cut off abruptly.


## Render and download media with GitHub Actions

A manual GitHub Actions workflow is included for generating the MP3 narration and MP4 demo in the cloud.

1. Push this repository to GitHub.
2. Open the repository's **Actions** tab.
3. Select **Render demo media**.
4. Click **Run workflow**. You can keep the default output directory and artifact name.
5. When the run finishes, open the workflow run summary and download the **krbl-demo-media** artifact.

The downloaded artifact contains:

- `krbl_narration.mp3`
- `krbl_streamlit_demo.mp4`

The workflow installs Python dependencies, ffmpeg, and Playwright Chromium, then runs:

```bash
python scripts/render_demo.py --output-dir rendered_demo
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
