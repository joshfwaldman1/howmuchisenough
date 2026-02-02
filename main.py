"""
"How Much Is Enough?" — a lifestyle cost calculator by Professor Mike Klausner.

A FastAPI web application that lets users design their dream lifestyle and
computes the total nest egg required to fund it all, demonstrating that
nobody actually needs a billion dollars.

Run with:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from calculator import (
    CostBreakdown,
    EconomicAssumptions,
    ChildSpec,
    HomeSpec,
    LifestyleCalculator,
    LifestyleInputs,
)
from cost_data import (
    ALL_LOCATIONS,
    HOTEL_TIERS,
    PRIMARY_LOCATIONS,
    VACATION_DESTINATIONS,
    VACATION_LOCATIONS,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="How Much Is Enough?")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ---------------------------------------------------------------------------
# Custom Jinja2 filters
# ---------------------------------------------------------------------------

def _format_currency(value: float) -> str:
    """Format a number as a human-friendly dollar string."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    if value >= 1_000:
        return f"${value:,.0f}"
    return f"${value:,.0f}"


def _format_currency_short(value: float) -> str:
    """Shorter version for chart labels."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


def _format_pct(value: float) -> str:
    """Format a fraction as a percentage string."""
    return f"{value:.1%}"


CHART_COLORS = [
    '#1a365d', '#c6922e', '#2d6a4f', '#9b2226',
    '#4a5568', '#6b46c1', '#d97706', '#0891b2', '#be185d',
]


def _chart_color(index: int) -> str:
    """Return a hex color for chart segment `index`."""
    return CHART_COLORS[index % len(CHART_COLORS)]


templates.env.filters["currency"] = _format_currency
templates.env.filters["currency_short"] = _format_currency_short
templates.env.filters["pct"] = _format_pct
templates.env.filters["chart_color"] = _chart_color


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the multi-step wizard form."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "primary_locations": PRIMARY_LOCATIONS,
            "vacation_locations": VACATION_LOCATIONS,
            "all_locations": ALL_LOCATIONS,
            "hotel_tiers": HOTEL_TIERS,
            "vacation_destinations": VACATION_DESTINATIONS,
        },
    )


@app.post("/calculate", response_class=HTMLResponse)
async def calculate(request: Request):
    """Parse the form data, run the calculator, and render results."""
    form = await request.form()

    # --- Parse user basics ------------------------------------------
    user_age = int(form.get("user_age", 40))

    # --- Parse housing ----------------------------------------------
    primary_loc = form.get("primary_home_location", "")
    primary_br = int(form.get("primary_home_bedrooms", 4))
    primary_home = HomeSpec(primary_loc, primary_br) if primary_loc else None

    has_vacation = form.get("has_vacation_home") == "on"
    vacation_home = None
    if has_vacation:
        vac_loc = form.get("vacation_home_location", "")
        vac_br = int(form.get("vacation_home_bedrooms", 4))
        if vac_loc:
            vacation_home = HomeSpec(vac_loc, vac_br)

    # --- Parse lifestyle --------------------------------------------
    annual_expenses = _parse_float(form.get("annual_expenses", "300000"))
    vacations_per_year = int(form.get("vacations_per_year", 0))
    vacation_weeks = int(form.get("vacation_weeks_each", 2))
    vacation_dest = form.get("vacation_destination", "Europe")
    vacation_tier = form.get("vacation_hotel_tier", "Ultra-luxury (Four Seasons, Aman)")

    has_sailboat = form.get("has_sailboat") == "on"
    sailboat_len = int(form.get("sailboat_length", 35))

    has_yacht = form.get("has_yacht") == "on"
    yacht_len = int(form.get("yacht_length", 60))
    yacht_crew = form.get("yacht_crew") == "on"

    custom_desc = form.get("custom_expense_description", "")
    custom_amount = _parse_float(form.get("custom_annual_expense", "0"))

    # --- Parse children ---------------------------------------------
    num_children = int(form.get("num_children", 0))
    children: list[ChildSpec] = []
    for i in range(num_children):
        child_age = int(form.get(f"child_{i}_age", 5))
        child_school = form.get(f"child_{i}_private_school") == "on"
        child_uni = form.get(f"child_{i}_private_university") == "on"
        child_house = form.get(f"child_{i}_buy_house") == "on"
        child_house_loc = form.get(f"child_{i}_house_location", "")
        child_house_br = int(form.get(f"child_{i}_house_bedrooms", 3))
        child_expenses = _parse_float(form.get(f"child_{i}_annual_expenses", "0"))

        children.append(
            ChildSpec(
                age=child_age,
                private_school=child_school,
                private_university=child_uni,
                buy_house=child_house,
                house_location=child_house_loc,
                house_bedrooms=child_house_br,
                annual_expenses=child_expenses,
            )
        )

    provide_gc = form.get("provide_for_grandchildren") == "on"
    gc_per_child = int(form.get("grandchildren_per_child", 2))

    # --- Build inputs and run calculator ----------------------------
    inputs = LifestyleInputs(
        user_age=user_age,
        primary_home=primary_home,
        vacation_home=vacation_home,
        annual_expenses=annual_expenses,
        vacations_per_year=vacations_per_year,
        vacation_weeks_each=vacation_weeks,
        vacation_destination=vacation_dest,
        vacation_hotel_tier=vacation_tier,
        sailboat=has_sailboat,
        sailboat_length=sailboat_len,
        yacht=has_yacht,
        yacht_length=yacht_len,
        yacht_crew=yacht_crew,
        custom_annual_expense=custom_amount,
        custom_expense_description=custom_desc,
        children=children,
        provide_for_grandchildren=provide_gc,
        grandchildren_per_child=gc_per_child,
    )

    assumptions = EconomicAssumptions()
    calc = LifestyleCalculator(assumptions)
    breakdown = calc.calculate(inputs)

    # --- Compute fun comparison stats --------------------------------
    billion = 1_000_000_000
    total = breakdown.grand_total
    pct_of_billion = total / billion if total > 0 else 0
    families_funded = int(billion / total) if total > 0 else 0
    leftover = billion - total

    # What could you do with the leftover?
    stanford_scholarships = int(leftover / 340_000)  # 4 years @ $85k
    affordable_homes = int(leftover / 250_000)
    teacher_salaries = int(leftover / 65_000)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "inputs": inputs,
            "breakdown": breakdown,
            "assumptions": assumptions,
            "total": total,
            "billion": billion,
            "pct_of_billion": pct_of_billion,
            "families_funded": families_funded,
            "leftover": leftover,
            "stanford_scholarships": stanford_scholarships,
            "affordable_homes": affordable_homes,
            "teacher_salaries": teacher_salaries,
            "categories": breakdown.as_categories(),
        },
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_float(value: str) -> float:
    """Parse a form value into a float, stripping commas and dollar signs."""
    cleaned = value.replace(",", "").replace("$", "").strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
