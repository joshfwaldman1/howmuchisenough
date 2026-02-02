"""
Financial engine for the "How Much Is Enough?" lifestyle calculator.

Uses present-value analysis with conservative economic assumptions to compute
the lump-sum nest egg a person would need TODAY to fund their specified
lifestyle — for themselves, their children, and optionally grandchildren.

Methodology
-----------
All calculations work in REAL (inflation-adjusted) dollars:

    real_return  =  (1 + nominal_return) / (1 + inflation)  -  1

Because we express every cost in today's dollars and discount at the real
rate, inflation cancels out of the arithmetic.  Education costs, which
historically outpace general inflation, get a separate "real education
growth" rate applied on top.

Key formulas:
    PV of a level annuity:    PMT * [1 - (1+r)^(-n)] / r
    PV of a growing annuity:  PMT * [1 - ((1+g)/(1+r))^n] / (r - g)
    PV of a future lump sum:  FV / (1+r)^n
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cost_data import (
    HOME_PRICES,
    HOTEL_COSTS_PER_NIGHT,
    VACATION_DAILY_EXTRAS,
    SAILBOAT_PRICES,
    YACHT_PRICES,
    PRIVATE_SCHOOL_ANNUAL,
    PRIVATE_UNIVERSITY_ANNUAL,
    get_property_tax_rate,
    interpolate_price,
    interpolate_yacht_crew_cost,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EconomicAssumptions:
    """
    Conservative economic assumptions underlying every calculation.

    These are shown to the user on the results page so they can evaluate
    how reasonable the numbers are.
    """
    nominal_return: float = 0.06          # 6% balanced-portfolio return
    inflation: float = 0.03              # 3% general CPI inflation
    education_inflation: float = 0.05    # 5% education-cost inflation
    home_maintenance_rate: float = 0.01  # 1% of home value / year
    boat_maintenance_rate: float = 0.10  # 10% of purchase price / year
    life_expectancy: int = 90            # plan to live to 90

    @property
    def real_return(self) -> float:
        """After-inflation portfolio return."""
        return (1 + self.nominal_return) / (1 + self.inflation) - 1

    @property
    def education_real_growth(self) -> float:
        """How fast education costs grow above general inflation."""
        return (1 + self.education_inflation) / (1 + self.inflation) - 1

    def describe(self) -> list[dict]:
        """Return a list of human-readable assumption descriptions."""
        return [
            {
                "label": "Portfolio return (nominal)",
                "value": f"{self.nominal_return:.1%}",
                "detail": (
                    "Expected annual return on a balanced 60/40 stock/bond "
                    "portfolio, slightly below the long-run historical average "
                    "to be conservative."
                ),
            },
            {
                "label": "General inflation",
                "value": f"{self.inflation:.1%}",
                "detail": (
                    "Slightly above the Federal Reserve's 2% target to "
                    "account for periods of above-target inflation."
                ),
            },
            {
                "label": "Real (after-inflation) return",
                "value": f"{self.real_return:.2%}",
                "detail": (
                    "The purchasing-power return your portfolio actually earns. "
                    "Calculated as (1 + nominal) / (1 + inflation) - 1."
                ),
            },
            {
                "label": "Education cost inflation",
                "value": f"{self.education_inflation:.1%}",
                "detail": (
                    "Tuition at elite private schools and universities has "
                    "historically grown at ~5% per year, well above general CPI."
                ),
            },
            {
                "label": "Home maintenance",
                "value": f"{self.home_maintenance_rate:.1%} of home value / year",
                "detail": (
                    "Standard rule of thumb for ongoing repairs, insurance, "
                    "and upkeep on a residential property."
                ),
            },
            {
                "label": "Boat / yacht maintenance",
                "value": f"{self.boat_maintenance_rate:.0%} of purchase price / year",
                "detail": (
                    "The 'hole in the water you pour money into' rule — boats "
                    "are notoriously expensive to dock, insure, and maintain."
                ),
            },
            {
                "label": "Property tax",
                "value": "Varies by state (0.3% – 2.3%)",
                "detail": (
                    "We use the actual effective property-tax rate for each "
                    "selected location (e.g. 0.77% in California, 2.27% in Illinois)."
                ),
            },
            {
                "label": "Life expectancy",
                "value": f"{self.life_expectancy} years",
                "detail": (
                    "We plan conservatively for a long life so the money "
                    "doesn't run out. Applies to you, your children, and "
                    "your grandchildren."
                ),
            },
        ]


@dataclass
class HomeSpec:
    """A home the user wants to buy."""
    location: str
    bedrooms: int

    @property
    def price(self) -> float:
        """Estimated purchase price from reference data."""
        loc_prices = HOME_PRICES.get(self.location, {})
        if self.bedrooms in loc_prices:
            return float(loc_prices[self.bedrooms])
        # Fallback: pick the closest bedroom count available
        if loc_prices:
            closest = min(loc_prices.keys(), key=lambda k: abs(k - self.bedrooms))
            return float(loc_prices[closest])
        return 1_500_000.0  # generic fallback

    @property
    def property_tax_rate(self) -> float:
        return get_property_tax_rate(self.location)


@dataclass
class ChildSpec:
    """What the user wants to provide for one child."""
    age: int
    private_school: bool = False
    private_university: bool = False
    buy_house: bool = False
    house_location: str = ""
    house_bedrooms: int = 3
    annual_expenses: float = 0.0


@dataclass
class LifestyleInputs:
    """Everything the user entered in the wizard form."""
    # About the user
    user_age: int = 40

    # Housing
    primary_home: Optional[HomeSpec] = None
    vacation_home: Optional[HomeSpec] = None

    # Annual living expenses
    annual_expenses: float = 300_000

    # Vacations
    vacations_per_year: int = 0
    vacation_weeks_each: int = 2
    vacation_destination: str = "Europe"
    vacation_hotel_tier: str = "Ultra-luxury (Four Seasons, Aman)"

    # Watercraft
    sailboat: bool = False
    sailboat_length: int = 35
    yacht: bool = False
    yacht_length: int = 60
    yacht_crew: bool = False

    # Custom annual expense
    custom_annual_expense: float = 0.0
    custom_expense_description: str = ""

    # Children
    children: List[ChildSpec] = field(default_factory=list)

    # Grandchildren
    provide_for_grandchildren: bool = False
    grandchildren_per_child: int = 2


@dataclass
class CostBreakdown:
    """Itemized present-value costs by category."""
    primary_home_purchase: float = 0.0
    primary_home_ongoing: float = 0.0
    vacation_home_purchase: float = 0.0
    vacation_home_ongoing: float = 0.0
    living_expenses: float = 0.0
    vacations: float = 0.0
    sailboat: float = 0.0
    yacht: float = 0.0
    custom_expenses: float = 0.0
    children_education: float = 0.0
    children_homes: float = 0.0
    children_expenses: float = 0.0
    grandchildren_total: float = 0.0

    @property
    def housing_total(self) -> float:
        return (self.primary_home_purchase + self.primary_home_ongoing +
                self.vacation_home_purchase + self.vacation_home_ongoing)

    @property
    def watercraft_total(self) -> float:
        return self.sailboat + self.yacht

    @property
    def children_total(self) -> float:
        return self.children_education + self.children_homes + self.children_expenses

    @property
    def grand_total(self) -> float:
        return (
            self.housing_total
            + self.living_expenses
            + self.vacations
            + self.watercraft_total
            + self.custom_expenses
            + self.children_total
            + self.grandchildren_total
        )

    def as_categories(self) -> list[dict]:
        """Return non-zero categories for charting and display."""
        cats = []
        if self.housing_total > 0:
            cats.append({"name": "Housing", "value": self.housing_total})
        if self.living_expenses > 0:
            cats.append({"name": "Living Expenses", "value": self.living_expenses})
        if self.vacations > 0:
            cats.append({"name": "Vacations", "value": self.vacations})
        if self.watercraft_total > 0:
            cats.append({"name": "Watercraft", "value": self.watercraft_total})
        if self.custom_expenses > 0:
            cats.append({"name": "Other Expenses", "value": self.custom_expenses})
        if self.children_education > 0:
            cats.append({"name": "Children's Education", "value": self.children_education})
        if self.children_homes > 0:
            cats.append({"name": "Children's Homes", "value": self.children_homes})
        if self.children_expenses > 0:
            cats.append({"name": "Children's Living Expenses", "value": self.children_expenses})
        if self.grandchildren_total > 0:
            cats.append({"name": "Grandchildren", "value": self.grandchildren_total})
        return cats


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

class LifestyleCalculator:
    """
    Computes the total present-value nest egg required to fund a lifestyle.

    All arithmetic is in REAL (today's) dollars, discounted at the real
    rate of return.  This correctly accounts for both investment growth
    and inflation without needing to inflate each future cost explicitly.
    """

    def __init__(self, assumptions: Optional[EconomicAssumptions] = None):
        self.assumptions = assumptions or EconomicAssumptions()
        self.r = self.assumptions.real_return

    # ---------------------------------------------------------------
    # Core present-value primitives
    # ---------------------------------------------------------------

    def pv_level_annuity(self, pmt: float, n: int) -> float:
        """
        PV of withdrawing `pmt` (real dollars) each year for `n` years.

        Formula: PMT * [1 - (1+r)^(-n)] / r
        """
        if n <= 0 or pmt == 0:
            return 0.0
        r = self.r
        if abs(r) < 1e-10:
            return pmt * n
        return pmt * (1 - (1 + r) ** (-n)) / r

    def pv_growing_annuity(self, first_pmt: float, n: int, g: float) -> float:
        """
        PV of an annuity whose payments grow at real rate `g` each year.

        Used for education costs that outpace general inflation.
        Formula: PMT * [1 - ((1+g)/(1+r))^n] / (r - g)
        """
        if n <= 0 or first_pmt == 0:
            return 0.0
        r = self.r
        if abs(r - g) < 1e-10:
            return first_pmt * n / (1 + r)
        return first_pmt * (1 - ((1 + g) / (1 + r)) ** n) / (r - g)

    def pv_lump_sum(self, amount: float, years: int) -> float:
        """
        PV of a lump sum needed `years` from now, expressed in today's dollars.

        Formula: amount / (1+r)^years
        """
        if years <= 0:
            return amount
        return amount / (1 + self.r) ** years

    def pv_deferred_annuity(
        self, pmt: float, duration: int, deferral: int, g: float = 0.0
    ) -> float:
        """
        PV of an annuity that begins `deferral` years from now and lasts
        `duration` years.

        Computes the value of the annuity AS OF its start date, then
        discounts that lump sum back to today.
        """
        if deferral < 0:
            # Already in progress — calculate remaining portion
            elapsed = -deferral
            remaining = duration - elapsed
            if remaining <= 0:
                return 0.0
            adjusted_pmt = pmt * (1 + g) ** elapsed if g else pmt
            if g > 0:
                return self.pv_growing_annuity(adjusted_pmt, remaining, g)
            return self.pv_level_annuity(adjusted_pmt, remaining)

        if g > 0:
            pv_at_start = self.pv_growing_annuity(pmt, duration, g)
        else:
            pv_at_start = self.pv_level_annuity(pmt, duration)

        return self.pv_lump_sum(pv_at_start, deferral)

    # ---------------------------------------------------------------
    # Full calculation
    # ---------------------------------------------------------------

    def calculate(self, inputs: LifestyleInputs) -> CostBreakdown:
        """Run the complete calculation and return an itemized breakdown."""
        b = CostBreakdown()
        years_left = max(1, self.assumptions.life_expectancy - inputs.user_age)

        # --- Housing ------------------------------------------------
        if inputs.primary_home:
            price = inputs.primary_home.price
            tax = inputs.primary_home.property_tax_rate
            annual = price * (tax + self.assumptions.home_maintenance_rate)
            b.primary_home_purchase = price
            b.primary_home_ongoing = self.pv_level_annuity(annual, years_left)

        if inputs.vacation_home:
            price = inputs.vacation_home.price
            tax = inputs.vacation_home.property_tax_rate
            annual = price * (tax + self.assumptions.home_maintenance_rate)
            b.vacation_home_purchase = price
            b.vacation_home_ongoing = self.pv_level_annuity(annual, years_left)

        # --- Living expenses ----------------------------------------
        b.living_expenses = self.pv_level_annuity(
            inputs.annual_expenses, years_left
        )

        # --- Vacations ----------------------------------------------
        if inputs.vacations_per_year > 0:
            nights = inputs.vacation_weeks_each * 7
            hotel = HOTEL_COSTS_PER_NIGHT.get(inputs.vacation_hotel_tier, 800)
            extras = VACATION_DAILY_EXTRAS.get(inputs.vacation_destination, 300)
            # Cost for 2 travelers
            annual_vac = inputs.vacations_per_year * nights * (hotel + extras) * 2
            b.vacations = self.pv_level_annuity(annual_vac, years_left)

        # --- Sailboat -----------------------------------------------
        if inputs.sailboat:
            purchase = interpolate_price(inputs.sailboat_length, SAILBOAT_PRICES)
            maint = purchase * self.assumptions.boat_maintenance_rate
            b.sailboat = purchase + self.pv_level_annuity(maint, years_left)

        # --- Yacht --------------------------------------------------
        if inputs.yacht:
            purchase = interpolate_price(inputs.yacht_length, YACHT_PRICES)
            maint = purchase * self.assumptions.boat_maintenance_rate
            crew = interpolate_yacht_crew_cost(inputs.yacht_length) if inputs.yacht_crew else 0
            b.yacht = purchase + self.pv_level_annuity(maint + crew, years_left)

        # --- Custom annual expense ----------------------------------
        if inputs.custom_annual_expense > 0:
            b.custom_expenses = self.pv_level_annuity(
                inputs.custom_annual_expense, years_left
            )

        # --- Children & grandchildren -------------------------------
        edu_g = self.assumptions.education_real_growth
        life_exp = self.assumptions.life_expectancy

        for child in inputs.children:
            self._calculate_child(child, inputs, b, edu_g, life_exp)

        return b

    # ---------------------------------------------------------------
    # Per-child calculation (extracted for clarity)
    # ---------------------------------------------------------------

    def _calculate_child(
        self,
        child: ChildSpec,
        inputs: LifestyleInputs,
        b: CostBreakdown,
        edu_g: float,
        life_exp: int,
    ) -> None:
        """
        Add a single child's costs (education, housing, expenses, and
        optionally grandchildren) to the running CostBreakdown.
        """
        # Private school: K-12, ages 5-17 (13 years)
        if child.private_school and child.age < 18:
            school_start = max(child.age, 5)
            years_until = school_start - child.age
            school_years = 18 - school_start
            if school_years > 0:
                b.children_education += self.pv_deferred_annuity(
                    PRIVATE_SCHOOL_ANNUAL, school_years, years_until, edu_g
                )

        # Private university: 4 years starting at age 18
        if child.private_university and child.age < 22:
            if child.age >= 18:
                remaining = 22 - child.age
                b.children_education += self.pv_growing_annuity(
                    PRIVATE_UNIVERSITY_ANNUAL, remaining, edu_g
                )
            else:
                years_until = 18 - child.age
                b.children_education += self.pv_deferred_annuity(
                    PRIVATE_UNIVERSITY_ANNUAL, 4, years_until, edu_g
                )

        # House for adult child at age 25
        if child.buy_house and child.house_location:
            home = HomeSpec(child.house_location, child.house_bedrooms)
            price = home.price
            years_until_25 = max(0, 25 - child.age)

            b.children_homes += self.pv_lump_sum(price, years_until_25)

            # Ongoing home costs from age 25 onward
            annual_home = price * (
                home.property_tax_rate + self.assumptions.home_maintenance_rate
            )
            adult_home_years = life_exp - max(child.age, 25)
            if adult_home_years > 0:
                b.children_homes += self.pv_deferred_annuity(
                    annual_home, adult_home_years, years_until_25
                )

        # Annual living expenses from age 25 onward
        if child.annual_expenses > 0:
            years_until_25 = max(0, 25 - child.age)
            adult_years = life_exp - max(child.age, 25)
            if adult_years > 0:
                b.children_expenses += self.pv_deferred_annuity(
                    child.annual_expenses, adult_years, years_until_25
                )

        # Grandchildren
        if inputs.provide_for_grandchildren and inputs.grandchildren_per_child > 0:
            self._calculate_grandchildren(
                child, inputs, b, edu_g, life_exp
            )

    def _calculate_grandchildren(
        self,
        child: ChildSpec,
        inputs: LifestyleInputs,
        b: CostBreakdown,
        edu_g: float,
        life_exp: int,
    ) -> None:
        """
        Add grandchildren costs for one child.

        Assumes grandchildren are born when the child is 30, spaced
        2 years apart, and receive the same provisions as the child
        (education, housing, expenses).
        """
        base_offset = max(0, 30 - child.age)

        for gc_idx in range(inputs.grandchildren_per_child):
            gc_born = base_offset + gc_idx * 2  # years from now

            # Private school for grandchild (13 years, starting age 5)
            if child.private_school:
                gc_school_start = gc_born + 5
                b.grandchildren_total += self.pv_deferred_annuity(
                    PRIVATE_SCHOOL_ANNUAL, 13, gc_school_start, edu_g
                )

            # Private university for grandchild (4 years at age 18)
            if child.private_university:
                gc_college_start = gc_born + 18
                b.grandchildren_total += self.pv_deferred_annuity(
                    PRIVATE_UNIVERSITY_ANNUAL, 4, gc_college_start, edu_g
                )

            # House at age 25 (same specs as child's house)
            if child.buy_house and child.house_location:
                gc_home = HomeSpec(child.house_location, child.house_bedrooms)
                gc_house_year = gc_born + 25
                b.grandchildren_total += self.pv_lump_sum(
                    gc_home.price, gc_house_year
                )
                # Ongoing home costs
                annual_gc_home = gc_home.price * (
                    gc_home.property_tax_rate + self.assumptions.home_maintenance_rate
                )
                gc_home_years = life_exp - 25
                if gc_home_years > 0:
                    b.grandchildren_total += self.pv_deferred_annuity(
                        annual_gc_home, gc_home_years, gc_house_year
                    )

            # Annual expenses from age 25 onward (same as child)
            if child.annual_expenses > 0:
                gc_adult_start = gc_born + 25
                gc_adult_years = life_exp - 25
                if gc_adult_years > 0:
                    b.grandchildren_total += self.pv_deferred_annuity(
                        child.annual_expenses, gc_adult_years, gc_adult_start
                    )
