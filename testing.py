import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Constants
NODAL_POINTS = [
    ("Nodal 1", 29384, 32398),
    ("Nodal 2", 34012, 37303),
    ("Nodal 3", 40257, 43923),
    ("Nodal 4", 51017, 55329),
    ("Nodal 5", 58398, 63152)
]
AVAILABLE_YEARS = [
    "2008/2009", "2009/2010", "2010/2011", "2011/2012", "2012/2013",
    "2013/2014", "2014/2015", "2015/2016", "2016/2017", "2017/2018",
    "2018/2019", "2019/2020", "2020/2021", "2021/2022", "2022/2023",
    "2023/2024"
]

# Calculation Functions
def calculate_real_terms_change(pay_rise, inflation):
    return ((1 + pay_rise) / (1 + inflation)) - 1

def calculate_new_pay_erosion(current_erosion, real_terms_change):
    return ((1 + current_erosion) * (1 + real_terms_change)) - 1

def calculate_fpr_percentage(start_year, end_year, inflation_type):
    # Data from the provided tables
    pay_data = [
        {"year": "2008/2009", "pay_award": 0.0, "rpi": 0.0, "cpi": 0.0},  # Baseline year
        {"year": "2009/2010", "pay_award": 0.015, "rpi": 0.053, "cpi": 0.037},
        {"year": "2010/2011", "pay_award": 0.010, "rpi": 0.052, "cpi": 0.045},
        {"year": "2011/2012", "pay_award": 0.000, "rpi": 0.035, "cpi": 0.030},
        {"year": "2012/2013", "pay_award": 0.000, "rpi": 0.029, "cpi": 0.024},
        {"year": "2013/2014", "pay_award": 0.010, "rpi": 0.025, "cpi": 0.018},
        {"year": "2014/2015", "pay_award": 0.000, "rpi": 0.009, "cpi": 0.000},
        {"year": "2015/2016", "pay_award": 0.000, "rpi": 0.013, "cpi": 0.003},
        {"year": "2016/2017", "pay_award": 0.010, "rpi": 0.035, "cpi": 0.027},
        {"year": "2017/2018", "pay_award": 0.010, "rpi": 0.034, "cpi": 0.024},
        {"year": "2018/2019", "pay_award": 0.020, "rpi": 0.030, "cpi": 0.021},
        {"year": "2019/2020", "pay_award": 0.023, "rpi": 0.015, "cpi": 0.008},
        {"year": "2020/2021", "pay_award": 0.030, "rpi": 0.029, "cpi": 0.015},
        {"year": "2021/2022", "pay_award": 0.030, "rpi": 0.111, "cpi": 0.090},
        {"year": "2022/2023", "pay_award": 0.030, "rpi": 0.114, "cpi": 0.087},  # CPI data not provided for this year
    ]
    
    start_index = next((i for i, data in enumerate(pay_data) if data["year"] == start_year), 0)
    end_index = next((i for i, data in enumerate(pay_data) if data["year"] == end_year), len(pay_data))
    cumulative_effect = 1.0
    
    inflation_key = "rpi" if inflation_type == "RPI" else "cpi"
    
    for data in pay_data[start_index:end_index]:
        inflation_rate = data[inflation_key]
        if inflation_rate == 0.0:  # Skip years with no inflation data
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
    
    # Calculate initial FPR targets
    update_fpr_targets()

def update_fpr_targets():
    st.session_state.fpr_targets = {
        name: calculate_fpr_percentage(st.session_state.fpr_start_year, st.session_state.fpr_end_year, st.session_state.inflation_type)
        for name, _, _ in NODAL_POINTS
    }

def update_end_year_options():
    start_index = AVAILABLE_YEARS.index(st.session_state.fpr_start_year)
    st.session_state.end_year_options = AVAILABLE_YEARS[start_index + 1:]
    if st.session_state.fpr_end_year not in st.session_state.end_year_options:
        st.session_state.fpr_end_year = st.session_state.end_year_options[-1]
    update_fpr_targets()
    
