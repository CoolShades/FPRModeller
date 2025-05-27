import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Constants
# NODAL_POINTS format: (Nodal name, 2024/25 actual pay, 2025/26 offered pay)
NODAL_POINTS = [
    ("Nodal 1", 36616, 38831),  # Current pay, Offered pay
    ("Nodal 2", 42008, 44439),  # Current pay, Offered pay
    ("Nodal 3", 49909, 52656),  # Current pay, Offered pay
    ("Nodal 4", 61825, 65048),  # Current pay, Offered pay
    ("Nodal 5", 70425, 73992)   # Current pay, Offered pay
]
AVAILABLE_YEARS = [
    "2008/2009", "2009/2010", "2010/2011", "2011/2012", "2012/2013",
    "2013/2014", "2014/2015", "2015/2016", "2016/2017", "2017/2018",
    "2018/2019", "2019/2020", "2020/2021", "2021/2022", "2022/2023",
    "2023/2024", "2024/2025", "2025/2026"
]

# Nodal-specific pay awards for recent years
NODAL_SPECIFIC_PAY_AWARDS = {
    "2023/2024": {
        "Nodal 1": 0.0371,
        "Nodal 2": 0.0371,
        "Nodal 3": 0.0505,
        "Nodal 4": 0.0371,
        "Nodal 5": 0.0371
    },
    "2024/2025": {
        "Nodal 1": 0.0900,
        "Nodal 2": 0.0860,
        "Nodal 3": 0.0820,
        "Nodal 4": 0.0770,
        "Nodal 5": 0.0750
    },
    "2025/2026": {
        "Nodal 1": 0.06049268079,
        "Nodal 2": 0.05786992953,
        "Nodal 3": 0.05504017311,
        "Nodal 4": 0.05213101496,
        "Nodal 5": 0.05064962726
    }
}

# Tax and NI calculation functions
def calculate_pension_contribution(basic_pay):
    # Pension cost is 23.7% of basic pay (without additional hours and out-of-hours)
    return basic_pay * 0.237

def calculate_income_tax(income):
    if income <= 12570:  # Personal Allowance
        return 0
    elif income <= 50270:
        tax = (income - 12570) * 0.2
        return tax
    elif income <= 125140:
        tax = (50270 - 12570) * 0.2 + (income - 50270) * 0.4
        return tax
    else:
        tax = (50270 - 12570) * 0.2 + (125140 - 50270) * 0.4 + (income - 125140) * 0.45
        return tax

def calculate_national_insurance(income):
    weekly_income = income / 52
    if weekly_income <= 242:
        return 0
    elif weekly_income <= 967:
        ni = (weekly_income - 242) * 0.08 * 52
        return ni
    else:
        ni = (967 - 242) * 0.08 * 52 + (weekly_income - 967) * 0.02 * 52
        return ni
    
def calculate_employer_ni(income):
    weekly_income = income / 52
    if weekly_income <= 175:
        return 0
    elif weekly_income <= 481:
        ni = (weekly_income - 175) * 0.138 * 52
        return ni
    elif weekly_income <= 967:
        ni = (481 - 175) * 0.138 * 52 + (weekly_income - 481) * 0.138 * 52
        return ni
    else:
        ni = (481 - 175) * 0.138 * 52 + (967 - 481) * 0.138 * 52 + (weekly_income - 967) * 0.138 * 52
        return ni

# Calculation Functions
def calculate_real_terms_change(pay_rise, inflation):
    return ((1 + pay_rise) / (1 + inflation)) - 1

def calculate_new_pay_erosion(current_erosion, real_terms_change):
    return ((1 + current_erosion) * (1 + real_terms_change)) - 1

