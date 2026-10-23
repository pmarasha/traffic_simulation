import streamlit as st
import pandas as pd
import plotly.express as px
import macro_model
import run_simulation

# Set page layout to wide
st.set_page_config(page_title="SIRDC Transport Twin", layout="wide")

st.title("🚦 SIRDC Transport Digital Twin")
st.markdown("A two-layer transport modelling platform for Zimbabwe.")

# Create two tabs at the top
tab1, tab2 = st.tabs(["📊 Macro Model (National)", "🚗 Micro Simulation (Live)"])

# ==========================================
# TAB 1: MACRO MODEL
# ==========================================
with tab1:
    st.header("National Corridor Loading")
    st.markdown("Adjust the sliders to model growth and peak-hour severity.")
    
    # Layout columns for sliders
    col1, col2 = st.columns(2)
    with col1:
        trip_mult = st.slider("Travel Demand Multiplier", 
                              min_value=0.5, max_value=3.0, value=1.0, step=0.05,
                              format="%.2f×")
    with col2:
        peak = st.slider("Peak Hour Severity", 
                         min_value=0.05, max_value=0.15, value=0.10, step=0.01,
                         format="%.0f%%")

    # Run the model (cached so it's instant)
    @st.cache_data
    def get_macro_data(mult, pk):
        return macro_model.run_macro_model(trip_multiplier=mult, peak_hour_factor=pk)

    result = get_macro_data(trip_mult, peak)
    summary = result["summary"]

    # Display KPI Metrics
    st.markdown("---")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Provinces", summary["num_zones"])
    c2.metric("Corridors", summary["num_links"])
    c3.metric("Daily Trips", f"{summary['total_daily_trips']:,.0f}")
    c4.metric("Overloaded", summary["overloaded_count"], delta_color="inverse")
    c5.metric("Total Delay", f"{summary['total_delay_min']:.0f} min", delta_color="inverse")

    st.markdown("---")
    
    # Format the link data for the table and chart
    df = pd.DataFrame(result["links"])
    
    # Show a bar chart of V/C ratios
    df_sorted = df.sort_values("vc_ratio", ascending=True)
    fig = px.bar(
        df_sorted, 
        x="vc_ratio", 
        y="link_id", 
        orientation="h",
        color="vc_ratio",
        color_continuous_scale=["#5fe87a", "#e8b85f", "#e8845f", "#e85f5f"],
        labels={"vc_ratio": "V/C Ratio", "link_id": "Corridor"},
        title="Corridor Loading (V/C Ratio)"
    )
    # Add a vertical line at 1.0 (capacity)
    fig.add_vline(x=1.0, line_dash="dash", line_color="white", annotation_text="Capacity")
    fig.update_layout(height=500, margin=dict(l=0, r=0, t=40, b=0))
    
    st.plotly_chart(fig, use_container_width=True)

    # Show the data table
    st.subheader("Corridor Ranking")
    # Reorder and rename columns for display
    display_df = df[["link_id", "flow_veh_per_day", "vc_ratio", "delay_min", "status"]]
    display_df.columns = ["Link", "Flow/Day", "V/C Ratio", "Delay (min)", "Status"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ==========================================
# TAB 2: MICRO SIMULATION
# ==========================================
with tab2:
    st.header("Harare Intersection Simulation")
    st.markdown("Run a 200-tick simulation and view the congestion trend.")
    
    if st.button("▶ Run Micro Simulation", type="primary"):
        with st.spinner("Generating simulation data..."):
            # Run the simulation
            sim_result = run_simulation.run_simulation(duration=200, time_step=1.0)
            history = sim_result["history"]
            
            # Convert to DataFrame
            hist_df = pd.DataFrame(history)
            
            # Show latest metrics
            latest = hist_df.iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Vehicles", int(latest["vehicles"]))
            c2.metric("Congestion", f"{latest['congestion']:.2f}", delta=latest["congestion_level"], delta_color="inverse")
            c3.metric("Queue Length", int(latest["queue_length"]))
            c4.metric("Avg Speed", f"{latest['avg_speed']:.1f} m/s")
            
            # Plot Congestion over Time
            fig2 = px.area(
                hist_df, 
                x="time", 
                y="congestion", 
                title="Congestion Over Time",
                color_discrete_sequence=["#e85f5f"]
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
            
            # Plot Queue Length over Time
            fig3 = px.line(
                hist_df, 
                x="time", 
                y="queue_length", 
                title="Queue Length Over Time",
                color_discrete_sequence=["#5fb3e8"]
            )
            fig3.update_layout(height=400)
            st.plotly_chart(fig3, use_container_width=True)