# UI Setup Functions
def setup_sidebar():
    initialize_session_state()
    
    st.sidebar.title("Doctor Pay Model Settings")
    
    inflation_type = st.sidebar.radio("Select inflation measure:", ("RPI", "CPI"), key="inflation_type", on_change=update_fpr_targets, horizontal=True)
    
    fpr_start_year = st.sidebar.selectbox(
        "FPR start year",
        options=AVAILABLE_YEARS,
        index=AVAILABLE_YEARS.index(st.session_state.fpr_start_year),
        key="fpr_start_year",
        on_change=update_end_year_options
    )
    
    fpr_end_year = st.sidebar.selectbox(
        "FPR end year",
        options=st.session_state.end_year_options,
        index=st.session_state.end_year_options.index(st.session_state.fpr_end_year),
        key="fpr_end_year",
        on_change=update_fpr_targets
    )
    
    num_years = st.sidebar.number_input("Number of years for the deal", min_value=1, max_value=10, value=5)
    
    # Ensure FPR targets are calculated
    if not st.session_state.fpr_targets:
        update_fpr_targets()
    
    # Display FPR targets
    fpr_df = pd.DataFrame(list(st.session_state.fpr_targets.items()), columns=['Nodal Point', 'FPR Target (%)'])
    fpr_df['FPR Target (%)'] = fpr_df['FPR Target (%)'].round(1)
    st.sidebar.dataframe(fpr_df, hide_index=True)
    
    return inflation_type, fpr_start_year, fpr_end_year, num_years, st.session_state.fpr_targets


def setup_doctor_counts():
    st.subheader("Number of Doctors in Each Nodal Point")
    cols = st.columns(5)
    doctor_counts = {}
    default_counts = [8000, 6000, 20000, 25000, 6000]
    for i, (name, _, _) in enumerate(NODAL_POINTS):
        with cols[i]:
            count = st.number_input(f"{name}", min_value=0, value=default_counts[i], step=100, key=f"doctors_{name}")
            doctor_counts[name] = count
    
    # Store doctor_counts in session state
    st.session_state.doctor_counts = doctor_counts
    
    return doctor_counts

def setup_year_inputs(num_years):
    year_containers = [st.container() for _ in range(num_years)]
    year_inputs = []

    # Initialize session state for all years
    for year in range(num_years):
        if f"percentage_{year}" not in st.session_state:
            st.session_state[f"percentage_{year}"] = 0.0 if year == 0 else 2.0
        if f"nodal_percentages_{year}" not in st.session_state:
            st.session_state[f"nodal_percentages_{year}"] = {name: 0.0 if year == 0 else 2.0 for name, _, _ in NODAL_POINTS}

    def update_main_slider(year):
        nodal_percentages = st.session_state[f"nodal_percentages_{year}"]
        weighted_avg = calculate_weighted_average(nodal_percentages, st.session_state.doctor_counts)
        st.session_state[f"percentage_{year}"] = weighted_avg * 100

    def update_single_nodal(year, name):
        st.session_state[f"nodal_percentages_{year}"][name] = st.session_state[f"nodal_{name}_{year}"] / 100
        update_main_slider(year)

    for year in range(num_years):
        with year_containers[year]:
            st.subheader(f"Year {year} ({2023+year}/{2024+year})")
            if year == 0:
                year_input = setup_first_year_input()
            else:
                year_input = setup_subsequent_year_input(year)
            
            # Add expander for individual nodal point adjustments
            with st.expander(f"Adjust individual nodal points for Year {year} ({2023+year}/{2024+year})"):
                nodal_percentages = {}
                for name, _, _ in NODAL_POINTS:
                    nodal_percentages[name] = st.slider(
                        f"{name} increase (%)",
                        min_value=0.0,
                        max_value=20.0,
                        value=st.session_state[f"nodal_percentages_{year}"][name] * 100,
                        step=0.1,
                        key=f"nodal_{name}_{year}",
                        on_change=update_single_nodal,
                        args=(year, name)
                    )
                year_input['nodal_percentages'] = {k: v / 100 for k, v in nodal_percentages.items()}
            
            year_inputs.append(year_input)

    return year_inputs