def calculate_fpr_percentage(start_year, end_year, inflation_type, nodal_point=None, year_inputs=None):
    # Base pay data from the provided tables
    pay_data = [
        {"year": "2008/2009", "pay_award": 0.0, "rpi": 0.0, "cpi": 0.0},  # Baseline year
        {"year": "2009/2010", "pay_award": 0.015, "rpi": 0.046, "cpi": 0.033},
        {"year": "2010/2011", "pay_award": 0.010, "rpi": 0.052, "cpi": 0.045},
        {"year": "2011/2012", "pay_award": 0.000, "rpi": 0.032, "cpi": 0.028},
        {"year": "2012/2013", "pay_award": 0.000, "rpi": 0.030, "cpi": 0.026},
        {"year": "2013/2014", "pay_award": 0.010, "rpi": 0.024, "cpi": 0.015},
        {"year": "2014/2015", "pay_award": 0.000, "rpi": 0.010, "cpi": 0.000},
        {"year": "2015/2016", "pay_award": 0.000, "rpi": 0.018, "cpi": 0.007},
        {"year": "2016/2017", "pay_award": 0.010, "rpi": 0.036, "cpi": 0.027},
        {"year": "2017/2018", "pay_award": 0.010, "rpi": 0.033, "cpi": 0.025},
        {"year": "2018/2019", "pay_award": 0.020, "rpi": 0.026, "cpi": 0.018},
        {"year": "2019/2020", "pay_award": 0.023, "rpi": 0.015, "cpi": 0.009},
        {"year": "2020/2021", "pay_award": 0.030, "rpi": 0.041, "cpi": 0.026},
        {"year": "2021/2022", "pay_award": 0.030, "rpi": 0.116, "cpi": 0.091},
        {"year": "2022/2023", "pay_award": 0.030, "rpi": 0.097, "cpi": 0.073},
        {"year": "2023/2024", "pay_award": None, "rpi": 0.036, "cpi": 0.025}, # Will use nodal-specific values
        {"year": "2024/2025", "pay_award": None, "rpi": 0.045, "cpi": 0.035}, # Will use nodal-specific values
        {"year": "2025/2026", "pay_award": None, "rpi": None, "cpi": None}  # Will use user-defined inflation rates
    ]
    
    # If a nodal point is specified, use nodal-specific pay awards for 2023/2024, 2024/2025, and 2025/2026
    if nodal_point is not None:
        for i, data in enumerate(pay_data):
            if data["year"] == "2023/2024":
                pay_data[i]["pay_award"] = NODAL_SPECIFIC_PAY_AWARDS["2023/2024"].get(nodal_point, 0.0371)
            elif data["year"] == "2024/2025":
                pay_data[i]["pay_award"] = NODAL_SPECIFIC_PAY_AWARDS["2024/2025"].get(nodal_point, 0.0820)
            elif data["year"] == "2025/2026":
                pay_data[i]["pay_award"] = NODAL_SPECIFIC_PAY_AWARDS["2025/2026"].get(nodal_point, 0.0560)
    else:
        # Use average values if nodal point is not specified
        for i, data in enumerate(pay_data):
            if data["year"] == "2023/2024":
                pay_data[i]["pay_award"] = 0.0400  # Average
            elif data["year"] == "2024/2025":
                pay_data[i]["pay_award"] = 0.0820  # Average
            elif data["year"] == "2025/2026":
                pay_data[i]["pay_award"] = 0.0560  # Average
    
    start_index = next((i for i, data in enumerate(pay_data) if data["year"] == start_year), 0)
    end_index = next((i for i, data in enumerate(pay_data) if data["year"] == end_year), len(pay_data))
    cumulative_effect = 1.0
    
    inflation_key = "rpi" if inflation_type == "RPI" else "cpi"
    
    for data in pay_data[start_index:end_index]:
        inflation_rate = data[inflation_key]
        
        # Handle None inflation - use user-defined values for 2025/2026
        if inflation_rate is None and data["year"] == "2025/2026" and year_inputs is not None:
            # Get the first year_input (index 0) which corresponds to 2025/2026
            if inflation_key == "rpi":
                inflation_rate = year_inputs[0]["rpi"]
            else:  # CPI
                inflation_rate = year_inputs[0]["cpi"]
        
        if inflation_rate == 0.0 or inflation_rate is None:  # Skip years with no inflation data
            continue
        real_terms_change = ((1 + data["pay_award"]) / (1 + inflation_rate)) - 1
        cumulative_effect *= (1 + real_terms_change)
    
    fpr_percentage = (1 - cumulative_effect) * 100
    return fpr_percentage

def calculate_weighted_average(percentages, doctor_counts):
    total_doctors = sum(doctor_counts.values())
    weighted_sum = sum(percentages[name] * doctor_counts[name] for name in percentages)
    return weighted_sum / total_doctors if total_doctors > 0 else 0

def update_nodal_percentages(year):
    for name, _, _ in NODAL_POINTS:
        st.session_state[f"nodal_percentages_{year}"][name] = st.session_state[f"percentage_{year}"] / 100

def update_first_year_nodal_percentages():
    year = 0
    if any(st.session_state[f"year1_pound_{name}"] > 0 for name, _, _ in NODAL_POINTS):
        for name, base_pay, _ in NODAL_POINTS:
            pound_increase = st.session_state[f"year1_pound_{name}"]
            st.session_state[f"nodal_percentages_{year}"][name] = pound_increase / base_pay
    else:
        update_nodal_percentages(year)

def initialize_session_state():
    if 'fpr_start_year' not in st.session_state:
        st.session_state.fpr_start_year = AVAILABLE_YEARS[0]
    if 'fpr_end_year' not in st.session_state:
        st.session_state.fpr_end_year = AVAILABLE_YEARS[-1]
    if 'inflation_type' not in st.session_state:
        st.session_state.inflation_type = "RPI"
    if 'end_year_options' not in st.session_state:
        st.session_state.end_year_options = AVAILABLE_YEARS[1:]
    if 'fpr_targets' not in st.session_state:
        st.session_state.fpr_targets = {}
    if 'year_inputs' not in st.session_state:
        st.session_state.year_inputs = []
    if 'global_inflation' not in st.session_state:
        st.session_state.global_inflation = 2.0
    if 'global_pay_rise' not in st.session_state:
        # Set default based on inflation type
        if st.session_state.inflation_type == "RPI":
            st.session_state.global_pay_rise = 18.85
        else:  # CPI
            st.session_state.global_pay_rise = 8.7
    if 'num_years' not in st.session_state:
        st.session_state.num_years = 2  # Default to 2 years
    
    # Initial targets will be calculated in setup_sidebar after year_inputs are created

def update_fpr_targets(year_inputs=None):
    st.session_state.fpr_targets = {
        name: calculate_fpr_percentage(st.session_state.fpr_start_year, st.session_state.fpr_end_year,
                                      st.session_state.inflation_type, name, year_inputs)
        for name, _, _ in NODAL_POINTS
    }

def update_end_year_options():
    start_index = AVAILABLE_YEARS.index(st.session_state.fpr_start_year)
    st.session_state.end_year_options = AVAILABLE_YEARS[start_index + 1:]
    if st.session_state.fpr_end_year not in st.session_state.end_year_options:
        st.session_state.fpr_end_year = st.session_state.end_year_options[-1]
    if 'year_inputs' in st.session_state and st.session_state.year_inputs:
        update_fpr_targets(st.session_state.year_inputs)
    else:
        update_fpr_targets()

# UI Setup Functions
def update_global_pay_rise_for_inflation():
    """Update global pay rise default based on inflation type"""
    if st.session_state.inflation_type == "RPI":
        st.session_state.global_pay_rise = 18.85
    else:  # CPI
        st.session_state.global_pay_rise = 8.7
    
    # Also update individual year settings if they exist
    if 'num_years' in st.session_state:
        for year in range(1, st.session_state.num_years + 1):
            # Update nodal percentages for each year
            if f"nodal_percentages_{year}" in st.session_state:
                for name, _, _ in NODAL_POINTS:
                    st.session_state[f"nodal_percentages_{year}"][name] = st.session_state.global_pay_rise
            # Update individual year controls
            for name, _, _ in NODAL_POINTS:
                if f"mypd_nodal_percentage_{name}_{year}" in st.session_state:
                    st.session_state[f"mypd_nodal_percentage_{name}_{year}"] = st.session_state.global_pay_rise

