import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import joblib
import qa
import dashboard
from PyPDF2 import PdfReader


# ✅ ---- Inject custom CSS ----
st.markdown("""
<style>
.st-emotion-cache-umot6g {
    display: inline-flex;
    -webkit-box-align: center;
    align-items: center;
    -webkit-box-pack: center;
    justify-content: center;
    font-weight: 400;
    padding: 12px 16px;
    border-radius: 0.5rem;
    min-height: 2.5rem;
    margin: 0px 0px 0.5rem 0px;
    line-height: 1.6;
    text-transform: none;
    font-size: inherit;
    font-family: inherit;
    color: inherit;
    width: 100%;
    cursor: pointer;
    user-select: none;
    background-color: rgb(43, 44, 54);
    border: 1px solid rgba(250, 250, 250, 0.2);
}

.st-emotion-cache-umot6g:hover {
    border-color: #14C76D;
    color: #14C76D;
}
.st-emotion-cache-umot6g:active {
    color: #14C76D;
    border-color: #14C76D;
    background-color: transparent;
}
.st-emotion-cache-z8vbw2 {
    display: inline-flex;
    -webkit-box-align: center;
    align-items: center;
    -webkit-box-pack: center;
    justify-content: center;
    font-weight: 400;
    padding: 12px 16px;
    border-radius: 0.5rem;
    min-height: 2.5rem;
    margin: 0px;
    line-height: 1.6;
    text-transform: none;
    font-size: inherit;
    font-family: inherit;
    color: inherit;
    width: auto;
    cursor: pointer;
    user-select: none;
    background-color: rgb(19, 23, 32);
    border: 1px solid rgba(250, 250, 250, 0.2);
}
.st-emotion-cache-z8vbw2:hover {
    border-color: #14C76D;
    color: #14C76D;
}
.st-emotion-cache-z8vbw2:active{
border-color:#14C76D !important;
color:#14C76D !important;
background:transparent;
}
.st-emotion-cache-z8vbw2:focus:not(:active){
border-color:#14C76D !important;
color:#14C76D !important;
background:transparent;
}
.st-emotion-cache-umot6g:focus:not(:active){
border-color:#14C76D !important;
color:#14C76D !important;
background:transparent;
}
.st-cc{
border-bottom-color: #14C79D !important;   
}
.st-cb{
border-top-color:#14C79D !important;    
} 
.st-ca{
border-right-color:#14C79D !important;
} 
.st-c9{
border-left-color:#14C79D !important;
}
.st-dd{
    height:3rem;
    }
.st-emotion-cache-9gx57n {
    display: flex;
    flex-flow: row;
    -webkit-box-align: center;
    align-items: center;
    height: 3rem;
    border-width: 1px;
    border-style: solid;
    border-color: #14C79D;
    transition-duration: 200ms;
    transition-property: border;
    transition-timing-function: cubic-bezier(0.2, 0.8, 0.4, 1);
    border-radius: 0.5rem;
    overflow: hidden;
}
.st-emotion-cache-9gx57n.focused {
    border-color: #14C79D !important; 
}
.st-d1 {
    line-height: 1.96;
}
</style>
""", unsafe_allow_html=True)


# ✅ Load ML Models
risk_model = joblib.load("risk_model.pkl")
premium_model = joblib.load("premium_model.pkl")

def run_app():
    st.title("📋Underwriter System (ML Powered)")

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
    st.sidebar.title("📋 Navigation")
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

        file_type = st.radio("Select file type", ["Excel (.xlsx)", "PDF (.pdf)"])
        uploaded_file = st.file_uploader("Choose file", type=['xlsx', 'pdf'])

        if uploaded_file is not None:
            if file_type == "Excel (.xlsx)":
                df = pd.read_excel(uploaded_file)
                st.write(df)

                if st.button("Save Excel to DB", key="save_excel"):
                    for _, row in df.iterrows():
                        cur.execute("""
                            INSERT INTO vehicle_inspection 
                            (user_id, client_name, model_year, make_name, sub_make_name, tracker_id, suminsured, clam_amount, grosspremium, netpremium, no_of_claims, vehicle_capacity)
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
                    st.success("✅ Excel data inserted into vehicle_inspection!")

            elif file_type == "PDF (.pdf)":
                pdf = PdfReader(uploaded_file)
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                st.session_state['pdf_context'] = text
                st.success("✅ PDF uploaded and context saved for Q&A!")

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