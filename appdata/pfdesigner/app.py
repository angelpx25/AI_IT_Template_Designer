#app.py

import streamlit as st
import config.config
import page.login
import page.main
from PIL import Image

config.config.load_pageconfig()

conf = config.config.load_config()
authenticator = config.config.load_authenticator(conf)

authenticator._check_cookie()

if 'page' not in st.session_state:
    st.session_state['page'] = 'login'

if st.session_state['name']:
    name, authentication_status, username = page.login.login(authenticator)
    page.main.main(conf,authenticator,name, authentication_status, username)
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            .stDeployButton {display:none;}
            footer {visibility: hidden;}
            #stDecoration {display:none;}
            .css-15zrgzn {display: none;}
            .css-eczf16 {display: none;}
            .css-jn99sy {display: none;}
            .css-1629p8f span {text-align: center;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
else:
    st.image(image=Image.open('./images/Project-Fuel-logo.png'))
    name, authentication_status, username = page.login.login(authenticator)
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            .stDeployButton {display:none;}
            footer {visibility: hidden;}
            #stDecoration {display:none;}
            .css-15zrgzn {display: none;}
            .css-eczf16 {display: none;}
            .css-jn99sy {display: none;}
            .css-1629p8f span {text-align: center;}
            .css-z5fcl4 {padding-left: 35%; padding-right: 35%;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    


