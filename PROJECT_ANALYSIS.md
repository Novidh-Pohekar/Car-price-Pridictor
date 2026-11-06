# Car Price Predictor - System Analysis & Architecture

## 📋 Project Overview
A comprehensive machine learning system for predicting car prices using Ford vehicle data. The project implements a complete microservices architecture with real-time data processing, ML model management, and an interactive web interface.

---

## 🏗️ System Architecture

### High-Level Flow
```
User Interface (Streamlit)
         ↓
    FastAPI Backend (REST API)
         ↓
   PostgreSQL Database
         ↓
  Debezium CDC (Change Data Capture)
         ↓
    Apache Kafka (Streaming)
         ↓
  ML Service (Real-time Prediction)
         ↓
MLflow + MinIO (Model Registry & Storage)
```

### Key Components

#### 1. **Frontend - Streamlit App** (`streamlit_app/app.py`)
- **Purpose**: Interactive web interface for car data visualization and prediction
- **Port**: 8501
- **Features**:
  - Add new car listings via form
  - View car database with filtering
  - Real-time price predictions visualization
  - Charts:
    - Price distribution histogram
    - Price vs mileage scatter plot
    - Price by year box plot
    - Predicted vs actual price comparison

#### 2. **Backend API - FastAPI** (`backend/main.py`)
- **Purpose**: REST API for car data management
- **Port**: 8000
- **Database**: PostgreSQL (cars_db)
- **Key Features**:
  - CRUD operations for car listings
  - Data validation (transmission types, fuel types)
  - Kafka producer integration (sends data to stream)
  - Kafka consumer integration (receives predictions)
  - Updates database with predicted prices
  
- **Endpoints**:
  - `GET /cars` - Fetch all cars
  - `POST /cars` - Add new car
  - `GET /cars/{car_id}` - Get specific car
  - `GET /health` - Health check

- **Data Model**:
  ```
  Car
  ├── id (Primary Key)
  ├── model (e.g., "Fiesta", "Focus")
  ├── year (1900-current)
  ├── price (actual price)
  ├── transmission (Manual/Automatic/Semi-Auto)
  ├── mileage (miles driven)
  ├── fuelType (Petrol/Diesel/Hybrid/Electric)
  ├── tax (tax amount)
  ├── mpg (miles per gallon)
  ├── engineSize (in liters)
  └── predicted_price (ML output)
  ```

#### 3. **ML Service** (`ml_service/`)
- **Purpose**: Real-time prediction engine consuming Kafka messages
- **Main Components**:

  **a) Model Training** (`train.py`):
  - Loads Ford car data (17,967 records)
  - Features used:
    - Numerical: year, mileage, tax, mpg, engineSize
    - Categorical: model, transmission, fuelType
  - **Algorithm**: Random Forest Regressor
    - n_estimators: 100
    - max_depth: 10
    - Hyperparameters logged to MLflow
  - **Preprocessing**:
    - Label encoding for categorical variables
    - StandardScaler for numerical features
    - 80/20 train-test split
  - **Metrics Tracked**:
    - RMSE (Root Mean Square Error)
    - MAE (Mean Absolute Error)
    - R² Score
  - **Output**: Saves to MLflow with model artifacts

  **b) Real-time Prediction** (`main.py`):
  - Consumes messages from `cars-db.public.listings` topic (Kafka)
  - Steps:
    1. Load trained model from MLflow
    2. Load preprocessing artifacts (label encoders, scaler)
    3. Poll Kafka for new car data
    4. Preprocess incoming data
    5. Generate price prediction
    6. Publish to `cars.public.predictions` topic
  - Handles data transformation consistently with training

#### 4. **Data Streaming - Apache Kafka**
- **Port**: 9092
- **Topics**:
  - `cars-db.public.listings`: New car data from database (via Debezium CDC)
  - `cars.public.predictions`: Predicted prices from ML service
- **Zookeeper**: Port 2181 (cluster coordination)
- **Flow**:
  1. New car inserted in PostgreSQL
  2. Debezium captures the change
  3. Message published to Kafka
  4. ML service consumes and predicts
  5. Predictions published back
  6. Backend API consumes predictions
  7. Database updated with predicted_price

#### 5. **Database - PostgreSQL**
- **Port**: 5432
- **Databases**:
  - `cars_db`: Main application database
  - `mlflow`: MLflow experiment tracking
- **Configuration**: 
  - WAL level set to logical (for CDC)
  - Enables Debezium to capture changes
- **Tables**:
  - `listings`: Stores car data with predicted prices

