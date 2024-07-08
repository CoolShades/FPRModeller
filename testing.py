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
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        fpr_start_year = st.selectbox(
            "FPR start year",
            options=AVAILABLE_YEARS,
            index=AVAILABLE_YEARS.index(st.session_state.fpr_start_year),
            key="fpr_start_year",
            on_change=update_end_year_options
        )
    with col2:
        fpr_end_year = st.selectbox(
            "FPR end year",
            options=st.session_state.end_year_options,
            index=st.session_state.end_year_options.index(st.session_state.fpr_end_year),
            key="fpr_end_year",
            on_change=update_fpr_targets
        )
    
    num_years = st.sidebar.number_input("Number of years for the deal", min_value=0, max_value=10, value=5)
    
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

def setup_year_inputs(num_years, inflation_type):
    year_inputs = []

    # Initialize session state for all years
    for year in range(num_years + 1):  # +1 to include year 0
        if f"nodal_percentages_{year}" not in st.session_state:
            st.session_state[f"nodal_percentages_{year}"] = {name: 0.0 if year == 0 else 7.0 for name, _, _ in NODAL_POINTS}
        if f"pound_increases_{year}" not in st.session_state:
            st.session_state[f"pound_increases_{year}"] = {name: 0 for name, _, _ in NODAL_POINTS}

    for year in range(num_years + 1):  # +1 to include year 0
        with st.expander(f"Year {year} ({2023+year}/{2024+year})"):
            year_input = {
                "nodal_percentages": {},
                "pound_increases": {},
                "inflation": 0.0
            }
            
            st.write("Consolidated pay offer:")
            cols_consolidated = st.columns(5)
            for i, (name, _, _) in enumerate(NODAL_POINTS):
                with cols_consolidated[i]:
                    year_input["pound_increases"][name] = st.number_input(
                        f"{name}",
                        min_value=0,
                        max_value=10000,
                        value=st.session_state[f"pound_increases_{year}"][name],
                        step=100,
                        key=f"pound_increase_{name}_{year}"
                    )
            
            st.write("Percentage pay rise:")
            cols_percentage = st.columns(5)
            for i, (name, _, _) in enumerate(NODAL_POINTS):
                with cols_percentage[i]:
                    year_input["nodal_percentages"][name] = st.number_input(
                        f"{name} (%)",
                        min_value=0.0,
                        max_value=20.0,
                        value=st.session_state[f"nodal_percentages_{year}"][name],
                        step=0.1,
                        format="%.1f",
                        key=f"nodal_percentage_{name}_{year}"
                    ) / 100
            
            if year == 0:
                # Set fixed inflation rate for year 0
                year_input["inflation"] = 0.033 if inflation_type == "RPI" else 0.023
                st.write(f"Inflation for Year 0 (2023/2024): {year_input['inflation']*100:.1f}%")
            else:
                year_input["inflation"] = st.slider(
                    f"Projected Inflation for Year {year} ({2023+year}/{2024+year}) (%)",
                    min_value=0.0,
                    max_value=10.0,
                    value=2.0,
                    step=0.1,
                    key=f"inflation_{year}"
                ) / 100
            
            # Calculate and display net change in pay for each nodal point
            st.write("Net change in pay:")
            cols_net_change = st.columns(5)
            for i, (name, base_pay, _) in enumerate(NODAL_POINTS):
                with cols_net_change[i]:
                    consolidated_increase = year_input["pound_increases"][name]
                    percentage_increase = year_input["nodal_percentages"][name]
                    inflation_rate = year_input["inflation"]
                    
                    if year == 0:
                        # For year 0, consider the existing DDRB award
                        existing_award = NODAL_POINTS[i][2] - base_pay
                        net_change = existing_award + consolidated_increase + (base_pay * percentage_increase)
                        total_percentage_increase = (net_change / base_pay)
                    else:
                        net_change = consolidated_increase + (base_pay * percentage_increase)
                        total_percentage_increase = (net_change / base_pay)
                    
                    # Calculate real terms pay increase
                    real_terms_increase = ((1 + total_percentage_increase) / (1 + inflation_rate)) - 1
                    
                    st.metric(
                        label=f"{name}",
                        value=f"£{net_change:,.0f}",
                        delta=f"{real_terms_increase*100:.1f}%"
                    )
            
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

def calculate_results(fpr_percentages, doctor_counts, year_inputs, inflation_type):
    results = []
    total_nominal_cost = 0
    total_real_cost = 0
    cumulative_costs = [0] * (len(year_inputs) + 1)

    for name, base_pay, post_ddrb_pay in NODAL_POINTS:
        result = calculate_nodal_point_results(name, base_pay, post_ddrb_pay, fpr_percentages[name], doctor_counts[name], year_inputs, inflation_type)
        results.append(result)
        total_nominal_cost += result["Total Nominal Cost"]
        total_real_cost += result["Total Real Cost"]

        for j, cost in enumerate(result["Yearly Total Costs"]):
            cumulative_costs[j] += cost

    return results, total_nominal_cost, total_real_cost, cumulative_costs