def setup_first_year_input():
    st.write("Additional offer for 2023/2024 (on top of existing award)")
    
    # Global percentage increase
    percentage_increase = st.slider(
        "Global Percentage increase (%)", 
        min_value=0.0, 
        max_value=20.0, 
        value=st.session_state["percentage_0"], 
        step=0.1, 
        key="year1_percentage",
        on_change=update_first_year_nodal_percentages
    )
    
    # Individual nodal point increases
    st.write("OR Consolidated pay rise (£) for each nodal point:")
    pound_increases = {}
    cols = st.columns(len(NODAL_POINTS))
    for i, (name, _, _) in enumerate(NODAL_POINTS):
        with cols[i]:
            pound_increases[name] = st.number_input(
                f"{name}", 
                min_value=0, 
                max_value=10000, 
                value=0, 
                step=100, 
                key=f"year1_pound_{name}",
                on_change=update_first_year_nodal_percentages
            )
    
    nodal_increases = st.session_state["nodal_percentages_0"]

    return {
        "percentage": percentage_increase / 100,
        "pound_increases": pound_increases,
        "nodal_increases": nodal_increases
    }

def setup_subsequent_year_input(year):
    inflation_rate = st.slider(f"Projected Inflation for Year {year} ({2022+year}/{2023+year}) (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1, key=f"inflation_{year}")
    percentage_increase = st.slider(
        f"Pay Rise for Year {year} ({2022+year}/{2023+year}) (%)", 
        min_value=0.0, 
        max_value=20.0, 
        value=st.session_state[f"percentage_{year}"], 
        step=0.1, 
        key=f"percentage_{year}",
        on_change=update_nodal_percentages,
        args=(year,)
    )
    
    return {
        "inflation": inflation_rate / 100,
        "percentage": percentage_increase / 100,
        "nodal_percentages": st.session_state[f"nodal_percentages_{year}"]
    }

# Calculation Functions
def calculate_results(fpr_percentages, doctor_counts, year_inputs, inflation_type):
    results = []
    total_nominal_cost = 0
    total_real_cost = 0
    cumulative_costs = [0] * (len(year_inputs) + 1)

    for name, base_pay, post_ddrb_pay in NODAL_POINTS:
        result = calculate_nodal_point_results(name, base_pay, post_ddrb_pay, fpr_percentages[name], doctor_counts[name], year_inputs, inflation_type)
        results.append(result)
        total_nominal_cost += result["Nominal Nodal Cost"]
        total_real_cost += result["Real Nodal Cost"]

        for j, cost in enumerate(result["Yearly Costs"]):
            cumulative_costs[j] += cost

    return results, total_nominal_cost, total_real_cost, cumulative_costs

def calculate_nodal_point_results(name, base_pay, post_ddrb_pay, fpr_percentage, doctor_count, year_inputs, inflation_type):
    pay_progression_nominal = [base_pay, post_ddrb_pay]
    pay_progression_real = [base_pay, post_ddrb_pay]
    real_terms_pay_cuts = [-fpr_percentage / 100]
    fpr_progress = [0]
    net_change_in_pay = [0]
    yearly_costs = []

    # Year 1 (2023/2024) calculations
    year1_input = year_inputs[0]
    year1_inflation = 0.033 if inflation_type == "RPI" else 0.023
    
    # Calculate the pay rise from the existing 2023/2024 award
    existing_pay_rise = (post_ddrb_pay / base_pay) - 1
    
    if year1_input["pound_increases"][name] > 0:
        additional_increase = year1_input["pound_increases"][name] / base_pay
    else:
        additional_increase = year1_input["nodal_increases"][name]
    
    total_pay_rise = existing_pay_rise + additional_increase
    
    # Add the additional increase for Year 1
    total_pay_rise = existing_pay_rise + year1_input["nodal_increases"][name]
    
    year1_real_terms_change = calculate_real_terms_change(total_pay_rise, year1_inflation)
    year1_pay_erosion = calculate_new_pay_erosion(real_terms_pay_cuts[0], year1_real_terms_change)
    new_nominal_pay = post_ddrb_pay * (1 + year1_input["nodal_increases"][name])
    new_real_pay = new_nominal_pay / (1 + year1_inflation)

    pay_progression_nominal.append(new_nominal_pay)
    pay_progression_real.append(new_real_pay)
    real_terms_pay_cuts.append(year1_pay_erosion)
    fpr_progress.append((fpr_percentage / 100 - abs(year1_pay_erosion)) / (fpr_percentage / 100) * 100)
    net_change_in_pay.append(total_pay_rise * 100)
    yearly_costs.append((new_nominal_pay - base_pay) * doctor_count)

    # Subsequent years
    for year_input in year_inputs[1:]:
        nominal_increase = year_input["percentage"]
        inflation_rate = year_input["inflation"]
        
        real_terms_change = calculate_real_terms_change(nominal_increase, inflation_rate)
        new_nominal_pay = pay_progression_nominal[-1] * (1 + nominal_increase)
        new_real_pay = new_nominal_pay / (1 + inflation_rate)
        
        current_pay_cut = calculate_new_pay_erosion(real_terms_pay_cuts[-1], real_terms_change)
        
        pay_progression_nominal.append(new_nominal_pay)
        pay_progression_real.append(new_real_pay)
        real_terms_pay_cuts.append(current_pay_cut)
        
        current_progress = (fpr_percentage / 100 - abs(current_pay_cut)) / (fpr_percentage / 100) * 100
        fpr_progress.append(min(max(current_progress, 0), 100))
        
        net_change_in_pay.append(nominal_increase * 100)
        yearly_costs.append((new_nominal_pay - pay_progression_nominal[-2]) * doctor_count)

    return {
        "Nodal Point": name,
        "Base Pay": base_pay,
        "Final Pay": pay_progression_nominal[-1],
        "FPR Target": base_pay * (1 + fpr_percentage / 100),
        "FPR Required (%)": fpr_percentage,
        "Nominal Total Increase": pay_progression_nominal[-1] - base_pay,
        "Real Total Increase": pay_progression_real[-1] - base_pay,
        "Nominal Percent Increase": (pay_progression_nominal[-1] / base_pay - 1) * 100,
        "Real Percent Increase": (pay_progression_real[-1] / base_pay - 1) * 100,
        "Real Terms Pay Cuts": [abs(x) * 100 for x in real_terms_pay_cuts],  # Convert to percentage and use absolute value
        "FPR Progress": fpr_progress,
        "Net Change in Pay": net_change_in_pay,
        "Doctor Count": doctor_count,
        "Nominal Nodal Cost": (pay_progression_nominal[-1] - base_pay) * doctor_count,
        "Real Nodal Cost": (pay_progression_real[-1] - base_pay) * doctor_count,
        "Pay Progression Nominal": pay_progression_nominal,
        "Pay Progression Real": pay_progression_real,
        "Yearly Costs": yearly_costs,
    }

# Display Functions
def display_results(results, total_nominal_cost, total_real_cost):
    df_results = pd.DataFrame(results)
    st.dataframe(df_results)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total real cost of the deal (above inflation)", value=f"£{total_real_cost:,.0f}")
    with col2:
        st.metric(label="Total nominal cost of the deal (BASIC PAY ONLY)", value=f"£{total_nominal_cost:,.0f}")
    st.divider()

def display_visualizations(results, cumulative_costs, year_inputs, inflation_type, num_years):
    st.subheader("Pay Progression, FPR Progress, and Pay Erosion Visualization")
    selected_nodal_point = st.selectbox("Select Nodal Point", [result["Nodal Point"] for result in results], key="nodal_point_selector")
    selected_data = next(item for item in results if item["Nodal Point"] == selected_nodal_point)

    fig = create_pay_progression_chart(selected_data)
    st.plotly_chart(fig, use_container_width=True)

    st.write(f"FPR progress and Pay Erosion for {selected_nodal_point}:")
    progress_df = create_fpr_progress_table(selected_data)
    st.table(progress_df)

    display_pay_increase_curve(year_inputs, cumulative_costs, inflation_type, num_years)

def create_pay_progression_chart(selected_data):
    years = [f"Year {i} ({2023+i}/{2024+i})" for i in range(len(selected_data["Pay Progression Nominal"]))]
    nominal_pay = selected_data["Pay Progression Nominal"]
    baseline_pay = nominal_pay[0]
    pay_increase = [max(0, pay - baseline_pay) for pay in nominal_pay]
    percent_increase = [(increase / baseline_pay) * 100 for increase in pay_increase]
    initial_pay_erosion = abs(selected_data["Real Terms Pay Cuts"][0])
    pay_erosion = [abs(x) for x in selected_data["Real Terms Pay Cuts"]]
    fpr_progress = selected_data["FPR Progress"]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=years, y=[baseline_pay] * len(years), name="Baseline Pay", marker_color='rgb(0, 123, 255)'),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(x=years, y=pay_increase, name="Pay Increase", marker_color='rgb(255, 165, 0)',
               hovertemplate='Year: %{x}<br>Total Pay: £%{customdata[0]:,.2f}<br>Increase: £%{y:,.2f} (%{customdata[1]:.2f}%)<extra></extra>',
               customdata=list(zip(nominal_pay, percent_increase))),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=years, y=fpr_progress, name="FPR Progress", line=dict(color='rgb(0, 200, 0)', width=2)),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(x=years, y=pay_erosion, name="Pay Erosion", line=dict(color='rgb(255, 0, 0)', width=2)),
        secondary_y=True,
    )

    fig.update_layout(
        title=f"Pay Progression, FPR Progress, and Pay Erosion for {selected_data['Nodal Point']}",
        xaxis_title="Year",
        yaxis_title="Pay (£)",
        yaxis2_title="Percentage (%)",
        legend=dict(x=0, y=1.1, orientation="h"),
        barmode='stack',
        height=600,
    )

    fig.update_yaxes(title_text="Pay (£)", secondary_y=False, range=[0, 120000])
    fig.update_yaxes(title_text="Percentage (%)", secondary_y=True)

    return fig