#### 6. **Model Registry - MLflow**
- **Port**: 5000
- **Web UI**: For tracking experiments and models
- **Artifact Storage**: MinIO (S3-compatible)
- **Features**:
  - Logs model parameters
  - Tracks metrics (RMSE, MAE, R²)
  - Stores model artifacts
  - Registers models for production use
  - Manages model versions and aliases

#### 7. **Object Storage - MinIO**
- **Port**: 9000
- **Console**: 9001
- **Purpose**: S3-compatible storage for MLflow artifacts
- **Bucket**: `mlflow` (stores model files and artifacts)

#### 8. **Change Data Capture - Debezium**
- **Port**: 8083
- **Purpose**: Captures database changes in real-time
- **Source**: PostgreSQL
- **Sink**: Apache Kafka
- **Configuration**: `debezium-connector-config.json`

---

## 📊 Data Flow

### Adding a New Car (Complete Flow)

```
1. User Input (Streamlit)
   ↓
2. POST /cars (FastAPI)
   ↓
3. Insert into PostgreSQL
   ↓
4. Debezium CDC detects change
   ↓
5. Publish to cars-db.public.listings (Kafka)
   ↓
6. ML Service consumes message
   ├─ Decode JSON payload
   ├─ Extract car features
   ├─ Preprocess (encode categorical, scale numerical)
   ├─ Run Random Forest model
   └─ Get predicted price
   ↓
7. Publish to cars.public.predictions (Kafka)
   ↓
8. FastAPI Backend consumes prediction
   ├─ Extract car ID and predicted price
   ├─ Update PostgreSQL
   └─ Commit transaction
   ↓
9. Streamlit refreshes data
   ↓
10. Display in UI with prediction
```

### Data Preprocessing Pipeline

**Training Phase** (`train.py`):
```
Ford Dataset (17,967 cars)
├─ Drop 'price' column → X (features)
├─ Keep 'price' column → y (target)
│
├─ Categorical Features → Label Encoder
│  ├─ model: "Fiesta" → 0, "Focus" → 1, etc.
│  ├─ transmission: "Manual" → 0, etc.
│  └─ fuelType: "Petrol" → 0, etc.
│
├─ Numerical Features → StandardScaler
│  ├─ (value - mean) / std
│  └─ Applied to: year, mileage, tax, mpg, engineSize
│
└─ Save preprocessors
   ├─ label_encoders.pkl
   └─ scaler.pkl
```

**Inference Phase** (`main.py`):
```
New Car Data (from Kafka)
├─ Load label_encoders.pkl
├─ Load scaler.pkl
├─ Transform categorical columns
├─ Scale numerical columns
├─ Input to trained Random Forest model
└─ Output: Predicted Price
```

---

## 🚀 Technical Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Interactive UI |
| **Backend** | FastAPI | REST API |
| **Database** | PostgreSQL | Data persistence |
| **Streaming** | Apache Kafka | Real-time data flow |
| **ML Framework** | scikit-learn | Model training |
| **Model Registry** | MLflow | Model versioning |
| **Storage** | MinIO | Artifact storage |
| **CDC** | Debezium | Change capture |
| **Orchestration** | Docker Compose | Container management |

---

## 💾 Dataset

**Source**: Ford car listings in UK market

**Records**: 17,967 cars

**Features** (9 input + 1 target):
| Feature | Type | Example | Range |
|---------|------|---------|-------|
| model | categorical | Fiesta, Focus, Kuga | 16 unique models |
| year | numerical | 2019 | 2013-2020 |
| price | numerical | £12,000 | £2,000 - £70,000+ |
| transmission | categorical | Manual, Automatic | 3 types |
| mileage | numerical | 15,944 | 0 - 100,000+ miles |
| fuelType | categorical | Petrol, Diesel | 4 types |
| tax | numerical | 150 | £0 - £250 |
| mpg | numerical | 57.7 | 20 - 80+ |
| engineSize | numerical | 1.0 | 0.5 - 5.0 liters |

---

## 🤖 Machine Learning Model

**Algorithm**: Random Forest Regressor

**Why Random Forest?**
- Handles mixed feature types (categorical + numerical)
- Robust to outliers
- Captures non-linear relationships
- Good generalization

**Hyperparameters**:
```python
{
    'n_estimators': 100,      # 100 decision trees
    'max_depth': 10,          # Tree depth limit
    'min_samples_split': 2,   # Min samples for split
    'min_samples_leaf': 1,    # Min samples in leaf
    'random_state': 42        # Reproducibility
}
```

