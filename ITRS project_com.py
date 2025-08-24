import pandas as pd
import re
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
import os

# ---------------------- Module 1: Load data ----------------------

def load_data(filepath):
    """
    Loads data from a CSV file into a Pandas DataFrame and converts date columns to datetime objects.

    Args:
        filepath (str): The path to the CSV file.

    Returns:
        pd.DataFrame: The DataFrame containing the loaded data with date columns converted to datetime objects.
    """
    df = pd.read_csv(filepath)
    # Iterate over date columns and convert them to datetime objects
    for col in ['opened_at', 'sys_created_at', 'sys_updated_at', 'resolved_at', 'closed_at']:
        if col in df.columns:
            # Convert column to datetime, inferring format and handling errors by coercing invalid dates to NaT
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
    return df

# ---------------------- Module 2: Clean data ----------------------

def clean_data(df):
    """
    Cleans the DataFrame by removing rows with invalid or missing data.

    Args:
        df (pd.DataFrame): The DataFrame to be cleaned.

    Returns:
        pd.DataFrame: The cleaned DataFrame.
    """
    # Remove rows where 'incident_state' is not a string
    df = df[df['incident_state'].apply(lambda x: isinstance(x, str))]
    # Remove rows where 'opened_at' or 'sys_created_at' is missing
    df = df.dropna(subset=['opened_at', 'sys_created_at'])
    # Remove rows where 'assignment_group' does not match the expected format ('Group X')
    df = df[df['assignment_group'].apply(lambda x: isinstance(x, str) and re.fullmatch(r'Group \d+', x) is not None)]
    # Remove rows where 'category' does not match the expected format ('Category X')
    df = df[df['category'].apply(lambda x: isinstance(x, str) and re.fullmatch(r'Category \d+', x) is not None)]
    return df

# ---------------------- Module 3: Calculate KPIs ----------------------

def extract_impact_number(impact_value):
    """
    Extracts the numerical impact level from the 'impact' column.

    Args:
        impact_value (str): The value from the 'impact' column.

    Returns:
        int: The extracted impact level as an integer, or None if extraction fails.
    """
    try:
        # Split the string, extract the first part, and convert to integer
        return int(str(impact_value).split('-')[0].strip())
    except:
        # Return None if any error occurs during extraction or conversion
        return None

def calculate_kpis(df):
    """
    Calculates Key Performance Indicators (KPIs) based on the incident data.

    Args:
        df (pd.DataFrame): The DataFrame containing incident data.

    Returns:
        pd.DataFrame: The DataFrame with added KPI columns ('impact_level', 'react_time', 'kpi_react_time', 'kpi_reassignments', 'kpi_sla').
    """
    # Extract the impact level from the 'impact' column
    df['impact_level'] = df['impact'].apply(extract_impact_number)
    # Calculate the reaction time in minutes
    df['react_time'] = (df['sys_created_at'] - df['opened_at']).dt.total_seconds() / 60

    def check_react(row):
        """
        Checks if the reaction time is within the acceptable limit based on the impact level.

        Args:
            row (pd.Series): A row of the DataFrame.

        Returns:
            bool: True if the reaction time is within the limit, False otherwise, or None if data is missing.
        """
        if pd.isna(row['react_time']) or pd.isna(row['impact_level']):
            return None
        # Define the reaction time limits for each impact level
        limits = {1: 5, 2: 10, 3: 15, 4: 30}
        # Check if the reaction time is within the limit for the given impact level
        return row['react_time'] <= limits.get(row['impact_level'], float('inf'))

    # Apply the check_react function to each row to determine if the reaction time KPI is met
    df['kpi_react_time'] = df.apply(check_react, axis=1)
    # Check if the number of reassignments is within the acceptable limit (<= 5)
    df['kpi_reassignments'] = df['reassignment_count'].apply(lambda x: x <= 5 if pd.notna(x) else None)
    # Check if the SLA was made
    df['kpi_sla'] = df['made_sla'].apply(lambda x: x is True)
    return df

# ---------------------- Module 4: Report builder ----------------------

