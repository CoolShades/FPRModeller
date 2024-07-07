import streamlit as st
import pandas as pd
import numpy as np

def calculate_pay_increase(base_pay, percentages, inflation_rate):
    pay = base_pay
    increases = [base_pay]  # Start with base pay
    for percentage in percentages:
        total_increase_rate = (1 + percentage/100) * (1 + inflation_rate/100) - 1
        pay += pay * total_increase_rate
        increases.append(pay)
    return increases

def calculate_weighted_average(percentages, weights):
    return sum(p * w for p, w in zip(percentages, weights)) / sum(weights)

def main():
    st.title("Doctor Pay Model with Pay Progression Visualization")

    # Slider for inflation rate
    inflation_rate = st.slider("Annual Inflation Rate (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1, key="inflation_rate")

    # Input for number of years
    num_years = st.number_input("Number of years", min_value=1, max_value=10, value=5, key="num_years")

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
    default_counts = [8000, 6000, 20000, 25000, 6000]  # Updated default counts
    for i, (name, base_pay) in enumerate(nodal_points):
        with cols[i]:
            doctor_counts[name] = st.number_input(f"{name}", min_value=0, value=default_counts[i], step=100, key=f"doctors_{name}")

    # Function to update the main slider when nodal percentages change
    def update_main_slider(year):
        weights = [doctor_counts[name] for name, _ in nodal_points]
        weighted_avg = calculate_weighted_average(st.session_state[f"nodal_percentages_{year}"], weights)
        st.session_state[f"percentage_{year}"] = weighted_avg

    # Function to update nodal percentages when the main slider changes
    def update_nodal_percentages(year):
        for i in range(5):
            st.session_state[f"nodal_{i}_{year}"] = st.session_state[f"percentage_{year}"]

    # Sliders for percentages with expandable sections for each nodal point
    percentages = []
    nodal_percentages = []
    for year in range(num_years):
        st.subheader(f"Year {year + 1}")
        
        # Initialize session state for this year if not already done
        if f"percentage_{year}" not in st.session_state:
            st.session_state[f"percentage_{year}"] = 8.0
        if f"nodal_percentages_{year}" not in st.session_state:
            st.session_state[f"nodal_percentages_{year}"] = [8.0] * 5

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
                    on_change=update_main_slider,
                    args=(year,)
                )
                st.session_state[f"nodal_percentages_{year}"][i] = nodal_value

        nodal_percentages.append(st.session_state[f"nodal_percentages_{year}"])

    # Calculate results
    results = []
    total_nominal_cost = 0
    total_real_cost = 0
    pay_progression = {}
    cumulative_costs = [0] * (num_years + 1)  # Initialize with zeros

    for i, (name, base_pay) in enumerate(nodal_points):
        pay_progression[name] = calculate_pay_increase(base_pay, [p[i] for p in nodal_percentages], inflation_rate)
        final_pay = pay_progression[name][-1]
        total_nominal_increase = final_pay - base_pay
        total_real_increase = total_nominal_increase / ((1 + inflation_rate/100) ** num_years)
        percent_increase = (total_nominal_increase / base_pay) * 100
        real_percent_increase = (total_real_increase / base_pay) * 100
        percent_of_fpr = (real_percent_increase / 46.30) * 100
        doctor_count = doctor_counts[name]
        nominal_nodal_cost = total_nominal_increase * doctor_count
        real_nodal_cost = total_real_increase * doctor_count
        total_nominal_cost += nominal_nodal_cost
        total_real_cost += real_nodal_cost
        
        # Calculate cumulative costs for each year
        nodal_yearly_costs = [
            (pay - base_pay) * doctor_count 
            for pay in pay_progression[name][1:]  # Skip the first element (base pay)
        ]
        for j, cost in enumerate(nodal_yearly_costs):
            cumulative_costs[j+1] += cost
        
        results.append({
            "Nodal Point": name,
            "Base Pay": base_pay,
            "Final Pay": final_pay,
            "Nominal Total Increase": total_nominal_increase,
            "Real Total Increase": total_real_increase,
            "Nominal Percent Increase": percent_increase,
            "Real Percent Increase": real_percent_increase,
            "Percent of FPR": percent_of_fpr,
            "Doctor Count": doctor_count,
            "Nominal Nodal Cost": nominal_nodal_cost,
            "Real Nodal Cost": real_nodal_cost
        })

    # Display results
    df_results = pd.DataFrame(results)
    st.dataframe(df_results)

    # Display total costs
    st.write(f"Total nominal cost of the deal: £{total_nominal_cost:,.2f}")
    st.write(f"Total real cost of the deal (above inflation): £{total_real_cost:,.2f}")

    # Calculate and display average percent of FPR achieved
    avg_fpr = df_results["Percent of FPR"].mean()
    st.write(f"Average progress towards full pay restoration: {avg_fpr:.2f}%")

    # Pay Progression Visualization
    st.subheader("Pay Progression Visualization")
    tabs = st.tabs([f"Year {i+1}" for i in range(num_years)])

    for i, tab in enumerate(tabs):
        with tab:
            chart_data = pd.DataFrame({
                name: pay_progression[name][:i+2] for name, _ in nodal_points
            })
            st.bar_chart(chart_data)
            st.caption(f"Pay Progression After {i+1} Years")

    # Plot pay increase curve with cumulative cost and FPR line
    st.subheader("Pay Increase Curve and Cumulative Cost")
    curve_data = pd.DataFrame({
        "Nominal Increase (including inflation)": [inflation_rate] + [p + inflation_rate for p in percentages],
        "Real Increase (above inflation)": [0] + percentages,
        "Cumulative Cost (£ millions)": [cost / 1e6 for cost in cumulative_costs],  # Convert to millions
        "Full Pay Restoration": [46.30] * (num_years + 1)  # Assuming 46.30% is full pay restoration
    }, index=range(num_years + 1))
    st.line_chart(curve_data)
    st.caption("Note: Cumulative Cost is shown in millions of pounds")

if __name__ == "__main__":
    main()