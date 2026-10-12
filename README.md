# ABC–XYZ Inventory Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()

An interactive, production-grade inventory analytics platform developed in Python and Streamlit for the subject **Python for Data Science**.

The dashboard delivers dual-criteria SKU segmentation:
- **ABC Analysis (Value-Based / Pareto):** Identifies top revenue drivers using annual sales contribution ($80\% / 15\% / 5\%$).
- **XYZ Analysis (Demand Predictability):** Classifies products by demand stability using the Coefficient of Variation ($\text{CV} = \sigma / \mu$) across 12 monthly cycles.

---

## Key Features

- **Side-Panel-Free Modern Interface:** Streamlined tabbed layout (`st.tabs`) maximizing horizontal real estate with zero sidebar clutter.
- **Automated Data Quality Audit:** Detects duplicates, clips negative figures, imputes missing demand, and reconciles derived totals.
- **Parametric Threshold Modeling:** Real-time adjustable sliders for ABC cutoffs and XYZ CV boundaries via a collapsible top settings panel.
- **Rich Visual Analytics:** Interactive Plotly charts (Dual-axis ABC Pareto curve, $3 \times 3$ contingency heatmap, CV histogram, demand trends).
- **Prescriptive Inventory Policies:** Rule-based inventory recommendations tailored for each matrix cell ($AX$ through $CZ$).
- **Multi-Filter Explorer & CSV Exports:** Instant search, multi-criteria filtering, and one-click data downloads.
- **Automated Test Suite:** Built-in unit tests verifying pipeline integrity and classification accuracy.

---

## Architecture & Tabs

1. **📋 Overview:** High-level portfolio KPIs (products, categories, total units, sales value), project background, methodology, and dataset preview.
2. **🧹 Data Cleaning:** Data audit checks, handling missing/negative values, duplicate removal, before/after previews, and cleaned CSV export.
3. **📊 Category Performance:** Category revenue and volume distribution bar charts, monthly demand trends, and top 10 products.
4. **🧮 ABC–XYZ Analysis:** Pareto analysis curve, CV distribution histogram, $3 \times 3$ product count matrix heatmap, product table, and inventory policy recommendations.
5. **⬇️ Explore & Download:** Dynamic search (by ID, Name, Category), multi-select filters (ABC class, XYZ class, Category), and CSV exports.

---

## Modular Code Architecture

The codebase follows a modular design pattern for easy presentation and code review:
- **[`app.py`](app.py):** Main application orchestrator managing layout, top configuration expander, and tab routing.
- **[`data_cleaning.py`](data_cleaning.py):** Ingestion (`load_data`), 8-step cleaning pipeline (`clean_data`), audit reporting, and Data Cleaning tab renderer.
- **[`category_performance.py`](category_performance.py):** Category business metrics (`compute_category_summary`), trend tracking (`compute_monthly_trend`), and Category Performance tab renderer.
- **[`abc_xyz_analysis.py`](abc_xyz_analysis.py):** ABC Pareto rankings, XYZ CV calculation (`classify_abc_xyz`), $3 \times 3$ matrix (`compute_matrix`), action recommendation mapper (`generate_action_recommendations`), and ABC-XYZ tab renderer.
- **[`data_utils.py`](data_utils.py):** Backward-compatible re-exports for existing imports and scripts.
- **[`tests/test_analytics.py`](tests/test_analytics.py):** Automated unit tests verifying data integrity, aggregations, and classification math.

---

## Project Structure

```text
├── .streamlit/
│   └── config.toml                # Streamlit UI configuration (sidebar disabled)
├── tests/
│   └── test_analytics.py          # Automated unit test suite (unittest)
├── abc_xyz_dataset.csv            # Default inventory dataset (1,000 SKUs)
├── ACADEMIC_REPORT.md             # Formal academic project report
├── abc_xyz_analysis.py            # ABC-XYZ classification engine & visualization module
├── app.py                         # Main orchestrator dashboard with tab navigation
├── category_performance.py        # Category performance analytics & visualization module
├── data_cleaning.py               # Data loading, validation, cleaning & audit module
├── data_utils.py                  # Backward-compatible utility re-exports
├── FORMULAS_AND_CALCULATIONS.txt  # Mathematical & graphical formulas reference
├── LICENSE                        # MIT Open-Source License
├── README.md                      # Project documentation and setup guide
└── requirements.txt               # Dependencies (streamlit, pandas, numpy, plotly)
```

---

## Quickstart & Installation (Windows / VS Code)

### 1. Clone or Open the Project
Open terminal in the project directory:
```bash
cd D:\ABC_XYZ_Dashboard
```

### 2. Create and Activate Virtual Environment
```bat
python -m venv venv
.\venv\Scripts\activate.bat
```

### 3. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Run Automated Tests
```bash
python -m unittest discover tests
```

### 5. Launch the Dashboard
```bash
python -m streamlit run app.py
```

---

## Dataset Schema

The input CSV requires the following columns:
| Column | Type | Description |
| :--- | :--- | :--- |
| `Item_ID` | String | Unique product identifier (e.g., `ITM_001`) |
| `Item_Name` | String | Commercial product name |
| `Category` | String | Product category |
| `Jan_Demand` .. `Dec_Demand` | Numeric | Monthly demand figures across 12 consecutive months |
| `Total_Annual_Units` | Numeric | Annual units demanded (reconciled as $\sum D_m$) |
| `Price_Per_Unit` | Numeric | Unit price in USD ($) |
| `Total_Sales_Value` | Numeric | Total annual revenue (reconciled as $\text{Units} \times \text{Price}$) |

---

## Mathematical Methodology Summary

- **ABC Classification:**
  - Descending sort by `Total_Sales_Value`.
  - Cumulative value share: $C_k = \sum_{i=1}^k \frac{V_i}{V_{\text{total}}}$.
  - Default cutoffs: **A** ($\le 80\%$), **B** ($80\% - 95\%$), **C** ($> 95\%$).
- **XYZ Classification:**
  - Mean monthly demand: $\mu = \frac{1}{12}\sum_{m=1}^{12} D_m$.
  - Sample standard deviation ($ddof=1$): $\sigma = \sqrt{\frac{1}{11}\sum_{m=1}^{12}(D_m - \mu)^2}$.
  - Coefficient of Variation: $\text{CV} = \sigma / \mu$.
  - Default cutoffs: **X** ($\text{CV} \le 0.50$), **Y** ($0.50 < \text{CV} \le 1.00$), **Z** ($\text{CV} > 1.00$), **N/A** ($\mu = 0$).

For complete mathematical derivations and visualization coordinate algorithms, refer to [**`FORMULAS_AND_CALCULATIONS.txt`**](FORMULAS_AND_CALCULATIONS.txt).

---

## License

This project is licensed under the [MIT License](LICENSE).
