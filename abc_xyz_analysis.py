"""ABC-XYZ classification engine, strategic inventory policies, and visualization module."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data_cleaning import MONTHS

# Strategic inventory actions mapped to the 9 ABC-XYZ segments plus inactive items
ACTIONS_MAP = {
    "AX": "High value, stable demand: Continuous replenishment / JIT; tight supplier SLAs and minimal safety stock.",
    "AY": "High value, moderately variable demand: Frequent forecast reviews and dynamic safety stock scaling.",
    "AZ": "High value, volatile demand: Make-to-order or consignment; require manual approvals and scenario planning.",
    "BX": "Medium value, stable demand: Routine automated replenishment controls (EOQ with standard reorder points).",
    "BY": "Medium value, variable demand: Periodic demand reviews and seasonal buffer adjustments.",
    "BZ": "Medium value, volatile demand: Flexible replenishment, shorter lead times, and closer managerial review.",
    "CX": "Lower value, stable demand: Simplified two-bin system or bulk quarterly purchases to minimize ordering costs.",
    "CY": "Lower value, moderately variable demand: Periodic reviews; avoid overstocking and set minimum order thresholds.",
    "CZ": "Lower value, volatile demand: Order-on-demand or scrap; consider SKU rationalization / catalog pruning.",
    "A-N/A": "High-value item with zero average demand: Investigate catalog inactivity or obsolete stock.",
    "B-N/A": "Medium-value item with zero average demand: Investigate item activity and customer demand history.",
    "C-N/A": "Lower-value item with zero average demand: Review whether item should remain active in the catalog.",
}


def classify_abc_xyz(
    df: pd.DataFrame,
    a_cutoff: float = 0.80,
    b_cutoff: float = 0.95,
    x_cutoff: float = 0.50,
    y_cutoff: float = 1.00,
) -> pd.DataFrame:
    """Classify items using dual-criteria ABC (revenue contribution) and XYZ (demand CV).
    
    Parameters:
      - df: Cleaned inventory dataframe
      - a_cutoff: Cumulative revenue threshold for Class A (default 0.80)
      - b_cutoff: Cumulative revenue threshold for Class A+B (default 0.95)
      - x_cutoff: Maximum Demand CV threshold for Class X (default 0.50)
      - y_cutoff: Maximum Demand CV threshold for Class Y (default 1.00)
    
    Returns:
      pd.DataFrame: Augmented dataframe with ABC, XYZ, and ABC_XYZ classification columns.
    """
    result = df.copy().sort_values("Total_Sales_Value", ascending=False).reset_index(drop=True)
    total_value = result["Total_Sales_Value"].sum()

    if total_value > 0:
        result["Sales_Value_Share"] = result["Total_Sales_Value"] / total_value
        result["Cumulative_Value_Share"] = result["Sales_Value_Share"].cumsum()
        previous_share = result["Cumulative_Value_Share"] - result["Sales_Value_Share"]
        result["ABC_Class"] = np.select(
            [previous_share < a_cutoff, previous_share < b_cutoff],
            ["A", "B"],
            default="C",
        )
    else:
        result["Sales_Value_Share"] = 0.0
        result["Cumulative_Value_Share"] = 0.0
        result["ABC_Class"] = "C"

    result["Mean_Monthly_Demand"] = result[MONTHS].mean(axis=1)
    result["Std_Monthly_Demand"] = result[MONTHS].std(axis=1, ddof=1)
    result["Demand_CV"] = result["Std_Monthly_Demand"] / result["Mean_Monthly_Demand"].replace(0, np.nan)

    result["XYZ_Class"] = np.select(
        [
            result["Mean_Monthly_Demand"].eq(0),
            result["Demand_CV"].le(x_cutoff),
            result["Demand_CV"].le(y_cutoff),
        ],
        ["N/A", "X", "Y"],
        default="Z",
    )

    result["ABC_XYZ_Class"] = np.where(
        result["XYZ_Class"].eq("N/A"),
        result["ABC_Class"] + "-N/A",
        result["ABC_Class"] + result["XYZ_Class"],
    )
    return result


def compute_matrix(classified_df: pd.DataFrame) -> pd.DataFrame:
    """Compute the 3x3 product count contingency table for active X, Y, Z classes."""
    return (
        classified_df[classified_df["XYZ_Class"].isin(["X", "Y", "Z"])]
        .pivot_table(
            index="ABC_Class",
            columns="XYZ_Class",
            values="Item_ID",
            aggfunc="count",
            fill_value=0,
        )
        .reindex(index=["A", "B", "C"], columns=["X", "Y", "Z"], fill_value=0)
    )


def generate_action_recommendations(classified_df: pd.DataFrame) -> pd.DataFrame:
    """Generate product-level inventory recommendations based on ABC_XYZ_Class."""
    rec = classified_df[["Item_ID", "Item_Name", "Category", "ABC_XYZ_Class"]].copy()
    rec["Suggested_Action"] = rec["ABC_XYZ_Class"].map(ACTIONS_MAP).fillna(
        "Review item-specific demand pattern and holding value."
    )
    return rec


def render_abc_xyz_analysis_tab(
    classified_df: pd.DataFrame,
    a_cutoff: float,
    b_cutoff: float,
    x_cutoff: float,
    y_cutoff: float,
):
    """Render the ABC-XYZ Classification analysis section in Streamlit."""
    st.subheader("🧮 ABC–XYZ Classification")
    st.caption(
        f"Active Thresholds: ABC: A up to {a_cutoff:.0%} cumulative sales, B up to {b_cutoff:.0%}. "
        f"XYZ: X CV ≤ {x_cutoff:.2f}, Y CV ≤ {y_cutoff:.2f}, Z CV > {y_cutoff:.2f}."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("A-Class Products", int((classified_df["ABC_Class"] == "A").sum()))
    c2.metric("B-Class Products", int((classified_df["ABC_Class"] == "B").sum()))
    c3.metric("C-Class Products", int((classified_df["ABC_Class"] == "C").sum()))
    c4.metric("Z-Class Products", int((classified_df["XYZ_Class"] == "Z").sum()))

    left, right = st.columns(2)
    with left:
        pareto = classified_df.copy()
        pareto["Rank"] = np.arange(1, len(pareto) + 1)
        fig = go.Figure()
        fig.add_bar(x=pareto["Rank"], y=pareto["Total_Sales_Value"], name="Sales value ($)")
        fig.add_scatter(
            x=pareto["Rank"],
            y=pareto["Cumulative_Value_Share"] * 100,
            yaxis="y2",
            mode="lines",
            name="Cumulative sales %",
        )
        fig.update_layout(
            title="ABC Pareto Analysis",
            xaxis_title="Products ranked by sales value",
            yaxis={"title": "Sales value ($)"},
            yaxis2={
                "title": "Cumulative sales (%)",
                "overlaying": "y",
                "side": "right",
                "range": [0, 100],
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        matrix = compute_matrix(classified_df)
        st.plotly_chart(
            px.imshow(
                matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Blues",
                title="ABC–XYZ Product Count Matrix",
                labels={"x": "XYZ class", "y": "ABC class", "color": "Products"},
            ),
            use_container_width=True,
        )

    st.plotly_chart(
        px.histogram(
            classified_df.dropna(subset=["Demand_CV"]),
            x="Demand_CV",
            color="XYZ_Class",
            nbins=35,
            title="Distribution of Demand Coefficient of Variation (CV)",
        ),
        use_container_width=True,
    )

    st.subheader("Product-Level Classification Results")
    cols = [
        "Item_ID", "Item_Name", "Category",
        "Total_Annual_Units", "Total_Sales_Value",
        "Mean_Monthly_Demand", "Std_Monthly_Demand", "Demand_CV",
        "ABC_Class", "XYZ_Class", "ABC_XYZ_Class",
    ]
    st.dataframe(
        classified_df[cols].style.format(
            {
                "Total_Annual_Units": "{:,.0f}",
                "Total_Sales_Value": "${:,.2f}",
                "Mean_Monthly_Demand": "{:,.2f}",
                "Std_Monthly_Demand": "{:,.2f}",
                "Demand_CV": "{:.3f}",
            },
            na_rep="—",
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Suggested Inventory Actions")
    rec_df = generate_action_recommendations(classified_df)
    st.dataframe(rec_df, use_container_width=True, hide_index=True)

    st.download_button(
        "Download ABC–XYZ Results",
        classified_df.to_csv(index=False).encode("utf-8"),
        "abc_xyz_results.csv",
        "text/csv",
        key="btn_download_abc_xyz_tab4",
    )
