"""
Day 3 — Train Delay DNA Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Train Delay DNA", page_icon="🚆", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252a3a);
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid #ff4b4b;
        margin: 8px 0;
    }
    .personality-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 13px;
        background: #ff4b4b22;
        color: #ff4b4b;
        border: 1px solid #ff4b4b44;
    }
    </style>
""", unsafe_allow_html=True)

# ── Load Data — convert train_no to string immediately ───────────────────────
@st.cache_data
def load_data():
    delays  = pd.read_csv("train_delays.csv")
    summary = pd.read_csv("train_analysis.csv")
    delays["train_no"]  = delays["train_no"].astype(str)
    summary["train_no"] = summary["train_no"].astype(str)
    return delays, summary

df, summary = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🚆 Train Delay DNA")
st.markdown("##### *What is your train's delay personality?*")
st.markdown("---")

# ── Top Metrics ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Trains Analysed", df["train_no"].nunique())
with col2:
    st.metric("Days of Data", df["date"].nunique())
with col3:
    st.metric("Avg Delay (All)", f"{df['delay_minutes'].mean():.1f} min")
with col4:
    most_delayed = summary.sort_values("overall_avg_delay", ascending=False).iloc[0]
    st.metric("Most Delayed Train", most_delayed["train_name"])

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — TRAIN DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("🔍 Train Deep Dive")
st.markdown("Select any train to see its full delay profile — where it loses time and why.")

# Build dropdown options — train_no is already a string
train_list = df[["train_no", "train_name"]].drop_duplicates()
train_list["label"] = train_list["train_no"] + " - " + train_list["train_name"]
selected_label    = st.selectbox("Choose a train:", train_list["label"].tolist())
selected_train_no = selected_label.split(" - ")[0]   # e.g. "12951"

# Filter — both sides are now strings so this always works
train_df      = df[df["train_no"] == selected_train_no].copy()
train_summary = summary[summary["train_no"] == selected_train_no].iloc[0]

# ── Personality card + journey chart ─────────────────────────────────────────
left, right = st.columns([1, 2])

with left:
    st.markdown(f"""
    <div class='metric-card'>
        <div style='color:#aaa; font-size:12px; margin-bottom:6px'>DELAY PERSONALITY</div>
        <div class='personality-badge'>{train_summary['personality']}</div>
        <div style='color:#ccc; font-size:13px; margin-top:12px'>{train_summary['reason']}</div>
        <br>
        <div style='color:#aaa; font-size:12px'>Worst Station</div>
        <div style='color:#fff; font-weight:bold'>{train_summary['worst_station']}</div>
        <div style='color:#ff4b4b'>{train_summary['worst_station_avg_delay']} min avg delay here</div>
        <br>
        <div style='color:#aaa; font-size:12px'>Weekend Savings</div>
        <div style='color:#4caf50; font-weight:bold'>-{train_summary['weekend_saves']} min on weekends</div>
    </div>
    """, unsafe_allow_html=True)