def report_kpi(df_filtered, kpi_column, kpi_name):
    """
    Generates a report of KPI performance by assignment group and displays it as a bar chart.

    Args:
        df_filtered (pd.DataFrame): The DataFrame containing filtered incident data.
        kpi_column (str): The name of the KPI column to report on.
        kpi_name (str): The name of the KPI for the report title and labels.
    """
    # Group by assignment group and calculate the mean KPI value (as a percentage)
    grouped = df_filtered.groupby('assignment_group').agg({kpi_column: lambda x: x.mean() * 100})
    # Sort and select the top 10 groups with the lowest KPI values
    filtered = grouped.sort_values(by=kpi_column).head(10)

    print(f"\nReport: {kpi_name} (10 groups with lowest values):")
    print(filtered.rename(columns={kpi_column: kpi_name}))

    # Create a bar chart of the KPI performance
    plt.figure(figsize=(10, 6))
    filtered.rename(columns={kpi_column: kpi_name}).plot(kind='bar', legend=False)
    plt.ylabel('Percentage of KPI')
    plt.title(kpi_name)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show(block=True)

def top10_categories(df_filtered):
    """
    Generates a report of the top 10 incident categories and displays it as a bar chart.

    Args:
        df_filtered (pd.DataFrame): The DataFrame containing filtered incident data.
    """
    # Count the occurrences of each category and select the top 10
    top10 = df_filtered['category'].value_counts().head(10)
    print("\nTop 10 categories of incidents:")
    print(top10)

    # Create a bar chart of the top 10 categories
    plt.figure(figsize=(10, 6))
    top10.plot(kind='bar')
    plt.ylabel('Amount of incidents')
    plt.title('TOP-10 categories')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show(block=True)

# ---------------------- Module 5: Analytics ----------------------

def analyze_category_priority_relation(df):
    """
    Analyzes the relationship between incident categories and critical priority using a Chi-squared test.

    Args:
        df (pd.DataFrame): The DataFrame containing incident data.
    """
    # Create a binary column indicating whether the incident is critical
    df['is_critical'] = df['priority'] == "1 - Critical"
    # Create a contingency table of categories and critical incidents
    contingency = pd.crosstab(df['category'], df['is_critical'])
    # Perform the Chi-squared test
    chi2, p, dof, expected = chi2_contingency(contingency)

    print("\nCategory vs Critical incidents dependency analytics:")
    print(f"Chi2 stat: {chi2:.4f}")
    print(f"p-value: {p:.4f}")
    print(f"Dof: {dof}")
    # Check if the p-value is less than the significance level (0.05)
    if p < 0.05:
        print("Yes, there is dependency between category and critical incidents (p < 0.05).")
    else:
        print("No, there is no dependency (p >= 0.05).")

    # Create a bar chart of critical incidents by category
    critical_counts = df[df['is_critical']]['category'].value_counts()
    if not critical_counts.empty:
        plt.figure(figsize=(10, 6))
        critical_counts.plot(kind='bar', color='skyblue')
        plt.ylabel('Amount of critical incidents')
        plt.title('Critical incidents by categories')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show(block=True)

# ---------------------- Utility: Clear screen ----------------------