def setup_sidebar():
    initialize_session_state()
    
    st.sidebar.title("Modeller Settings ⚙️")
    
    inflation_type = st.sidebar.radio("Select inflation measure:", ("RPI", "CPI"), key="inflation_type", on_change=lambda: [update_fpr_targets(), update_global_pay_rise_for_inflation()], horizontal=True)
    
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        fpr_start_year = st.selectbox(
            "Calculation start year",
            options=AVAILABLE_YEARS,
            index=AVAILABLE_YEARS.index(st.session_state.fpr_start_year),
            key="fpr_start_year",
            on_change=update_end_year_options
        )
    with col2:
        fpr_end_year = st.selectbox(
            "Calculation end year",
            options=st.session_state.end_year_options,
            index=st.session_state.end_year_options.index(st.session_state.fpr_end_year),
            key="fpr_end_year",
            on_change=update_fpr_targets
        )
    with col3:
        num_years = st.number_input("Number of Years", min_value=0, max_value=10, value=st.session_state.num_years, key="num_years")
    
    # Display FPR targets
    fpr_text = "FPR Targets: "
    fpr_values = ", ".join([f"N{i+1}: {value:.1f}%" for i, value in enumerate(st.session_state.fpr_targets.values())])
    st.sidebar.write(f":blue[{fpr_text}**{fpr_values}**]")
    
    # Setup doctor counts
    st.sidebar.subheader("Number of Doctors in Each Nodal Point")
    cols = st.sidebar.columns(5)
    doctor_counts = {}
    default_counts = [8000, 6000, 20000, 25000, 6000]
    for i, (name, _, _) in enumerate(NODAL_POINTS):
        with cols[i]:
            doctor_counts[name] = st.number_input(f"{name}", min_value=0, value=default_counts[i], step=100, key=f"doctors_{name}")
    
    # Store doctor_counts in session state
    st.session_state.doctor_counts = doctor_counts
    
    # Add additional hours and out-of-hours assumptions
    st.sidebar.subheader("Working Hours Assumptions")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        additional_hours = st.number_input("Additional Hours", min_value=0, max_value=24, value=8, step=1, key="additional_hours")
    with col2:
        out_of_hours = st.number_input("Out of Hours", min_value=0, max_value=24, value=8, step=1, key="out_of_hours")
    
    # Add global controls
    st.sidebar.subheader("Global Settings for Future Years")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        global_inflation = st.number_input("Global Inflation Rate (%)", min_value=0.0, max_value=30.0, value=st.session_state.global_inflation, step=0.1, key="global_inflation", on_change=update_global_settings)
    with col2:
        global_pay_rise = st.number_input("Global Pay Rise (%)", min_value=0.0, max_value=30.0, value=st.session_state.global_pay_rise, step=0.1, key="global_pay_rise", on_change=update_global_settings)
    
    # Check for individual changes and display warning if necessary
    if check_individual_changes():
        st.sidebar.warning("Individual year changes detected. Global settings are disabled.")
    
    # Add subheader for individual year settings
    st.sidebar.subheader("Settings for Individual Years")
    
    # Setup year inputs
    year_inputs = setup_year_inputs_sidebar(st.session_state.num_years, inflation_type)
    
    # Store year_inputs in session_state for access in other functions
    st.session_state.year_inputs = year_inputs
    
    # Update FPR targets with the new year inputs
    update_fpr_targets(year_inputs)
    
    return inflation_type, fpr_start_year, fpr_end_year, num_years, st.session_state.fpr_targets, st.session_state.doctor_counts, year_inputs, additional_hours, out_of_hours

def update_global_settings():
    for year in range(1, st.session_state.num_years + 1):
        st.session_state[f"inflation_{year}"] = st.session_state.global_inflation
        for name, _, _ in NODAL_POINTS:
            st.session_state[f"mypd_nodal_percentage_{name}_{year}"] = st.session_state.global_pay_rise

def check_individual_changes():
    for year in range(1, st.session_state.num_years + 1):
        if f"inflation_{year}" in st.session_state and st.session_state[f"inflation_{year}"] != st.session_state.global_inflation:
            return True
        for name, _, _ in NODAL_POINTS:
            if f"mypd_nodal_percentage_{name}_{year}" in st.session_state and st.session_state[f"mypd_nodal_percentage_{name}_{year}"] != st.session_state.global_pay_rise:
                return True
    return False

