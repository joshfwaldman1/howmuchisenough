"""
Reference cost data for the "How Much Is Enough?" lifestyle calculator.

All prices are approximate 2025 USD values based on public market data.
These are deliberately conservative (high-side) estimates so the calculator
slightly *overstates* what you need — strengthening the argument that even
with generous assumptions, a billion dollars is far more than enough.
"""

from typing import Dict

# ---------------------------------------------------------------------------
# Home prices by location and number of bedrooms
# ---------------------------------------------------------------------------
HOME_PRICES: Dict[str, Dict[int, int]] = {
    # Primary-home metro areas
    "Palo Alto, CA":        {2: 2_200_000, 3: 3_200_000, 4: 4_500_000, 5: 6_000_000, 6: 8_000_000},
    "San Francisco, CA":    {2: 1_400_000, 3: 1_900_000, 4: 2_800_000, 5: 3_600_000, 6: 4_500_000},
    "New York City, NY":    {2: 1_600_000, 3: 2_300_000, 4: 3_800_000, 5: 5_200_000, 6: 7_000_000},
    "Los Angeles, CA":      {2: 1_100_000, 3: 1_500_000, 4: 2_200_000, 5: 3_000_000, 6: 4_000_000},
    "Miami, FL":            {2:   650_000, 3:   950_000, 4: 1_500_000, 5: 2_100_000, 6: 2_900_000},
    "Seattle, WA":          {2:   850_000, 3: 1_150_000, 4: 1_650_000, 5: 2_200_000, 6: 3_000_000},
    "Austin, TX":           {2:   480_000, 3:   650_000, 4:   900_000, 5: 1_250_000, 6: 1_700_000},
    "Chicago, IL":          {2:   420_000, 3:   580_000, 4:   850_000, 5: 1_200_000, 6: 1_600_000},
    "Denver, CO":           {2:   530_000, 3:   700_000, 4:   950_000, 5: 1_350_000, 6: 1_800_000},
    "Boston, MA":           {2:   850_000, 3: 1_150_000, 4: 1_750_000, 5: 2_400_000, 6: 3_200_000},
    "Washington, DC":       {2:   750_000, 3: 1_000_000, 4: 1_500_000, 5: 2_100_000, 6: 2_800_000},
    # Vacation-home locations
    "Hawaii (Maui)":        {2: 1_300_000, 3: 1_900_000, 4: 2_600_000, 5: 3_600_000, 6: 4_800_000},
    "Hawaii (Oahu)":        {2:   950_000, 3: 1_350_000, 4: 1_900_000, 5: 2_600_000, 6: 3_400_000},
    "Aspen, CO":            {2: 2_800_000, 3: 4_200_000, 4: 6_500_000, 5: 9_000_000, 6: 12_000_000},
    "Lake Tahoe, CA/NV":    {2:   850_000, 3: 1_250_000, 4: 1_850_000, 5: 2_600_000, 6: 3_400_000},
    "The Hamptons, NY":     {2: 1_600_000, 3: 2_600_000, 4: 4_200_000, 5: 6_500_000, 6: 8_500_000},
    "Naples, FL":           {2:   650_000, 3:   950_000, 4: 1_500_000, 5: 2_100_000, 6: 2_900_000},
    "Jackson Hole, WY":     {2: 1_600_000, 3: 2_400_000, 4: 3_800_000, 5: 5_500_000, 6: 7_000_000},
    "Martha's Vineyard, MA":{2: 1_300_000, 3: 1_900_000, 4: 3_000_000, 5: 4_200_000, 6: 5_800_000},
    "Napa Valley, CA":      {2: 1_000_000, 3: 1_500_000, 4: 2_200_000, 5: 3_200_000, 6: 4_200_000},
}

# Which locations are available as primary vs vacation homes
PRIMARY_LOCATIONS = [
    "Palo Alto, CA", "San Francisco, CA", "New York City, NY",
    "Los Angeles, CA", "Miami, FL", "Seattle, WA", "Austin, TX",
    "Chicago, IL", "Denver, CO", "Boston, MA", "Washington, DC",
]

VACATION_LOCATIONS = [
    "Hawaii (Maui)", "Hawaii (Oahu)", "Aspen, CO", "Lake Tahoe, CA/NV",
    "The Hamptons, NY", "Naples, FL", "Jackson Hole, WY",
    "Martha's Vineyard, MA", "Napa Valley, CA",
]

# Also allow any primary location as a child's home location
ALL_LOCATIONS = PRIMARY_LOCATIONS + VACATION_LOCATIONS

# ---------------------------------------------------------------------------
# Vacation costs
# ---------------------------------------------------------------------------

# Per-room per-night hotel costs (assume one room for two adults)
HOTEL_COSTS_PER_NIGHT: Dict[str, int] = {
    "Ultra-luxury (Four Seasons, Aman)": 1_500,
    "Luxury (Ritz-Carlton, St. Regis)":    800,
    "Upscale (Marriott, Hyatt)":           350,
    "Mid-range":                           200,
}

