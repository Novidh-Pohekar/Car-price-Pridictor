"""
Simplified Streamlit App - Local Mode (No Kafka)
"""

import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Car Price Predictor",
    page_icon="🚗",
    layout="wide"
)

st.markdown("""
    <style>
        .prediction-box {
            background-color: #e6f3ff;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5)
def fetch_cars():
    """Fetch cars from API"""
    try:
        response = requests.get(f"{API_URL}/cars", timeout=5)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

def create_plot(df, plot_type):
    """Create visualizations"""
    try:
        if df.empty:
            return None
            
        if plot_type == "distribution":
            fig = px.histogram(
                df, x="price",
                title="Price Distribution",
                nbins=30,
                labels={"price": "Price (£)", "count": "Number of Cars"}
            )
            
        elif plot_type == "scatter":
            fig = px.scatter(
                df[df['price'].notna()],
                x="mileage", y="price",
                color="model",
                size="engineSize",
                title="Price vs Mileage",
                labels={"mileage": "Mileage (miles)", "price": "Price (£)"}
            )
            
        elif plot_type == "box":
            fig = px.box(
                df[df['price'].notna()],
                x="year", y="price",
                title="Price by Year",
                labels={"year": "Year", "price": "Price (£)"}
            )
            
        elif plot_type == "prediction":
            valid_data = df[df['price'].notna() & df['predicted_price'].notna()]
            if not valid_data.empty:
                fig = px.scatter(
                    valid_data,
                    x="price", y="predicted_price",
                    color="model",
                    title="Predicted vs Actual Price",
                    labels={"price": "Actual (£)", "predicted_price": "Predicted (£)"}
                )
                min_val = min(valid_data['price'].min(), valid_data['predicted_price'].min())
                max_val = max(valid_data['price'].max(), valid_data['predicted_price'].max())
                fig.add_shape(type='line', line=dict(dash='dash', color='gray'),
                             x0=min_val, y0=min_val, x1=max_val, y1=max_val)
                return fig
            return None
            
        return fig
    except Exception as e:
        st.error(f"Plot error: {str(e)}")
        return None

# ===== Main Layout =====
st.title("🚗 Car Price Predictor (Simplified)")

with st.sidebar:
    st.header("➕ Add New Car")
    
    with st.form("car_form", clear_on_submit=True):
        model = st.text_input("Model", value="Fiesta")
        year = st.number_input("Year", min_value=1900, max_value=datetime.now().year, value=2019)
        price = st.number_input("Price (£)", min_value=0, value=12000)
        transmission = st.selectbox("Transmission", ["Manual", "Automatic", "Semi-Auto"])
        mileage = st.number_input("Mileage (miles)", min_value=0, value=25000)
        fuelType = st.selectbox("Fuel Type", ["Petrol", "Diesel", "Hybrid", "Electric"])
        tax = st.number_input("Tax (£)", min_value=0, value=145)
        mpg = st.number_input("MPG", min_value=0.0, value=55.4)
        engineSize = st.number_input("Engine Size (L)", min_value=0.0, value=1.0)
        
        submitted = st.form_submit_button("Add Car", use_container_width=True)
        
        if submitted:
            try:
                response = requests.post(
                    f"{API_URL}/cars",
                    json={
                        "model": model,
                        "year": year,
                        "price": price,
                        "transmission": transmission,
                        "mileage": mileage,
                        "fuelType": fuelType,
                        "tax": tax,
                        "mpg": mpg,
                        "engineSize": engineSize
                    }
                )
                if response.status_code == 200:
                    car = response.json()
                    st.success(f"✅ Car added! ID: {car['id']}")
                    if car.get('predicted_price'):
                        st.info(f"💰 Predicted Price: £{car['predicted_price']:,.2f}")
                    st.rerun()
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Failed to add car: {str(e)}")

# ===== Main Content =====
st.header("📊 Car Database")

df = fetch_cars()

if df.empty:
    st.warning("⚠️ No cars in database. Add one using the form on the left!")
else:
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cars", len(df))
    with col2:
        st.metric("Avg Price", f"£{df['price'].mean():,.0f}")
    with col3:
        st.metric("Avg Predicted", f"£{df['predicted_price'].mean():,.0f}" if df['predicted_price'].notna().any() else "N/A")
    with col4:
        if df['predicted_price'].notna().any():
            diff = df['predicted_price'].mean() - df['price'].mean()
            st.metric("Avg Diff", f"£{diff:,.0f}")
    
    st.divider()
    
    # Data table
    st.subheader("Car Listings")
    display_df = df[[
        'id', 'model', 'year', 'price', 'transmission', 
        'mileage', 'fuelType', 'mpg', 'engineSize', 'predicted_price'
    ]].copy()
    
    # Format for display
    display_df['price'] = display_df['price'].apply(lambda x: f"£{x:,.0f}")
    display_df['predicted_price'] = display_df['predicted_price'].apply(
        lambda x: f"£{x:,.0f}" if pd.notna(x) else "Pending"
    )
    
    st.dataframe(display_df, use_container_width=True)
    
    st.divider()
    
    # Visualizations
    st.subheader("📈 Analytics")
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = create_plot(df, "distribution")
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
        
        fig3 = create_plot(df, "box")
        if fig3:
            st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        fig2 = create_plot(df, "scatter")
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
        
        fig4 = create_plot(df, "prediction")
        if fig4:
            st.plotly_chart(fig4, use_container_width=True)

# Footer
st.divider()
st.caption("🔧 Simplified Car Price Predictor - Local Mode (No Docker)")