def setup_year_inputs_sidebar(num_years, inflation_type):
    year_inputs = []

    # Initialize session state for all years
    for year in range(num_years + 1):
        if f"nodal_percentages_{year}" not in st.session_state:
            st.session_state[f"nodal_percentages_{year}"] = {name: 0.0 if year == 0 else st.session_state.global_pay_rise for name, _, _ in NODAL_POINTS}
        if f"pound_increases_{year}" not in st.session_state:
            st.session_state[f"pound_increases_{year}"] = {name: 0 for name, _, _ in NODAL_POINTS}
        if f"inflation_{year}" not in st.session_state:
            st.session_state[f"inflation_{year}"] = 0.033 if year == 0 else st.session_state.global_inflation

    for year in range(num_years + 1):
        if year == 0:
            with st.sidebar.expander("Additional Offer for 2025/2026 (not part of MYPD)"):
                st.info("This section is for any additional offer for 2025/2026. It is not part of the Multi-Year Pay Deal and is shown separately to avoid confusion.")
                
                # Initialize with default inflation values
                if 'rpi_2025_26' not in st.session_state:
                    st.session_state.rpi_2025_26 = 4.5  # Default 4.5% as requested
                if 'cpi_2025_26' not in st.session_state:
                    st.session_state.cpi_2025_26 = 3.5  # Default 3.5% as requested
                
                # Create year_input with correct inflation values
                year_input = {
                    "nodal_percentages": {},
                    "pound_increases": {},
                    "rpi": st.session_state.rpi_2025_26 / 100,
                    "cpi": st.session_state.cpi_2025_26 / 100,
                    "inflation": st.session_state.rpi_2025_26 / 100 if inflation_type == "RPI" else st.session_state.cpi_2025_26 / 100
                }
                
                # Add UI control for inflation rate based on selected type
                st.subheader("2025/2026 Projected Inflation")
                
                if inflation_type == "RPI":
                    # Show only RPI slider when RPI is selected
                    rpi = st.slider("RPI Inflation Rate (%)",
                                  min_value=0.0,
                                  max_value=10.0,
                                  value=st.session_state.rpi_2025_26,
                                  step=0.1,
                                  key="rpi_2025_26",
                                  help="Set the projected RPI inflation rate for 2025/26")
                    # Update both RPI and inflation values
                    year_input["rpi"] = rpi / 100
                    year_input["inflation"] = rpi / 100
                else:
                    # Show only CPI slider when CPI is selected
                    cpi = st.slider("CPI Inflation Rate (%)",
                                  min_value=0.0,
                                  max_value=10.0,
                                  value=st.session_state.cpi_2025_26,
                                  step=0.1,
                                  key="cpi_2025_26",
                                  help="Set the projected CPI inflation rate for 2025/26")
                    # Update both CPI and inflation values
                    year_input["cpi"] = cpi / 100
                    year_input["inflation"] = cpi / 100
                
                st.write("Consolidated pay offer:")
                cols = st.columns(5)
                for i, (name, _, _) in enumerate(NODAL_POINTS):
                    with cols[i]:
                        year_input["pound_increases"][name] = st.number_input(
                            f"{name}",
                            min_value=0,
                            max_value=10000,
                            value=st.session_state[f"pound_increases_{year}"][name],
                            step=100,
                            key=f"additional_offer_pound_increase_{name}",
                            help=f"This is an additional pound amount on top of the already offered {NODAL_SPECIFIC_PAY_AWARDS['2025/2026'][name] * 100:.1f}% for {name}"
                        )
                
                # Removed redundant inflation display - now the slider makes it clear
                
                st.write("Percentage pay rise:")
                cols = st.columns(5)
                for i, (name, _, _) in enumerate(NODAL_POINTS):
                    with cols[i]:
                        year_input["nodal_percentages"][name] = st.number_input(
                            f"{name} (%)",
                            min_value=0.0,
                            max_value=20.0,
                            value=NODAL_SPECIFIC_PAY_AWARDS['2025/2026'][name] * 100,
                            step=0.1,
                            format="%.1f",
                            key=f"additional_offer_nodal_percentage_{name}",
                            help=f"This is the already offered {NODAL_SPECIFIC_PAY_AWARDS['2025/2026'][name] * 100:.1f}% for {name}. Any change will be additional to this."
                        ) / 100
        else:
            with st.sidebar.expander(f"Year {year} ({2025+year}/{2026+year})"):
                year_input = {
                    "nodal_percentages": {},
                    "pound_increases": {},
                    "inflation": st.slider(
                        f"Projected Inflation for Year {year} ({2025+year}/{2026+year}) (%)",
                        min_value=0.0,
                        max_value=10.0,
                        value=st.session_state[f"inflation_{year}"],
                        step=0.1,
                        key=f"inflation_{year}",
                        on_change=check_individual_changes
                    ) / 100
                }
                
                st.write("Consolidated pay offer:")
                cols = st.columns(5)
                for i, (name, _, _) in enumerate(NODAL_POINTS):
                    with cols[i]:
                        year_input["pound_increases"][name] = st.number_input(
                            f"{name}",
                            min_value=0,
                            max_value=10000,
                            value=st.session_state[f"pound_increases_{year}"][name],
                            step=100,
                            key=f"mypd_pound_increase_{name}_{year}"
                        )
                
                st.write("Percentage pay rise above inflation:")
                cols = st.columns(5)
                for i, (name, _, _) in enumerate(NODAL_POINTS):
                    with cols[i]:
                        year_input["nodal_percentages"][name] = st.number_input(
                            f"{name} (%)",
                            min_value=0.0,
                            max_value=20.0,
                            value=st.session_state[f"nodal_percentages_{year}"][name],
                            step=0.1,
                            format="%.1f",
                            key=f"mypd_nodal_percentage_{name}_{year}",
                            on_change=check_individual_changes
                        ) / 100
        
        year_inputs.append(year_input)

    return year_inputs

def calculate_results(fpr_percentages, doctor_counts, year_inputs, inflation_type, additional_hours, out_of_hours):
    results = []
    total_nominal_cost = 0
    total_real_cost = 0
    cumulative_costs = [0] * (len(year_inputs) + 1)

    for name, base_pay, post_ddrb_pay in NODAL_POINTS:
        result = calculate_nodal_point_results(name, base_pay, post_ddrb_pay, fpr_percentages[name], doctor_counts[name], year_inputs, inflation_type, additional_hours, out_of_hours)
        results.append(result)
        total_nominal_cost += result["Total Nominal Cost"]
        total_real_cost += result["Total Real Cost"]

        for j, cost in enumerate(result["Yearly Total Costs"]):
            cumulative_costs[j] += cost

    return results, total_nominal_cost, total_real_cost, cumulative_costs