with right:
    station_avg = (
        train_df.groupby(["station_index", "station"])["delay_minutes"]
        .mean().round(1).reset_index().sort_values("station_index")
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=station_avg["station"], y=station_avg["delay_minutes"],
        fill="tozeroy", fillcolor="rgba(255,75,75,0.15)",
        line=dict(color="#ff4b4b", width=3),
        mode="lines+markers", marker=dict(size=8, color="#ff4b4b"),
        name="Avg Delay",
        hovertemplate="<b>%{x}</b><br>Avg delay: %{y} min<extra></extra>"
    ))

    # Highlight bottleneck station
    btn_rows = train_df[train_df["is_bottleneck"] == True]
    if not btn_rows.empty:
        btn_station = btn_rows["station"].iloc[0]
        btn_row = station_avg[station_avg["station"] == btn_station]
        if not btn_row.empty:
            fig.add_trace(go.Scatter(
                x=[btn_station], y=[btn_row["delay_minutes"].values[0]],
                mode="markers", marker=dict(size=16, color="#ffd700", symbol="star"),
                name="Bottleneck",
            ))

    fig.update_layout(
        title="Average Delay at Each Station (star = Bottleneck)",
        xaxis_title="Station", yaxis_title="Avg Delay (min)",
        plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        font=dict(color="#ffffff"), height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — DAY OF WEEK + TIME OF DAY
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📅 When Is This Train Worst?")

def time_bucket(hour):
    if 6 <= hour < 12:    return "Morning"
    elif 12 <= hour < 18: return "Afternoon"
    else:                 return "Evening"

train_df["time_of_day"] = train_df["departure_hour"].apply(time_bucket)

col_a, col_b = st.columns(2)

with col_a:
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_avg = (
        train_df.groupby("day_of_week")["delay_minutes"]
        .mean().round(1).reindex(day_order).reset_index()
    )
    day_avg.columns = ["Day", "Avg Delay"]
    fig2 = px.bar(day_avg, x="Day", y="Avg Delay",
        color="Avg Delay", color_continuous_scale=["#4caf50","#ff9800","#ff4b4b"],
        title="Delay by Day of Week")
    fig2.update_layout(plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        font=dict(color="#ffffff"), coloraxis_showscale=False, height=320)
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    time_avg = (
        train_df.groupby("time_of_day")["delay_minutes"]
        .mean().round(1).reindex(["Morning","Afternoon","Evening"]).reset_index()
    )
    time_avg.columns = ["Time of Day", "Avg Delay"]
    fig3 = px.bar(time_avg, x="Time of Day", y="Avg Delay",
        color="Avg Delay", color_continuous_scale=["#4caf50","#ff9800","#ff4b4b"],
        title="Delay by Time of Departure")
    fig3.update_layout(plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        font=dict(color="#ffffff"), coloraxis_showscale=False, height=320)
    st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — ALL TRAINS COMPARED
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📊 All Trains Compared")

col_c, col_d = st.columns(2)

with col_c:
    sorted_s = summary.sort_values("overall_avg_delay", ascending=True)
    fig4 = px.bar(sorted_s, x="overall_avg_delay", y="train_name", orientation="h",
        color="overall_avg_delay", color_continuous_scale=["#4caf50","#ff9800","#ff4b4b"],
        title="Overall Average Delay", text="overall_avg_delay",
        labels={"overall_avg_delay":"Avg Delay (min)","train_name":""})
    fig4.update_traces(texttemplate="%{text} min", textposition="outside")
    fig4.update_layout(plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        font=dict(color="#ffffff"), coloraxis_showscale=False, height=320)
    st.plotly_chart(fig4, use_container_width=True)

with col_d:
    fig5 = px.scatter(summary, x="weekday_avg", y="weekend_avg",
        text="train_name", size="weekend_saves", color="weekend_saves",
        color_continuous_scale=["#ff4b4b","#4caf50"],
        title="Weekday vs Weekend Delay",
        labels={"weekday_avg":"Weekday Avg (min)","weekend_avg":"Weekend Avg (min)"})
    max_val = max(summary["weekday_avg"].max(), summary["weekend_avg"].max()) + 5
    fig5.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(color="rgba(255,255,255,0.27)", dash="dash"))
    fig5.update_traces(textposition="top center")
    fig5.update_layout(plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
        font=dict(color="#ffffff"), coloraxis_showscale=False, height=320)
    st.plotly_chart(fig5, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — HEATMAP
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🌡️ Delay Heatmap — Every Train × Every Day")

day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
heatmap_data = (
    df.groupby(["train_name","day_of_week"])["delay_minutes"]
    .mean().round(1).reset_index()
    .pivot(index="train_name", columns="day_of_week", values="delay_minutes")
    .reindex(columns=day_order)
)
fig6 = go.Figure(data=go.Heatmap(
    z=heatmap_data.values, x=heatmap_data.columns.tolist(), y=heatmap_data.index.tolist(),
    colorscale=[[0,"#1a3a1a"],[0.5,"#ff9800"],[1,"#ff1a1a"]],
    text=heatmap_data.values.round(1), texttemplate="%{text} min",
    hovertemplate="<b>%{y}</b><br>%{x}<br>%{z} min<extra></extra>"
))
fig6.update_layout(plot_bgcolor="#1e2130", paper_bgcolor="#1e2130",
    font=dict(color="#ffffff"), height=280)
st.plotly_chart(fig6, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("📋 Personality Summary Table")
display_cols = ["train_no","train_name","personality","worst_station",
                "worst_station_avg_delay","weekend_saves","overall_avg_delay"]
st.dataframe(summary[display_cols].rename(columns={
    "train_no":"Train No","train_name":"Train Name","personality":"Personality",
    "worst_station":"Worst Station","worst_station_avg_delay":"Worst Station Delay (min)",
    "weekend_saves":"Weekend Saves (min)","overall_avg_delay":"Overall Avg Delay (min)",
}), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<div style='text-align:center;color:#555;font-size:13px'>Train Delay DNA · Python + Streamlit + Plotly · AI powered by Claude API</div>",
    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — AI REPORT CARD
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.subheader("🤖 AI Report Card")
st.markdown("Click below to generate a plain-English explanation of this train's delay pattern, powered by Claude AI.")

if st.button("✨ Generate AI Report Card", type="primary"):
    with st.spinner("Analysing delay patterns and generating report..."):
        try:
            from ai_report import generate_report_card

            # Prepare station stats for this train
            station_stats = (
                train_df.groupby(["station_index", "station", "is_bottleneck"])
                ["delay_minutes"].mean().round(1).reset_index()
                .sort_values("station_index")
            )

            report = generate_report_card(train_summary, station_stats)

            # Display the report in a styled box
            st.markdown(f"""
            <div style='
                background: linear-gradient(135deg, #1a2a1a, #1e2e1e);
                border-radius: 12px;
                padding: 24px;
                border-left: 4px solid #4caf50;
                margin-top: 12px;
                font-size: 15px;
                line-height: 1.7;
                color: #e0e0e0;
            '>
                <div style='color:#4caf50; font-size:12px; margin-bottom:10px; font-weight:bold'>
                    AI REPORT CARD — {train_summary['train_name'].upper()}
                </div>
                {report}
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Could not generate report card. Make sure your API key is set correctly.\n\nError: {e}")
