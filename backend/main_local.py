"""
Simplified Backend API - Local Mode (No Kafka)
Uses PostgreSQL or SQLite database directly
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import pickle
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Car Price Prediction API - Local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Database Configuration =====
# Option 1: PostgreSQL (recommended)
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/cars_db"

# Option 2: SQLite (no installation needed)
SQLALCHEMY_DATABASE_URL = "sqlite:///./cars.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ===== Database Models =====
class Car(Base):
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String)
    year = Column(Integer)
    price = Column(Float)
    transmission = Column(String)
    mileage = Column(Integer)
    fuelType = Column(String)
    tax = Column(Float)
    mpg = Column(Float)
    engineSize = Column(Float)
    predicted_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ===== Pydantic Models =====
class CarBase(BaseModel):
    model: str = Field(..., example="Fiesta")
    year: int = Field(..., ge=1900, le=datetime.now().year, example=2019)
    price: float = Field(..., gt=0, example=12000)
    transmission: str = Field(..., example="Manual")
    mileage: int = Field(..., ge=0, example=25000)
    fuelType: str = Field(..., example="Petrol")
    tax: float = Field(..., ge=0, example=145)
    mpg: float = Field(..., ge=0, example=55.4)
    engineSize: float = Field(..., gt=0, example=1.0)

    @validator('transmission')
    def validate_transmission(cls, v):
        allowed = {'Manual', 'Automatic', 'Semi-Auto'}
        if v not in allowed:
            raise ValueError(f'transmission must be one of {allowed}')
        return v

    @validator('fuelType')
    def validate_fuel_type(cls, v):
        allowed = {'Petrol', 'Diesel', 'Hybrid', 'Electric'}
        if v not in allowed:
            raise ValueError(f'fuelType must be one of {allowed}')
        return v

class CarCreate(CarBase):
    pass

class CarResponse(CarBase):
    id: int
    predicted_price: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ===== ML Model Loading =====
def load_model():
    """Load trained model and preprocessing artifacts"""
    ml_dir = Path(__file__).parent.parent / "ml_service"
    
    model_path = ml_dir / "model.pkl"
    encoder_path = ml_dir / "label_encoders.pkl"
    scaler_path = ml_dir / "scaler.pkl"
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            "Run 'python train_local.py' first!"
        )
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(encoder_path, 'rb') as f:
        label_encoders = pickle.load(f)
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    logger.info("✅ Model, encoders, and scaler loaded")
    return model, label_encoders, scaler

# Load model at startup
try:
    MODEL, LABEL_ENCODERS, SCALER = load_model()
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    MODEL = None
    LABEL_ENCODERS = None
    SCALER = None

def predict_price(car_data: dict) -> float:
    """Predict car price using trained model"""
    if MODEL is None:
        raise RuntimeError("Model not loaded. Train the model first!")
    
    import pandas as pd
    
    # Create dataframe
    df = pd.DataFrame([car_data])
    
    # Encode categorical features
    categorical_columns = ['model', 'transmission', 'fuelType']
    for col in categorical_columns:
        if col in LABEL_ENCODERS:
            df[col] = LABEL_ENCODERS[col].transform([df[col].iloc[0]])
    
    # Scale numerical features
    numerical_features = ['year', 'mileage', 'tax', 'mpg', 'engineSize']
    df[numerical_features] = SCALER.transform(df[numerical_features])
    
    # Predict
    prediction = MODEL.predict(df)[0]
    return float(prediction)

# ===== Database Dependency =====
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== API Routes =====
@app.get("/cars", response_model=List[CarResponse])
def get_cars():
    """Get all cars"""
    db = SessionLocal()
    try:
        cars = db.query(Car).all()
        return cars
    finally:
        db.close()

@app.post("/cars", response_model=CarResponse)
def create_car(car: CarCreate):
    """Add new car and get prediction"""
    db = SessionLocal()
    try:
        # Prepare data for prediction
        car_dict = car.dict()
        
        # Get prediction
        try:
            predicted_price = predict_price(car_dict)
            logger.info(f"Predicted price for {car.model}: £{predicted_price:,.2f}")
        except Exception as e:
            logger.warning(f"Prediction failed: {str(e)}")
            predicted_price = None
        
        # Save to database
        db_car = Car(**car_dict, predicted_price=predicted_price)
        db.add(db_car)
        db.commit()
        db.refresh(db_car)
        
        logger.info(f"Saved car {db_car.id} to database")
        return db_car
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/cars/{car_id}", response_model=CarResponse)
def get_car(car_id: int):
    """Get specific car"""
    db = SessionLocal()
    try:
        car = db.query(Car).filter(Car.id == car_id).first()
        if car is None:
            raise HTTPException(status_code=404, detail="Car not found")
        return car
    finally:
        db.close()

@app.delete("/cars/{car_id}")
def delete_car(car_id: int):
    """Delete a car"""
    db = SessionLocal()
    try:
        car = db.query(Car).filter(Car.id == car_id).first()
        if car is None:
            raise HTTPException(status_code=404, detail="Car not found")
        db.delete(car)
        db.commit()
        return {"message": f"Car {car_id} deleted"}
    finally:
        db.close()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "model_loaded": MODEL is not None
    }

@app.on_event("startup")
async def startup_event():
    """Create tables on startup"""
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