def calculate_nodal_point_results(name, base_pay, post_ddrb_pay, fpr_percentage, doctor_count, year_inputs, inflation_type):
    pay_progression_nominal = [base_pay, post_ddrb_pay]
    pay_progression_real = [base_pay, post_ddrb_pay]
    real_terms_pay_cuts = [-fpr_percentage / 100]
    fpr_progress = [0]
    net_change_in_pay = [0]
    yearly_basic_costs = []
    yearly_total_costs = []

    for year, year_input in enumerate(year_inputs):
        if year == 0:
            # Year 1 (2023/2024) calculations
            existing_pay_rise = (post_ddrb_pay / base_pay) - 1
            consolidated_increase = year_input["pound_increases"][name]
            percentage_increase = year_input["nodal_percentages"][name]
            total_pay_rise = existing_pay_rise + (consolidated_increase / base_pay) + percentage_increase
            new_nominal_pay = post_ddrb_pay * (1 + percentage_increase) + consolidated_increase
        else:
            # Subsequent years
            total_pay_rise = year_input["nodal_percentages"][name]
            new_nominal_pay = pay_progression_nominal[-1] * (1 + total_pay_rise)

        inflation_rate = year_input["inflation"]
        new_real_pay = new_nominal_pay / (1 + inflation_rate)
        
        real_terms_change = calculate_real_terms_change(total_pay_rise, inflation_rate)
        current_pay_cut = calculate_new_pay_erosion(real_terms_pay_cuts[-1], real_terms_change)
        
        pay_progression_nominal.append(new_nominal_pay)
        pay_progression_real.append(new_real_pay)
        real_terms_pay_cuts.append(current_pay_cut)
        
        current_progress = (fpr_percentage / 100 - abs(current_pay_cut)) / (fpr_percentage / 100) * 100
        fpr_progress.append(min(max(current_progress, 0), 100))
        
        net_change_in_pay.append(total_pay_rise * 100)
        
        # Calculate costs
        basic_pay_increase = new_nominal_pay - pay_progression_nominal[-2]
        basic_pay_cost = basic_pay_increase * doctor_count
        pension_cost = basic_pay_cost * 0.237
        additional_hours_cost = (basic_pay_cost / 40) * 8
        ooh_component = additional_hours_cost * 0.37
        
        total_cost = basic_pay_cost + pension_cost + additional_hours_cost + ooh_component
        
        yearly_basic_costs.append(basic_pay_cost)
        yearly_total_costs.append(total_cost)

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
        "Real Terms Pay Cuts": [abs(x) * 100 for x in real_terms_pay_cuts],
        "FPR Progress": fpr_progress,
        "Net Change in Pay": net_change_in_pay,
        "Doctor Count": doctor_count,
        "Total Nominal Cost": sum(yearly_total_costs),
        "Total Real Cost": sum(yearly_total_costs) / (1 + year_inputs[-1]["inflation"]),
        "Pay Progression Nominal": pay_progression_nominal,
        "Pay Progression Real": pay_progression_real,
        "Yearly Basic Costs": yearly_basic_costs,
        "Yearly Total Costs": yearly_total_costs,
    }

def display_cost_breakdown(results, year_inputs):
    st.subheader("Cost Breakdown by Year")
    
    yearly_totals = []
    
    tabs = st.tabs([f"{'Initial Year' if year == 0 else f'Year {year}'}: {2023 + year}/{2024 + year}" for year in range(len(year_inputs))])
    
    for year, tab in enumerate(tabs):
        with tab:
            cost_data = []
            year_total = 0
            for result in results:
                if year < len(result["Yearly Basic Costs"]):
                    basic_pay_cost = result["Yearly Basic Costs"][year]
                else:
                    continue
                
                pension_cost = basic_pay_cost * 0.237
                additional_hours = (basic_pay_cost / 40) * 8
                ooh_component = additional_hours * 0.37
                total_cost = basic_pay_cost + pension_cost + additional_hours + ooh_component
                year_total += total_cost
                
                cost_data.append({
                    "Nodal Point": result["Nodal Point"],
                    "Total Gov Offer Cost (BASIC PAY ONLY)": basic_pay_cost,
                    "Pension Cost (23.7% employer contribution)": pension_cost,
                    "Additional Hours (8 hours)": additional_hours,
                    "OOH component (8 hours)": ooh_component,
                    "Total Cost": total_cost
                })
            
            df = pd.DataFrame(cost_data)
            df = df.set_index("Nodal Point")
            
            # Format currency values
            for col in df.columns:
                df[col] = df[col].apply(lambda x: f"£{x:,.2f}")
            
            st.dataframe(df.style.set_properties(**{'text-align': 'right'}))
            
            yearly_totals.append({"Year": f"Year {year} ({2023 + year}/{2024 + year})", "Total Cost": year_total})
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.metric(label=f"Total Cost for Year {year}", value=f"£{year_total:,.2f}")
            with col2:
                st.write(f"Cumulative Cost: £{sum(item['Total Cost'] for item in yearly_totals):,.2f}")
    
    total_nominal_cost = sum(item['Total Cost'] for item in yearly_totals)
    st.metric(label="Total nominal cost of the deal", value=f"£{total_nominal_cost:,.2f}")
    st.divider()