def clear_screen():
    """
    Clears the console screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

# ---------------------- Module 6: Menus ----------------------

def show_main_menu():
    """
    Displays the main menu options.
    """
    clear_screen()
    print("--- Main menu ---")
    print("1. Show available date options")
    print("2. Report parameters")
    print("3. KPI Reports")
    print("4. Build TOP-10 categories report")
    print("5. Analytical reports")
    print("6. README")
    print("0. Exit")
    print("Incident Report System (C)2025 v.1.0.3")

def show_kpi_menu():
    """
    Displays the KPI report menu options.
    """
    clear_screen()
    print("\nKPI reports:")
    print("1. React Time KPI")
    print("2. Reassignments KPI")
    print("3. SLA KPI")
    print("4. Back")

def show_analytics_menu():
    """
    Displays the analytics menu options.
    """
    clear_screen()
    print("\nAnalytics:")
    print("1. Dependency incidents vs categories (Chi²)")
    print("2. Back")

def input_date(prompt):
    """
    Prompts the user to enter a date and validates the input.

    Args:
        prompt (str): The prompt message to display to the user.

    Returns:
        pd.Timestamp: The entered date as a Timestamp object.
    """
    while True:
        try:
            return pd.to_datetime(input(prompt))
        except:
            print("Wrong input. Enter date in format (YYYY-MM-DD).")

def show_available_period(df):
    """
    Displays the available date range in the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame containing incident data.
    """
    print("\nAvailable period (using sys_created_at field):")
    print(f"From {df['sys_created_at'].min().date()} to {df['sys_created_at'].max().date()}")

# ---------------------- Module 7: Read README ----------------------

def show_readme():
    """
    Displays the content of the README.txt file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    readme_path = os.path.join(script_dir, "README.txt")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            print("\nREADME content:\n")
            print(f.read())
    else:
        print("README.txt file not found in script directory.")

# ---------------------- MAIN ----------------------

def main():
    """
    Main function to run the incident reporting system.
    """
    # Determine the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the file path to the data file
    filepath = os.path.join(script_dir, "incident_event_log.csv")
    # Load data
    df = load_data(filepath)
    # Clean data
    df = clean_data(df)
    # Calculate KPIs
    df = calculate_kpis(df)

    # Initialize filtered DataFrame to None
    df_filtered = None

    # Main loop
    while True:
        # Show the main menu
        show_main_menu()
        # Get user choice
        choice = input("Select option: ").strip()

        # Handle user choices
        if choice == "1":
            # Show available date period
            show_available_period(df)
            input("\nPress Enter to return to main menu...")

        elif choice == "2":
            # Input start and end dates for filtering
            start_date = input_date("Starting date (YYYY-MM-DD): ")
            end_date = input_date("End date (YYYY-MM-DD): ")
            # Filter the DataFrame based on the selected date range
            df_filtered = df[(df['opened_at'] >= start_date) & (df['opened_at'] <= end_date)]
            print(f"\nSelected period: {start_date.date()} - {end_date.date()}, total records: {len(df_filtered)}")
            input("\nPress Enter to return to main menu...")

        elif choice == "3":
            # KPI Reports menu
            if df_filtered is None:
                print("Error: Please set report parameters first (option 2).")
                input("\nPress Enter to continue...")
                continue
            while True:
                show_kpi_menu()
                kpi_choice = input("Choose KPI: ").strip()
                if kpi_choice == "1":
                    report_kpi(df_filtered, 'kpi_react_time', 'React Time KPI')
                    input("\nPress Enter to continue...")
                elif kpi_choice == "2":
                    report_kpi(df_filtered, 'kpi_reassignments', 'Reassignments KPI')
                    input("\nPress Enter to continue...")
                elif kpi_choice == "3":
                    report_kpi(df_filtered, 'kpi_sla', 'SLA KPI')
                    input("\nPress Enter to continue...")
                elif kpi_choice == "4":
                    break
                else:
                    print("Wrong selection.")
                    input("\nPress Enter to continue...")

        elif choice == "4":
            # Build TOP-10 categories report
            if df_filtered is None:
                print("Error: Please set report parameters first (option 2).")
            else:
                top10_categories(df_filtered)
            input("\nPress Enter to return to main menu...")

        elif choice == "5":
            # Analytical reports menu
            while True:
                show_analytics_menu()
                a_choice = input("Select option: ").strip()
                if a_choice == "1":
                    analyze_category_priority_relation(df)
                    input("\nPress Enter to continue...")
                elif a_choice == "2":
                    break
                else:
                    print("Wrong choice.")
                    input("\nPress Enter to continue...")

        elif choice == "6":
            # Show README
            show_readme()
            input("\nPress Enter to return to main menu...")

        elif choice == "0":
            # Exit the program
            print("Exiting...")
            break

        else:
            # Handle wrong choices
            print("Wrong choice.")
            input("\nPress Enter to continue...")

# Check if the script is run as the main program
if __name__ == "__main__":
    # Run the main function
    main()
