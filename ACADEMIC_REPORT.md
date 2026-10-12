# Academic Project Report: ABC–XYZ Inventory Analytics Dashboard
**Subject:** Python for Data Science  
**Domain:** Supply Chain Analytics & Inventory Management  
**Application Platform:** Streamlit & Plotly (Python)  
**Dataset:** Multi-Category Retail Inventory (1,000 SKUs)  

---

## Executive Summary / Abstract

In modern supply chain and retail operations, inventory management represents a critical balance between working capital efficiency and service level maintenance. Managing thousands of distinct Stock Keeping Units (SKUs) under homogeneous stocking policies inevitably causes capital lockup in slow-moving items and costly stockouts in high-demand items.

This project implements an end-to-end, interactive data science solution—the **ABC–XYZ Inventory Analytics Dashboard**—developed in Python and deployed via Streamlit. Using empirical demand data across 1,000 SKUs spanning five merchandise categories (Grocery, Apparel, Electronics, Toys, and Home & Kitchen), the system couples value-based Pareto segmentation (**ABC Analysis**) with demand predictability profiling based on the Coefficient of Variation (**XYZ Analysis**). 

The software pipeline enforces an automated data validation and cleaning audit, recalculates derived demand totals to guarantee mathematical consistency, executes real-time multi-criteria classifications with customizable cutoffs, and visualizes multi-dimensional insights across an intuitive, side-panel-free tabbed layout. The analysis reveals that 8.8% of products generate 80% of revenue (Class A), while 93.9% of SKUs exhibit stable demand patterns (Class X), enabling differentiated stocking, ordering, and reviewing strategies across all 9 segments of the ABC–XYZ matrix.

---

## 1. Introduction & Background

### 1.1 The Inventory Control Dilemma
Organizations holding diverse product catalogs face the dual challenges of inventory holding costs and stockout penalties. Traditional one-size-fits-all inventory models (such as uniform reorder points or blanket safety stock days) fail because items differ fundamentally in:
1. **Financial Impact:** A small fraction of items accounts for the vast majority of cash flow and revenue.
2. **Demand Uncertainty:** Some products have steady, predictable consumption month-over-month, whereas others have intermittent, erratic, or seasonal demand.

### 1.2 The ABC Classification Framework (Pareto Analysis)
Derived from Vilfredo Pareto’s 80/20 principle, ABC analysis classifies inventory items based on their annual consumption value:
- **Class A (High Value):** Top ~70–80% of total annual sales value, typically representing 10–20% of inventory items. Requires rigorous control, accurate forecasting, and frequent cycle counting.
- **Class B (Moderate Value):** The next ~15% of annual sales value, representing ~20–30% of items. Requires moderate oversight and automated replenishment rules.
- **Class C (Low Value):** The bottom ~5% of annual sales value, comprising 50–70% of items. Requires simplified rules, periodic reviews, and bulk ordering to minimize procurement overhead.

### 1.3 The XYZ Classification Framework (Demand Predictability)
While ABC analysis highlights financial importance, it disregards demand variability. XYZ analysis categorizes items by the stability of their consumption history using the **Coefficient of Variation (CV)**:
$$\text{CV} = \frac{\sigma}{\mu}$$
Where $\sigma$ is the sample standard deviation of monthly demand and $\mu$ is the mean monthly demand.
- **Class X (Constant / Stable Demand):** $\text{CV} \le 0.50$. Characterized by high predictability; ideal for automated, Just-In-Time (JIT) or Economic Order Quantity (EOQ) replenishment.
- **Class Y (Variable / Fluctuating Demand):** $0.50 < \text{CV} \le 1.00$. Moderate predictability due to promotional cycles, seasonality, or customer trends; requires safety buffer stocks.
- **Class Z (Erratic / Sporadic Demand):** $\text{CV} > 1.00$. Highly irregular consumption; prone to forecasting error and obsolescence risk; requires manual review or on-demand procurement.

### 1.4 Synthesis: The Integrated ABC–XYZ Matrix
Combining ABC and XYZ classifications generates a $3 \times 3$ matrix (plus handling for zero-demand edge cases) yielding actionable, granular stocking policies. High-revenue, steady items ($AX$) can be automated with minimal buffer, while high-revenue, volatile items ($AZ$) demand executive attention and strict safety margins.

