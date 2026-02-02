# Ethiopia Financial Inclusion Forecasting System

📋 Project Overview

A comprehensive forecasting system for Ethiopia's financial inclusion indicators, focusing on account ownership (Access)

 and digital payment adoption (Usage). This project addresses Ethiopia's unique challenge: despite massive mobile money 

expansion (65M+ accounts), account ownership grew only +3pp from 2021-2024.

🎯 Business Need

Selam Analytics has been engaged by a consortium including development finance institutions, mobile money operators, and

the National Bank of Ethiopia to:

Understand what drives financial inclusion in Ethiopia

Model how events like product launches, policy changes, and infrastructure investments affect inclusion outcomes

Forecast 2025-2027 trajectories for Access and Usage indicators

📊 Core Indicators (Global Findex Framework)

Access (Account Ownership)

*"The share of adults (age 15+) who report having an account at a bank or another type of financial institution or
report personally using a mobile money service."*

Ethiopia's Trajectory:

Year	Account Ownership	Change

2011	14%	—

2014	22%	+8pp

2017	35%	+13pp

2021	46%	+11pp

2024	49%	+3pp
Usage (Digital Payments)

"The share of adults who report using mobile money, cards, or mobile phones to make payments in the past 12 months."

Ethiopia 2024 Indicators:

Mobile money account ownership: 9.45%

Made/received digital payment: ~35%

Used account for wages: ~15%

🏗️ Project Structure

text

ethiopia-fi-forecast/

├── .github/workflows/

│   └── unittests.yml                    # CI/CD pipeline

├── data/

│   ├── raw/                             # Original datasets

│   │   ├── ethiopia_fi_unified_data.xlsx

│   │   ├── reference_codes.xlsx

│   │   └── Additional Data Points Guide.xlsx

│   └── processed/                       # Analysis-ready data

├── notebooks/

│   ├── data_enrichment.ipynb        # Task 1: Enrichment workflow

│   ├── eda_analysis.ipynb          # Task 2: Exploratory analysis

├── src/

│   ├── data_loader.py                  # Load and validate data

│   ├── data_enricher.py                # Add new observations/events

│   ├── schema_validator.py             # Validate against schema

│   ├── visualization.py                # Plotting utilities

│   └── utils.py                        # Helper functions

├── dashboard/

│   └── app.py                         # Interactive dashboard

├── tests/

│   ├── test_data_loader.py

│   ├── test_enricher.py

│   └── __init__.py

├── models/                             # Forecasting models

├── reports/

│   ├── data_enrichment_log.md         # Task 1 documentation

│   └── figures/                       # Visualizations

├── requirements.txt

├── README.md

└── .gitignore

📁 Dataset Schema

ethiopia_fi_unified_data.xlsx

Sheet 1: ethiopia_fi_unified_data - Core records:

record_type: observation (30), event (10), impact_link (14), target (3)

Key columns: pillar, indicator, indicator_code, value_numeric, observation_date

Observation: Measured values from surveys, reports, operators

Event: Policies, product launches, market entries, milestones

Impact_link: Modeled relationships between events and indicators via parent_id

Target: Official policy goals (e.g., NFIS-II targets)

Sheet 2: Impact_sheet - Additional impact relationships

reference_codes.xlsx

Valid values for all categorical fields (record_type, pillar, source_type, confidence, etc.)

🚀 Installation & Setup

1. Clone Repository

git clone https://github.com/Saronzeleke/Ethiopia-fi-forecast.git

cd ethiopia-fi-forecast

2. Create Virtual Environment

python -m venv venv

# Windows

venv\Scripts\activate

# Mac/Linux

source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

4. Convert Excel to CSV (Required)

bash

python src/convert_excel_to_csv.py

This creates:

data/raw/ethiopia_fi_unified_data.csv

data/raw/reference_codes.csv

data/raw/guide_*.csv (optional reference files)

📊 Task 1: Data Exploration and Enrichment

Objective

Understand the starter dataset and enrich it with additional data useful for forecasting.

Steps to Complete:

# Create branch for Task 1

git checkout -b task-1

# Run data exploration notebook

jupyter notebook notebooks/data_exploration.ipynb

# Execute data enrichment

python -c "
from src.data_loader import DataLoader
from src.data_enricher import DataEnricher

loader = DataLoader()
data_dict = loader.load_data('data/raw/ethiopia_fi_unified_data.csv', 
                            'data/raw/reference_codes.csv')

enricher = DataEnricher(data_dict['data'])
enricher.add_findex_microdata()
enricher.add_nbe_infrastructure_data()
enricher.add_gsma_mobile_data()
enricher.add_policy_events()
enricher.add_impact_links()

enriched = enricher.get_enriched_data()
enriched.to_csv('data/processed/enriched_data.csv', index=False)
print(f'✅ Enriched data saved with {len(enriched)} records')
"

# Generate enrichment log

python src/generate_enrichment_log.py

Deliverables for Task 1:

✅ Updated dataset with 25+ new records (observations, events, impact_links)