def calculate_nodal_point_results(name, base_pay, post_ddrb_pay, fpr_percentage, doctor_count, year_inputs, inflation_type, additional_hours, out_of_hours):
    # Helper functions for comprehensive cost calculations
    def calculate_total_pay(basic_pay):
        additional_pay = (basic_pay / 40) * additional_hours
        ooh_pay = (basic_pay / 40) * out_of_hours * 0.37
        return basic_pay, additional_pay, ooh_pay, basic_pay + additional_pay + ooh_pay

    def calculate_tax_and_ni(total_pay, basic_pay):
        pension_contribution = calculate_pension_contribution(basic_pay)
        taxable_pay = total_pay - pension_contribution
        income_tax = calculate_income_tax(taxable_pay)
        ni = calculate_national_insurance(taxable_pay)
        employer_ni = calculate_employer_ni(total_pay)
        return income_tax, ni, pension_contribution, employer_ni

    # Initialize tracking arrays
    pay_progression_nominal = [base_pay]  # Starting with 2024/25 pay
    pay_progression_real = [base_pay]
    real_terms_pay_cuts = [-fpr_percentage / 100]
    fpr_progress = [0]
    net_change_in_pay = [0]
    yearly_basic_costs = []
    yearly_total_costs = []
    yearly_tax_recouped = []
    yearly_net_costs = []
    yearly_employer_ni_costs = []
    yearly_pension_costs = []

    for year, year_input in enumerate(year_inputs):
        if year == 0:
            # Year 0 (2025/2026) calculations
            consolidated_increase = year_input["pound_increases"][name]
            
            # The standard 2025/26 percentage increase is already calculated in post_ddrb_pay
            standard_2025_26_increase = (post_ddrb_pay / base_pay) - 1
            percentage_increase = year_input["nodal_percentages"][name] - standard_2025_26_increase
            if percentage_increase < 0:
                percentage_increase = 0
                
            total_pay_rise = standard_2025_26_increase + percentage_increase + (consolidated_increase / base_pay)
            new_nominal_pay = base_pay * (1 + total_pay_rise)
            
            # Calculate comprehensive costs for Year 0
            current_basic, current_additional, current_ooh, current_total_pay = calculate_total_pay(new_nominal_pay)
            current_income_tax, current_ni, current_pension, current_employer_ni = calculate_tax_and_ni(current_total_pay, new_nominal_pay)
            
            # Compare with post-DDRB baseline (the already offered deal)
            post_ddrb_basic, post_ddrb_additional, post_ddrb_ooh, post_ddrb_total_pay = calculate_total_pay(post_ddrb_pay)
            post_ddrb_income_tax, post_ddrb_ni, post_ddrb_pension, post_ddrb_employer_ni = calculate_tax_and_ni(post_ddrb_total_pay, post_ddrb_pay)
            
            basic_pay_cost = (current_basic - post_ddrb_basic) * doctor_count
            pension_cost = (current_pension - post_ddrb_pension) * doctor_count
            employer_ni_cost = (current_employer_ni - post_ddrb_employer_ni) * doctor_count
            total_cost = (current_total_pay - post_ddrb_total_pay) * doctor_count + pension_cost + employer_ni_cost
            tax_recouped = ((current_income_tax + current_ni) - (post_ddrb_income_tax + post_ddrb_ni)) * doctor_count
            
        else:
            # Subsequent years (2026/2027 onwards)
            consolidated_increase = year_input["pound_increases"][name]
            percentage_increase = year_input["nodal_percentages"][name] + year_input["inflation"]
            total_pay_rise = percentage_increase + (consolidated_increase / pay_progression_nominal[-1])
            new_nominal_pay = pay_progression_nominal[-1] * (1 + percentage_increase) + consolidated_increase
            
            # Calculate comprehensive costs for subsequent years
            current_basic, current_additional, current_ooh, current_total_pay = calculate_total_pay(new_nominal_pay)
            current_income_tax, current_ni, current_pension, current_employer_ni = calculate_tax_and_ni(current_total_pay, new_nominal_pay)
            
            # Compare with previous year
            prev_basic, prev_additional, prev_ooh, prev_total_pay = calculate_total_pay(pay_progression_nominal[-1])
            prev_income_tax, prev_ni, prev_pension, prev_employer_ni = calculate_tax_and_ni(prev_total_pay, pay_progression_nominal[-1])
            
            basic_pay_cost = (current_basic - prev_basic) * doctor_count
            pension_cost = (current_pension - prev_pension) * doctor_count
            employer_ni_cost = (current_employer_ni - prev_employer_ni) * doctor_count
            total_cost = (current_total_pay - prev_total_pay) * doctor_count + pension_cost + employer_ni_cost
            tax_recouped = ((current_income_tax + current_ni) - (prev_income_tax + prev_ni)) * doctor_count

        net_cost = total_cost - tax_recouped
        
        # Store yearly costs
        yearly_basic_costs.append(basic_pay_cost)
        yearly_total_costs.append(total_cost)
        yearly_tax_recouped.append(tax_recouped)
        yearly_net_costs.append(net_cost)
        yearly_employer_ni_costs.append(employer_ni_cost)
        yearly_pension_costs.append(pension_cost)

        # Calculate pay progression and FPR metrics
        inflation_rate = year_input["inflation"]
        new_real_pay = new_nominal_pay / (1 + inflation_rate)
        
        real_terms_change = calculate_real_terms_change(total_pay_rise, inflation_rate)
        current_pay_cut = calculate_new_pay_erosion(real_terms_pay_cuts[-1], real_terms_change)
        
        pay_progression_nominal.append(new_nominal_pay)
        pay_progression_real.append(new_real_pay)
        real_terms_pay_cuts.append(current_pay_cut)
        
        # Calculate FPR progress without capping at 100%
        current_progress = (fpr_percentage / 100 + current_pay_cut) / (fpr_percentage / 100) * 100
        fpr_progress.append(current_progress)
        
        net_change_in_pay.append(total_pay_rise * 100)

    return {
        "Nodal Point": name,
        "2024/25 Pay": base_pay,
        "Final Pay": pay_progression_nominal[-1],
        "FPR Target": base_pay * (1 + fpr_percentage / 100),
        "FPR Required (%)": fpr_percentage,
        "Nominal Total Increase": pay_progression_nominal[-1] - base_pay,
        "Real Total Increase": pay_progression_real[-1] - base_pay,
        "Nominal Percent Increase": (pay_progression_nominal[-1] / base_pay - 1) * 100,
        "Real Percent Increase": (pay_progression_real[-1] / base_pay - 1) * 100,
        "Real Terms Pay Cuts": real_terms_pay_cuts[1:],
        "FPR Progress": fpr_progress[1:],
        "Net Change in Pay": net_change_in_pay[1:],
        "Doctor Count": doctor_count,
        "Total Nominal Cost": sum(yearly_total_costs),
        "Total Real Cost": sum(yearly_total_costs) / (1 + year_inputs[-1]["inflation"]),
        "Pay Progression Nominal": pay_progression_nominal[1:],
        "Pay Progression Real": pay_progression_real[1:],
        "Yearly Basic Costs": yearly_basic_costs,
        "Yearly Total Costs": yearly_total_costs,
        "Yearly Tax Recouped": yearly_tax_recouped,
        "Yearly Net Costs": yearly_net_costs,
        "Yearly Employer NI Costs": yearly_employer_ni_costs,
        "Yearly Pension Costs": yearly_pension_costs,
    }

