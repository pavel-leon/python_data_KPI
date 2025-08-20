
import pandas as pd
import re
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency
import os

# ---------------------- Module 1: Load data ----------------------

def load_data(filepath):
    df = pd.read_csv(filepath)
    for col in ['opened_at', 'sys_created_at', 'sys_updated_at', 'resolved_at', 'closed_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
    return df

# ---------------------- Module 2: Clean data ----------------------

def clean_data(df):
    df = df[df['incident_state'].apply(lambda x: isinstance(x, str))]
    df = df.dropna(subset=['opened_at', 'sys_created_at'])
    df = df[df['assignment_group'].apply(lambda x: isinstance(x, str) and re.fullmatch(r'Group \d+', x) is not None)]
    df = df[df['category'].apply(lambda x: isinstance(x, str) and re.fullmatch(r'Category \d+', x) is not None)]
    return df

# ---------------------- Module 3: Calculate KPIs ----------------------

def extract_impact_number(impact_value):
    try:
        return int(str(impact_value).split('-')[0].strip())
    except:
        return None

def calculate_kpis(df):
    df['impact_level'] = df['impact'].apply(extract_impact_number)
    df['react_time'] = (df['sys_created_at'] - df['opened_at']).dt.total_seconds() / 60

    def check_react(row):
        if pd.isna(row['react_time']) or pd.isna(row['impact_level']):
            return None
        limits = {1: 5, 2: 10, 3: 15, 4: 30}
        return row['react_time'] <= limits.get(row['impact_level'], float('inf'))

    df['kpi_react_time'] = df.apply(check_react, axis=1)
    df['kpi_reassignments'] = df['reassignment_count'].apply(lambda x: x <= 5 if pd.notna(x) else None)
    df['kpi_sla'] = df['made_sla'].apply(lambda x: x is True)
    return df

# ---------------------- Module 4: Report builder ----------------------

def report_kpi(df_filtered, kpi_column, kpi_name):
    grouped = df_filtered.groupby('assignment_group').agg({kpi_column: lambda x: x.mean() * 100})
    filtered = grouped.sort_values(by=kpi_column).head(10)

    print(f"\nReport: {kpi_name} (10 groups with lowest values):")
    print(filtered.rename(columns={kpi_column: kpi_name}))

    plt.figure(figsize=(10, 6))
    filtered.rename(columns={kpi_column: kpi_name}).plot(kind='bar', legend=False)
    plt.ylabel('Percentage of KPI')
    plt.title(kpi_name)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show(block=True)

def top10_categories(df_filtered):
    top10 = df_filtered['category'].value_counts().head(10)
    print("\nTop 10 categories of incidents:")
    print(top10)

    plt.figure(figsize=(10, 6))
    top10.plot(kind='bar')
    plt.ylabel('Amount of incidents')
    plt.title('TOP-10 categories')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show(block=True)

# ---------------------- Module 5: Analytics ----------------------

def analyze_category_priority_relation(df):
    df['is_critical'] = df['priority'] == "1 - Critical"
    contingency = pd.crosstab(df['category'], df['is_critical'])
    chi2, p, dof, expected = chi2_contingency(contingency)

    print("\nCategory vs Critical incidents dependency analytics:")
    print(f"Chi2 stat: {chi2:.4f}")
    print(f"p-value: {p:.4f}")
    print(f"Dof: {dof}")
    if p < 0.05:
        print("Yes, there is dependency between category and critical incidents (p < 0.05).")
    else:
        print("No, there is no dependency (p >= 0.05).")

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
    os.system('cls' if os.name == 'nt' else 'clear')

# ---------------------- Module 6: Menus ----------------------

def show_main_menu():
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
    clear_screen()
    print("\nKPI reports:")
    print("1. React Time KPI")
    print("2. Reassignments KPI")
    print("3. SLA KPI")
    print("4. Back")

def show_analytics_menu():
    clear_screen()
    print("\nAnalytics:")
    print("1. Dependency incidents vs categories (Chi²)")
    print("2. Back")

def input_date(prompt):
    while True:
        try:
            return pd.to_datetime(input(prompt))
        except:
            print("Wrong input. Enter date in format (YYYY-MM-DD).")

def show_available_period(df):
    print("\nAvailable period (using sys_created_at field):")
    print(f"From {df['sys_created_at'].min().date()} to {df['sys_created_at'].max().date()}")

# ---------------------- Module 7: Read README ----------------------

def show_readme():
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
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, "incident_event_log.csv")
    df = load_data(filepath)
    df = clean_data(df)
    df = calculate_kpis(df)

    df_filtered = None

    while True:
        show_main_menu()
        choice = input("Select option: ").strip()

        if choice == "1":
            show_available_period(df)
            input("\nPress Enter to return to main menu...")

        elif choice == "2":
            start_date = input_date("Starting date (YYYY-MM-DD): ")
            end_date = input_date("End date (YYYY-MM-DD): ")
            df_filtered = df[(df['opened_at'] >= start_date) & (df['opened_at'] <= end_date)]
            print(f"\nSelected period: {start_date.date()} - {end_date.date()}, total records: {len(df_filtered)}")
            input("\nPress Enter to return to main menu...")

        elif choice == "3":
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
            if df_filtered is None:
                print("Error: Please set report parameters first (option 2).")
            else:
                top10_categories(df_filtered)
            input("\nPress Enter to return to main menu...")

        elif choice == "5":
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
            show_readme()
            input("\nPress Enter to return to main menu...")

        elif choice == "0":
            print("Exiting...")
            break

        else:
            print("Wrong choice.")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()