import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import joblib
import qa
import dashboard

# ✅ Load ML Models
risk_model = joblib.load("risk_model.pkl")
premium_model = joblib.load("premium_model.pkl")

def run_app():
    st.title("📋 Underwriter System (ML Powered)")

    # ---- DB CONNECTION ----
    conn = psycopg2.connect(
        dbname="Underwritter",
        user="postgres",
        password="United2025",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    # ---- SESSION ----
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = 1

    if 'active_page' not in st.session_state:
        st.session_state['active_page'] = "Upload File"

    # ---- Sidebar ----
    if st.sidebar.button("Upload File"):
        st.session_state['active_page'] = "Upload File"
    if st.sidebar.button("Risk Profile"):
        st.session_state['active_page'] = "Risk Profile"
    if st.sidebar.button("Premium Calculation"):
        st.session_state['active_page'] = "Premium Calculation"
    if st.sidebar.button("Dashboard"):
       st.session_state['active_page'] = "Dashboard"
    if st.sidebar.button("Question Answer"):
        st.session_state['active_page'] = "Question Answer"

    # ================================
    # 🚩 Upload Page
    # ================================
    if st.session_state['active_page'] == "Upload File":
        st.subheader("Upload Vehicle Data")

        uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file)
            st.write(df)

            if st.button("Save to DB"):
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO vehicle_inspection
                        (user_id, client_name, model_year, make_name, sub_make_name,
                        tracker_id, suminsured, clam_amount, grosspremium, netpremium,
                        no_of_claims, vehicle_capacity)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        st.session_state['user_id'],
                        row['CLIENT_NAME'],
                        row['MODEL_YEAR'],
                        row['MAKE_NAME'],
                        row['SUB_MAKE_NAME'],
                        row['TRACKER_ID'],
                        row['SUMINSURED'],
                        row['CLM_AMOUNT'],
                        row['GROSSPREMIUM'],
                        row['NETPREMIUM'],
                        row['NO_OF_CLAIMS'],
                        row['VEHICLE_CAPACITY']
                    ))
                conn.commit()
                st.success("✅ Data saved!")

    # ================================
    # 🚩 Risk Profile Page
    # ================================
    elif st.session_state['active_page'] == "Risk Profile":
        st.subheader("Calculate Risk Profile (ML)")

        driver_age = st.number_input("Driver Age", 18, 100)
        make_name = st.text_input("Make Name")
        sub_make_name = st.text_input("Sub Make Name")
        model_year = st.number_input("Model Year", 1990, 2035)

        if st.button("Calculate Risk"):
            current_year = datetime.now().year

            # ✅ Check: If older than 5 years — do NOT calculate
            if model_year < (current_year - 5):
                st.warning(f"⚠️ Vehicle too old. Must be {current_year - 5} or newer.")
            else:
                if model_year == (current_year + 1):  # If 2025
                    cur.execute("""
                        SELECT AVG(no_of_claims)::FLOAT, AVG(vehicle_capacity)::FLOAT
                        FROM vehicle_inspection
                        WHERE upper(make_name) = %s AND upper(sub_make_name) = %s
                        AND model_year BETWEEN %s AND %s
                    """, (make_name.upper(), sub_make_name.upper(), current_year - 4, current_year - 1))
                    used_year = current_year  # Input to ML
                else:
                    cur.execute("""
                        SELECT AVG(no_of_claims)::FLOAT, AVG(vehicle_capacity)::FLOAT
                        FROM vehicle_inspection
                        WHERE upper(make_name) = %s AND upper(sub_make_name) = %s
                        AND model_year BETWEEN %s AND %s
                    """, (make_name.upper(), sub_make_name.upper(), model_year - 3, model_year))
                    used_year = model_year

                row = cur.fetchone()
                if row and all(v is not None for v in row):
                    avg_claims, avg_capacity = row

                    features = [[used_year, avg_claims, avg_capacity, driver_age]]
                    risk_numeric = int(risk_model.predict(features)[0])

                    risk_map = ["Low", "Low to Moderate", "Moderate to High", "High"]
                    risk_level = risk_map[risk_numeric]

                    st.markdown(f"""
                        <div style="background-color: #0c2d48; color: #ffffff; padding: 16px; border-radius: 6px;">
                            ✅ <b>Risk Profile Level:</b> {risk_level}<br>
                            🔢 <b>Avg Claims:</b> {avg_claims:.2f}<br>
                            🚗 <b>Capacity:</b> {avg_capacity:.2f}
                        </div>
                    """, unsafe_allow_html=True)

                    cur.execute("""
                        INSERT INTO vehicle_risk
                        (user_id, driver_age, make_name, sub_make_name, model_year, capacity, num_claims, risk_level, created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id
                    """, (
                        st.session_state['user_id'],
                        driver_age,
                        make_name, sub_make_name, model_year,
                        avg_capacity, avg_claims, risk_level,
                        datetime.now()
                    ))
                    st.session_state['risk_id'] = cur.fetchone()[0]
                    conn.commit()
                    st.success("✅ Saved!")
                else:
                    st.error("❌ No data found!")

    # ================================
    # 🚩 Premium Calculation Page
    # ================================
    elif st.session_state['active_page'] == "Premium Calculation":
        st.subheader("Calculate Premium (ML)")

        if 'risk_id' not in st.session_state:
            st.warning("⚠️ Run Risk Profile first.")
        else:
            make_name = st.text_input("Make Name", key="premium_make")
            sub_make_name = st.text_input("Sub Make Name", key="premium_sub_make")
            model_year = st.number_input("Model Year", 1990, 2035, key="premium_year")

            if st.button("Calculate Premium"):
                current_year = datetime.now().year

                if model_year == (current_year + 1):  # If 2025
                    cur.execute("""
                        SELECT suminsured, netpremium
                        FROM vehicle_inspection
                        WHERE upper(make_name) = %s AND upper(sub_make_name) = %s
                        AND model_year = %s
                        ORDER BY id DESC LIMIT 1
                    """, (make_name.upper(), sub_make_name.upper(), current_year - 1))
                else:
                    cur.execute("""
                        SELECT suminsured, netpremium
                        FROM vehicle_inspection
                        WHERE upper(make_name) = %s AND upper(sub_make_name) = %s
                        AND model_year = %s
                        ORDER BY id DESC LIMIT 1
                    """, (make_name.upper(), sub_make_name.upper(), model_year - 1))

                row = cur.fetchone()
                if row and all(v is not None for v in row):
                    suminsured, netpremium = row
                    features = [[model_year, suminsured, netpremium]]
                    predicted_premium = float(premium_model.predict(features)[0])

                    st.success(f"💰 Predicted Premium: {predicted_premium:.2f}")

                    cur.execute("""
                        UPDATE vehicle_risk
                        SET premium_rate = %s
                        WHERE id = %s
                    """, (predicted_premium, st.session_state['risk_id']))
                    conn.commit()
                else:
                    st.error("❌ No inspection data found!")

if __name__ == "__main__":
    run_app()


 # ✅ ---- Render correct page ----
   
    if st.session_state['active_page'] == "Dashboard":
        dashboard.show_dashboard()
    elif st.session_state['active_page'] == "Question Answer":
        qa.show_question_answer()