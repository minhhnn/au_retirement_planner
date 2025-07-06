# --- Core Functions ---

def calculate_super_growth(current_balance, annual_contribution, annual_return_rate, years):
    """
    Calculates the super balance after a specified number of years.

    Args:
        current_balance (float): Starting super balance.
        annual_contribution (float): Annual contribution to super.
        annual_return_rate (float): Annual investment return rate (e.g., 0.05 for 5%).
        years (int): Number of years to project.

    Returns:
        float: Super balance after 'years'.
    """
    balance = current_balance
    for _ in range(years):
        balance += annual_contribution
        balance *= (1 + annual_return_rate)
    return balance

def years_to_reach_target_super(start_age, current_balance, target_balance, annual_contribution, annual_return_rate):
    """
    Calculates how many years it will take to reach a specific super balance target.

    Args:
        start_age (int): Your current age.
        current_balance (float): Your current super balance.
        target_balance (float): The super balance you aim to reach.
        annual_contribution (float): Your annual contribution to super.
        annual_return_rate (float): Annual investment return rate (e.g., 0.05 for 5%).

    Returns:
        tuple: (years_to_reach_target, age_at_target, final_balance)
    """
    years = 0
    age = start_age
    balance = current_balance
    
    # Defensive check to avoid infinite loops if target is unreachable or already met
    if target_balance <= current_balance:
        return 0, start_age, current_balance
    if annual_contribution <= 0 and annual_return_rate <= 0:
        return float('inf'), float('inf'), current_balance # Indicate it's unreachable

    # Add a safety break for extremely long projections
    max_years_projection = 100 
    
    while balance < target_balance and years < max_years_projection:
        balance += annual_contribution
        balance *= (1 + annual_return_rate)
        years += 1
        age += 1

    if years == max_years_projection and balance < target_balance:
        return float('inf'), float('inf'), balance # Indicate it couldn't reach in max_years
    
    return years, age, balance

