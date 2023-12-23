import yaml
import config.settings as settings
import streamlit as st
from page.home import home

def main(config, authenticator, name, authentication_status, username ):
    if authentication_status:
        st.sidebar.subheader('Account Details:')
        st.sidebar.write(f'Welcome *{name} {username}*')
        with st.sidebar:
            col1,col2,col3,col4 = st.columns(4)
            with col1:
                if not st.session_state['page'] == 'updateaccount':
                    if st.button('Edit Profile',use_container_width=True):
                        st.session_state['page'] = 'updateaccount'
                        st.experimental_rerun()
                elif st.button('Back',use_container_width=True):
                        st.session_state['page'] = 'home'
                        st.experimental_rerun()
            with col2:
                if not st.session_state['page'] == 'changepass':
                    if st.button('Password',use_container_width=True):
                        st.session_state['page'] = 'changepass'
                        st.experimental_rerun()
                else:
                    if st.button('Back',use_container_width=True,key='Back2'):
                        st.session_state['page'] = 'home'
                        st.experimental_rerun()
            with col3:
                authenticator.logout('Logout')
            with col4:
                st.button('Refresh Data',use_container_width=True,key='refresh')
                
        if st.session_state['page'] == 'updateaccount':
            try:
                if authenticator.update_user_details(username=username,form_name='Reset Password'):
                    with open('./config/config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
                    st.sidebar.success('Account Updated!')
                    st.session_state['page'] = 'home'
            except Exception as e:
                st.error("An error has ocurred")
        elif st.session_state['page'] == 'changepass':
            try:
                if authenticator.reset_password(username=username,form_name='Change Password'):
                    with open('./config/config.yaml', 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
                    st.success('Password Changed!')
                    st.session_state['page'] = 'home'
            except Exception as e:
                st.error("Password is incorrect!")
        else:
            home()
    elif authentication_status == False:
        st.error('Username/password is incorrect')
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
    elif authentication_status == None:
        st.caption(settings.AUTH_CONTACT)
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