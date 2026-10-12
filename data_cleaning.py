"""Data loading, validation, cleaning, and cleaning tab presentation module."""
from io import BytesIO
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

MONTHS = [
    "Jan_Demand", "Feb_Demand", "Mar_Demand", "Apr_Demand",
    "May_Demand", "Jun_Demand", "Jul_Demand", "Aug_Demand",
    "Sep_Demand", "Oct_Demand", "Nov_Demand", "Dec_Demand",
]

REQUIRED = [
    "Item_ID", "Item_Name", "Category", *MONTHS,
    "Total_Annual_Units", "Price_Per_Unit", "Total_Sales_Value"
]


def read_csv_bytes(data: bytes) -> pd.DataFrame:
    """Parse CSV bytes from a file uploader into a pandas DataFrame."""
    return pd.read_csv(BytesIO(data))


def load_data(uploaded=None, default_path=None) -> tuple[pd.DataFrame, str]:
    """Load dataset from either an uploaded file or the local default CSV file.
    
    Returns:
        tuple[pd.DataFrame, str]: The raw dataframe and its source filename.
    """
    if default_path is None:
        default_path = Path(__file__).parent / "abc_xyz_dataset.csv"

    if uploaded is not None:
        raw = read_csv_bytes(uploaded.getvalue())
        source = uploaded.name
    elif Path(default_path).exists():
        raw = pd.read_csv(default_path)
        source = Path(default_path).name
    else:
        raise FileNotFoundError(
            f"Dataset not found. Please upload a CSV file or place '{Path(default_path).name}' in the project directory."
        )

    return raw, source


def clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean the raw inventory dataset and generate a validation audit report.
    
    Pipeline Steps:
      1. Strips header whitespace and confirms required columns exist.
      2. Trims string fields and casts empty strings to NA.
      3. Coerces numeric fields to numeric types.
      4. Removes exact duplicate records.
      5. Handles missing and negative monthly demand (clips to zero).
      6. Drops records missing primary identifiers (Item_ID, Item_Name, Category).
      7. Replaces invalid/negative unit prices with zero.
      8. Mathematically recalculates Total_Annual_Units and Total_Sales_Value.
    
    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (cleaned_dataframe, audit_dataframe)
    """
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    missing_columns = [c for c in REQUIRED if c not in df.columns]
    if missing_columns:
        raise ValueError("Required columns missing: " + ", ".join(missing_columns))

    original_rows = len(df)
    missing_before = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    for col in ["Item_ID", "Item_Name", "Category"]:
        df[col] = df[col].astype("string").str.strip().replace("", pd.NA)

    numeric_cols = MONTHS + ["Total_Annual_Units", "Price_Per_Unit", "Total_Sales_Value"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.drop_duplicates().copy()
    missing_demand = int(df[MONTHS].isna().sum().sum())
    negative_demand = int((df[MONTHS] < 0).sum().sum())
    # Assumption: missing monthly demand means zero demand during that month.
    df[MONTHS] = df[MONTHS].fillna(0).clip(lower=0)

    rows_before_id_drop = len(df)
    df = df.dropna(subset=["Item_ID", "Item_Name", "Category"]).copy()
    dropped_missing_ids = rows_before_id_drop - len(df)

    invalid_prices = int((df["Price_Per_Unit"].isna() | (df["Price_Per_Unit"] < 0)).sum())
    df["Price_Per_Unit"] = df["Price_Per_Unit"].where(df["Price_Per_Unit"] >= 0, np.nan).fillna(0)

    monthly_total = df[MONTHS].sum(axis=1)
    annual_mismatch = int((~np.isclose(df["Total_Annual_Units"].fillna(-999), monthly_total)).sum())
    expected_sales = monthly_total * df["Price_Per_Unit"]
    sales_mismatch = int((~np.isclose(df["Total_Sales_Value"].fillna(-999), expected_sales)).sum())

    df["Total_Annual_Units"] = monthly_total
    df["Total_Sales_Value"] = expected_sales
    df = df.reset_index(drop=True)

    audit = pd.DataFrame({
        "Check": [
            "Original rows",
            "Missing cells before cleaning",
            "Exact duplicate rows removed",
            "Rows dropped for missing ID/name/category",
            "Missing monthly demand cells filled with zero",
            "Negative monthly demand cells changed to zero",
            "Missing/negative prices changed to zero",
            "Annual totals inconsistent with monthly totals",
            "Sales values inconsistent with units × price",
            "Final rows retained",
        ],
        "Result": [
            original_rows,
            missing_before,
            duplicate_rows,
            dropped_missing_ids,
            missing_demand,
            negative_demand,
            invalid_prices,
            annual_mismatch,
            sales_mismatch,
            len(df),
        ],
    })
    return df, audit


def render_data_cleaning_tab(raw: pd.DataFrame, clean: pd.DataFrame, audit: pd.DataFrame):
    """Render the interactive Data Cleaning & Validation section in Streamlit."""
    st.subheader("🧹 Data Cleaning and Validation")
    st.write(
        "This module standardizes text columns, coerces numeric fields, eliminates duplicate records, "
        "imputes missing or negative demand figures, and recalculates derived annual units and sales values."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Raw Rows", f"{len(raw):,}")
    c2.metric("Cleaned Rows", f"{len(clean):,}")
    c3.metric("Missing Cells After Cleaning", f"{int(clean.isna().sum().sum()):,}")

    st.subheader("Cleaning Audit Report")
    st.dataframe(audit, use_container_width=True, hide_index=True)

    col_raw, col_clean = st.columns(2)
    with col_raw:
        st.subheader("Raw Data Preview")
        st.dataframe(raw.head(15), use_container_width=True, hide_index=True)
    with col_clean:
        st.subheader("Cleaned Data Preview")
        st.dataframe(clean.head(15), use_container_width=True, hide_index=True)

    st.warning(
        "Assumption: missing monthly demand is filled with zero. Missing values may represent unrecorded "
        "transactions rather than true zero demand; validate this assumption with domain owners."
    )
    st.download_button(
        "Download Cleaned CSV",
        clean.to_csv(index=False).encode("utf-8"),
        "cleaned_inventory.csv",
        "text/csv",
        key="btn_download_cleaned_tab2",
    )
