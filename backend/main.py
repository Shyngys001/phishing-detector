import os
import random
import logging
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier
import uvicorn

# ----------------------------------------------------
# Настройки логирования
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ----------------------------------------------------
# Пути к файлам
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "phishing.csv")
MODEL_PATH = os.path.join(BASE_DIR, "phishing_model.pkl")

# ----------------------------------------------------
# Функция генерирует N=1000 строк для датасета
# ----------------------------------------------------
def generate_large_dataset(n=1000):
    phishing_patterns = [
        "Verify your account at {link}",
        "Important: payment update required at {link}",
        "FREE gift for you: click {link} now!",
        "Your bank details need verification: {link}",
        "Alert: confirm your billing info at {link}",
        "Urgent: password reset needed at {link}",
        "Login to secure your account: {link}",
        "Update your bank credentials: {link}",
        "You have won a prize! Visit {link} now!",
        "Please confirm your payment via {link}"
    ]
    legit_patterns = [
        "Check our official website: {link}",
        "Welcome to our corporate portal: {link}",
        "New article posted: {link}",
        "Thank you for using our services",
        "Monthly newsletter update at {link}",
        "Hello, just checking in to say hi.",
        "Your order has shipped. Track it here: {link}",
        "Download your invoice at {link}",
        "Share your feedback at {link}",
        "Learn more about our solutions: {link}"
    ]
    phishing_domains = [
        "login-securebank.com", "payment-update.com", "free-offer.net", "bank-verify.org",
        "click4prize.io", "secure-check.org", "verify-account.me", "urgent-update.net"
    ]
    legit_domains = [
        "www.google.com", "www.wikipedia.org", "www.medium.com", "www.youtube.com",
        "www.shoponline.com", "www.delivery-service.com", "gov.kz", "travel.com"
    ]

    lines = ["text,label"]  # заголовок CSV
    for i in range(n):
        is_phishing = random.random() < 0.5
        if is_phishing:
            pattern = random.choice(phishing_patterns)
            domain = random.choice(phishing_domains)
            link = f"https://{domain}/update?id={random.randint(100,999)}"
            text = pattern.format(link=link)
            label = 1
        else:
            pattern = random.choice(legit_patterns)
            domain = random.choice(legit_domains)
            link = f"https://{domain}/info?ref={random.randint(100,999)}"
            text = pattern.format(link=link)
            label = 0

        # 5% убираем ссылку
        if random.random() < 0.05:
            text = text.split(":")[0]

        text_escaped = text.replace('"', '""')  # экранируем кавычки
        lines.append(f"\"{text_escaped}\",{label}")
    return "\n".join(lines)

# ----------------------------------------------------
# Генерация CSV-файла на 1000 строк
# ----------------------------------------------------
def create_csv():
    dataset = generate_large_dataset(n=1000)
    with open(DATASET_PATH, "w", encoding="utf-8") as f:
        f.write(dataset)
    logging.info(f"Сгенерирован phishing.csv на 1000 строк: {DATASET_PATH}")

# ----------------------------------------------------
# Извлекаем 4 признака из текста
# ----------------------------------------------------
def extract_features(text: str):
    has_https = int('https' in text.lower())
    text_len = len(text)
    num_dots = text.count('.')
    suspicious_keywords = ['login', 'verify', 'bank', 'click', 'payment', 'update', 'free']
    contains_keywords = int(any(word in text.lower() for word in suspicious_keywords))
    return [has_https, text_len, num_dots, contains_keywords]

# ----------------------------------------------------
# Обучение модели
# ----------------------------------------------------
def train_model():
    logging.info("⏳ Обучаем модель с нуля на 1000 строках...")
    df = pd.read_csv(DATASET_PATH)
    if "text" not in df.columns or "label" not in df.columns:
        raise RuntimeError("CSV-файл не содержит нужных колонок: text, label.")

    X = df["text"].apply(extract_features).tolist()
    y = df["label"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)
    logging.info("✅ Модель обучена и сохранена в phishing_model.pkl.")
    return model

# ----------------------------------------------------
# 1. Создаём/обновляем CSV, 2. Загружаем/обучаем модель
#    -- ВАЖНО: это делаем при импорте, но app объявляем
#       на уровне модуля, чтобы Render мог найти
# ----------------------------------------------------
create_csv()
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        logging.info("✅ Модель загружена из файла phishing_model.pkl.")
    except Exception as e:
        logging.warning(f"⚠️ Не удалось загрузить модель: {e}. Переобучаем...")
        model = train_model()
else:
    model = train_model()

# ----------------------------------------------------
# САМ APP = FastAPI, на уровне модуля
# ----------------------------------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        logging.error(f"Ошибка при предсказании: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------
# Точка входа (для локального запуска)
# На Render указывать: backend.main:app
# ----------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)