"""
Pay Erosion Calculator - Detailed Year-by-Year Analysis
This script calculates and displays detailed pay erosion analysis for all nodal points
"""

# Constants - same as in main.py
NODAL_POINTS = [
    ("Nodal 1", 36616, 38831),  # Current pay, Offered pay
    ("Nodal 2", 42008, 44439),  # Current pay, Offered pay
    ("Nodal 3", 49909, 52656),  # Current pay, Offered pay
    ("Nodal 4", 61825, 65048),  # Current pay, Offered pay
    ("Nodal 5", 70425, 73992)   # Current pay, Offered pay
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
    }
}

# Historical data - same as in main.py
def get_pay_data():
    return [
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
        {"year": "2024/2025", "pay_award": None, "rpi": 0.045, "cpi": 0.035, "cpih": 0.041}  # Will use nodal-specific values
    ]

def calculate_fpr_detailed(nodal_point, inflation_type="CPI", start_year="2008/2009", end_year="2024/2025", output_file=None):
    """
    Calculate FPR with detailed year-by-year breakdown
    """
    name, current_pay, _ = nodal_point
    pay_data = get_pay_data()
    
    # Set inflation key
    if inflation_type == "RPI":
        inflation_key = "rpi"
    elif inflation_type == "CPI":
        inflation_key = "cpi"
    else:  # CPIH
        inflation_key = "cpih"
    
    # Update pay awards for nodal-specific years
    for i, data in enumerate(pay_data):
        if data["year"] == "2023/2024":
            pay_data[i]["pay_award"] = NODAL_SPECIFIC_PAY_AWARDS["2023/2024"].get(name, 0.0371)
        elif data["year"] == "2024/2025":
            pay_data[i]["pay_award"] = NODAL_SPECIFIC_PAY_AWARDS["2024/2025"].get(name, 0.0820)
    
    # Find start and end indices
    start_index = next((i for i, data in enumerate(pay_data) if data["year"] == start_year), 0)
    end_index = next((i for i, data in enumerate(pay_data) if data["year"] == end_year), len(pay_data) - 1)
    
    output_file.write(f"-------------------- {name} (Current Pay: £{current_pay:,}) --------------------\n")
    output_file.write(f"\nCalculating FPR for {name} using {inflation_type}\n")
    output_file.write(f"Period: {start_year} to {end_year}\n")
    output_file.write("=" * 84 + "\n")
    output_file.write(f"{'Year':<13} {'Pay Award':<12} {inflation_type:<12} {'Real Change':<13} {'Cumulative':<12}\n")
    output_file.write("=" * 84 + "\n")
    
    cumulative_effect = 1.0
    
    for i in range(start_index, end_index + 1):
        data = pay_data[i]
        year = data["year"]
        pay_award = data["pay_award"]
        inflation_rate = data[inflation_key]
        
        if year == start_year:
            # Baseline year - skip calculation
            output_file.write(f"{year:<13} {pay_award*100:>8.1f}% {inflation_rate*100:>8.1f}%      SKIPPED      {cumulative_effect:>10.6f}\n")
            continue
        
        if inflation_rate == 0.0 or inflation_rate is None:
            continue
        
        # Calculate real terms change
        real_terms_change = ((1 + pay_award) / (1 + inflation_rate)) - 1
        cumulative_effect *= (1 + real_terms_change)
        
        output_file.write(f"{year:<13} {pay_award*100:>8.1f}% {inflation_rate*100:>8.1f}% {real_terms_change*100:>11.2f}% {cumulative_effect:>10.6f}\n")
    
    # Calculate final results
    pay_erosion = (1 - cumulative_effect) * 100
    fpr_percentage = (1/cumulative_effect - 1) * 100  # Correct calculation for restoration
    purchasing_power = cumulative_effect * 100
    pay_needed_for_fpr = current_pay * (1 + fpr_percentage / 100)
    current_shortfall = pay_needed_for_fpr - current_pay
    
    output_file.write(f"\nRESULTS:\n")
    output_file.write(f"FPR Required: {fpr_percentage:.2f}%\n")
    output_file.write(f"Pay Erosion: {pay_erosion:.2f}%\n")
    output_file.write("\n")
    
    return {
        "cumulative_effect": cumulative_effect,
        "fpr_percentage": fpr_percentage,
        "pay_erosion": pay_erosion,
        "purchasing_power": purchasing_power,
        "pay_needed_for_fpr": pay_needed_for_fpr,
        "current_shortfall": current_shortfall
    }

def main():
    """
    Main function to run the pay erosion analysis and generate 3 files
    """
    inflation_types = ["RPI", "CPI", "CPIH"]
    
    for inflation_type in inflation_types:
        filename = f"{inflation_type}_Calculations.txt"
        
        with open(filename, 'w') as file:
            # Write header
            file.write("BMA [C O N F I D E N T I A L ]\n")
            file.write("\n")
            file.write("=" * 50 + f" {inflation_type} CALCULATIONS " + "=" * 50 + "\n")
            file.write("\n")
            
            # Calculate for each nodal point and collect results
            results = []
            for nodal_point in NODAL_POINTS:
                result = calculate_fpr_detailed(nodal_point, inflation_type, output_file=file)
                results.append(result)
            
            # Calculate averages
            avg_pay_erosion = sum(result['pay_erosion'] for result in results) / len(results)
            avg_fpr_required = sum(result['fpr_percentage'] for result in results) / len(results)
            
            # Write average summary
            file.write("=" * 80 + "\n")
            file.write("AVERAGE ACROSS ALL NODAL POINTS\n")
            file.write("=" * 80 + "\n")
            file.write(f"Average Pay Erosion: {avg_pay_erosion:.2f}%\n")
            file.write(f"Average FPR Required: {avg_fpr_required:.2f}%\n")
            file.write("\n")
        
        print(f"Generated {filename}")
    
    print("All calculation files generated successfully!")

if __name__ == "__main__":
    main()