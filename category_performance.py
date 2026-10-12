"""Category-level performance analytics, aggregations, and visualization module."""
import pandas as pd
import plotly.express as px
import streamlit as st
from data_cleaning import MONTHS


def compute_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregate business metrics grouped by product category.
    
    Metrics:
      - Product_Count: Number of distinct SKUs
      - Annual_Units: Total annual quantity demanded
      - Sales_Value: Total annual gross revenue
      - Average_Unit_Price: Mean price per unit
      - Average_Annual_Units_Per_Product: Mean units demanded per SKU
      - Sales_Share_%: Percentage of total portfolio sales value
    """
    summary = (
        df.groupby("Category", as_index=False)
        .agg(
            Product_Count=("Item_ID", "nunique"),
            Annual_Units=("Total_Annual_Units", "sum"),
            Sales_Value=("Total_Sales_Value", "sum"),
            Average_Unit_Price=("Price_Per_Unit", "mean"),
            Average_Annual_Units_Per_Product=("Total_Annual_Units", "mean"),
        )
        .sort_values("Sales_Value", ascending=False)
    )
    total_sales = summary["Sales_Value"].sum()
    summary["Sales_Share_%"] = (summary["Sales_Value"] / max(total_sales, 1e-12)) * 100
    return summary


def compute_monthly_trend(view_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly demand chronologically across Jan-Dec for the filtered view."""
    monthly = view_df[MONTHS].sum().rename_axis("Month").reset_index(name="Demand")
    month_names = [m.replace("_Demand", "") for m in MONTHS]
    monthly["Month"] = pd.Categorical(
        monthly["Month"].str.replace("_Demand", "", regex=False),
        categories=month_names,
        ordered=True,
    )
    return monthly.sort_values("Month")


def get_top_products(view_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Extract top N products ranked by Total_Sales_Value."""
    cols = [
        "Item_ID", "Item_Name", "Category",
        "Total_Annual_Units", "Price_Per_Unit", "Total_Sales_Value"
    ]
    return view_df.nlargest(n, "Total_Sales_Value")[cols]


def render_category_performance_tab(clean_df: pd.DataFrame):
    """Render the Category-wise Performance Analysis tab in Streamlit."""
    st.subheader("📊 Category-wise Performance Analysis")

    categories = ["All categories"] + sorted(clean_df["Category"].dropna().unique().tolist())
    selected = st.selectbox("Select category", categories, key="select_cat_perf")
    view = clean_df if selected == "All categories" else clean_df[clean_df["Category"] == selected]

    summary = compute_category_summary(view)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            px.bar(
                summary,
                x="Category",
                y="Sales_Value",
                color="Category",
                text_auto=".3s",
                title="Sales value by category ($)",
            ),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            px.bar(
                summary,
                x="Category",
                y="Annual_Units",
                color="Category",
                text_auto=".3s",
                title="Annual units demanded by category",
            ),
            use_container_width=True,
        )

    monthly = compute_monthly_trend(view)
    st.plotly_chart(
        px.line(
            monthly,
            x="Month",
            y="Demand",
            markers=True,
            title=f"Monthly demand trend ({selected})",
        ),
        use_container_width=True,
    )

    st.subheader("Category Performance Metrics")
    st.dataframe(
        summary.style.format(
            {
                "Annual_Units": "{:,.0f}",
                "Sales_Value": "${:,.2f}",
                "Average_Unit_Price": "${:,.2f}",
                "Average_Annual_Units_Per_Product": "{:,.2f}",
                "Sales_Share_%": "{:.2f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Top 10 Products by Sales Value")
    top_products = get_top_products(view, n=10)
    st.dataframe(
        top_products.style.format(
            {
                "Total_Annual_Units": "{:,.0f}",
                "Price_Per_Unit": "${:,.2f}",
                "Total_Sales_Value": "${:,.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