✅ reports/data_enrichment_log.md documenting source_url, confidence, rationale

✅ Understanding of unified schema and impact_link connections

📈 Task 2: Exploratory Data Analysis

Objective

Analyze patterns and factors influencing financial inclusion in Ethiopia.

Steps to Complete:

# Update from main and create new branch

git checkout main

git pull origin main

git checkout -b task-2

# Run EDA notebook

jupyter notebook notebooks/03_eda_analysis.ipynb

# Or run via script

python src/run_eda.py

EDA Components:

Dataset Overview: Record types, pillars, source types

Access Analysis: Account ownership trajectory (2011-2024), gender gap, 2021-2024 slowdown investigation

Usage Analysis: Mobile money penetration, digital payment adoption, P2P/ATM crossover

Infrastructure: 4G coverage, mobile penetration relationships

Event Timeline: Overlay events on indicator trends

Correlation Analysis: Between different indicators

Data Quality Assessment: Limitations and gaps

Deliverables for Task 2:

✅ EDA notebook with comprehensive visualizations

✅ 5+ key insights with supporting evidence

✅ Data quality assessment documenting limitations

✅ Event timeline visualization

🔑 Key Insights (From Preliminary Analysis)

1. Post-2021 Growth Deceleration

Account ownership grew only +3pp (2021-2024) vs. +11pp (2017-2021) despite 65M+ mobile money accounts.

2. Mobile Money-Account Ownership Mismatch

54.84M Telebirr users ≠ 49% account ownership → high dormancy/duplication.

3. Persistent Gender Gap

~20pp gap in 2021, estimated ~18pp in 2024 despite interventions.

4. P2P Dominance

128.3M P2P transactions vs. 119.3M ATM transactions (FY2024/25) → digital > cash.

5. Infrastructure-Usage Decoupling

4G coverage grew 89% (37.5% → 70.8%) but digital payment adoption grew modestly.

📋 Repository Best Practices

Branch Strategy

# Feature branches

git checkout -b task-1

git checkout -b task-2

# Pull request workflow

git push origin task-1

# Create PR on GitHub → Review → Merge to main

Commit Messages

Use descriptive, conventional commits:

text

feat: add gender-disaggregated Findex data
fix: correct date parsing in data loader
docs: update enrichment log with sources
analysis: add correlation matrix visualization

File Organization

Raw data in data/raw/

Processed data in data/processed/

Notebooks in notebooks/ with clear numbering

Source code in src/ (modular, reusable)

Tests in tests/ (pytest compatible)

Reports in reports/ (logs, figures)

💻 Code Best Practices

Modular Design

# src/data_loader.py

class DataLoader:
    """Single responsibility: load and validate data"""
    
# src/data_enricher.py 

class DataEnricher:
    """Single responsibility: add new data following schema"""
    
# src/visualization.py

class FinancialInclusionVisualizer:
    """Single responsibility: create plots and charts"""
Error Handling
python
try:
    data = pd.read_csv(path, parse_dates=dates)
except FileNotFoundError:
    logger.error(f"Dataset not found: {path}")
    raise
except ValueError as e:
    logger.error(f"Schema validation failed: {e}")
    raise
Testing


# Run tests

pytest tests/ -v

# Test coverage

pytest --cov=src tests/

🎯 Success Criteria Checklist

Task 1: Data Exploration and Enrichment (6 pts)

Successfully load CSV files (after conversion)

Demonstrate clear understanding of unified schema

Correctly connect impact_links to events via parent_id

Enrich dataset with new observations/events adhering to schema

Provide detailed data_enrichment_log.md

Task 2: Exploratory Data Analysis (6 pts)

EDA notebook with comprehensive visualizations

5+ well-supported key insights

Thorough data quality assessment

Event timeline visualization overlaying events on trends

Repository Best Practices (4 pts)

Clean repository with proper folder structure

Meaningful commit messages and GitHub branches with PRs

Logical file organization

Complete requirements.txt and README.md

Code Best Practices (3 pts)

Modular code with clear function definitions

Effective error handling

Readability and documentation within code

📞 Support & Resources

Data Sources

World Bank Findex Database - Primary demand-side data

National Bank of Ethiopia - Supply-side metrics, regulations

GSMA Mobile Economy Reports - Mobile penetration, 4G coverage

EthSwitch - Transaction volumes, P2P/ATM metrics

IMF Financial Access Survey - Infrastructure density

Key Contacts

Project Lead:Saron Zeleke, Data Scientist at Selam Analytics

Stakeholders: NBE, Mobile Money Operators, Development Partners

Data Sources: World Bank, GSMA, ITU, NBE reports

Next Steps

Complete Task 1 & 2 (current)

Build forecasting models (ARIMA, Prophet with event regressors)

Develop interactive dashboard

Policy simulation and scenario analysis

📄 License

This project is developed by Selam Analytics for the Ethiopia Financial Inclusion Consortium. Data sources are credited 

per their respective licenses.