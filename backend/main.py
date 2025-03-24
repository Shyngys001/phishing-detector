from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Можно указать конкретно: ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Датасет и обучение модели (встроенное)
data = {
    'text': [
        'https://secure-login.com',  # phishing
        'Dear user, please verify your account',  # phishing
        'https://google.com',  # legit
        'Click here to win a free iPhone',  # phishing
        'Meeting at 10am tomorrow',  # legit
        'http://bank-update.ru/login',  # phishing
        'Hi John, see you at the office',  # legit
        'Your invoice is attached',  # legit
        'Update your payment info now',  # phishing
        'https://my.university.kz'  # legit
    ],
    'label': [1, 1, 0, 1, 0, 1, 0, 0, 1, 0]
}
df = pd.DataFrame(data)

def extract_features(text):
    has_https = int('https' in text.lower())
    text_len = len(text)
    num_dots = text.count('.')
    suspicious_keywords = ['login', 'verify', 'bank', 'click', 'payment', 'update', 'free']
    contains_keywords = int(any(word in text.lower() for word in suspicious_keywords))
    return [has_https, text_len, num_dots, contains_keywords]

X = df['text'].apply(extract_features).tolist()
y = df['label']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

class InputData(BaseModel):
    url_or_text: str

@app.post("/predict")
def predict_phishing(data: InputData):
    try:
        features = extract_features(data.url_or_text)
        prediction = model.predict([features])[0]
        result = "Phishing" if prediction == 1 else "Legitimate"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))