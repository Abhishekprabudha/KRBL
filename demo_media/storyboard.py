"""Storyboard content for the KRBL Streamlit MP4 demo renderer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUTPUT_DIR = Path("rendered_demo")
DEFAULT_NARRATION = DEFAULT_OUTPUT_DIR / "krbl_narration.mp3"
DEFAULT_VIDEO = DEFAULT_OUTPUT_DIR / "krbl_streamlit_demo.mp4"

NARRATION_TEXT = """
AIonOS presents the KRBL agentic inventory replenishment engine.
The walkthrough opens with KRBL's supply chain context: a compressed forty five day harvest window, a three hundred twenty four day inventory holding baseline, thirteen CNFs, more than eight hundred fifty dealers, and more than ninety export markets.
We start with the paddy procurement pool, where the agent watches mandi to Dhuri mill supply, projected demand, receipts, and stock position against the reorder point.
The operating telemetry converts the stream into decisions: current inventory, demand, backlog proxy, procurement savings target, order accuracy, and exception SLA.
The domestic dealer replenishment choice shows how the same agent protects service across thirteen CNFs and more than eight hundred fifty dealers.
The premium aged basmati export recovery lane shows how Middle East and global distributor volatility changes demand sensing and CNF release priorities.
The new categories choice shows how spices and rice bran oil can be added to the same decision cockpit as KRBL expands beyond rice.
Next, the live timeline tab shows the end to end flow of demand, inventory, receipts, and CNF rebalance signals as the demo day advances.
The agent recommendation tab turns those signals into the next replenishment trigger, replenish quantity, release window, projected holding period improvement, and service level protection.
Finally, KRBL GenBI is demonstrated with multiple natural language questions: current stock and reorder point, the three hundred twenty four day holding period reduction, dealer service level, and CNF rebalance recommendations.
Thankyou and Welcome to AIonOS.
""".strip()


@dataclass(frozen=True)
class StoryboardStep:
    """A single capture step in the Streamlit walkthrough."""

    name: str
    caption: str
    duration: float
    action: str = "none"
    query: str | None = None
    flow: str | None = None


STORYBOARD_STEPS = [
    StoryboardStep(
        name="01_scope_paddy",
        caption="KRBL replenishment scope and baseline pressures",
        duration=5.0,
    ),
    StoryboardStep(
        name="02_advance_paddy",
        caption="Advance the telemetry stream to show replenishment movement",
        duration=5.0,
        action="advance_timeline",
    ),
    StoryboardStep(
        name="03_domestic_choice",
        caption="Choice: domestic dealer replenishment across 13 CNFs and 850+ dealers",
        duration=5.0,
        action="select_flow",
        flow="India Gate Classic | Domestic dealer replenishment",
    ),
    StoryboardStep(
        name="04_export_choice",
        caption="Choice: premium aged basmati export recovery lane",
        duration=5.0,
        action="select_flow",
        flow="Premium aged basmati | Export recovery lane",
    ),
    StoryboardStep(
        name="05_new_categories_choice",
        caption="Choice: new categories using the same replenishment cockpit",
        duration=5.0,
        action="select_flow",
        flow="New categories | Spices + rice bran oil",
    ),
    StoryboardStep(
        name="06_live_timeline",
        caption="Live timeline tab: demand, inventory, receipts, and CNF rebalance",
        duration=6.0,
        action="open_live_timeline",
    ),
    StoryboardStep(
        name="07_live_timeline_advanced",
        caption="Advance the timeline again to demonstrate live telemetry movement",
        duration=5.0,
        action="advance_timeline",
    ),
    StoryboardStep(
        name="08_agent_recommendation",
        caption="Agent recommendation tab: trigger, replenish quantity, and release window",
        duration=6.0,
        action="open_agent_recommendation",
    ),
    StoryboardStep(
        name="09_genbi_inventory",
        caption="GenBI answers current inventory and reorder point questions",
        duration=6.0,
        action="ask_genbi",
        query="What is KRBL's current stock and reorder point?",
    ),
    StoryboardStep(
        name="10_genbi_holding",
        caption="GenBI explains the 324-day holding-period reduction target",
        duration=6.0,
        action="ask_genbi",
        query="How does the 324 day holding period improve?",
    ),
    StoryboardStep(
        name="11_genbi_dealer_service",
        caption="GenBI explains dealer service levels and exception SLA",
        duration=6.0,
        action="ask_genbi",
        query="What dealer service level and exception SLA are protected?",
    ),
    StoryboardStep(
        name="12_genbi_cnf_rebalance",
        caption="GenBI recommends CNF rebalance actions for the selected flow",
        duration=6.0,
        action="ask_genbi",
        query="What CNF rebalance should KRBL make now?",
    ),
]
