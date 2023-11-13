import streamlit as st
from streamlit_authenticator import Authenticate, Hasher
from yaml.loader import SafeLoader
import yaml

def get_email_password(email_address):
    with open('config.yaml', 'r') as file:
        data = yaml.safe_load(file)
    email_data = data.get('email', {})
    stored_email = email_data.get('address', None)
    stored_password = email_data.get('password', None)
    if stored_email == email_address and stored_password:
        return stored_password
    else:
        return None

def set_email_password(email_address, new_password):
    with open('config.yaml') as file:
        data = yaml.safe_load(file)
        data['credentials']['usernames'][email_address]['password'] = Hasher([new_password]).generate()[0]
    with open('config.yaml', 'w') as file:
        yaml.dump(data, file)