def project_retirement_income(start_super, start_age, end_age, super_return_rate, target_after_tax_income, relationship_status):
    """
    Projects retirement income year by year, integrating Age Pension and tax,
    now supporting single or couple scenarios.

    Args:
        start_super (float): Initial super balance at the start_age.
                             (Combined for couples)
        start_age (int): The age at which the projection starts.
        end_age (int): The age at which the projection ends.
        super_return_rate (float): Annual investment return rate for super.
        target_after_tax_income (float): Desired annual income after tax.
                                         (Combined for couples)
        relationship_status (str): 'single' or 'couple'.

    Returns:
        list of dict: A list of dictionaries, each representing a year's projection.
    """

    # --- Constants for Age Pension and Tax (as of July 1, 2025, Homeowner) ---
    # These constants are now dynamic based on relationship status

    CONSTANTS = {
        'single': {
            'MAX_ANNUAL_AGE_PENSION': 29874, # $1,149/fortnight * 26 fortnights
            'DEEM_THRESH1': 64200,
            'DEEM_RATE1': 0.0025,
            'DEEM_RATE2': 0.0225,
            'ASSET_FULL_PENSION': 321500,
            'ASSET_PART_PENSION_CUTOFF': 704500, # Asset value where pension becomes zero
            'INCOME_FULL_PENSION': 5668, # $218/fortnight * 26 fortnights
            'INCOME_PART_PENSION_CUTOFF': 65416, # $2,516/fortnight * 26 fortnights
            'AP_INCOME_REDUCTION_RATE': 0.5, # $0.50 per dollar over threshold
            'SAPTO_MAX': 2230,
            'SAPTO_EFFECTIVE_TAX_FREE_THRESHOLD': 32279, # Approx. based on SAPTO
            'SAPTO_PHASE_OUT_RATE': 0.125,
            'MEDICARE_LEVY_THRESHOLD_SENIOR': 43020,
            'MEDICARE_LEVY_RATE': 0.02
        },
        'couple': {
            'MAX_ANNUAL_AGE_PENSION': 45037.20, # $1,732.20/fortnight * 26 fortnights (combined)
            'DEEM_THRESH1': 106200, # Combined for couple
            'DEEM_RATE1': 0.0025,
            'DEEM_RATE2': 0.0225,
            'ASSET_FULL_PENSION': 481500, # Combined for couple
            'ASSET_PART_PENSION_CUTOFF': 1059000, # Combined for couple
            'INCOME_FULL_PENSION': 9880, # $380/fortnight * 26 fortnights (combined)
            'INCOME_PART_PENSION_CUTOFF': 99954.40, # $3,844.40/fortnight * 26 fortnights (combined)
            'AP_INCOME_REDUCTION_RATE': 0.5, # $0.25 per person per dollar over threshold, so $0.50 combined
            'SAPTO_MAX': 1602, # Max for *each* partner
            'SAPTO_EFFECTIVE_TAX_FREE_THRESHOLD': 30994, # Approx. for *each* partner based on SAPTO rules
            'SAPTO_PHASE_OUT_RATE': 0.125,
            'MEDICARE_LEVY_THRESHOLD_SENIOR': 59886, # Combined for family (senior/pensioner)
            'MEDICARE_LEVY_RATE': 0.02
        }
    }
    
    selected_constants = CONSTANTS[relationship_status]

    MAX_ANNUAL_AGE_PENSION = selected_constants['MAX_ANNUAL_AGE_PENSION']
    DEEM_RATE1 = selected_constants['DEEM_RATE1']
    DEEM_THRESH1 = selected_constants['DEEM_THRESH1']
    DEEM_RATE2 = selected_constants['DEEM_RATE2']
    ASSET_FULL_PENSION = selected_constants['ASSET_FULL_PENSION']
    ASSET_PART_PENSION_CUTOFF = selected_constants['ASSET_PART_PENSION_CUTOFF']
    INCOME_FULL_PENSION = selected_constants['INCOME_FULL_PENSION']
    INCOME_PART_PENSION_CUTOFF = selected_constants['INCOME_PART_PENSION_CUTOFF']
    AP_INCOME_REDUCTION_RATE = selected_constants['AP_INCOME_REDUCTION_RATE']

    SAPTO_MAX = selected_constants['SAPTO_MAX']
    SAPTO_EFFECTIVE_TAX_FREE_THRESHOLD = selected_constants['SAPTO_EFFECTIVE_TAX_FREE_THRESHOLD']
    SAPTO_PHASE_OUT_RATE = selected_constants['SAPTO_PHASE_OUT_RATE']
    MEDICARE_LEVY_THRESHOLD_SENIOR = selected_constants['MEDICARE_LEVY_THRESHOLD_SENIOR']
    MEDICARE_LEVY_RATE = selected_constants['MEDICARE_LEVY_RATE']

    AGE_PENSION_ELIGIBILITY_AGE = 67

    # --- Minimum Super Drawdown Rates ---
    MIN_DRAWDOWN_RATES = {
        (0, 64): 0.04,
        (65, 74): 0.05,
        (75, 79): 0.06,
        (80, 84): 0.07,
        (85, 89): 0.09,
        (90, 94): 0.11,
        (95, 200): 0.14
    }

    def get_min_drawdown_rate(age):
        for age_range, rate in MIN_DRAWDOWN_RATES.items():
            if age_range[0] <= age <= age_range[1]:
                return rate
        return 0.0 # Should not happen if ranges cover all ages

    def calculate_tax(taxable_income, age, is_couple_tax=False):
        gross_tax = 0
        # 2025-26 Tax Brackets
        if taxable_income <= 18200:
            gross_tax = 0
        elif taxable_income <= 45000:
            gross_tax = (taxable_income - 18200) * 0.16
        elif taxable_income <= 135000:
            gross_tax = 4288 + (taxable_income - 45000) * 0.30
        elif taxable_income <= 190000:
            gross_tax = 31288 + (taxable_income - 135000) * 0.37
        else:
            gross_tax = 51638 + (taxable_income - 190000) * 0.45
        
        sapto_offset = 0
        if age >= AGE_PENSION_ELIGIBILITY_AGE:
            # Apply SAPTO based on whether it's a single's tax calculation or half of a couple's
            sapto_max_current = SAPTO_MAX # This will be per person for couple
            sapto_effective_threshold_current = SAPTO_EFFECTIVE_TAX_FREE_THRESHOLD # This will be per person for couple

            if taxable_income <= sapto_effective_threshold_current:
                sapto_offset = gross_tax
            else:
                sapto_offset = max(0, sapto_max_current - (taxable_income - sapto_effective_threshold_current) * SAPTO_PHASE_OUT_RATE)
                sapto_offset = min(sapto_offset, gross_tax)

        tax_after_sapto = max(0, gross_tax - sapto_offset)

        medicare_levy = 0
        # For a couple, the Medicare levy threshold is for the *combined* income.
        # Here we are calculating tax for an *individual's* income (half of the combined AP).
        # We need to use the combined threshold and apply Medicare Levy only if the total combined deemed income
        # plus any other taxable income (not super withdrawal) crosses the combined threshold.
        # For simplicity in this function, we assume `taxable_income` here already represents the relevant
        # individual's portion of taxable income relative to their own thresholds.
        # This is a simplification; a full tax model for couples would be more complex,
        # often requiring both partners' incomes for MLS.
        # For now, let's keep it based on the individual's slice of taxable AP income.
        
        # If the taxable income is below the individual senior threshold, no MLS.
        # If it's a couple scenario, we apply the couple's MLS threshold to the *combined* taxable income (which is just the AP here).
        if not is_couple_tax: # Single person's tax calc
            if taxable_income > MEDICARE_LEVY_THRESHOLD_SENIOR:
                medicare_levy = taxable_income * MEDICARE_LEVY_RATE
        else: # For a couple, this taxable_income is *half* of the combined AP. We need to check combined AP against combined MLS threshold.
            # We are calculating tax for one partner, but MLS applies based on combined threshold.
            # Let's adjust this: if total combined AP > couple's ML threshold, then ML applies to each partner's taxable AP portion.
            # This is a bit of a tricky simplification. For now, let's assume we're passing the relevant individual portion for MLS test.
            # A more robust model would pass the combined income and distribute MLS.
            # For simplicity, if we pass `taxable_income` as the individual slice, we can just use the single threshold as a proxy here for individual ML.
            # OR, more correctly, Medicare Levy for couples is based on combined taxable income.
            # For this simplified model, where taxable income is only the AP, let's assume `taxable_income` is the AP portion for ONE person.
            # We'll apply the single Medicare Levy threshold to this individual's portion for now for simplicity of this `calculate_tax` function.
            # A truly accurate couple's tax would need the full combined gross income for MLS.
            # Reverting to the logic that `taxable_income` here is the *individual* slice being taxed for SAPTO, and Medicare Levy applies based on individual threshold,
            # or the combined threshold if passed as the *total* taxable income.
            # For a couple, the Age Pension is divided. So, if `taxable_income` is the half share of AP,
            # we need to consider if the *total combined* AP crosses the *couple's* ML threshold.
            # To simplify, `calculate_tax` will assume `taxable_income` is the individual's portion.
            # The calling code will need to divide the Age Pension for tax calculation.

            # For now, if the total AP (taxable income being considered) for this *person* (which is half the couple's AP)
            # exceeds the SINGLE senior threshold, apply MLS. This is a simplification but keeps the function modular.
            # Proper MLS for couples is based on combined income.
            if taxable_income > selected_constants['MEDICARE_LEVY_THRESHOLD_SENIOR'] / (1 if relationship_status == 'single' else 2): # Divide by 2 if checking against individual slice for a couple
                 medicare_levy = taxable_income * MEDICARE_LEVY_RATE


        return tax_after_sapto + medicare_levy

    results = []
    current_super = start_super

    for age in range(start_age, end_age + 1): # Iterate by age
        
        annual_age_pension = 0
        if age >= AGE_PENSION_ELIGIBILITY_AGE:
            # 1. Calculate Deemed Income
            deemed_income = 0
            if current_super > 0: # Only deem if there's a balance
                deemed_income = (min(current_super, DEEM_THRESH1) * DEEM_RATE1) + \
                                (max(0, current_super - DEEM_THRESH1) * DEEM_RATE2)

            # 2. Calculate Age Pension based on Income Test
            ap_by_income = 0
            if deemed_income <= INCOME_FULL_PENSION:
                ap_by_income = MAX_ANNUAL_AGE_PENSION
            elif deemed_income < INCOME_PART_PENSION_CUTOFF:
                # Pension reduces by AP_INCOME_REDUCTION_RATE per dollar over income free area
                ap_by_income = max(0, MAX_ANNUAL_AGE_PENSION - (deemed_income - INCOME_FULL_PENSION) * AP_INCOME_REDUCTION_RATE)
            # Else, it's 0 if above cut-off

            # 3. Calculate Age Pension based on Assets Test
            ap_by_asset = 0
            if current_super <= ASSET_FULL_PENSION:
                ap_by_asset = MAX_ANNUAL_AGE_PENSION
            elif current_super < ASSET_PART_PENSION_CUTOFF:
                # Pension reduces by $3 per fortnight for every $1,000 over the limit
                # Annually: ($3/$1000) * 26 fortnights = 0.0078
                ap_by_asset = max(0, MAX_ANNUAL_AGE_PENSION - (current_super - ASSET_FULL_PENSION) * 0.0078)
            # Else, it's 0 if above cut-off

            annual_age_pension = min(ap_by_income, ap_by_asset)
            annual_age_pension = max(0, annual_age_pension) # Ensure no negative pension

        # Calculate tax on Age Pension
        # For couples, Age Pension is received by each partner, so for tax purposes, we assume it's split.
        # The tax calculation function (`calculate_tax`) will then use the per-person SAPTO/ML thresholds.
        taxable_age_pension_for_tax_calc = annual_age_pension / (2 if relationship_status == 'couple' else 1)
        tax_payment_per_person = calculate_tax(taxable_age_pension_for_tax_calc, age, is_couple_tax=(relationship_status == 'couple'))
        total_tax_payment = tax_payment_per_person * (2 if relationship_status == 'couple' else 1)
        
        after_tax_age_pension = annual_age_pension - total_tax_payment

        # Determine required super withdrawal to meet target after-tax income
        required_super_withdrawal = target_after_tax_income - after_tax_age_pension
        
        # Get minimum drawdown amount
        min_drawdown_rate = get_min_drawdown_rate(age)
        min_drawdown_amt = current_super * min_drawdown_rate

        # The actual super withdrawal should be at least the minimum drawdown amount,
        # but also enough to meet the desired after-tax income.
        annual_super_withdrawal = max(min_drawdown_amt, required_super_withdrawal)
        
        # Ensure we don't withdraw more than available super
        annual_super_withdrawal = min(annual_super_withdrawal, current_super)

        # If after-tax Age Pension alone meets or exceeds the target,
        # we still need to take the minimum drawdown if super exists and age requires.
        if target_after_tax_income <= after_tax_age_pension:
            annual_super_withdrawal = min_drawdown_amt # Still need to meet minimum drawdown if applicable
            annual_super_withdrawal = min(annual_super_withdrawal, current_super) # Don't overdraw

        # Ensure super withdrawal is not negative
        annual_super_withdrawal = max(0, annual_super_withdrawal)

        total_annual_income_before_tax = annual_super_withdrawal + annual_age_pension
        total_income_after_tax = total_annual_income_before_tax - total_tax_payment

        # Calculate investment return for the *remaining* super balance
        super_balance_after_withdrawal = current_super - annual_super_withdrawal
        investment_return = super_balance_after_withdrawal * super_return_rate
        
        end_super = super_balance_after_withdrawal + investment_return

        results.append({
            "Age": age,
            "Start Super ($)": round(current_super, 2),
            "Min Drawdown %": round(min_drawdown_rate * 100, 2),
            "Min Drawdown ($)": round(min_drawdown_amt, 2),
            "Annual Super Withdrawal ($)": round(annual_super_withdrawal, 2),
            "Annual Age Pension ($)": round(annual_age_pension, 2),
            "Total Annual Income (Pre-Tax) ($)": round(total_annual_income_before_tax, 2),
            "Taxable Income ($)": round(taxable_age_pension_for_tax_calc, 2), # Show per-person taxable portion for couple
            "Tax Payment ($)": round(total_tax_payment, 2), # Show total tax paid by the household
            "Total Income (After Tax) ($)": round(total_income_after_tax, 2),
            "Investment Return ($)": round(investment_return, 2),
            "End Super ($)": round(end_super, 2)
        })

        current_super = end_super
        if current_super <= 0 and age < end_age: # If super depletes early
            current_super = 0 # Cap at zero
            if annual_age_pension == 0 and total_income_after_tax < target_after_tax_income:
                 # If super is 0 and no Age Pension, and target income not met, then stop.
                 break
    return results