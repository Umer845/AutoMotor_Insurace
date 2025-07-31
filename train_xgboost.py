import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

df = pd.read_csv("vehicle_inspection.csv")

df['risk_level'] = df['no_of_claims'].apply(lambda x: 'Low' if x <= 1 else 'Moderate' if x <= 3 else 'High')
le_risk = LabelEncoder()
df['risk_level_encoded'] = le_risk.fit_transform(df['risk_level'])

X_risk = df[['model_year', 'no_of_claims', 'suminsured', 'grosspremium', 'netpremium']]
y_risk = df['risk_level_encoded']

X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_risk, y_risk, test_size=0.2, random_state=42)

risk_model = xgb.XGBClassifier()
risk_model.fit(X_train_r, y_train_r)

print(f"Risk Model Accuracy: {risk_model.score(X_test_r, y_test_r) * 100:.2f}%")

joblib.dump(risk_model, "risk_model.pkl")
joblib.dump(le_risk, "risk_label_encoder.pkl")

df['premium_rate'] = (df['netpremium'] / df['suminsured']) * 100

X_premium = df[['model_year', 'no_of_claims', 'suminsured', 'grosspremium', 'netpremium']]
y_premium = df['premium_rate']

X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_premium, y_premium, test_size=0.2, random_state=42)

premium_model = xgb.XGBRegressor()
premium_model.fit(X_train_p, y_train_p)

print(f"Premium Model R^2 Score: {premium_model.score(X_test_p, y_test_p) * 100:.2f}%")

joblib.dump(premium_model, "premium_model.pkl")

print("✅ Models saved!")
