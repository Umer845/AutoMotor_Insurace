import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import psycopg2

def show_dashboard():
    st.set_page_config(layout="wide")

    st.markdown(
        """
        <style>
        body {
            background-color: #121212;
            color: #ffffff;
        }
        .block-container {
            padding: 2rem;
        }
        .metric-box {
            background: #1f1f1f;
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown("##### Overview of Vehicle Risk & Premium Data")

    # ---- DB Connection ----
    conn = psycopg2.connect(
        dbname="Underwritter",
        user="postgres",
        password="United2025",
        host="localhost",
        port="5432"
    )

    df = pd.read_sql("SELECT * FROM vehicle_risk", conn)

    if df.empty:
        st.warning("No risk data found yet. Please calculate some risk profiles first.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            fig1 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=len(df),
                title={'text': "Total Records"},
                gauge={'axis': {'range': [0, len(df) + 10]}, 'bar': {'color': "#f39c12"}},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
            fig1.update_layout(paper_bgcolor="#1f1f1f", font={'color': "white"})
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=df['premium_rate'].mean(),
                number={'suffix': "%"},
                title={'text': "Avg Premium Rate"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00cec9"}},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
            fig2.update_layout(paper_bgcolor="#1f1f1f", font={'color': "white"})
            st.plotly_chart(fig2, use_container_width=True)

        with col3:
            fig3 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=df['make_name'].nunique(),
                title={'text': "Unique Makes"},
                gauge={'axis': {'range': [0, df['make_name'].nunique() + 5]}, 'bar': {'color': "#e84393"}},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
            fig3.update_layout(paper_bgcolor="#1f1f1f", font={'color': "white"})
            st.plotly_chart(fig3, use_container_width=True)

        st.divider()

        # ---- Risk Level Distribution ----
        fig4 = px.histogram(
            df, x="risk_level", color="risk_level",
            title="Risk Level Distribution",
            template="plotly_dark"
        )
        fig4.update_layout(
            plot_bgcolor="#1f1f1f",
            paper_bgcolor="#1f1f1f",
            bargap=0.3,
            xaxis_title="Risk Level",
            yaxis_title="Count"
        )
        st.plotly_chart(fig4, use_container_width=True)

        # ---- Premium Rate by Make Name ----
        fig5 = px.box(
            df, x="make_name", y="premium_rate", color="risk_level",
            title="Premium Rate by Make Name & Risk Level",
            template="plotly_dark"
        )
        fig5.update_layout(
            plot_bgcolor="#1f1f1f",
            paper_bgcolor="#1f1f1f",
            boxmode="group",
            xaxis_title="Make Name",
            yaxis_title="Premium Rate (%)"
        )
        st.plotly_chart(fig5, use_container_width=True)

        # ---- Average Premium by Year ----
        avg_by_year = df.groupby(['model_year'])['premium_rate'].mean().reset_index()
        fig6 = px.line(
            avg_by_year,
            x="model_year", y="premium_rate",
            title="Average Premium Rate Over Model Years",
            markers=True,
            template="plotly_dark"
        )
        fig6.update_layout(
            plot_bgcolor="#1f1f1f",
            paper_bgcolor="#1f1f1f",
            xaxis_title="Model Year",
            yaxis_title="Avg Premium Rate (%)"
        )
        st.plotly_chart(fig6, use_container_width=True)

    conn.close()