def create_fpr_progress_table(selected_data):
    years = [f"Year {i} ({2022+i}/{2023+i})" for i in range(len(selected_data["FPR Progress"]))]
    
    df = pd.DataFrame({
        "Year": years,
        "FPR Progress (%)": selected_data["FPR Progress"],
        "Pay Erosion (%)": selected_data["Real Terms Pay Cuts"]
    })

    df["FPR Progress (%)"] = df["FPR Progress (%)"].apply(lambda x: f"{x:.2f}")
    df["Pay Erosion (%)"] = df["Pay Erosion (%)"].apply(lambda x: f"{x:.2f}")

    return df

def display_pay_increase_curve(year_inputs, cumulative_costs, inflation_type, num_years):    
    # Prepare data for the curve
    years = [f"Year {i} ({2023+i}/{2024+i})" for i in range(num_years + 1)]
    nominal_increases = [year_inputs[0]["percentage"]] + [year_input["percentage"] for year_input in year_inputs[1:]]
    inflation_rates = [0.033 if inflation_type == "RPI" else 0.023] + [year_input["inflation"] for year_input in year_inputs[1:]]
    real_increases = [nominal_increases[i] - inflation_rates[i] for i in range(len(nominal_increases))]
    
    # Ensure all lists have the same length
    max_length = max(len(years), len(nominal_increases), len(real_increases), len(cumulative_costs))
    years = years + [f"Year {i} ({2023+i}/{2024+i})" for i in range(len(years), max_length)]
    nominal_increases = nominal_increases + [0] * (max_length - len(nominal_increases))
    real_increases = real_increases + [0] * (max_length - len(real_increases))
    cumulative_costs = cumulative_costs + [cumulative_costs[-1]] * (max_length - len(cumulative_costs))
    
    curve_data = pd.DataFrame({
        "Year": years,
        "Nominal Increase (including inflation)": [x * 100 for x in nominal_increases],
        "Real Increase (above inflation)": [x * 100 for x in real_increases],
        "Cumulative Cost (£ millions)": [cost / 1e6 for cost in cumulative_costs],
    })
    st.subheader("Pay Increase Curve and Cumulative Cost")
    
    # Prepare data for the curve
    years = [f"Year {i} ({2022+i}/{2023+i})" for i in range(num_years + 1)]
    nominal_increases = [year_inputs[0]["percentage"]] + [year_input["percentage"] for year_input in year_inputs[1:]]
    inflation_rates = [0.033 if inflation_type == "RPI" else 0.023] + [year_input["inflation"] for year_input in year_inputs[1:]]
    real_increases = [nominal_increases[i] - inflation_rates[i] for i in range(len(nominal_increases))]
    
    # Ensure all lists have the same length
    max_length = max(len(years), len(nominal_increases), len(real_increases), len(cumulative_costs))
    years = years + [f"Year {i} ({2022+i}/{2023+i})" for i in range(len(years), max_length)]
    nominal_increases = nominal_increases + [0] * (max_length - len(nominal_increases))
    real_increases = real_increases + [0] * (max_length - len(real_increases))
    cumulative_costs = cumulative_costs + [cumulative_costs[-1]] * (max_length - len(cumulative_costs))
    
    curve_data = pd.DataFrame({
        "Year": years,
        "Nominal Increase (including inflation)": [x * 100 for x in nominal_increases],
        "Real Increase (above inflation)": [x * 100 for x in real_increases],
        "Cumulative Cost (£ millions)": [cost / 1e6 for cost in cumulative_costs],
    })
    
    fig_curve = make_subplots(specs=[[{"secondary_y": True}]])

    fig_curve.add_trace(
        go.Scatter(x=curve_data["Year"], y=curve_data['Nominal Increase (including inflation)'], name="Nominal Increase"),
        secondary_y=False
    )
    fig_curve.add_trace(
        go.Scatter(x=curve_data["Year"], y=curve_data['Real Increase (above inflation)'], name="Real Increase"),
        secondary_y=False
    )
    fig_curve.add_trace(
        go.Scatter(x=curve_data["Year"], y=curve_data['Cumulative Cost (£ millions)'], name="Cumulative Cost"),
        secondary_y=True
    )

    fig_curve.update_layout(
        title_text="Pay Increase Curve and Cumulative Cost",
        xaxis_title="Year",
        legend=dict(x=0, y=1, traceorder="normal")
    )
    fig_curve.update_yaxes(title_text="Percentage Increase", secondary_y=False)
    fig_curve.update_yaxes(title_text="Cumulative Cost (£ millions)", secondary_y=True)

    st.plotly_chart(fig_curve, use_container_width=True)
    st.caption("Note: Cumulative Cost is shown in millions of pounds")

def main():
    st.title("Doctor Pay Model with Dynamic FPR Calculation")

    inflation_type, fpr_start_year, fpr_end_year, num_years, fpr_percentages = setup_sidebar()
    
    # Ensure FPR targets are calculated
    if not fpr_percentages:
        update_fpr_targets()
        fpr_percentages = st.session_state.fpr_targets

    doctor_counts = setup_doctor_counts()
    year_inputs = setup_year_inputs(num_years)

    results, total_nominal_cost, total_real_cost, cumulative_costs = calculate_results(
        fpr_percentages, doctor_counts, year_inputs, inflation_type
    )

    display_results(results, total_nominal_cost, total_real_cost)
    display_visualizations(results, cumulative_costs, year_inputs, inflation_type, num_years)

if __name__ == "__main__":
    main()