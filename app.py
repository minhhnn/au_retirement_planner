import pandas as pd
import streamlit as st

import superannuation as sp

# --- Streamlit App ---

st.set_page_config(layout="wide", page_title="Australian Retirement Planner")

st.title("Australian Retirement Planner")
st.write("Plan your superannuation growth and retirement income scenarios.")

st.sidebar.header("About This App")
st.sidebar.info(
    "This application helps you project your superannuation balance and "
    "simulate retirement income scenarios, considering Age Pension eligibility "
    "and Australian tax rules. "
    "**Please note: This tool provides estimates only and should not be considered "
    "financial advice. Always consult a qualified financial advisor for personalized guidance.**"
)

st.sidebar.header("General Assumptions")
st.sidebar.markdown("""
* All values are in today's dollars (no inflation adjustment).
* Investment returns are pre-tax (but super is generally taxed at 15% in accumulation, 0% in pension phase after age 60). This model assumes net returns in pension phase.
* Age Pension and Tax rules are based on **July 2025** rates for **homeowners**.
* Super withdrawals after age 60 are tax-free. Only Age Pension is taxable income.
* For **couples**, all super balances and income figures entered/projected are **combined** for the couple. The Age Pension calculation is based on combined assets/income, and tax is calculated as if the Age Pension is split evenly between two individuals, each applying their own SAPTO and tax thresholds relevant for a couple.
""")

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["🚀 Super Growth Calculator", "🎯 Years to Reach Target Super", "📈 Retirement Income Projection"])

with tab1:
    st.header("Super Growth Calculator")
    st.write("Estimate your super balance after a specified number of years.")

    col1, col2 = st.columns(2)
    with col1:
        sg_current_balance = st.number_input("Current Super Balance ($)", min_value=0, value=240000, step=10000)
        sg_annual_contribution = st.number_input("Annual Contribution to Super ($)", min_value=0, value=30000, step=1000)
    with col2:
        sg_annual_return = st.slider("Annual Super Return Rate (%)", min_value=1.0, max_value=10.0, value=20.0, step=0.1) / 100
        sg_years = st.slider("Number of Years to Project", min_value=1, max_value=50, value=10, step=1)

    if st.button("Calculate Super Growth"):
        final_balance = sp.calculate_super_growth(sg_current_balance, sg_annual_contribution, sg_annual_return, sg_years)
        st.success(f"After {sg_years} years, your super balance will be approximately **${final_balance:,.2f}**")

with tab2:
    st.header("Years to Reach Target Super")
    st.write("Find out how many years it will take to reach a specific super balance goal.")

    col1, col2 = st.columns(2)
    with col1:
        tr_start_age = st.number_input("Your Current Age", min_value=18, max_value=60, value=38, step=1)
        tr_current_balance = st.number_input("Current Super Balance ($) ", min_value=0, value=240000, step=10000)
        tr_annual_contribution = st.number_input("Annual Contribution to Super ($) ", min_value=0, value=30000, step=1000)
    with col2:
        tr_target_balance = st.number_input("Target Super Balance ($)", min_value=100000, value=950000, step=10000)
        tr_annual_return = st.slider("Annual Super Return Rate (%) ", min_value=1.0, max_value=10.0, value=20.0, step=0.1) / 100
        

    if st.button("Calculate Years to Target"):
        years, age, final_bal = sp.years_to_reach_target_super(tr_start_age, tr_current_balance, tr_target_balance, tr_annual_contribution, tr_annual_return)
        
        if years == float('inf'):
            st.warning(f"Based on your inputs, it might not be possible to reach ${tr_target_balance:,.2f} within a reasonable timeframe (100 years). Current balance reached: ${final_bal:,.2f}")
        else:
            st.success(f"To reach **${tr_target_balance:,.2f}** in super:")
            st.info(f"It will take approximately **{years} years**.")
            st.info(f"You will be **{age} years old** when you reach this target. (Final balance: ${final_bal:,.2f})")

