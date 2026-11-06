"""
Simplified ML Service - Local Training (No MLflow, No Kafka)
Trains and saves model locally for use with backend
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import pickle
import logging
from pathlib import Path
import warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

def prepare_data(df):
    """Prepare and preprocess the data"""
    # Convert numeric columns
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
    for col in numeric_columns:
        df[col] = df[col].astype('float64')

    # Separate features and target
    X = df.drop('price', axis=1)
    y = df['price']

    # Label encode categorical columns
    label_encoders = {}
    categorical_columns = ['model', 'transmission', 'fuelType']
    for column in categorical_columns:
        le = LabelEncoder()
        X[column] = le.fit_transform(X[column])
        label_encoders[column] = le

    return X, y, label_encoders

def train_model():
    """Train Random Forest model and save artifacts"""
    
    # Load data - try multiple paths
    script_dir = Path(__file__).parent  # ml_service directory
    project_root = script_dir.parent    # car-price-predictor directory
    
    # Try different possible paths
    possible_paths = [
        project_root / 'data' / 'ford.csv',
        Path('data/ford.csv'),
        Path('../data/ford.csv'),
        Path('D:/NOVIDH/github_data_of_Novidh/car-price-predictor/data/ford.csv'),
    ]
    
    data_path = None
    for path in possible_paths:
        if path.exists():
            data_path = path
            break
    
    if data_path is None:
        logger.error(f"Tried paths: {[str(p.resolve()) for p in possible_paths]}")
        raise FileNotFoundError("Data file ford.csv not found in any expected location")
    
    df = pd.read_csv(data_path)
    logger.info(f"Dataset shape: {df.shape}")

    # Prepare data
    X, y, label_encoders = prepare_data(df)
    
    # Save label encoders
    encoder_path = Path(__file__).parent / 'label_encoders.pkl'
    with open(encoder_path, 'wb') as f:
        pickle.dump(label_encoders, f)
    logger.info(f"Saved label encoders to {encoder_path}")

    # Scale numerical features
    numerical_features = ['year', 'mileage', 'tax', 'mpg', 'engineSize']
    scaler = StandardScaler()

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Fit and transform
    X_train[numerical_features] = scaler.fit_transform(X_train[numerical_features])
    X_test[numerical_features] = scaler.transform(X_test[numerical_features])

    # Save scaler
    scaler_path = Path(__file__).parent / 'scaler.pkl'
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    logger.info(f"Saved scaler to {scaler_path}")

    # Train Random Forest
    logger.info("Training Random Forest model...")
    params = {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': 42,
        'n_jobs': -1
    }
    
    rf = RandomForestRegressor(**params)
    rf.fit(X_train, y_train)

    # Evaluate
    y_pred = rf.predict(X_test)
    metrics = {
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
        'mae': float(mean_absolute_error(y_test, y_pred)),
        'r2': float(r2_score(y_test, y_pred))
    }

    logger.info(f"Model metrics: {metrics}")
    logger.info(f"  RMSE: £{metrics['rmse']:,.2f}")
    logger.info(f"  MAE: £{metrics['mae']:,.2f}")
    logger.info(f"  R²: {metrics['r2']:.4f}")

    # Save model
    model_path = Path(__file__).parent / 'model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(rf, f)
    logger.info(f"Saved model to {model_path}")

    logger.info("✅ Model trained and saved successfully!")
    return rf, label_encoders, scaler, metrics

if __name__ == "__main__":
    try:
        train_model()
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        raise