---

## 2. Problem Statement & Project Objectives

### 2.1 Problem Statement
Raw transaction and inventory logs frequently suffer from data anomalies (negative values, unrecorded sales, discrepancies between monthly entries and annual totals). Furthermore, supply chain analysts require an accessible, interactive graphical platform that allows real-time scenario modeling (tuning cutoff thresholds) without requiring manual spreadsheet recalculations or command-line scripting.

### 2.2 Objectives
1. **Automated Data Cleaning & Integrity Auditing:** Detect duplicate entries, impute missing demand data, handle price inconsistencies, and verify that monthly sums match reported annual totals.
2. **Category Performance Analytics:** Evaluate revenue, unit demand, and price dynamics across product categories, including longitudinal 12-month demand trend charting.
3. **Parametric ABC–XYZ Segmentation:** Implement real-time classification algorithms with user-adjustable thresholds ($A\%$, $B\%$, $X_{\text{max}}$, $Y_{\text{max}}$).
4. **Visual Analytics & Strategic Decision Support:** Provide Pareto charts, CV distribution histograms, cross-classification heatmaps, and tailored inventory policy recommendations.
5. **Modern, Responsive User Experience:** Refactor the user interface into an organized tabbed dashboard without side-panel clutter, enabling multi-attribute filtering and raw/processed CSV exports.

---

## 3. Dataset Architecture & Preprocessing

### 3.1 Input Schema
The dataset consists of 1,000 SKUs characterized by 16 features:

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `Item_ID` | String / Alphanumeric | Unique item identifier (e.g., `ITM_001`) |
| `Item_Name` | String | Commercial product name |
| `Category` | Categorical | Merchandise classification (`Grocery`, `Apparel`, `Electronics`, `Toys`, `Home & Kitchen`) |
| `Jan_Demand` to `Dec_Demand` | Numeric (Float/Int) | Monthly unit demand records across 12 consecutive months |
| `Total_Annual_Units` | Numeric | Annual units demanded |
| `Price_Per_Unit` | Numeric | Retail/inventory price per unit (\$) |
| `Total_Sales_Value` | Numeric | Total annual revenue (\$) |

### 3.2 Data Preprocessing & Validation Pipeline (`data_utils.py`)
To ensure robust analytical validity, the raw data undergoes a systematic six-stage cleaning and auditing pipeline:
1. **Header Sanitization & Column Verification:** Leading/trailing whitespace in column headers is stripped, and presence of all 16 mandatory features is confirmed.
2. **Text Normalization:** String fields (`Item_ID`, `Item_Name`, `Category`) are trimmed of extraneous spaces and empty strings converted to missing values (`pd.NA`).
3. **Deduplication:** Full-row duplicate scans ensure SKUs are uniquely represented.
4. **Demand & Price Sanitization:**
   - Missing monthly demand cells are imputed as `0` under the documented operational assumption that missing values indicate zero demand rather than unrecorded transactions.
   - Negative demand values resulting from data entry errors or unadjusted returns are clipped to `0`:
     $$D_{m, \text{clean}} = \max(0, D_m)$$
   - Negative unit prices are identified and imputed to `0`.
5. **Mathematical Reconciliation of Totals:**
   Reported annual totals in commercial datasets frequently disagree with the sum of monthly records due to asynchronous logging. The pipeline enforces mathematical reconciliation:
   $$\text{Total\_Annual\_Units} = \sum_{m=1}^{12} D_m$$
   $$\text{Total\_Sales\_Value} = \text{Total\_Annual\_Units} \times \text{Price\_Per\_Unit}$$
6. **Audit Generation:** A structured dataframe summarizes raw row counts, duplicate drops, missing cell imputations, and reconciliation fixes.

---

## 4. Analytical Methodology & Mathematical Formulations

### 4.1 ABC Value-Based Classification Algorithm
1. **Sorting:** Sort all $N$ items in descending order of $\text{Total\_Sales\_Value}_i$:
   $$\text{Total\_Sales\_Value}_{(1)} \ge \text{Total\_Sales\_Value}_{(2)} \ge \dots \ge \text{Total\_Sales\_Value}_{(N)}$$
2. **Share Computation:**
   $$\text{Sales\_Value\_Share}_i = \frac{\text{Total\_Sales\_Value}_i}{\sum_{j=1}^N \text{Total\_Sales\_Value}_j}$$
