import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Constants
FPR_REFERENCE_YEAR = 2008
CURRENT_YEAR = 2024
HISTORICAL_INFLATION = 2.0  # You may want to adjust this value

def calculate_pay_increase(base_pay, percentages, inflation_rate):
    pay = base_pay
    increases = [base_pay]
    for percentage in percentages:
        total_increase_rate = (1 + percentage/100) * (1 + inflation_rate/100) - 1
        pay *= (1 + total_increase_rate)
        increases.append(pay)
    return increases

def calculate_weighted_average(percentages, weights):
    return sum(p * w for p, w in zip(percentages, weights)) / sum(weights)

def calculate_real_terms_pay_cut(nominal_increase, inflation_rate):
    return ((1 + nominal_increase) / (1 + inflation_rate)) - 1

def calculate_fpr_percentage(start_year, inflation_type):
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
    cumulative_effect = 1.0
    
    inflation_key = "rpi" if inflation_type == "RPI" else "cpi"
    
    for data in pay_data[start_index:]:
        inflation_rate = data[inflation_key]
        if inflation_rate == 0.0:  # Skip years with no inflation data
            continue
        real_terms_change = ((1 + data["pay_award"]) / (1 + inflation_rate)) - 1
        cumulative_effect *= (1 + real_terms_change)
    
    fpr_percentage = (1 - cumulative_effect) * 100
    return fpr_percentage

