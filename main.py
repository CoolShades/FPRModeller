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
        "Nodal 1": 0.1401,
        "Nodal 2": 0.1341,
        "Nodal 3": 0.1415,
        "Nodal 4": 0.1221,
        "Nodal 5": 0.1181
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

# Default nodal percentages for MYPD years based on inflation type
DEFAULT_NODAL_PERCENTAGES = {
    "RPI": {
        1: {"Nodal 1": 9.0, "Nodal 2": 9.5, "Nodal 3": 9.0, "Nodal 4": 10.0, "Nodal 5": 11.0},
        2: {"Nodal 1": 8.1, "Nodal 2": 8.9, "Nodal 3": 9.4, "Nodal 4": 11.1, "Nodal 5": 10.9}
    },
    "CPI": {
        1: {"Nodal 1": 0.0, "Nodal 2": 0.5, "Nodal 3": 0.5, "Nodal 4": 2.0, "Nodal 5": 2.0},
        2: {"Nodal 1": 0.0, "Nodal 2": 0.0, "Nodal 3": 0.0, "Nodal 4": 1.0, "Nodal 5": 1.7}
    },
    "CPIH": {
        1: {"Nodal 1": 0.0, "Nodal 2": 0.0, "Nodal 3": 0.0, "Nodal 4": 0.7, "Nodal 5": 1.4},
        2: {"Nodal 1": 0.0, "Nodal 2": 0.0, "Nodal 3": 0.0, "Nodal 4": 0.0, "Nodal 5": 0.0}
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
        {"year": "2008/2009", "pay_award": 0.0, "rpi": 0.0, "cpi": 0.0, "cpih": 0.0},  # Baseline year
        {"year": "2009/2010", "pay_award": 0.015, "rpi": 0.053, "cpi": 0.037, "cpih": 0.027},
        {"year": "2010/2011", "pay_award": 0.010, "rpi": 0.052, "cpi": 0.045, "cpih": 0.038},
        {"year": "2011/2012", "pay_award": 0.000, "rpi": 0.035, "cpi": 0.030, "cpih": 0.028},
        {"year": "2012/2013", "pay_award": 0.000, "rpi": 0.029, "cpi": 0.024, "cpih": 0.022},
        {"year": "2013/2014", "pay_award": 0.010, "rpi": 0.025, "cpi": 0.018, "cpih": 0.017},
        {"year": "2014/2015", "pay_award": 0.000, "rpi": 0.009, "cpi": -0.001, "cpih": 0.003},
        {"year": "2015/2016", "pay_award": 0.000, "rpi": 0.013, "cpi": 0.003, "cpih": 0.007},
        {"year": "2016/2017", "pay_award": 0.010, "rpi": 0.035, "cpi": 0.027, "cpih": 0.026},
        {"year": "2017/2018", "pay_award": 0.010, "rpi": 0.034, "cpi": 0.024, "cpih": 0.022},
        {"year": "2018/2019", "pay_award": 0.020, "rpi": 0.030, "cpi": 0.021, "cpih": 0.020},
        {"year": "2019/2020", "pay_award": 0.023, "rpi": 0.015, "cpi": 0.008, "cpih": 0.009},
        {"year": "2020/2021", "pay_award": 0.030, "rpi": 0.029, "cpi": 0.015, "cpih": 0.016},
        {"year": "2021/2022", "pay_award": 0.030, "rpi": 0.111, "cpi": 0.090, "cpih": 0.078},
        {"year": "2022/2023", "pay_award": 0.030, "rpi": 0.114, "cpi": 0.087, "cpih": 0.078},
        {"year": "2023/2024", "pay_award": None, "rpi": 0.033, "cpi": 0.023, "cpih": 0.030}, # Will use nodal-specific values
        {"year": "2024/2025", "pay_award": None, "rpi": 0.045, "cpi": 0.035, "cpih": 0.041}, # Will use nodal-specific values
        {"year": "2025/2026", "pay_award": None, "rpi": 0.045, "cpi": 0.035, "cpih": 0.041}
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
    
    if inflation_type == "RPI":
        inflation_key = "rpi"
    elif inflation_type == "CPI":
        inflation_key = "cpi"
    else:  # CPIH
        inflation_key = "cpih"
    
    for data in pay_data[start_index:end_index]:
        inflation_rate = data[inflation_key]
        
        # Handle None inflation - use user-defined values for 2025/2026
        if inflation_rate is None and data["year"] == "2025/2026" and year_inputs is not None:
            # Get the first year_input (index 0) which corresponds to 2025/2026
            if inflation_key == "rpi":
                inflation_rate = year_inputs[0]["rpi"]
            elif inflation_key == "cpi":
                inflation_rate = year_inputs[0]["cpi"]
            else:  # CPIH
                inflation_rate = year_inputs[0]["cpih"]
        
        if inflation_rate == 0.0 or inflation_rate is None:  # Skip years with no inflation data
            continue
        real_terms_change = ((1 + data["pay_award"]) / (1 + inflation_rate)) - 1
        cumulative_effect *= (1 + real_terms_change)
    
    fpr_percentage = (1/cumulative_effect - 1) * 100  # Correct calculation for restoration
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
        st.session_state.fpr_end_year = "2025/2026"  # Set default to 2025/26
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
        # Keep global pay rise blank by default
        st.session_state.global_pay_rise = 0.0
    if 'num_years' not in st.session_state:
        st.session_state.num_years = 2  # Default to 2 years
    
    # Initial targets will be calculated in setup_sidebar after year_inputs are created

def update_fpr_targets(year_inputs=None):
    # If year_inputs is None or empty, create default year_inputs for 2025/26
    if not year_inputs:
        # Create default year_inputs with 2025/26 inflation values
        default_rpi = 4.5 / 100  # 4.5% RPI
        default_cpi = 3.5 / 100  # 3.5% CPI
        default_cpih = 4.0 / 100  # 4.0% CPIH
        if st.session_state.inflation_type == "RPI":
            default_inflation = default_rpi
        elif st.session_state.inflation_type == "CPI":
            default_inflation = default_cpi
        else:  # CPIH
            default_inflation = default_cpih
        year_inputs = [{
            "rpi": default_rpi,
            "cpi": default_cpi,
            "cpih": default_cpih,
            "inflation": default_inflation
        }]
    
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
    """Update individual year settings when inflation type changes"""
    # Don't automatically set global pay rise - keep it blank for user input
    
    # Update individual year settings if they exist
    if 'num_years' in st.session_state:
        for year in range(1, st.session_state.num_years + 1):
            # Update nodal percentages for each year using inflation-type-specific defaults
            if f"nodal_percentages_{year}" in st.session_state:
                if year <= 2 and year in DEFAULT_NODAL_PERCENTAGES.get(st.session_state.inflation_type, {}):
                    # Use inflation-type-specific defaults for Years 1-2
                    defaults = DEFAULT_NODAL_PERCENTAGES[st.session_state.inflation_type][year]
                    for name, _, _ in NODAL_POINTS:
                        st.session_state[f"nodal_percentages_{year}"][name] = defaults.get(name, 0.0)
                else:
                    # Keep existing values or use 0.0 for Years 3+
                    for name, _, _ in NODAL_POINTS:
                        if st.session_state.global_pay_rise > 0:
                            st.session_state[f"nodal_percentages_{year}"][name] = st.session_state.global_pay_rise
                        else:
                            st.session_state[f"nodal_percentages_{year}"][name] = 0.0
            
            # Update individual year controls
            for name, _, _ in NODAL_POINTS:
                if f"mypd_nodal_percentage_{name}_{year}" in st.session_state:
                    if year <= 2 and year in DEFAULT_NODAL_PERCENTAGES.get(st.session_state.inflation_type, {}):
                        # Use inflation-type-specific defaults for Years 1-2
                        default_value = DEFAULT_NODAL_PERCENTAGES[st.session_state.inflation_type][year].get(name, 0.0)
                        st.session_state[f"mypd_nodal_percentage_{name}_{year}"] = default_value
                    else:
                        # Keep existing values or use 0.0 for Years 3+
                        if st.session_state.global_pay_rise > 0:
                            st.session_state[f"mypd_nodal_percentage_{name}_{year}"] = st.session_state.global_pay_rise
                        else:
                            st.session_state[f"mypd_nodal_percentage_{name}_{year}"] = 0.0

def setup_sidebar():
    initialize_session_state()
    
    st.sidebar.title("Modeller Settings ⚙️")
    
    inflation_type = st.sidebar.radio("Select inflation measure:", ("RPI", "CPI", "CPIH"), key="inflation_type", on_change=lambda: [update_fpr_targets(), update_global_pay_rise_for_inflation()], horizontal=True)
    
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
    
    # Setup doctor counts in expander
    with st.sidebar.expander("Number of Doctors in Each Nodal Point"):
        cols = st.columns(5)
        doctor_counts = {}
        default_counts = [8000, 6000, 20000, 25000, 6000]
        for i, (name, _, _) in enumerate(NODAL_POINTS):
            with cols[i]:
                doctor_counts[name] = st.number_input(f"{name}", min_value=0, value=default_counts[i], step=100, key=f"doctors_{name}")
    
    # Store doctor_counts in session state
    st.session_state.doctor_counts = doctor_counts
    
    # Add additional hours and out-of-hours assumptions in expander
    with st.sidebar.expander("Working Hours Assumptions"):
        col1, col2 = st.columns(2)
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
    
    # Display FPR targets AFTER year_inputs are created and FPR targets are calculated
    fpr_text = "FPR Targets (% rise needed): "
    if st.session_state.fpr_targets:  # Only display if targets exist
        fpr_values = ", ".join([f"N{i+1}: {value:.1f}%" for i, value in enumerate(st.session_state.fpr_targets.values())])
        st.sidebar.write(f":blue[{fpr_text}**{fpr_values}**]")
        
        # Calculate and display current pay erosion
        pay_erosion_text = "Pay Erosion (current): "
        pay_erosion_values = []
        for name, fpr_target in st.session_state.fpr_targets.items():
            # If FPR target is X%, then pay erosion is calculated as:
            # pay_erosion = (1 - 1/(1 + fpr_target/100)) * 100
            # This is because if you need X% to restore, then current value is 100/(1+X/100) of original
            fpr_decimal = fpr_target / 100
            pay_erosion_percent = (1 - 1/(1 + fpr_decimal)) * 100
            pay_erosion_values.append(f"N{list(st.session_state.fpr_targets.keys()).index(name)+1}: -{pay_erosion_percent:.1f}%")
        
        pay_erosion_display = ", ".join(pay_erosion_values)
        st.sidebar.write(f":red[{pay_erosion_text}**{pay_erosion_display}**]")
    else:
        st.sidebar.write(f":blue[{fpr_text}**Calculating...**]")
        st.sidebar.write(f":red[Pay Erosion (current): **Calculating...**]")
    
    return inflation_type, fpr_start_year, fpr_end_year, num_years, st.session_state.fpr_targets, st.session_state.doctor_counts, year_inputs, additional_hours, out_of_hours

def update_global_settings():
    for year in range(1, st.session_state.num_years + 1):
        st.session_state[f"inflation_{year}"] = st.session_state.global_inflation
        
        # If global pay rise is set (> 0), override ALL individual nodal percentages
        if st.session_state.global_pay_rise > 0:
            for name, _, _ in NODAL_POINTS:
                st.session_state[f"mypd_nodal_percentage_{name}_{year}"] = st.session_state.global_pay_rise
                # Also update the nodal_percentages session state
                if f"nodal_percentages_{year}" in st.session_state:
                    st.session_state[f"nodal_percentages_{year}"][name] = st.session_state.global_pay_rise

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
            if year == 0:
                # Year 0 (Additional offer) - keep at 0.0
                st.session_state[f"nodal_percentages_{year}"] = {name: 0.0 for name, _, _ in NODAL_POINTS}
            elif year <= 2 and year in DEFAULT_NODAL_PERCENTAGES.get(inflation_type, {}):
                # Years 1-2: Use inflation-type-specific defaults
                defaults = DEFAULT_NODAL_PERCENTAGES[inflation_type][year]
                st.session_state[f"nodal_percentages_{year}"] = {name: defaults.get(name, 0.0) for name, _, _ in NODAL_POINTS}
            else:
                # Years 3+: Use global pay rise if set, otherwise 0.0
                default_value = st.session_state.global_pay_rise if st.session_state.global_pay_rise > 0 else 0.0
                st.session_state[f"nodal_percentages_{year}"] = {name: default_value for name, _, _ in NODAL_POINTS}
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
                if 'cpih_2025_26' not in st.session_state:
                    st.session_state.cpih_2025_26 = 4.0  # Default 4.0% for CPIH
                
                # Create year_input with correct inflation values
                if inflation_type == "RPI":
                    selected_inflation = st.session_state.rpi_2025_26 / 100
                elif inflation_type == "CPI":
                    selected_inflation = st.session_state.cpi_2025_26 / 100
                else:  # CPIH
                    selected_inflation = st.session_state.cpih_2025_26 / 100
                
                year_input = {
                    "nodal_percentages": {},
                    "pound_increases": {},
                    "rpi": st.session_state.rpi_2025_26 / 100,
                    "cpi": st.session_state.cpi_2025_26 / 100,
                    "cpih": st.session_state.cpih_2025_26 / 100,
                    "inflation": selected_inflation
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
                elif inflation_type == "CPI":
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
                else:  # CPIH
                    # Show only CPIH slider when CPIH is selected
                    cpih = st.slider("CPIH Inflation Rate (%)",
                                   min_value=0.0,
                                   max_value=10.0,
                                   value=st.session_state.cpih_2025_26,
                                   step=0.1,
                                   key="cpih_2025_26",
                                   help="Set the projected CPIH inflation rate for 2025/26")
                    # Update both CPIH and inflation values
                    year_input["cpih"] = cpih / 100
                    year_input["inflation"] = cpih / 100
                
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
                            max_value=50.0,
                            value=NODAL_SPECIFIC_PAY_AWARDS['2025/2026'][name] * 100,
                            step=0.1,
                            format="%.1f",
                            key=f"additional_offer_nodal_percentage_{name}",
                            help=f"Total percentage pay rise for {name}. Current offer is {NODAL_SPECIFIC_PAY_AWARDS['2025/2026'][name] * 100:.1f}%. Set to {st.session_state.fpr_targets.get(name, 0):.1f}% to achieve FPR."
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
                        # If global pay rise is set (> 0), use it for all nodal points
                        if st.session_state.global_pay_rise > 0:
                            default_value = st.session_state.global_pay_rise
                        elif year <= 2 and year in DEFAULT_NODAL_PERCENTAGES.get(inflation_type, {}):
                            # Use inflation-type-specific defaults for Years 1-2 when global is not set
                            default_value = DEFAULT_NODAL_PERCENTAGES[inflation_type][year].get(name, 0.0)
                        else:
                            # For years 3+ when global not set, use stored value
                            default_value = st.session_state[f"nodal_percentages_{year}"][name]
                        
                        year_input["nodal_percentages"][name] = st.number_input(
                            f"{name} (%)",
                            min_value=0.0,
                            max_value=30.0,
                            value=default_value,
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
            
            # Use the input percentage as the total pay rise for 2025/26
            total_percentage_from_input = year_input["nodal_percentages"][name]
            consolidated_percentage = consolidated_increase / base_pay
            
            total_pay_rise = total_percentage_from_input + consolidated_percentage
            new_nominal_pay = base_pay * (1 + total_pay_rise)
            
            # Calculate comprehensive costs for Year 0
            current_basic, current_additional, current_ooh, current_total_pay = calculate_total_pay(new_nominal_pay)
            current_income_tax, current_ni, current_pension, current_employer_ni = calculate_tax_and_ni(current_total_pay, new_nominal_pay)
            
            # Compare with 2024/25 baseline (since we're now calculating total pay rise from 2024/25)
            baseline_basic, baseline_additional, baseline_ooh, baseline_total_pay = calculate_total_pay(base_pay)
            baseline_income_tax, baseline_ni, baseline_pension, baseline_employer_ni = calculate_tax_and_ni(baseline_total_pay, base_pay)
            
            basic_pay_cost = (current_basic - baseline_basic) * doctor_count
            pension_cost = (current_pension - baseline_pension) * doctor_count
            employer_ni_cost = (current_employer_ni - baseline_employer_ni) * doctor_count
            total_cost = (current_total_pay - baseline_total_pay) * doctor_count + pension_cost + employer_ni_cost
            tax_recouped = ((current_income_tax + current_ni) - (baseline_income_tax + baseline_ni)) * doctor_count
            
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
        
        # Calculate pay erosion directly based on FPR achievement
        fpr_target_decimal = fpr_percentage / 100
        total_nominal_rise_given = (new_nominal_pay / base_pay) - 1
        
        # Calculate what nominal rise is needed to achieve FPR with current inflation
        adjusted_fpr_target = (1 + fpr_target_decimal) * (1 + inflation_rate) - 1
        
        # Calculate current pay erosion based on how much we've achieved vs what's needed
        if adjusted_fpr_target > 0:
            # Calculate the real-terms effect of what we gave vs what was needed
            real_terms_achieved = (1 + total_nominal_rise_given) / (1 + inflation_rate) - 1
            real_terms_needed = fpr_target_decimal
            
            # Pay erosion/gain = difference between what was achieved and what was needed
            current_pay_cut = real_terms_needed - real_terms_achieved
        else:
            current_pay_cut = 0
        
        pay_progression_nominal.append(new_nominal_pay)
        pay_progression_real.append(new_real_pay)
        real_terms_pay_cuts.append(current_pay_cut)
        
        # Calculate FPR progress correctly accounting for current year inflation
        # FPR progress should measure real-terms restoration, not just nominal pay rise
        fpr_target_decimal = fpr_percentage / 100  # Target nominal pay rise needed for FPR (calculated without current year inflation)
        total_nominal_rise_given = (new_nominal_pay / base_pay) - 1  # Total nominal pay rise from 2024/25 baseline
        
        # Adjust FPR target for current year inflation
        # If inflation is higher, we need a higher nominal rise to achieve the same real restoration
        adjusted_fpr_target = (1 + fpr_target_decimal) * (1 + inflation_rate) - 1
        
        # Calculate progress as percentage of adjusted target achieved
        if adjusted_fpr_target > 0:
            current_progress = (total_nominal_rise_given / adjusted_fpr_target) * 100
        else:
            current_progress = 100  # If no FPR target needed, we're at 100%
        
        # Don't cap progress - it can exceed 100% if more than FPR is achieved
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
    
    # Add toggle for including Year 0 in cost calculations
    include_year_0 = st.checkbox("Include Year 0 (2025/2026) in cost calculations", value=False, key="include_year_0")
    
    num_years = len(year_inputs)
    
    # Determine which years to include based on toggle
    if include_year_0:
        year_range = range(0, num_years)
        tab_labels = [f"Year 0: 2025/2026"] + [f"Year {year}: {2025 + year}/{2026 + year}" for year in range(1, num_years)]
    else:
        year_range = range(1, num_years)
        tab_labels = [f"Year {year}: {2025 + year}/{2026 + year}" for year in year_range]
    
    if len(tab_labels) == 0:
        st.write("No years configured for cost breakdown.")
        return
    
    tabs = st.tabs(tab_labels)
    
    # Initialize cumulative totals
    cumulative_cost = 0
    cumulative_net_cost = 0
    cumulative_tax_recouped = 0
    
    # Display tabs based on selected years
    for tab_index, tab in enumerate(tabs):
        if include_year_0:
            year = tab_index  # Start from Year 0 if included
        else:
            year = tab_index + 1  # Start from Year 1 if Year 0 excluded
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
            
            # Add displayed years to cumulative totals
            cumulative_cost += year_total
            cumulative_net_cost += year_net_total
            cumulative_tax_recouped += year_tax_recouped
            
            col1, col2 = st.columns(2)
            with col1:
                year_label = f"Year 0" if year == 0 else f"Year {year}"
                st.metric(label=f"Total Cost for {year_label}", value=f"£{year_total:,.2f}")
            with col2:
                st.metric(label=f"Net Cost for {year_label}", value=f"£{year_net_total:,.2f}",
                          delta=f"Tax Recouped: £{year_tax_recouped:,.2f}")

    col1, col2 = st.columns(2)
    with col1:
        cost_label = "Total nominal cost of the deal"
        if include_year_0:
            cost_label += " (including Year 0)"
        else:
            cost_label += " (excluding Year 0)"
        st.metric(label=cost_label, value=f"£{cumulative_cost:,.2f}")
    with col2:
        net_cost_label = "Total net cost of the deal"
        if include_year_0:
            net_cost_label += " (including Year 0)"
        else:
            net_cost_label += " (excluding Year 0)"
        st.metric(label=net_cost_label, value=f"£{cumulative_net_cost:,.2f}",
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
    # Add header for the metrics section
    st.subheader("📊 Current Pay Erosion vs FPR Progress")
    st.write("**Current Pay Erosion** (large numbers): How much purchasing power has been lost since baseline")
    st.write("**FPR Progress** (green arrows): How much of Full Pay Restoration this deal achieves")
    
    # Display detailed FPR progress for each nodal point using st.metric
    cols = st.columns(len(results))
    for i, result in enumerate(results):
        with cols[i]:
            fpr_progress = result["FPR Progress"][-1]
            
            # Get the current pay erosion from FPR targets (same calculation as sidebar)
            nodal_name = result["Nodal Point"]
            if nodal_name in st.session_state.fpr_targets:
                fpr_target = st.session_state.fpr_targets[nodal_name]
                fpr_decimal = fpr_target / 100
                current_pay_erosion_percent = (1 - 1/(1 + fpr_decimal)) * 100
                current_pay_erosion_formatted = f"-{current_pay_erosion_percent:.1f}%"
            else:
                current_pay_erosion_formatted = "Calculating..."
            
            # Format FPR progress for delta
            fpr_progress_formatted = f"FPR: {fpr_progress:.2f}%"
            
            st.metric(
                label=f"{result['Nodal Point']}",
                value=current_pay_erosion_formatted,
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

    st.title("MYPD-FPR Modeller 2025/2026")
    st.write("This app is best used on a desktop/laptop. Adjust settings in the sidebar.")
    st.divider()

    inflation_type, fpr_start_year, fpr_end_year, num_years, fpr_percentages, doctor_counts, year_inputs, additional_hours, out_of_hours = setup_sidebar()

    results, total_nominal_cost, total_real_cost, cumulative_costs = calculate_results(
        fpr_percentages, doctor_counts, year_inputs, inflation_type, additional_hours, out_of_hours
    )

    display_fpr_achievement(results)
    display_visualizations(results, cumulative_costs, year_inputs, inflation_type, num_years)
    display_results(results, total_nominal_cost, total_real_cost, year_inputs, additional_hours, out_of_hours)

if __name__ == "__main__":
    main()