def display_cost_breakdown(results, year_inputs, additional_hours, out_of_hours):
    st.subheader("Cost Breakdown by Year")
    
    num_years = len(year_inputs)
    # Skip Year 0, start from Year 1
    tabs = st.tabs([f"Year {year}: {2025 + year}/{2026 + year}" for year in range(1, num_years)])
    
    cumulative_cost = 0
    cumulative_net_cost = 0
    cumulative_tax_recouped = 0
    
    for tab_index, tab in enumerate(tabs):
        year = tab_index + 1  # Start from Year 1 instead of Year 0
        with tab:
            cost_data = []
            year_total = 0
            year_net_total = 0
            year_tax_recouped = 0
            
            for result in results:
                if year < len(result["Yearly Total Costs"]):
                    total_cost = result["Yearly Total Costs"][year]
                    employer_ni_cost = result["Yearly Employer NI Costs"][year]
                    basic_pay_cost = result["Yearly Basic Costs"][year]
                    pension_cost = result["Yearly Pension Costs"][year]
                    additional_hours_cost = (basic_pay_cost / 40) * additional_hours
                    ooh_cost = (basic_pay_cost / 40) * out_of_hours * 0.37
                    tax_recouped = result["Yearly Tax Recouped"][year]
                    net_cost = result["Yearly Net Costs"][year]
                    
                    year_total += total_cost
                    year_net_total += net_cost
                    year_tax_recouped += tax_recouped
                    
                    cost_data.append({
                        "Nodal Point": result["Nodal Point"],
                        "Basic Pay Costs": basic_pay_cost,
                        "Pension Costs": pension_cost,
                        "Additional Hours Costs": additional_hours_cost,
                        "OOH Costs": ooh_cost,
                        "Employer NI Costs": employer_ni_cost,
                        "Total Costs": total_cost,
                        "Tax Recouped": tax_recouped,
                        "Net Cost": net_cost
                    })
            
            df = pd.DataFrame(cost_data)
            df = df.set_index("Nodal Point")
            
            for col in df.columns:
                df[col] = df[col].apply(lambda x: f"£{x:,.2f}")
            
            st.dataframe(df.style.set_properties(**{'text-align': 'right'}))
            
            cumulative_cost += year_total
            cumulative_net_cost += year_net_total
            cumulative_tax_recouped += year_tax_recouped
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label=f"Total Cost for Year {year}", value=f"£{year_total:,.2f}")
            with col2:
                st.metric(label=f"Net Cost for Year {year}", value=f"£{year_net_total:,.2f}",
                          delta=f"Tax Recouped: £{year_tax_recouped:,.2f}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total nominal cost of the deal", value=f"£{cumulative_cost:,.2f}")
    with col2:
        st.metric(label="Total net cost of the deal", value=f"£{cumulative_net_cost:,.2f}",
                  delta=f"Total Tax Recouped: £{cumulative_tax_recouped:,.2f}")
    st.divider()

def display_results(results, total_nominal_cost, total_real_cost, year_inputs, additional_hours, out_of_hours):
    # Display the detailed cost breakdown
    st.divider()
    display_cost_breakdown(results, year_inputs, additional_hours, out_of_hours)
    
    st.write("All Calculation Summary Table")
    df_results = pd.DataFrame(results)
    
    # Function to round and format numbers for display
    def round_and_format(x):
        if isinstance(x, (int, float)):
            return f"{x:.2f}"
        elif isinstance(x, list):
            return [f"{val:.2f}" for val in x]
        else:
            return x

    # Apply rounding to all columns except 'Nodal Point'
    for col in df_results.columns:
        if col != 'Nodal Point':
            df_results[col] = df_results[col].apply(round_and_format)
    
    # Format currency columns
    currency_columns = ['2024/25 Pay', 'Final Pay', 'FPR Target', 'Nominal Total Increase', 'Real Total Increase']
    for col in currency_columns:
        df_results[col] = df_results[col].apply(lambda x: f"£{float(x):,.2f}")
    
    # Format percentage columns
    percentage_columns = ['FPR Required (%)', 'Nominal Percent Increase', 'Real Percent Increase']
    for col in percentage_columns:
        df_results[col] = df_results[col].apply(lambda x: f"{float(x):.2f}%")
    
    # Special handling for 'Real Terms Pay Cuts' and 'FPR Progress' columns
    list_columns = ['Real Terms Pay Cuts', 'FPR Progress']
    for col in list_columns:
        df_results[col] = df_results[col].apply(lambda x: [f"{float(val):.2f}%" for val in x])
    
    st.dataframe(df_results)
    