def main():
    st.title("Doctor Pay Model with Dynamic FPR Calculation")

    # Add RPI/CPI toggle
    inflation_type = st.radio("Select inflation measure:", ("RPI", "CPI"))

    # Add FPR start year selection
    fpr_start_year = st.selectbox(
        "Select the starting year for Full Pay Restoration calculation",
        options=[
            "2008/2009", "2009/2010", "2010/2011", "2011/2012", "2012/2013",
            "2013/2014", "2014/2015", "2015/2016", "2016/2017", "2017/2018",
            "2018/2019", "2019/2020", "2020/2021", "2021/2022", "2022/2023"
        ],
        index=0  # Default to the earliest year
    )

    # Calculate FPR percentage based on the selected start year and inflation type
    fpr_percentage = calculate_fpr_percentage(fpr_start_year, inflation_type)

    st.write(f"Full Pay Restoration target: {fpr_percentage:.1f}%")

    # Slider for inflation rate
    inflation_rate = st.slider("Projected Annual Inflation Rate (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1, key="inflation_rate")

    # Input for number of years
    num_years = st.number_input("Number of years for the deal", min_value=1, max_value=10, value=5, key="num_years")

    # Input for nodal points and doctor counts
    st.subheader("Number of Doctors in Each Nodal Point")
    cols = st.columns(5)
    nodal_points = [
        ("Nodal 1", 29384),
        ("Nodal 2", 34012),
        ("Nodal 3", 40257),
        ("Nodal 4", 51017),
        ("Nodal 5", 58398)
    ]
    doctor_counts = {}
    default_counts = [8000, 6000, 20000, 25000, 6000]
    for i, (name, base_pay) in enumerate(nodal_points):
        with cols[i]:
            doctor_counts[name] = st.number_input(f"{name}", min_value=0, value=default_counts[i], step=100, key=f"doctors_{name}")

    # Create containers for the year sliders
    year_containers = [st.container() for _ in range(num_years)]

    # Calculate default nodal increases for the first year
    default_nodal_increases = [10.26, 9.68, 9.11, 8.45, 8.14]
    weights = [doctor_counts[name] for name, _ in nodal_points]
    default_weighted_avg = calculate_weighted_average(default_nodal_increases, weights)

    # Initialize session state for all years
    for year in range(num_years):
        if f"percentage_{year}" not in st.session_state:
            st.session_state[f"percentage_{year}"] = default_weighted_avg if year == 0 else 8.0
        if f"nodal_percentages_{year}" not in st.session_state:
            st.session_state[f"nodal_percentages_{year}"] = default_nodal_increases if year == 0 else [8.0] * 5

    # Function to update the main slider when nodal percentages change
    def update_main_slider(year):
        weights = [doctor_counts[name] for name, _ in nodal_points]
        weighted_avg = calculate_weighted_average(st.session_state[f"nodal_percentages_{year}"], weights)
        st.session_state[f"percentage_{year}"] = weighted_avg

    # Function to update nodal percentages when the main slider changes
    def update_nodal_percentages(year):
        for i in range(5):
            st.session_state[f"nodal_{i}_{year}"] = st.session_state[f"percentage_{year}"]
        st.session_state[f"nodal_percentages_{year}"] = [st.session_state[f"nodal_{i}_{year}"] for i in range(5)]

    # Function to update a single nodal percentage
    def update_single_nodal(year, index):
        st.session_state[f"nodal_percentages_{year}"][index] = st.session_state[f"nodal_{index}_{year}"]
        update_main_slider(year)

    # Sliders for percentages with expandable sections for each nodal point
    percentages = []
    nodal_percentages = []
    for year in range(num_years):
        with year_containers[year]:
            st.subheader(f"Year {year + 1}")
            
            # Main slider for the year
            percentage = st.slider(
                f"Real Percentage increase for Year {year + 1} (above inflation)", 
                min_value=0.0, max_value=20.0, value=st.session_state[f"percentage_{year}"], step=0.1, 
                key=f"percentage_{year}",
                on_change=update_nodal_percentages,
                args=(year,)
            )
            percentages.append(percentage)

            # Expander for individual nodal point adjustments
            with st.expander(f"Adjust individual nodal points for Year {year + 1}"):
                for i, (name, _) in enumerate(nodal_points):
                    nodal_value = st.slider(
                        f"{name} increase (%)",
                        min_value=0.0, max_value=20.0,
                        value=st.session_state[f"nodal_percentages_{year}"][i],
                        step=0.1,
                        key=f"nodal_{i}_{year}",
                        on_change=update_single_nodal,
                        args=(year, i)
                    )
            nodal_percentages.append(st.session_state[f"nodal_percentages_{year}"])

    # Calculate results
    results = []
    total_nominal_cost = 0
    total_real_cost = 0
    cumulative_costs = [0] * (num_years + 1)  # Initialize with zeros

    for i, (name, base_pay) in enumerate(nodal_points):
        pay_progression_nominal = calculate_pay_increase(base_pay, [p[i] for p in nodal_percentages], inflation_rate)
        pay_progression_real = [base_pay]
        real_terms_pay_cuts = [0]  # Initial pay cut is 0
        fpr_progress = [0]  # Initialize FPR progress tracking
        pay_erosion = [fpr_percentage / 100]  # Initialize pay erosion with FPR percentage
        
        fpr_target = base_pay * (1 + fpr_percentage / 100)
        
        for year in range(1, num_years + 1):
            nominal_increase = (pay_progression_nominal[year] - pay_progression_nominal[year-1]) / pay_progression_nominal[year-1]
            real_terms_pay_cut = calculate_real_terms_pay_cut(nominal_increase, inflation_rate / 100)
            real_terms_pay_cuts.append(real_terms_pay_cut)
            
            current_real_pay = pay_progression_real[-1] * (1 + real_terms_pay_cut)
            pay_progression_real.append(current_real_pay)
            
            # Calculate new pay erosion
            new_erosion_after_inflation = 1 - (1 - pay_erosion[-1]) / (1 + inflation_rate / 100)
            new_erosion = 1 - ((1 - new_erosion_after_inflation) * (1 + real_terms_pay_cut))
            pay_erosion.append(new_erosion)
            
            # Calculate FPR progress for this year
            current_fpr_progress = ((1 - new_erosion) - (1 - pay_erosion[0])) / pay_erosion[0] * 100
            fpr_progress.append(current_fpr_progress)
        
        final_pay = pay_progression_nominal[-1]
        total_nominal_increase = final_pay - base_pay
        total_real_increase = pay_progression_real[-1] - base_pay
        percent_increase = (total_nominal_increase / base_pay) * 100
        real_percent_increase = (total_real_increase / base_pay) * 100
        
        doctor_count = doctor_counts[name]
        nominal_nodal_cost = total_nominal_increase * doctor_count
        real_nodal_cost = total_real_increase * doctor_count
        total_nominal_cost += nominal_nodal_cost
        total_real_cost += real_nodal_cost
        
        # Calculate cumulative costs for each year
        nodal_yearly_costs = [
            (pay - base_pay) * doctor_count 
            for pay in pay_progression_nominal[1:]  # Skip the first element (base pay)
        ]
        for j, cost in enumerate(nodal_yearly_costs):
            cumulative_costs[j+1] += cost
        
        results.append({
            "Nodal Point": name,
            "Base Pay": base_pay,
            "Final Pay": final_pay,
            "FPR Target": fpr_target,
            "FPR Required (%)": fpr_percentage,
            "Nominal Total Increase": total_nominal_increase,
            "Real Total Increase": total_real_increase,
            "Nominal Percent Increase": percent_increase,
            "Real Percent Increase": real_percent_increase,
            "FPR Progress by Year": fpr_progress,
            "Pay Erosion by Year": pay_erosion,
            "Doctor Count": doctor_count,
            "Nominal Nodal Cost": nominal_nodal_cost,
            "Real Nodal Cost": real_nodal_cost,
            "Pay Progression Nominal": pay_progression_nominal,
            "Pay Progression Real": pay_progression_real,
            "Real Terms Pay Cuts": real_terms_pay_cuts
        })

    # Display results
    df_results = pd.DataFrame(results)
    st.dataframe(df_results)

    # Display total costs
    st.write(f"Total nominal cost of the deal: £{total_nominal_cost:,.2f}")
    st.write(f"Total real cost of the deal (above inflation): £{total_real_cost:,.2f}")

    # Calculate and display average percent of FPR achieved
    avg_fpr = df_results["FPR Progress by Year"].apply(lambda x: x[-1]).mean()
    st.write(f"Average progress towards full pay restoration: {avg_fpr:.2f}%")

    # Update the Pay Progression and FPR Visualization
    st.subheader("Pay Progression, FPR Progress, and Pay Erosion Visualization")
    selected_nodal_point = st.selectbox("Select Nodal Point", [name for name, _ in nodal_points], key="nodal_point_selector")
    
    # Get data for the selected nodal point
    selected_data = next(item for item in results if item["Nodal Point"] == selected_nodal_point)
    
     # Create a combined bar and line chart using Plotly
    fig = go.Figure()
    
    # Add bar chart for pay progression
    fig.add_trace(
        go.Bar(
            x=[f"Year {i}" for i in range(num_years + 1)],
            y=selected_data["Pay Progression Nominal"],
            name="Nominal Pay"
        )
    )
    
    # Add line chart for FPR progress
    fig.add_trace(
        go.Scatter(
            x=[f"Year {i}" for i in range(num_years + 1)],
            y=[fpr for fpr in selected_data["FPR Progress by Year"]],
            name="FPR Progress",
            line=dict(color="green", width=2),
            yaxis="y2"
        )
    )
    
    # Add line chart for Pay Erosion
    fig.add_trace(
        go.Scatter(
            x=[f"Year {i}" for i in range(num_years + 1)],
            y=[pe * 100 for pe in selected_data["Pay Erosion by Year"]],
            name="Pay Erosion",
            line=dict(color="red", width=2),
            yaxis="y2"
        )
    )
    
    # Update layout
    fig.update_layout(
        title=f"Pay Progression, FPR Progress, and Pay Erosion for {selected_nodal_point}",
        xaxis_title="Year",
        yaxis_title="Pay (£)",
        yaxis2=dict(title="Percentage (%)", overlaying="y", side="right", range=[0, 100]),
        legend=dict(x=0, y=1, traceorder="normal"),
        barmode="relative"
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

    # Display FPR progress and Pay Erosion
    st.write(f"FPR progress and Pay Erosion for {selected_nodal_point}:")
    progress_df = pd.DataFrame({
        "Year": [f"Year {i}" for i in range(num_years + 1)],
        "FPR Progress (%)": selected_data["FPR Progress by Year"],
        "Pay Erosion (%)": [pe * 100 for pe in selected_data["Pay Erosion by Year"]]
    })
    st.dataframe(progress_df)

    # Plot pay increase curve with cumulative cost
    st.subheader("Pay Increase Curve and Cumulative Cost")
    curve_data = pd.DataFrame({
        "Nominal Increase (including inflation)": [inflation_rate] + [p + inflation_rate for p in percentages],
        "Real Increase (above inflation)": [0] + percentages,
        "Cumulative Cost (£ millions)": [cost / 1e6 for cost in cumulative_costs],  # Convert to millions
    }, index=range(num_years + 1))
    
    fig_curve = make_subplots(specs=[[{"secondary_y": True}]])

    fig_curve.add_trace(
        go.Scatter(x=curve_data.index, y=curve_data['Nominal Increase (including inflation)'], name="Nominal Increase"),
        secondary_y=False
    )
    fig_curve.add_trace(
        go.Scatter(x=curve_data.index, y=curve_data['Real Increase (above inflation)'], name="Real Increase"),
        secondary_y=False
    )
    fig_curve.add_trace(
        go.Scatter(x=curve_data.index, y=curve_data['Cumulative Cost (£ millions)'], name="Cumulative Cost"),
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

if __name__ == "__main__":
    main()