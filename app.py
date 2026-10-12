import streamlit as st
import pandas as pd
from pathlib import Path

# Modular imports for easy presentation and clean code separation
from data_cleaning import load_data, clean_data, render_data_cleaning_tab
from category_performance import render_category_performance_tab
from abc_xyz_analysis import classify_abc_xyz, render_abc_xyz_analysis_tab

# Configure page settings
st.set_page_config(
    page_title="ABC–XYZ Inventory Analytics Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Completely remove/hide the side panel and collapse arrow
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Application Header
st.title("📦 ABC–XYZ Inventory Analytics Dashboard")
st.caption("Interactive inventory analytics: data cleaning, category performance, classification, and exports")

# Top Configuration Panel (replaces the sidebar)
with st.expander("⚙️ Data Source & ABC–XYZ Threshold Settings", expanded=False):
    col_src, col_abc, col_xyz = st.columns([1.2, 1.4, 1.4])

    with col_src:
        st.markdown("##### 📁 Data Source")
        uploaded = st.file_uploader(
            "Upload inventory CSV",
            type=["csv"],
            key="uploaded_inventory_csv",
            help="Upload a custom CSV or leave empty to use the default dataset.",
        )

    with col_abc:
        st.markdown("##### 📈 ABC Thresholds")
        a_cutoff = st.slider("ABC A cutoff (% of value)", 50, 90, 80, key="slider_a_cutoff") / 100
        b_cutoff = st.slider("ABC A+B cutoff (% of value)", 85, 99, 95, key="slider_b_cutoff") / 100
        if b_cutoff <= a_cutoff:
            st.error("A+B cutoff must be greater than the A cutoff.")
            st.stop()

    with col_xyz:
        st.markdown("##### 📊 XYZ Thresholds")
        x_cutoff = st.number_input(
            "X maximum CV",
            min_value=0.05,
            max_value=2.0,
            value=0.50,
            step=0.05,
            key="input_x_cutoff",
        )
        y_cutoff = st.number_input(
            "Y maximum CV",
            min_value=0.10,
            max_value=5.0,
            value=1.00,
            step=0.05,
            key="input_y_cutoff",
        )
        if y_cutoff <= x_cutoff:
            st.error("Y maximum CV must be greater than X maximum CV.")
            st.stop()

# Data Loading & Processing Pipeline (via imported modules)
try:
    raw, source = load_data(uploaded=uploaded)
    clean, audit = clean_data(raw)
except Exception as exc:
    st.error(f"Unable to load or clean the dataset: {exc}")
    st.stop()

classified = classify_abc_xyz(clean, a_cutoff, b_cutoff, x_cutoff, y_cutoff)

# Status Information Bar
st.caption(
    f"📁 Active dataset: **{source}** ({len(clean):,} items) | "
    f"⚙️ Active thresholds: A ≤ {a_cutoff:.0%}, B ≤ {b_cutoff:.0%}, X CV ≤ {x_cutoff:.2f}, Y CV ≤ {y_cutoff:.2f}"
)

# Tab Navigation (replaces sidebar multipage navigation)
tab_overview, tab_cleaning, tab_category, tab_analysis, tab_explore = st.tabs([
    "📋 Overview",
    "🧹 Data Cleaning",
    "📊 Category Performance",
    "🧮 ABC–XYZ Analysis",
    "⬇️ Explore & Download",
])

# -------------------------------------------------------------
# TAB 1: OVERVIEW
# -------------------------------------------------------------
with tab_overview:
    st.subheader("Key Portfolio Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products", f"{len(clean):,}")
    c2.metric("Categories", f"{clean['Category'].nunique():,}")
    c3.metric("Annual Units Demanded", f"{clean['Total_Annual_Units'].sum():,.0f}")
    c4.metric("Total Sales Value", f"${clean['Total_Sales_Value'].sum():,.2f}")

    st.markdown("---")

    col_about, col_guide = st.columns(2)
    with col_about:
        st.markdown("### 📌 Project Background & Objectives")
        st.markdown(
            """
            This dashboard is developed for the **Python for Data Science** course to conduct comprehensive **ABC–XYZ inventory analytics**.
            
            - **ABC Analysis (Value-Based):** Segregates inventory items based on their annual revenue contribution following Pareto's principle:
              - **A Items:** High revenue contribution (top cumulative sales up to cutoff, default 80%).
              - **B Items:** Moderate revenue contribution (next cumulative sales up to cutoff, default 95%).
              - **C Items:** Low revenue contribution (remaining items).
            - **XYZ Analysis (Demand Variability):** Classifies items based on demand predictability using the monthly demand Coefficient of Variation (CV = standard deviation / mean):
              - **X Items:** Low demand variability (CV ≤ X cutoff, default 0.50) — highly predictable.
              - **Y Items:** Moderate demand variability (X cutoff < CV ≤ Y cutoff, default 1.00) — moderate predictability.
              - **Z Items:** High demand variability / sporadic demand (CV > Y cutoff) — difficult to forecast.
            """
        )

    with col_guide:
        st.markdown("### 🧭 Tab Navigation Guide")
        st.markdown(
            """
            - **🧹 Data Cleaning:** Data audit checks, handling missing/negative values, and before/after inspection.
            - **📊 Category Performance:** Sales distribution, units demanded by category, and monthly demand trends.
            - **🧮 ABC–XYZ Analysis:** Pareto curve, CV distribution histogram, 3×3 matrix, and actionable inventory recommendations.
            - **⬇️ Explore & Download:** Multi-filter query tool and CSV export options for cleaned and classified data.
            """
        )

    st.markdown("---")
    st.markdown("### 📄 Dataset Preview")
    st.write(f"Previewing first 10 rows of cleaned dataset (**{source}**):")
    st.dataframe(clean.head(10), use_container_width=True, hide_index=True)

# -------------------------------------------------------------
# TAB 2: DATA CLEANING (Imported from data_cleaning.py)
# -------------------------------------------------------------
with tab_cleaning:
    render_data_cleaning_tab(raw, clean, audit)

# -------------------------------------------------------------
# TAB 3: CATEGORY PERFORMANCE (Imported from category_performance.py)
# -------------------------------------------------------------
with tab_category:
    render_category_performance_tab(clean)

# -------------------------------------------------------------
# TAB 4: ABC–XYZ ANALYSIS (Imported from abc_xyz_analysis.py)
# -------------------------------------------------------------
with tab_analysis:
    render_abc_xyz_analysis_tab(classified, a_cutoff, b_cutoff, x_cutoff, y_cutoff)

# -------------------------------------------------------------
# TAB 5: EXPLORE & DOWNLOAD
# -------------------------------------------------------------
with tab_explore:
    st.subheader("⬇️ Explore and Download Results")
    search = st.text_input("Search by item ID, item name or category", key="search_query_explore")
    c_f1, c_f2, c_f3 = st.columns(3)
    with c_f1:
        abc_filter = st.multiselect("ABC class", ["A", "B", "C"], default=["A", "B", "C"], key="filter_abc")
    with c_f2:
        xyz_filter = st.multiselect(
            "XYZ class", ["X", "Y", "Z", "N/A"], default=["X", "Y", "Z", "N/A"], key="filter_xyz"
        )
    with c_f3:
        all_cats = sorted(classified["Category"].dropna().unique().tolist())
        cat_filter = st.multiselect("Category", all_cats, default=all_cats, key="filter_cat")

    filtered = classified[
        classified["ABC_Class"].isin(abc_filter)
        & classified["XYZ_Class"].isin(xyz_filter)
        & classified["Category"].isin(cat_filter)
    ].copy()

    if search.strip():
        mask = (
            filtered["Item_ID"].astype(str).str.contains(search, case=False, na=False)
            | filtered["Item_Name"].astype(str).str.contains(search, case=False, na=False)
            | filtered["Category"].astype(str).str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    st.caption(f"Showing {len(filtered):,} of {len(classified):,} products")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    c_d1, c_d2, c_d3 = st.columns(3)
    with c_d1:
        st.download_button(
            "Download Cleaned Dataset CSV",
            clean.to_csv(index=False).encode("utf-8"),
            "cleaned_inventory.csv",
            "text/csv",
            key="btn_dl_cleaned_tab5",
            use_container_width=True,
        )
    with c_d2:
        st.download_button(
            "Download All ABC–XYZ Results CSV",
            classified.to_csv(index=False).encode("utf-8"),
            "abc_xyz_results.csv",
            "text/csv",
            key="btn_dl_all_tab5",
            use_container_width=True,
        )
    with c_d3:
        st.download_button(
            "Download Filtered Results CSV",
            filtered.to_csv(index=False).encode("utf-8"),
            "filtered_inventory.csv",
            "text/csv",
            key="btn_dl_filtered_tab5",
            use_container_width=True,
        )