def display_visualizations(results, cumulative_costs, year_inputs, inflation_type, num_years):
    st.subheader("Pay Progression & FPR Progress Visualisation")

    # Create tabs for individual nodal points only
    tab_names = [result["Nodal Point"] for result in results]
    tabs = st.tabs(tab_names)

    # Individual nodal point tabs
    for i, result in enumerate(results):
        with tabs[i]:
            fig = create_pay_progression_chart(result, num_years)
            st.plotly_chart(fig, use_container_width=True)

            st.write(f"FPR progress and Pay Erosion for {result['Nodal Point']}:")
            progress_df = create_fpr_progress_table(result, num_years, year_inputs)
            st.table(progress_df)
            

def create_pay_progression_chart(result, num_years):
    # Update year labels to show Year 0 as 2025/2026
    years = [f"Year 0 ({2025}/{2026})"] + [f"Year {i+1} ({2026+i}/{2027+i})" for i in range(num_years)]
    nominal_pay = result["Pay Progression Nominal"]
    baseline_pay = result["2024/25 Pay"]  # Use the 2024/25 pay as baseline
    pay_increase = [max(0, pay - baseline_pay) for pay in nominal_pay]
    percent_increase = [(increase / baseline_pay) * 100 for increase in pay_increase]
    pay_erosion = [-(x) * 100 for x in result["Real Terms Pay Cuts"]]
    fpr_progress = result["FPR Progress"]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add baseline pay bars
    fig.add_trace(
        go.Bar(x=years, y=[baseline_pay] * len(years), name="Baseline Pay", marker_color='rgb(0, 123, 255)'),
        secondary_y=False,
    )

    # Add pay increase bars
    fig.add_trace(
        go.Bar(x=years, y=pay_increase, name="Pay Increase", marker_color='rgb(255, 165, 0)',
               hovertemplate='Year: %{x}<br>Total Pay: £%{customdata[0]:,.2f}<br>Increase: £%{y:,.2f} (%{customdata[1]:.2f}%)<extra></extra>',
               customdata=list(zip(nominal_pay, percent_increase))),
        secondary_y=False,
    )

    # Add text annotations showing total pay amounts above each bar
    for i, (year, total_pay) in enumerate(zip(years, nominal_pay)):
        fig.add_annotation(
            x=year,
            y=total_pay + 2000,  # Position slightly above the bar
            text=f"£{total_pay:,.0f}",
            showarrow=False,
            font=dict(size=12, color="black", family="Arial Black"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1,
            borderpad=2
        )

    # Add FPR Progress line
    fig.add_trace(
        go.Scatter(x=years, y=fpr_progress, name="FPR Progress", line=dict(color='rgb(0, 200, 0)', width=2)),
        secondary_y=True,
    )

    # Add FPR Progress percentage labels above each node
    for i, (year, progress) in enumerate(zip(years, fpr_progress)):
        fig.add_annotation(
            x=year,
            y=progress + 5,  # Position slightly above the line point
            text=f"{progress:.1f}%",
            showarrow=False,
            font=dict(size=10, color="rgb(0, 150, 0)", family="Arial Bold"),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="rgb(0, 150, 0)",
            borderwidth=1,
            borderpad=1,
            yref="y2"  # Reference the secondary y-axis
        )

    # Add Pay Erosion line
    fig.add_trace(
        go.Scatter(x=years, y=pay_erosion, name="Pay Erosion", line=dict(color='rgb(255, 0, 0)', width=2)),
        secondary_y=True,
    )

    fig.update_layout(
        title=f"Pay Progression, FPR Progress, and Pay Erosion for {result['Nodal Point']} (Base pay: £{baseline_pay:,.2f})",
        xaxis_title="Year",
        yaxis_title="Pay (£)",
        yaxis2_title="Percentage (%)",
        legend=dict(x=0, y=1.1, orientation="h"),
        barmode='stack',
        height=600,
    )

    # Adjust y-axis range to accommodate the text annotations
    max_pay = max(nominal_pay)
    fig.update_yaxes(title_text="Pay (£)", secondary_y=False, range=[0, max_pay * 1.15])
    fig.update_yaxes(title_text="Percentage (%)", secondary_y=True)

    return fig

def create_fpr_progress_table(selected_data, num_years, year_inputs):
    # Update year labels to show Year 0 as 2025/2026
    years = [f"Year 0 ({2025}/{2026})"] + [f"Year {i+1} ({2026+i}/{2027+i})" for i in range(num_years)]
    
    pay_rises = []
    for year, year_input in enumerate(year_inputs):
        inflation = year_input["inflation"] * 100
        percentage_increase = selected_data["Net Change in Pay"][year]
        consolidated_increase = year_input["pound_increases"][selected_data["Nodal Point"]]
        
        difference = percentage_increase - inflation
        
        if difference >= 0:
            pay_rise = f"Inflation + {difference:.1f}%"
        else:
            pay_rise = f"Inflation - {abs(difference):.1f}%"
        
        if consolidated_increase > 0:
            pay_rise += f" + £{consolidated_increase:,}"
        
        pay_rises.append(pay_rise)
    
    df = pd.DataFrame({
        "Year": years,
        "Pay Rise": pay_rises,
        "FPR Progress (%)": selected_data["FPR Progress"],
        "Pay Erosion (%)": selected_data["Real Terms Pay Cuts"]
    })

    df["FPR Progress (%)"] = df["FPR Progress (%)"].apply(lambda x: f"{x:.2f}")
    df["Pay Erosion (%)"] = df["Pay Erosion (%)"].apply(lambda x: f"{-x * 100:.2f}")

    return df
    
def display_fpr_achievement(results):
    st.subheader(":blue-background[👈 Will FPR be achieved from this pay deal? 🕵️]")
    fpr_achieved = all(result["FPR Progress"][-1] >= 100 for result in results)
    
    if fpr_achieved:
        st.success("Yes, FPR will be achieved for all nodal points.")
    else:
        st.error("No, FPR will not be achieved for all nodal points. But some progress has been made...  \nNote the residual pay erosion figures in % below.")
    
    # Display detailed FPR progress for each nodal point using st.metric
    cols = st.columns(len(results))
    for i, result in enumerate(results):
        with cols[i]:
            fpr_progress = result["FPR Progress"][-1]
            pay_erosion = result["Real Terms Pay Cuts"][-1]
            
            # Format pay erosion as a percentage with reversed polarity
            pay_erosion_formatted = f"{pay_erosion * 100:.2f}%"
            
            # Format FPR progress for delta
            fpr_progress_formatted = f"FPR: {fpr_progress:.2f}%"
            
            st.metric(
                label=f"{result['Nodal Point']}",
                value=pay_erosion_formatted,
                delta=fpr_progress_formatted,
                delta_color="normal"  # This ensures the delta is green for positive values
            )
    st.divider()

def main():
    # Custom CSS to set sidebar width and improve layout
    st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        width: 600px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )  

    st.title("DoctorsVote MYPD-FPR Modeller 2025/2026")
    st.write("This app is best used on a desktop/laptop. Adjust settings in the sidebar.")
    # Add the introduction and explanations
    with st.expander("About This App", expanded=False):
        st.markdown("""
        ## Introduction

        Welcome to the DoctorsVote Multi-Year Pay Deal (MYPD) and Full Pay Restoration (FPR) Modeller. This sophisticated tool is designed to help medical professionals, union representatives, and policymakers understand and visualize the complex interplay between pay deals, inflation, and the goal of full pay restoration for doctors in the UK.

        The modeller allows you to:

        1. Input and adjust parameters for multi-year pay deals
        2. Visualize the progression of pay and its relation to inflation over time
        3. Track the progress towards Full Pay Restoration (FPR) for different nodal points
        4. Calculate and display the costs associated with proposed pay deals

        ## How It Works

        ### Sidebar Controls

        The sidebar on the left contains all the input controls for the model:

        1. **Inflation Measure**: Choose between RPI (Retail Price Index) and CPI (Consumer Price Index) as the basis for calculations.
        2. **FPR Start and End Years**: Select the range of years over which to calculate the Full Pay Restoration target.
        3. **Number of Years**: Set the duration of the pay deal you want to model.
        4. **Doctor Counts**: Input the number of doctors at each nodal point for accurate cost calculations.
        5. **Year-by-Year Inputs**: For each year of the deal, you can set:
           - Consolidated pay offers (in pounds)
           - Percentage pay rises
           - Projected inflation rates

        ### Main Display

        The main area of the app displays the results of your inputs:

        1. **FPR Achievement**: A summary of whether the proposed deal achieves Full Pay Restoration, with a breakdown by nodal point.
        2. **Pay Progression & FPR Progress Visualization**: Interactive charts showing:
           - Nominal and real pay progression
           - FPR progress over time
           - Pay erosion due to inflation
        3. **Pay Increase Curve**: A chart displaying nominal increases, real increases, and cumulative costs over the years of the deal.
        4. **Cost Breakdown**: Detailed yearly costs, including basic pay, pension contributions, and additional hours.
        5. **Full Results Table**: A comprehensive table with all calculated metrics for each nodal point.

        ## Key Concepts

        ### Full Pay Restoration (FPR)
        
        FPR represents the goal of restoring doctors' pay to what it would have been if it had kept pace with inflation since a chosen baseline year. The FPR target is calculated based on the cumulative effect of inflation between the start and end years you select.
        
        This updated version for 2025/2026 includes the actual pay awards from 2023/2024 and 2024/2025, which were nodal-specific:
        - 2023/2024: 3.71% for N1, 3.71% for N2, 5.05% for N3, 3.71% for N4, and 3.71% for N5
        - 2024/2025: 9.0% for N1, 8.6% for N2, 8.2% for N3, 7.7% for N4, and 7.5% for N5
        - 2025/2026 (current offer): 6.0% for N1, 5.8% for N2, 5.5% for N3, 5.2% for N4, and 5.1% for N5

        ### Pay Erosion

        Pay erosion occurs when pay increases fail to keep up with inflation, resulting in a decrease in real-terms pay. The modeller calculates and displays pay erosion as a percentage, showing how much the value of pay has decreased relative to inflation.

        ### Nodal Points

        The model uses five nodal points representing different stages in a doctor's career. Each nodal point has its own base pay and progression, allowing for a nuanced view of how pay deals affect doctors at different career stages.

        ### Real vs Nominal Increases

        - **Nominal Increases**: The actual percentage or pound value increase in pay.
        - **Real Increases**: The increase in pay after accounting for inflation, representing the true change in purchasing power.

        ## Using the Model

        1. Start by setting your desired parameters in the sidebar.
        2. Observe the "FPR Achievement" section to see if the proposed deal meets the FPR targets.
        3. Use the visualizations to understand how pay progresses over time and how it compares to inflation.
        4. Examine the cost breakdown to understand the financial implications of the proposed deal.
        5. Adjust your inputs and observe how changes affect the outcomes.

        This model is a powerful tool for understanding the long-term implications of pay deals and their progress towards restoring doctors' pay. By providing a clear, data-driven view of complex pay scenarios, it aims to facilitate informed discussions and decision-making in pay negotiations.
        """)

    inflation_type, fpr_start_year, fpr_end_year, num_years, fpr_percentages, doctor_counts, year_inputs, additional_hours, out_of_hours = setup_sidebar()

    results, total_nominal_cost, total_real_cost, cumulative_costs = calculate_results(
        fpr_percentages, doctor_counts, year_inputs, inflation_type, additional_hours, out_of_hours
    )

    display_fpr_achievement(results)
    display_visualizations(results, cumulative_costs, year_inputs, inflation_type, num_years)
    display_results(results, total_nominal_cost, total_real_cost, year_inputs, additional_hours, out_of_hours)

if __name__ == "__main__":
    main()