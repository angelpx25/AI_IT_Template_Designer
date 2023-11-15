#sidebar.py

import streamlit as st
import config.settings as settings
import utils.utils as ut
import os
import openpyxl

def sidebar_header():
    st.header(settings.HOME_SIDEBAR_HEADER)

def sidebar_mode():
    selected_function = st.selectbox("Application mode:", options=['Proposal Template Designer', 'AI Proposal Development'], placeholder='Select Mode')
    return selected_function

def sidebar_proposal_settings(pvalues):
    pvalues['pname'] = st.text_input("Proposal Name:",value='')
    pvalues['breq'] = st.text_input("Business Requirements:", value='')

    col1,col2 = st.columns(2)
    with col1:
        clients_list = os.listdir("./templates/clients")
        clients_list.insert(0, 'Select a Client')
        client = st.selectbox("Client:", clients_list, key='client')
    with col2:
        pvalues['pnumber'] = st.text_input("Proposal Number:", value='')
    return pvalues,client

def sidebar_proposal_info():
    col1,col2,col3 = st.columns(3)
    with col1:
        phase = st.selectbox("Phase:", ['All', 'Plan', 'Prepare', 'Implement','Operate','Optimize'], key='phase')
    with col2:
        products = st.selectbox("Products:", ['No', 'Yes'], key='products',disabled=True)
    with col3:
        notes = st.selectbox("Default Notes:", ['No', 'Yes'], key='notes',disabled=True)

    col1,col2,col3 = st.columns(3)
    with col1:
        technology_list = os.listdir("./templates/technologies")
        technology = st.selectbox("Techonology:", technology_list, key='technology')
    with col2:
        make_list = os.listdir("./templates/technologies/" + technology) 
        make = st.selectbox("Make:", make_list, key='make')
    with col3:
        procedure_list = os.listdir("./templates/procedures")
        procedure = st.selectbox("Procedure:", procedure_list, key='procedure')
    return phase,products,notes,technology,make,procedure

def sidebar_proposal_buttons():
    col1, col2 = st.columns(2)
    with col1:
        st.button('Insert Content',use_container_width=True)
    with col2:
        reset = st.button('Reset Settings',use_container_width=True)
    return reset

def reset_proposal_settings(psettings,pvalues):
    col1,col2 = st.columns(2)
    pvalues['mwin'] = col1.number_input(label='Maintenace Windows',min_value=0,max_value=10,step=1,value=0)
    pvalues['standby'] = col2.number_input(label='Standby Time',min_value=0.0,max_value=50.0,step=1.0,value=0.0)
    with st.expander(label='Template Settings'):
            for key,value in psettings.items():
                psettings[key] = st.text_input(label=key,value=' ',disabled=True)
    return psettings

def proposal_settings(psettings,pvalues):
    col1,col2 = st.columns(2)
    pvalues['mwin'] = col1.number_input(label='Maintenace Windows',min_value=0,max_value=10,step=1)
    pvalues['standby'] = col2.number_input(label='Standby Time',min_value=0.0,max_value=50.0,step=1.0)
    psettings['Proposal Name [Ticket]'] = f"{pvalues['pname']} [{pvalues['pnumber']}]"
    psettings['Enter Business Requirements'] = pvalues['breq']
    psettings['Day Prior to Maintenance Window'] = f"Day Prior to Maintenance Window ({pvalues['mwin']})"
    psettings['mtime1'] = int(pvalues['mwin']) * 0.25
    psettings['15 Minutes Prior to Maintenance Window'] = f"15 Minutes Prior to Maintenance Window ({pvalues['mwin']})"
    psettings['mtime2'] = int(pvalues['mwin']) * 0.16
    psettings['Maintenance Window Has Ended'] = f"Maintenance Window Has Ended ({pvalues['mwin']})"
    psettings['mtime3'] = int(pvalues['mwin']) * 0.08
    with st.expander(label='Template Settings'):
        for psettings_key, psettings_value in psettings.items():
                psettings[psettings_key] = st.text_input(label=psettings_key, value=psettings_value)
    return psettings

import io
def get_download_link(file : io.BytesIO):
    # Function to create a download link
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{file.read().decode()}" download="example.xlsx">Download XLSX File</a>'
    return href

def sidebar():
    pvalues= {}
    with st.sidebar:
        sidebar_header()
        pvalues,client = sidebar_proposal_settings(pvalues)
        if client == 'Select a Client':
            debugmode = products = notes = False
            phase = procedure = technology = make = ''
            pvalues['pname'] = 'HOW TO USE THE TOOL'
        else:
            cell_values = ut.get_variables_from_excel(client)
            phase,products,notes,technology,make,procedure = sidebar_proposal_info()
            reset = sidebar_proposal_buttons()
            psettings = {}
            if pvalues['pname']:
                for cell_value in cell_values:
                    if cell_value not in psettings:
                        psettings[cell_value] = ''
                if reset:
                    psettings = reset_proposal_settings(psettings,pvalues)
                else:
                    psettings = proposal_settings(psettings,pvalues)
                col1,col2,col3 = st.columns(3)
                with col1:                        
                    prepared = False
                    if st.button("Prepare",use_container_width=True):
                        with st.spinner():
                            df = ut.prepare_content(client,phase,procedure,technology)
                            workbook = openpyxl.load_workbook(f"./templates/clients/{client}/Template.xlsx")
                            workbook = ut.replace_cell_in_coordinates(workbook,psettings)
                            workbook = ut.insert_dataframe_in_excel(workbook, df)
                            data = ut.download_template(workbook)
                            prepared = True
                with col2:
                    if prepared:
                        st.download_button(label="Download", data=data, file_name=f"{pvalues['pname']} [{pvalues['pnumber']}].xlsx", key='download',use_container_width=True,disabled=False)
                        workbook.close
                    else:
                        st.button(label="Download",use_container_width=True,disabled=True)
                with col3:
                    debugmode = st.toggle(label="Debug Mode")
            else:
                debugmode = False
                pvalues['mwin'] = 0
    return debugmode,pvalues,client,phase,procedure,technology,make,products,notes