def display_results(results, total_nominal_cost, total_real_cost, year_inputs):
    df_results = pd.DataFrame(results)
    st.dataframe(df_results)
    
    # Display the detailed cost breakdown
    display_cost_breakdown(results, year_inputs)
    
def display_visualizations(results, cumulative_costs, year_inputs, inflation_type, num_years):
    st.subheader("Pay Progression, FPR Progress, and Pay Erosion Visualization")
    selected_nodal_point = st.selectbox("Select Nodal Point", [result["Nodal Point"] for result in results], key="nodal_point_selector")
    selected_data = next(item for item in results if item["Nodal Point"] == selected_nodal_point)

    fig = create_pay_progression_chart(selected_data, num_years)
    st.plotly_chart(fig, use_container_width=True)

    st.write(f"FPR progress and Pay Erosion for {selected_nodal_point}:")
    progress_df = create_fpr_progress_table(selected_data, num_years)
    st.table(progress_df)

    display_pay_increase_curve(year_inputs, cumulative_costs, inflation_type, num_years)

def create_pay_progression_chart(selected_data, num_years):
    years = [f"Year {i} ({2023+i}/{2024+i})" for i in range(num_years + 1)]  # +1 to include Year 0
    nominal_pay = selected_data["Pay Progression Nominal"][:num_years + 1]  # Limit to selected number of years
    baseline_pay = nominal_pay[0]
    pay_increase = [max(0, pay - baseline_pay) for pay in nominal_pay]
    percent_increase = [(increase / baseline_pay) * 100 for increase in pay_increase]
    initial_pay_erosion = abs(selected_data["Real Terms Pay Cuts"][0])
    pay_erosion = [abs(x) for x in selected_data["Real Terms Pay Cuts"][:num_years + 1]]  # Limit to selected number of years
    fpr_progress = selected_data["FPR Progress"][:num_years + 1]  # Limit to selected number of years

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

def create_fpr_progress_table(selected_data, num_years):
    years = [f"Year {i} ({2023+i}/{2024+i})" for i in range(num_years + 1)]  # +1 to include Year 0
    
    df = pd.DataFrame({
        "Year": years,
        "FPR Progress (%)": selected_data["FPR Progress"][:num_years + 1],
        "Pay Erosion (%)": selected_data["Real Terms Pay Cuts"][:num_years + 1]
    })

    df["FPR Progress (%)"] = df["FPR Progress (%)"].apply(lambda x: f"{x:.2f}")
    df["Pay Erosion (%)"] = df["Pay Erosion (%)"].apply(lambda x: f"{x:.2f}")

    return df

def display_pay_increase_curve(year_inputs, cumulative_costs, inflation_type, num_years):
    years = [f"Year {i} ({2023+i}/{2024+i})" for i in range(num_years + 1)]  # +1 to include Year 0
    
    nominal_increases = [0]  # Start with 0 for Year 0
    nominal_increases += [
        sum(year_input["nodal_percentages"].values()) / len(year_input["nodal_percentages"])
        for year_input in year_inputs
    ]
    nominal_increases = nominal_increases[:num_years + 1]  # Limit to selected number of years
    
    inflation_rates = [0.033 if inflation_type == "RPI" else 0.023]  # Base year inflation
    inflation_rates += [year_input.get("inflation", inflation_rates[0]) for year_input in year_inputs]
    inflation_rates = inflation_rates[:num_years + 1]  # Limit to selected number of years
    
    real_increases = [nominal_increases[i] - inflation_rates[i] for i in range(len(nominal_increases))]
    
    cumulative_costs = cumulative_costs[:num_years + 1]  # Limit to selected number of years
    
    # Calculate the actual cumulative costs
    actual_cumulative_costs = [sum(cumulative_costs[:i+1]) for i in range(len(cumulative_costs))]
    
    curve_data = pd.DataFrame({
        "Year": years,
        "Nominal Increase (including inflation)": [x * 100 for x in nominal_increases],
        "Real Increase (above inflation)": [x * 100 for x in real_increases],
        "Cumulative Cost (£ millions)": [cost / 1e6 for cost in actual_cumulative_costs],
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
    year_inputs = setup_year_inputs(num_years, inflation_type)

    results, total_nominal_cost, total_real_cost, cumulative_costs = calculate_results(
        fpr_percentages, doctor_counts, year_inputs, inflation_type
    )

    display_results(results, total_nominal_cost, total_real_cost, year_inputs)
    display_visualizations(results, cumulative_costs, year_inputs, inflation_type, num_years)


if __name__ == "__main__":
    main()