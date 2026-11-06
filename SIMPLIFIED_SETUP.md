# Simplified Car Price Predictor - No Docker Required

## 📋 Prerequisites

- **Python 3.9+**
- **PostgreSQL 12+** (or use SQLite as fallback)
- **pip** (Python package manager)

---

## 🚀 Quick Setup (5 minutes)

### **Step 1: Create & Activate Virtual Environment**

```powershell
cd "d:\NOVIDH\github_data_of_Novidh\car-price-predictor"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### **Step 2: Install All Dependencies**

```powershell
pip install pandas scikit-learn mlflow streamlit fastapi uvicorn psycopg2-binary pydantic requests plotly python-dotenv numpy
```

### **Step 3: Setup Database (PostgreSQL)**

**Option A: Using PostgreSQL (Recommended)**

1. Install PostgreSQL from: https://www.postgresql.org/download/windows/
2. Create database:
```powershell
# Open PostgreSQL command line
psql -U postgres

# In psql:
CREATE DATABASE cars_db;
\c cars_db

CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    model VARCHAR(100),
    year INTEGER,
    price DECIMAL,
    transmission VARCHAR(50),
    mileage INTEGER,
    fuelType VARCHAR(50),
    tax DECIMAL,
    mpg DECIMAL,
    engineSize DECIMAL,
    predicted_price DECIMAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

\q
```

**Option B: Using SQLite (No installation needed)**
- Database is created automatically in local file
- Use `sqlite:///cars.db` in connection string

---

## 🤖 Step 4: Train the Model

```powershell
cd ml_service
python train_local.py
```

Should complete in 30-60 seconds with output like:
```
Model metrics: {'rmse': 2500, 'mae': 1800, 'r2': 0.92}
Model saved successfully
```

---

## 🚀 Step 5: Start Backend API

**New PowerShell terminal:**
```powershell
cd "d:\NOVIDH\github_data_of_Novidh\car-price-predictor\backend"
uvicorn main_local:app --reload --port 8000
```

Should show:
```
Uvicorn running on http://127.0.0.1:8000
```

---

## 🎨 Step 6: Start Streamlit Frontend

**New PowerShell terminal:**
```powershell
cd "d:\NOVIDH\github_data_of_Novidh\car-price-predictor\streamlit_app"
streamlit run app_local.py
```

Browser opens to: **http://localhost:8501**

---

## ✅ Test It

1. Go to http://localhost:8501
2. Fill in car details in sidebar
3. Click "Add Car"
4. See predicted price appear instantly!

---

## 📁 What's Different?

| Original | Simplified |
|----------|-----------|
| Kafka streaming | Direct API calls |
| Debezium CDC | No change capture needed |
| MLflow server | Local file storage |
| MinIO S3 storage | Local file storage |
| 5+ Docker containers | Just your machine |
| 90+ second startup | <5 second startup |

---

## 🔧 Configuration

Edit `config.py` if needed:

```python
# Database
DATABASE_URL = "postgresql://postgres:postgres123@localhost/cars_db"
# or for SQLite:
# DATABASE_URL = "sqlite:///cars.db"

# MLflow
MLFLOW_BACKEND = "./mlruns"  # Local directory

# Prediction
MODEL_PATH = "./ml_service/model.pkl"
ENCODER_PATH = "./ml_service/label_encoders.pkl"
SCALER_PATH = "./ml_service/scaler.pkl"
```

---

## 🆘 Troubleshooting

**PostgreSQL connection error?**
```powershell
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# If not, start PostgreSQL service (Windows)
net start postgresql-x64-14  # Version may differ
```

**Port 8000 already in use?**
```powershell
uvicorn main_local:app --reload --port 8001
```

**Port 8501 already in use?**
```powershell
streamlit run app_local.py --server.port 8502
```

**Model not found?**
Make sure you ran `python train_local.py` first

---

## 📊 Performance

- **Model Training**: 30-60 seconds
- **Single Prediction**: <100ms
- **API Response**: 50-100ms
- **Streamlit Refresh**: 1-2 seconds

---

## 🎯 Next Steps

1. Run the 2-terminal setup above
2. Add sample cars
3. Check predictions are reasonable
4. Explore data visualizations
5. Modify model hyperparameters if needed
