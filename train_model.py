import numpy as np
import pandas as pd
from model import SimpleWeatherModel
import joblib
from sklearn.preprocessing import LabelEncoder


def train_weather_model_from_csv(csv_path="seattle-weather.csv"):
    # Load data
    df = pd.read_csv(csv_path)
    feature_cols = [col for col in df.columns if col not in ["date", "weather"]]
    X = df[feature_cols].values
    y = df["weather"].values
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    # Train model
    model = SimpleWeatherModel()
    model.train(X, y_encoded)
    return model, le

if __name__ == "__main__":
    model, le = train_weather_model_from_csv()
    model.save("weather_model.joblib")
    joblib.dump(le, "weather_label_encoder.joblib")
    print("Model and label encoder trained and saved.")