HOTEL_TIERS = list(HOTEL_COSTS_PER_NIGHT.keys())

# Daily extras beyond the hotel (food, activities, transport) for 2 people
VACATION_DAILY_EXTRAS: Dict[str, int] = {
    "Europe":         400,
    "Asia":           300,
    "Caribbean":      350,
    "US domestic":    250,
    "South America":  250,
    "Africa":         350,
    "Australia / NZ": 350,
}

VACATION_DESTINATIONS = list(VACATION_DAILY_EXTRAS.keys())

# ---------------------------------------------------------------------------
# Watercraft
# ---------------------------------------------------------------------------

# Sailboat purchase price by length in feet
SAILBOAT_PRICES: Dict[int, int] = {
    25:   80_000,
    30:  170_000,
    35:  280_000,
    40:  450_000,
    45:  650_000,
    50:  950_000,
}

# Motor yacht purchase price by length in feet
YACHT_PRICES: Dict[int, int] = {
    40:    500_000,
    50:  1_000_000,
    60:  1_800_000,
    80:  4_000_000,
    100:  9_000_000,
    120: 18_000_000,
    150: 35_000_000,
    200: 90_000_000,
}

# Annual crew cost for a full-time yacht crew, by yacht length
YACHT_CREW_COST: Dict[int, int] = {
    40:    100_000,
    50:    150_000,
    60:    250_000,
    80:    400_000,
    100:   700_000,
    120: 1_000_000,
    150: 1_800_000,
    200: 3_000_000,
}

# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------

# Annual costs in 2025 dollars
PRIVATE_SCHOOL_ANNUAL: int = 55_000   # elite K-12 private school
PRIVATE_UNIVERSITY_ANNUAL: int = 90_000  # tuition + room & board at top privates

# ---------------------------------------------------------------------------
# Property tax — effective rates by state
# ---------------------------------------------------------------------------
PROPERTY_TAX_RATES: Dict[str, float] = {
    "CA": 0.0077,
    "NY": 0.0149,
    "FL": 0.0089,
    "TX": 0.0180,
    "WA": 0.0093,
    "CO": 0.0055,
    "IL": 0.0227,
    "MA": 0.0123,
    "DC": 0.0056,
    "HI": 0.0028,
    "WY": 0.0057,
    "NV": 0.0060,
}

# Map every location name to its state abbreviation for tax lookup
_LOCATION_TO_STATE: Dict[str, str] = {
    "Palo Alto, CA":        "CA",
    "San Francisco, CA":    "CA",
    "Los Angeles, CA":      "CA",
    "Napa Valley, CA":      "CA",
    "Lake Tahoe, CA/NV":    "NV",
    "New York City, NY":    "NY",
    "The Hamptons, NY":     "NY",
    "Miami, FL":            "FL",
    "Naples, FL":           "FL",
    "Austin, TX":           "TX",
    "Seattle, WA":          "WA",
    "Denver, CO":           "CO",
    "Aspen, CO":            "CO",
    "Chicago, IL":          "IL",
    "Boston, MA":           "MA",
    "Martha's Vineyard, MA":"MA",
    "Washington, DC":       "DC",
    "Hawaii (Maui)":        "HI",
    "Hawaii (Oahu)":        "HI",
    "Jackson Hole, WY":     "WY",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_property_tax_rate(location: str) -> float:
    """Return the effective annual property-tax rate for a given location."""
    state = _LOCATION_TO_STATE.get(location, "CA")
    return PROPERTY_TAX_RATES.get(state, 0.01)


def interpolate_price(length_ft: int, price_table: Dict[int, int]) -> float:
    """
    Linearly interpolate a price from a {length: price} lookup table.

    If the requested length is below the smallest key, returns the smallest
    value; if above the largest key, extrapolates linearly from the last two
    entries (capped at 2x the largest entry).
    """
    sizes = sorted(price_table.keys())

    if length_ft <= sizes[0]:
        return float(price_table[sizes[0]])
    if length_ft >= sizes[-1]:
        # Extrapolate, but cap at 2x the largest entry to stay reasonable
        slope = (price_table[sizes[-1]] - price_table[sizes[-2]]) / (sizes[-1] - sizes[-2])
        extrapolated = price_table[sizes[-1]] + slope * (length_ft - sizes[-1])
        return min(extrapolated, price_table[sizes[-1]] * 2.0)

    for i in range(len(sizes) - 1):
        if sizes[i] <= length_ft <= sizes[i + 1]:
            frac = (length_ft - sizes[i]) / (sizes[i + 1] - sizes[i])
            return price_table[sizes[i]] + frac * (price_table[sizes[i + 1]] - price_table[sizes[i]])

    return float(price_table[sizes[-1]])


def interpolate_yacht_crew_cost(length_ft: int) -> float:
    """Interpolate annual yacht crew cost from the reference table."""
    return interpolate_price(length_ft, YACHT_CREW_COST)
