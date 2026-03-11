import streamlit as st

def set_pro_design():
    st.markdown("""
        <style>
        header
        footer {visibility: hidden;}
        
        div[data-testid="stMetric"] {
            background-color: #151B2B;
            border-radius: 12px;
            padding: 15px 20px;
            border: 1px solid #2A354D;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            transition: transform 0.2s ease-in-out;
        }
        
        div[data-testid="stButton"] button {
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        div[data-testid="stButton"] button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 255, 170, 0.3);
            border-color: #00FFAA;
        }
        
        video {
            border-radius: 12px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }
        </style>
    """, unsafe_allow_html=True)