3. **Cumulative Distribution:**
   $$\text{Cumulative\_Share}_k = \sum_{i=1}^k \text{Sales\_Value\_Share}_i$$
4. **Boundary Assignment:** Let $P_k = \text{Cumulative\_Share}_{k-1}$ (with $P_1 = 0$). With user thresholds $\alpha$ (default 0.80) and $\beta$ (default 0.95):
   $$\text{ABC\_Class}_k = \begin{cases} \text{A}, & \text{if } P_k < \alpha \\ \text{B}, & \text{if } \alpha \le P_k < \beta \\ \text{C}, & \text{if } P_k \ge \beta \end{cases}$$

### 4.2 XYZ Demand Variability Classification Algorithm
1. **Monthly Mean Demand ($\mu$):**
   $$\mu_i = \frac{1}{12} \sum_{m=1}^{12} D_{i, m}$$
2. **Sample Standard Deviation ($\sigma$, with Bessel's correction $ddof=1$):**
   $$\sigma_i = \sqrt{\frac{1}{11} \sum_{m=1}^{12} (D_{i, m} - \mu_i)^2}$$
3. **Coefficient of Variation (CV):**
   $$\text{CV}_i = \frac{\sigma_i}{\mu_i}$$
4. **Threshold Assignment:** With cutoffs $X_{\text{cutoff}}$ (default 0.50) and $Y_{\text{cutoff}}$ (default 1.00):
   $$\text{XYZ\_Class}_i = \begin{cases} \text{N/A}, & \text{if } \mu_i = 0 \\ \text{X}, & \text{if } \mu_i > 0 \text{ and } \text{CV}_i \le X_{\text{cutoff}} \\ \text{Y}, & \text{if } X_{\text{cutoff}} < \text{CV}_i \le Y_{\text{cutoff}} \\ \text{Z}, & \text{if } \text{CV}_i > Y_{\text{cutoff}} \end{cases}$$

---

## 5. Empirical Results & Findings

Executing the analytics engine on the 1,000-SKU dataset produces the following empirical distributions:

### 5.1 Macro Portfolio Summary
- **Total Catalog Size:** 1,000 SKUs
- **Merchandise Categories:** 5
- **Annual Units Demanded:** 16,961,896 units
- **Total Portfolio Sales Value:** \$1,072,287,900.00

### 5.2 Category-Wise Performance Breakdown
| Category | Product Count | Annual Units | Sales Value (\$) | Average Price (\$) | Revenue Share (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Grocery** | 402 | 14,328,734 | \$911,737,236.00 | \$65.78 | 85.03% |
| **Apparel** | 216 | 1,404,956 | \$99,381,360.00 | \$57.82 | 9.27% |
| **Electronics** | 193 | 624,622 | \$25,081,150.00 | \$44.87 | 2.34% |
| **Toys** | 89 | 306,774 | \$21,945,148.00 | \$63.24 | 2.05% |
| **Home & Kitchen** | 100 | 296,810 | \$14,143,006.00 | \$41.36 | 1.32% |

*Key Takeaway:* **Grocery** dominates operations, contributing 85.03% of revenue and 84.48% of total unit volume. Operational improvements in Grocery will disproportionately drive overall business performance.

### 5.3 ABC & XYZ Marginal Distributions
- **ABC Breakdown (at 80% / 95% Cutoffs):**
  - **Class A:** 88 SKUs (8.8% of items drive ~80% of revenue)
  - **Class B:** 170 SKUs (17.0% of items drive the next ~15% of revenue)
  - **Class C:** 742 SKUs (74.2% of items drive the remaining ~5% of revenue)
- **XYZ Breakdown (at CV cutoffs 0.50 / 1.00):**
  - **Class X (CV ≤ 0.50):** 939 SKUs (93.9% of portfolio exhibits high demand stability)
  - **Class Y (0.50 < CV ≤ 1.00):** 59 SKUs (5.9% exhibit moderate variability)
  - **Class Z (CV > 1.00):** 2 SKUs (0.2% exhibit high volatility)

### 5.4 The ABC–XYZ Contingency Matrix
Cross-tabulating the classifications yields the following distribution across the 1,000 SKUs:

| ABC / XYZ | X (Stable, $\text{CV} \le 0.50$) | Y (Variable, $0.50 < \text{CV} \le 1.00$) | Z (Erratic, $\text{CV} > 1.00$) | Total |
| :---: | :---: | :---: | :---: | :---: |
| **A (High Value)** | **88** | 0 | 0 | **88** |
| **B (Medium Value)** | **165** | **5** | 0 | **170** |
| **C (Low Value)** | **686** | **54** | **2** | **742** |
| **Total** | **939** | **59** | **2** | **1,000** |

*Crucial Empirical Finding:* All 88 Class A products fall into Class X ($AX$). This indicates that the core revenue generators possess stable, predictable demand, presenting an ideal operational opportunity for Just-In-Time replenishment and automated ordering with minimal safety buffers.

---

## 6. Strategic Inventory Management Policies

Based on the empirical matrix, prescriptive policies are established for inventory managers:

| Matrix Segment | Product Count | Characteristics | Recommended Inventory Policy |
| :---: | :---: | :--- | :--- |
| **AX** | 88 | High value, highly predictable demand | **Continuous Replenishment / JIT:** High service level target (98–99%), strict supplier SLAs, low safety stocks, daily/weekly cycle counts, automated replenishment. |
| **AY** | 0 | High value, moderate variability | **Forecast Collaboration:** Frequent review of promotional lifts, buffer stocks dynamically scaled with demand forecasts. |
| **AZ** | 0 | High value, erratic demand | **Make-to-Order / Consignment:** Minimize physical holding; require manual purchase order approvals; negotiate rapid supplier lead times. |
| **BX** | 165 | Medium value, predictable demand | **Standard Automated EOQ:** Periodic review (bi-weekly/monthly), standard safety buffers, automated purchase orders upon reaching reorder point. |
| **BY** | 5 | Medium value, fluctuating demand | **Dynamic Safety Stock:** Seasonal/trend adjusted safety stock; monthly demand reviews. |
| **BZ** | 0 | Medium value, erratic demand | **Cautious Batching:** Flexible order quantities; safety buffers tied to lead-time variability. |
| **CX** | 686 | Low value, predictable demand | **Simplified Two-Bin / Bulk Ordering:** Low management oversight; quarterly large batch orders to capture quantity discounts; low risk of obsolescence. |
| **CY** | 54 | Low value, variable demand | **Periodic Review / Minimum Stock:** Review every 2–3 months; avoid excess stocking; set minimum reorder thresholds. |
| **CZ** | 2 | Low value, erratic demand | **Scrap / Order-on-Demand:** Evaluate catalog pruning or SKU rationalization; keep zero or negligible shelf stock; procure strictly upon customer request. |

---

## 7. System Architecture & UI/UX Implementation

### 7.1 Software Stack
- **Language:** Python 3.12
- **Data Engineering:** `pandas` (vectorized transformations), `numpy` (conditional logic)
- **Visualization:** `plotly.express` and `plotly.graph_objects` (interactive web graphics)
- **Web Framework:** `streamlit` 1.65 (reactive web application framework)

### 7.2 Modular Multi-File Software Architecture
To adhere to clean software engineering and data science best practices, the codebase decouples concerns into dedicated modules that are cleanly imported into the primary entrypoint:
- **`data_cleaning.py`:** Enapsulates data loading (`load_data`, `read_csv_bytes`), automated validation checks, duplicate removal, demand/price sanitization, derivation reconciliation (`clean_data`), and the interactive Data Cleaning tab renderer.
- **`category_performance.py`:** Contains category-level analytical functions (`compute_category_summary`, `compute_monthly_trend`, `get_top_products`) and generates interactive Plotly visualizations for category revenue, volume, and trends.
- **`abc_xyz_analysis.py`:** Contains the core classification engine (`classify_abc_xyz`), $3 \times 3$ contingency matrix generator (`compute_matrix`), prescriptive policy mapper (`generate_action_recommendations`), and renders the ABC-XYZ Analysis tab.
- **`app.py`:** Serves as the central Streamlit application orchestrator, managing global UI configuration, the top settings expander, data pipeline execution, and tab-based routing.
- **`data_utils.py`:** Provides backward-compatible re-exports of core utility functions.
- **`tests/test_analytics.py`:** Automated unit test suite verifying data integrity, reconciliation checks, category aggregations, and classification math using Python's `unittest` framework.

### 7.3 Interface Architecture: Side-Panel-Free Tabbed Layout
To optimize horizontal screen space on wide desktop displays and eliminate navigation friction, the dashboard eliminates the legacy Streamlit sidebar in favor of a clean, responsive layout:
1. **Collapsible Settings Expander (`⚙️ Data Source & ABC–XYZ Threshold Settings`):**
   - Placed at the top of the interface.
   - Houses the CSV file uploader, ABC cutoffs ($A\%$, $B\%$), and XYZ cutoffs ($X_{\text{max}}$, $Y_{\text{max}}$).
   - Dynamically broadcasts state changes across all tabs upon adjustment.
2. **Tab 1: 📋 Overview:**
   - 4 executive metric cards (`Products`, `Categories`, `Annual Units Demanded`, `Total Sales Value`).
   - Educational overview of ABC and XYZ principles.
   - Comprehensive tab navigation guide and 10-row dataset preview.
3. **Tab 2: 🧹 Data Cleaning:**
   - Data quality metrics, full audit table, raw vs. cleaned data comparison, and cleaned CSV export button.
4. **Tab 3: 📊 Category Performance:**
   - Category filter dropdown, dual category bar charts (Sales Value & Volume), 12-month demand trend line chart, and top 10 products table.
5. **Tab 4: 🧮 ABC–XYZ Analysis:**
   - Classification distribution summary cards, dual-axis ABC Pareto chart (Sales bar vs. cumulative % curve), $3 \times 3$ product count heatmap, demand CV distribution histogram, formatted product classification table, and prescriptive actions table.
6. **Tab 5: ⬇️ Explore & Download:**
   - Instant search input across Item ID, Name, and Category, combined with multi-select filters for ABC class, XYZ class, and Category.
   - 3 export triggers: Cleaned dataset CSV, Full ABC-XYZ classified CSV, and Filtered query CSV.

---

## 8. Limitations & Future Scope

### 8.1 Methodological Limitations
1. **12-Month Demand Window:** Calculating CV over only 12 monthly observations limits statistical power and cannot detect multi-year cyclical patterns or long-term product lifecycles.
2. **Absence of Cost & Supply Lead Times:** The dataset excludes unit holding costs, order processing costs, and vendor lead times. True reorder points (ROP) and Economic Order Quantities (EOQ) cannot be computed without lead-time variance.
3. **Imputation Assumption:** Treating missing demand as zero is standard when transactions are unrecorded, but may distort CV for newly launched products with late-year introductions.

### 8.2 Future Enhancements
- **Multi-Year Time Series Forecasting:** Integrate ARIMA or Prophet models for predictive demand forecasting in addition to historical CV profiling.
- **Service Level Optimization:** Incorporate stockout cost penalties and holding costs to calculate optimal cycle-service levels ($CSL$).
- **Multi-Location / Warehouse Allocation:** Extend segmentation across regional distribution centers (DCs) to support localized stocking policies.

---

## 9. Conclusion

This project successfully demonstrates the application of Python data science techniques to resolve real-world supply chain challenges. By unifying automated data quality assurance, mathematical modeling, and interactive visualization in a streamlined Streamlit application, the **ABC–XYZ Inventory Analytics Dashboard** equips decision-makers with clear, actionable intelligence. 

The empirical findings highlight that the organization’s highest-value items (Class A) exhibit highly stable consumption (Class X), enabling significant working capital reductions through lean replenishment policies without risking stockouts.

---

## References & Academic Bibliography

1. Silver, E. A., Pyke, D. F., & Thomas, D. J. (2016). *Inventory and Production Management in Supply Chains*. CRC Press.
2. Chopra, S., & Meindl, P. (2016). *Supply Chain Management: Strategy, Planning, and Operation*. Pearson.
3. Pareto, V. (1896). *Cours d'économie politique*. Rouge, Lausanne.
4. Syntetos, A. A., & Boylan, J. E. (2005). The accuracy of intermittent demand estimates. *International Journal of Forecasting*, 21(2), 303–314.
5. McKinney, W. (2022). *Python for Data Analysis: Data Wrangling with pandas, NumPy, and Jupyter*. O'Reilly Media.
