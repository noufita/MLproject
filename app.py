import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# Page setup
# =========================
st.set_page_config(
    page_title="Healthcare Claims EDA Dashboard",
    layout="wide"
)

# =========================
# Load data
# =========================
df = pd.read_csv("claims_cleaned.csv")

# Make sure status is numeric
# 1 = Approved, 0 = Rejected
df["status"] = df["status"].astype(int)

# Create readable status column
df["claim_status"] = df["status"].map({
    1: "Approved",
    0: "Rejected"
})

# Convert visitdate if exists
if "visitdate" in df.columns:
    df["visitdate"] = pd.to_datetime(df["visitdate"], errors="coerce")
    df["month"] = df["visitdate"].dt.to_period("M").astype(str)

# =========================
# Title
# =========================
st.title("Healthcare Claims EDA Dashboard")
st.write("Exploratory Data Analysis for Healthcare Claims Dataset")

# =========================
# Tabs
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Financial Analysis",
    "Rejection Reasons",
    "ICD Analysis"
])

# =========================
# Tab 1: Overview
# =========================
with tab1:
    st.subheader("Dataset Overview")

    total_rows = len(df)
    total_cols = df.shape[1]
    approved_count = (df["status"] == 1).sum()
    rejected_count = (df["status"] == 0).sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Rows", f"{total_rows:,}")
    col2.metric("Total Columns", f"{total_cols:,}")
    col3.metric("Approved Claims", f"{approved_count:,}")
    col4.metric("Rejected Claims", f"{rejected_count:,}")

    st.divider()

    col5, col6, col7 = st.columns(3)

    total_net = df["net_amount"].sum()
    rejected_net = df[df["status"] == 0]["net_amount"].sum()
    approved_net = df[df["status"] == 1]["net_amount"].sum()

    col5.metric("Total Net Amount", f"SAR {total_net:,.2f}")
    col6.metric("Approved Net Amount", f"SAR {approved_net:,.2f}")
    col7.metric("Rejected Net Amount", f"SAR {rejected_net:,.2f}")

    st.divider()

    st.subheader("Claim Status Distribution")

    status_count = df["claim_status"].value_counts().reset_index()
    status_count.columns = ["Claim Status", "Count"]

    fig = px.pie(
        status_count,
        names="Claim Status",
        values="Count",
        hole=0.45,
        title="Approved vs Rejected Claims"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Data Preview")
    st.dataframe(df.head(20), use_container_width=True)


# =========================
# Tab 2: Financial Analysis
# =========================
with tab2:
    st.subheader("Financial Analysis")

    status_filter = st.selectbox(
        "Select Claim Status",
        ["All", "Approved", "Rejected"],
        key="financial_status_filter"
    )

    if status_filter == "Approved":
        filtered_df = df[df["status"] == 1]
    elif status_filter == "Rejected":
        filtered_df = df[df["status"] == 0]
    else:
        filtered_df = df

    total_net = filtered_df["net_amount"].sum()
    avg_net = filtered_df["net_amount"].mean()
    max_net = filtered_df["net_amount"].max()
    claim_count = len(filtered_df)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Net Amount", f"SAR {total_net:,.2f}")
    col2.metric("Average Net Amount", f"SAR {avg_net:,.2f}")
    col3.metric("Highest Net Amount", f"SAR {max_net:,.2f}")
    col4.metric("Number of Claims", f"{claim_count:,}")

    st.divider()

    colA, colB = st.columns(2)

    with colA:
        st.subheader("Net Amount Distribution")
        fig1 = px.histogram(
            filtered_df,
            x="net_amount",
            nbins=40,
            title="Distribution of Net Amount"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with colB:
        st.subheader("Net Amount Boxplot")
        fig2 = px.box(
            filtered_df,
            y="net_amount",
            points="outliers",
            title="Boxplot of Net Amount"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Approved vs Rejected Net Amount")

    fig3 = px.box(
        df,
        x="claim_status",
        y="net_amount",
        color="claim_status",
        title="Net Amount Comparison by Claim Status"
    )
    st.plotly_chart(fig3, use_container_width=True)





# =========================
# Tab 3: Rejection Reasons
# =========================
with tab3:
    st.subheader("Rejection Reasons Analysis")

    rejected_df = df[df["status"] == 0].copy()

    total_rejected = len(rejected_df)
    rejected_amount = rejected_df["net_amount"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Rejected Claims", f"{total_rejected:,}")
    col2.metric("Rejected Net Amount", f"SAR {rejected_amount:,.2f}")
    col3.metric(
        "Rejection Rate",
        f"{(total_rejected / len(df)) * 100:.1f}%"
    )

    st.divider()

    st.subheader("Top 5 Rejection Reasons")

    top5_reasons = (
        rejected_df["reason"]
        .dropna()
        .value_counts()
        .head(5)
        .reset_index()
    )
    top5_reasons.columns = ["Reason", "Count"]

    fig1 = px.bar(
        top5_reasons,
        x="Count",
        y="Reason",
        orientation="h",
        text="Count",
        title="Top 5 Rejection Reasons"
    )
    fig1.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Financial Loss by Top 5 Rejection Reasons")

    loss_by_reason = (
        rejected_df
        .groupby("reason")["net_amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    loss_by_reason.columns = ["Reason", "Rejected Net Amount"]

    fig2 = px.bar(
        loss_by_reason,
        x="Rejected Net Amount",
        y="Reason",
        orientation="h",
        text="Rejected Net Amount",
        title="Top 5 Reasons by Rejected Net Amount"
    )
    fig2.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Reason Table")

    reason_table = (
        rejected_df
        .groupby("reason")
        .agg(
            rejected_claims=("reason", "count"),
            rejected_net_amount=("net_amount", "sum"),
            average_net_amount=("net_amount", "mean")
        )
        .reset_index()
        .sort_values("rejected_claims", ascending=False)
    )

    st.dataframe(reason_table, use_container_width=True)




# =========================
# Tab 4: ICD Analysis
# =========================
with tab4:
    st.subheader("ICD Analysis")

    status_filter_icd = st.selectbox(
        "Select Claim Status",
        ["All", "Approved", "Rejected"],
        key="icd_status_filter"
    )

    if status_filter_icd == "Approved":
        icd_df = df[df["status"] == 1]
    elif status_filter_icd == "Rejected":
        icd_df = df[df["status"] == 0]
    else:
        icd_df = df

    unique_icd = icd_df["icd"].nunique()
    total_icd_amount = icd_df["net_amount"].sum()

    col1, col2 = st.columns(2)

    col1.metric("Unique ICD Codes", f"{unique_icd:,}")
    col2.metric("Total Net Amount", f"SAR {total_icd_amount:,.2f}")

    st.divider()

    st.subheader("Top 10 ICD Codes by Count")

    top_icd = (
        icd_df["icd"]
        .dropna()
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_icd.columns = ["ICD", "Count"]

    fig1 = px.bar(
        top_icd,
        x="Count",
        y="ICD",
        orientation="h",
        text="Count",
        title="Top 10 ICD Codes by Count"
    )
    fig1.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Top 10 Rejected ICD Codes")

    rejected_icd = (
        df[df["status"] == 0]
        .groupby("icd")
        .agg(
            rejected_claims=("icd", "count"),
            rejected_amount=("net_amount", "sum")
        )
        .reset_index()
        .sort_values("rejected_claims", ascending=False)
        .head(10)
    )

    fig2 = px.bar(
        rejected_icd,
        x="rejected_claims",
        y="icd",
        orientation="h",
        text="rejected_claims",
        title="Top 10 Rejected ICD Codes"
    )
    fig2.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("ICD Table")

    icd_table = (
        df
        .groupby("icd")
        .agg(
            total_claims=("icd", "count"),
            total_net_amount=("net_amount", "sum"),
            rejected_claims=("status", lambda x: (x == 0).sum())
        )
        .reset_index()
    )

    icd_table["rejection_rate"] = (
        icd_table["rejected_claims"] / icd_table["total_claims"] * 100
    ).round(2)

    icd_table = icd_table.sort_values("rejected_claims", ascending=False)

    st.dataframe(icd_table, use_container_width=True)