with tab3:
    st.header("Retirement Income Projection")
    st.write("Project your annual after-tax income and super balance throughout retirement, including Age Pension.")

    col1, col2 = st.columns(2)
    with col1:
        ri_relationship_status = st.radio("Are you single or a couple?", ('single', 'couple'))
        super_balance_label = "Initial Super Balance at Retirement Start ($)"
        target_income_label = "Desired Annual After-Tax Income ($)"

        if ri_relationship_status == 'couple':
            super_balance_label = "Combined Super Balance at Retirement Start ($)"
            target_income_label = "Desired Annual Combined After-Tax Income ($)"
            st.info("For 'couple' scenario, all super and income figures are **combined** for both partners.")
            
        ri_start_super = st.number_input(super_balance_label, min_value=0, value=950000 if ri_relationship_status == 'single' else 1400000, step=10000)
        ri_start_age = st.number_input("Age at Retirement Start (for eldest partner if couple)", min_value=60, max_value=75, value=65, step=1)
        
    with col2:
        ri_end_age = st.number_input("Project Until Age", min_value=80, max_value=100, value=95, step=1)
        ri_super_return = st.slider("Super Return Rate During Retirement (%)", min_value=1.0, max_value=20.0, value=4.0, step=0.1) / 100
        ri_target_income = st.number_input(target_income_label, min_value=0, value=60000 if ri_relationship_status == 'single' else 90000, step=1000)

    if st.button("Run Retirement Projection"):
        if ri_start_age >= ri_end_age:
            st.error("Retirement start age must be less than the end age.")
        else:
            projection_results = sp.project_retirement_income(ri_start_super, ri_start_age, ri_end_age, ri_super_return, ri_target_income, ri_relationship_status)
            
            if not projection_results:
                st.warning("No projection could be generated with the given inputs. Please check your values.")
            else:
                df_results = pd.DataFrame(projection_results)
                
                st.subheader("Year-by-Year Projection")
                st.dataframe(df_results.style.format({
                    "Start Super ($)": "${:,.2f}",
                    "Min Drawdown ($)": "${:,.2f}",
                    "Annual Super Withdrawal ($)": "${:,.2f}",
                    "Annual Age Pension ($)": "${:,.2f}",
                    "Total Annual Income (Pre-Tax) ($)": "${:,.2f}",
                    "Taxable Income ($)": "${:,.2f}", # For couples, this is the per-person taxable portion of AP
                    "Tax Payment ($)": "${:,.2f}", # This is the total tax paid by the household
                    "Total Income (After Tax) ($)": "${:,.2f}",
                    "Investment Return ($)": "${:,.2f}",
                    "End Super ($)": "${:,.2f}"
                }))

                st.subheader("Summary")
                last_year_data = df_results.iloc[-1]
                
                status_text = "your" if ri_relationship_status == 'single' else "your combined"
                income_status_text = "your" if ri_relationship_status == 'single' else "the household's"
                
                st.write(f"Projection runs from **Age {ri_start_age}** to **Age {last_year_data['Age']}** (for {status_text} eldest partner if couple).")
                
                if last_year_data["End Super ($)"] <= 0:
                    st.warning(f"**{status_text.capitalize()} super balance was depleted at Age {last_year_data['Age']}**.")
                    if last_year_data["Annual Age Pension ($)"] > 0:
                        st.info(f"From that point onwards, {income_status_text} annual income (if any) would rely solely on the Age Pension, which was **${last_year_data['Annual Age Pension ($)'] :,.2f}** (pre-tax) / **${last_year_data['Total Income (After Tax) ($)'] :,.2f}** (after-tax) at Age {last_year_data['Age']}.")
                        if last_year_data['Total Income (After Tax) ($)'] < ri_target_income:
                             st.error(f"Note: Desired after-tax income of ${ri_target_income:,.2f} was not consistently met after super depletion.")
                    else:
                        st.error(f"{status_text.capitalize()} super balance depleted and no Age Pension was received at Age {last_year_data['Age']}. Income would likely cease.")
                else:
                    st.success(f"At **Age {last_year_data['Age']}**, {status_text} projected super balance remaining is **${last_year_data['End Super ($)']:,.2f}**.")
                    st.info(f"{income_status_text.capitalize()} consistently achieved an after-tax income of at least **${ri_target_income:,.2f}** per year.")

st.markdown("---")
st.markdown("Disclaimer: This tool is for illustrative purposes only and provides general information. "
            "It does not take into account your personal financial situation, objectives, or needs. "
            "Financial decisions should always be made with the advice of a qualified professional.")