**Performance Metrics**:
- **RMSE**: Root Mean Square Error (in £)
- **MAE**: Mean Absolute Error (in £)
- **R²**: Coefficient of Determination (0-1 scale)

**Model Signature**:
- Input: Preprocessed features (numerical + encoded categorical)
- Output: Single float value (predicted price in £)

---

## 🔧 How to Use

### 1. Start All Services
```bash
docker-compose up --build
```

### 2. Train Initial Model
```bash
cd ml_service
python train.py
```

### 3. Access Applications
- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **MLflow UI**: http://localhost:5000
- **MinIO Console**: http://localhost:9001
- **Kafka UI**: http://localhost:8080

### 4. Add a Car
1. Go to Streamlit sidebar
2. Fill in car details
3. Click "Add Car"
4. System processes through entire pipeline
5. See predicted price appear in database

---

## 📈 Key Processing Steps

### Backend API Processing
1. **Validation**: Pydantic validates car data
2. **Storage**: Inserts into PostgreSQL
3. **Publishing**: Sends to Kafka topic
4. **Consumption**: Listens for predictions
5. **Update**: Updates database with prediction

### ML Service Processing
1. **Consumption**: Reads from Kafka topic
2. **Extraction**: Gets car data from message
3. **Validation**: Checks required fields
4. **Preprocessing**: Encodes and scales features
5. **Prediction**: Runs through RF model
6. **Publishing**: Sends prediction to Kafka

### Frontend Rendering
1. **API Call**: Fetches cars from backend
2. **Caching**: Caches data for 5 minutes
3. **Display**: Shows cars in table
4. **Visualization**: Creates interactive charts
5. **Form**: Allows adding new cars

---

## 🔄 Asynchronous Event Processing

The system uses **event-driven architecture**:

1. **Synchronous**: User adds car → FastAPI saves to DB (immediate)
2. **Asynchronous**: 
   - DB change → Debezium captures
   - Published to Kafka
   - ML Service consumes
   - ML Service predicts
   - Backend consumer updates prediction

**Benefits**:
- Decoupled components
- Scalable prediction service
- Non-blocking operations
- Real-time data flow

---

## 🛡️ Data Validation

**FastAPI Validation**:
```python
# Transmission must be in allowed set
transmission ∈ {Manual, Automatic, Semi-Auto}

# Fuel type must be in allowed set
fuelType ∈ {Petrol, Diesel, Hybrid, Electric}

# Year must be realistic
1900 ≤ year ≤ current_year

# Prices must be positive
price > 0

# Engine size must be positive
engineSize > 0

# Mileage must be non-negative
mileage ≥ 0
```

---

## 📦 Docker Services Summary

| Service | Image | Port(s) | Purpose |
|---------|-------|---------|---------|
| PostgreSQL | postgres:15 | 5432 | Data storage |
| Zookeeper | cp-zookeeper | 2181 | Kafka coordination |
| Kafka | cp-kafka | 9092 | Message streaming |
| MLflow | Custom | 5000 | Model registry |
| MinIO | Custom | 9000/9001 | Artifact storage |
| Debezium | Custom | 8083 | CDC connector |
| Backend | Custom | 8000 | FastAPI server |
| Streamlit | Custom | 8501 | Web UI |

---

## 🎯 Key Insights

1. **Real-time Processing**: Uses Kafka streaming for immediate predictions
2. **Reproducibility**: Label encoders and scalers saved for consistent preprocessing
3. **Model Management**: MLflow tracks experiments and versions
4. **Data Integrity**: CDC ensures no data loss through change capture
5. **Scalability**: Microservices architecture allows independent scaling
6. **API-First**: Backend API enables multi-client access (web, mobile, etc.)
7. **Interactive Dashboard**: Streamlit provides business-friendly interface

---

## ⚠️ Important Notes

1. **Training Data**: Model trained on Ford cars only (domain-specific)
2. **Categorical Encoding**: Uses ordinal encoding; order doesn't matter for Random Forest
3. **Feature Scaling**: Only numerical features scaled (crucial for fair contribution)
4. **Kafka Persistence**: Messages consumed then discarded (not for backfilling)
5. **Model Artifact Storage**: All models stored in MinIO S3-compatible storage
6. **Error Handling**: Services include retry logic and logging

---

## 🔍 Potential Improvements

1. Add feature importance visualization
2. Implement model retraining pipeline
3. Add A/B testing for new models
4. Implement prediction confidence intervals
5. Add anomaly detection for outlier predictions
6. Implement model explainability (SHAP values)
7. Add data drift monitoring
8. Create alerts for prediction failures
