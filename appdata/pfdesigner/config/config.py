#pageconfig.py

import streamlit as st
import yaml
import config.settings as settings

def load_pageconfig():
    st.set_page_config(
        page_title=settings.PAGE_TITLE,
        page_icon=settings.PAGE_ICON,
        layout=settings.PAGE_LAYOUT
        )
    #st.title(settings.HOME_TITLE)

def load_config():
    with open('./config/config.yaml') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
    return config

def load_authenticator(config):
    from src.streamlit_auth import Authenticate
    authenticator = Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    return authenticator