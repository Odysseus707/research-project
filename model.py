import numpy as np
from sklearn.neural_network import MLPClassifier
import joblib


class SimpleWeatherModel:
    def __init__(self):
        self.model = MLPClassifier(
            hidden_layer_sizes=(16,), max_iter=500, random_state=42
        )
        self.is_trained = False

    def train(self, X, y):
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, X):
        if not self.is_trained:
            raise ValueError("Model not trained yet.")
        return self.model.predict(X)

    def save(self, path):
        joblib.dump(self.model, path)

    def load(self, path):
        self.model = joblib.load(path)
        self.is_trained = True
