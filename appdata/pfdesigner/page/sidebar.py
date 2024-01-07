#sidebar.py

import streamlit as st
import config.settings as settings
import utils.utils as ut
import os
import pandas as pd


def sidebar_mode():
    selected_function = st.selectbox("Application mode:", options=['Proposal Template Designer', 'AI Proposal Development'], placeholder='Select Mode')
    return selected_function

def reset_proposal_settings(psettings,pvalues):
    col1,col2,col3 = st.columns(3)
    pvalues['mwin'] = col1.number_input(label='Maintenace Windows',min_value=0,max_value=10,step=1,value=0)
    pvalues['standbytime'] = "{:.2f}".format(float(col2.number_input(label='Standby Time (hours)',min_value=0.00,max_value=50.00,step=1.00,value=0.00)))
    pvalues['closuretime'] = "{:.2f}".format(float(col3.number_input(label='Closure Time (hours)',min_value=0.00,max_value=50.00,step=1.00,value=0.25)))
    with st.expander(label='Advance Settings'):
            for key,value in psettings.items():
                psettings[key] = st.text_input(label=key,value=' ',disabled=True)
    return psettings

def proposal_settings(psettings,pvalues):
    col1,col2,col3 = st.columns(3)
    pvalues['mwin'] = col1.number_input(label='Maintenace Windows',min_value=0,max_value=10,step=1)
    pvalues['standbytime'] = "{:.2f}".format(float(col2.number_input(label='Standby Time (hours)',min_value=0.00,max_value=50.00,step=1.00)))
    pvalues['closuretime'] = "{:.2f}".format(float(col3.number_input(label='Closure Time (hours)',min_value=0.00,max_value=50.00,step=0.25)))
    psettings['Proposal Name [Ticket]'] = f"{pvalues['pname']} [{pvalues['pnumber']}]"
    psettings['Enter Business Requirements'] = pvalues['breq']
    psettings['Day Prior to Maintenance Window'] = f"Day Prior to Maintenance Window ({pvalues['mwin']})"
    psettings['mtime1'] = int(pvalues['mwin']) * 0.25
    psettings['15 Minutes Prior to Maintenance Window'] = f"15 Minutes Prior to Maintenance Window ({pvalues['mwin']})"
    psettings['mtime2'] = int(pvalues['mwin']) * 0.16
    psettings['Maintenance Window Has Ended'] = f"Maintenance Window Has Ended ({pvalues['mwin']})"
    psettings['mtime3'] = int(pvalues['mwin']) * 0.08
    with st.expander(label='Advance Settings'):
        for psettings_key, psettings_value in psettings.items():
                psettings[psettings_key] = st.text_input(label=psettings_key, value=psettings_value)
    return psettings

@st.cache_resource(show_spinner=False)
def load_sharepoint_data_queue():
    df = ut.Get_SharePoint_data("Proposal Queues","TicketStatus eq 'KT Complete' or TicketStatus eq 'In Progress'")
    df = pd.DataFrame(df)
    df = df[df['TicketStatus'].isin(['KT Complete', 'In Progress'])]
    return df

@st.cache_resource(show_spinner=False)
def load_sharepoint_data_KT_info(KTNumber:str):
    df = ut.Get_SharePoint_data("New KT",f"Title eq '{KTNumber}'")
    df = pd.DataFrame(df)
    return df

def sidebar():
    sbvalues= {'settings': {},'pname':'','pnumber':'','breq':'','client':'Select a Client','phase':'','products':False,'notes':False,'library':'','technology':'','version':'','procedure':'','phase':'','continue':False}
    psettings = {}

    if 'content' not in st.session_state:
        st.session_state['content'] = {}
        st.session_state['content']['Technology'] = []
        st.session_state['content']['Version'] = []
        st.session_state['content']['Procedure'] = []
        st.session_state['content']['Library'] = []
        st.session_state['content']['Phase'] = []
        st.session_state['content']['psettings'] = []

    if 'Library' not in st.session_state['content']:
        st.session_state['content']['Technology'] = []
        st.session_state['content']['Version'] = []
        st.session_state['content']['Procedure'] = []
        st.session_state['content']['Library'] = []
    
    if 'debugmode' not in st.session_state:
        st.session_state['debugmode'] = False
    
    with st.sidebar:
        if st.session_state['refresh']:
            with st.spinner('Loading Data...'):
                st.cache_resource.clear()
                df = load_sharepoint_data_queue()
                #dfKT = load_sharepoint_data_KT_info()
        else:
            with st.spinner('Loading Data...'):
                df = load_sharepoint_data_queue()
                #dfKT = load_sharepoint_data_KT_info()
    
        if 'df' in locals():
            st.subheader(settings.HOME_SIDEBAR_INFO_SUBHEADER)

            if st.session_state['debugmode']:
                st.write('**AKTIS Data**')
                st.dataframe(df[['ProposalName_x0028_TicketSummary','Title','ClientName']],use_container_width=True,hide_index=True,column_config={'ProposalName_x0028_TicketSummary':'Proposal Name','Title': 'Company','ClientName':'Client'})

            selected = st.selectbox('Select a Proposal:',df['ProposalName_x0028_TicketSummary'],placeholder='Select a Proposal')
            dfdata = df[df['ProposalName_x0028_TicketSummary'] == selected]
            KTNumber = (str(dfdata['RevisionKTNumbers'].values[0]).split(','))[0]
            dfKT = load_sharepoint_data_KT_info(KTNumber)

            if st.session_state['debugmode']:
                st.write('**Proposal Data**')
                st.write(dfdata)
                st.write('**KT Data**')
                st.write(dfKT)

            sbvalues['pname'] = st.text_input("Proposal Name:",value=dfdata['ProposalName_x0028_TicketSummary'].values[0],disabled=True)

            if dfKT.empty:
                dfKT_breq = 'Could not read business requirements!'
            else:
                dfKT_breq = dfKT[dfKT['Question0'] == 'What is the business requirement for this project?']['SingleLineText'].values[0]

            if sbvalues['pname'] and dfKT_breq:
                sbvalues['breq'] = st.text_area("Business Requirements:",value=dfKT_breq,disabled=True)

            col1,col2 = st.columns(2)
            with col1:
                if sbvalues['breq']:
                    sbvalues['pnumber'] = st.text_input("Proposal Number:",value=dfdata['TicketNumber'].values[0],disabled=True)
            with col2:
                if sbvalues['pnumber']:
                    clients_list = [settings.CLIENT_DEFAULT_TEXT]
                    clients_list.extend(os.listdir("./templates/clients"))
                    sbvalues['client'] = st.text_input("Company:",value=dfdata['Title'].values[0],disabled=True)

            st.subheader(settings.HOME_SIDEBAR_CONTENT_SUBHEADER)
            
            if dfdata['Title'].values[0] in clients_list:
                client_path = f"./templates/clients/{sbvalues['client']}/Template.xlsx"
                library_list = [settings.LIBRARY_DEFAULT_TEXT]
                library_list.extend(os.listdir(f"{settings.LIBRARY_DEFAULT_PATH}" ))
                sbvalues['library'] = st.selectbox("Library:", library_list)

                col1,col2,col3 = st.columns(3)
                with col1:
                    if sbvalues['library'] != settings.LIBRARY_DEFAULT_TEXT:
                        procedure_list = [settings.PROCEDURE_DEFAULT_TEXT]
                        procedure_path = f"{settings.LIBRARY_DEFAULT_PATH}/{sbvalues['library']}/procedures"
                        if os.path.exists(procedure_path):
                            procedure_list.extend(os.listdir(procedure_path))
                            sbvalues['procedure'] = st.selectbox("Procedure:", procedure_list)
                with col2:
                    if sbvalues['procedure'] != settings.PROCEDURE_DEFAULT_TEXT and sbvalues['library'] != settings.LIBRARY_DEFAULT_TEXT:
                        technology_list = [settings.TECHNOLOGY_DEFAULT_TEXT]
                        technology_path = f"{settings.LIBRARY_DEFAULT_PATH}/{sbvalues['library']}/procedures/{sbvalues['procedure']}"
                        if os.path.exists(technology_path):
                            technology_list.extend(os.listdir(technology_path))
                            sbvalues['technology'] = st.selectbox("Techonology:", map(lambda file: os.path.splitext(file)[0], technology_list))
                with col3:
                    if (sbvalues['procedure'] != settings.PROCEDURE_DEFAULT_TEXT and sbvalues['library'] != settings.LIBRARY_DEFAULT_TEXT and sbvalues['technology'] != settings.TECHNOLOGY_DEFAULT_TEXT):
                        version_list = [settings.VERSION_DEFAULT_TEXT, 'New Content']
                        version_path = f"{settings.LIBRARY_DEFAULT_PATH}/{sbvalues['library']}/procedures/{sbvalues['procedure']}/{sbvalues['technology']}"
                        if os.path.exists(version_path):
                            version_list.extend(os.listdir(version_path))
                            sbvalues['version'] = st.selectbox("Version:", map(lambda file: os.path.splitext(file)[0], version_list))

                if (sbvalues['version'] != settings.VERSION_DEFAULT_TEXT and sbvalues['procedure'] != settings.PROCEDURE_DEFAULT_TEXT and sbvalues['library'] != settings.LIBRARY_DEFAULT_TEXT and sbvalues['technology'] != settings.TECHNOLOGY_DEFAULT_TEXT):
                    procedure_file_path = f"./templates/libraries/{sbvalues['library']}/procedures/{sbvalues['procedure']}/{sbvalues['technology']}/{sbvalues['version']}.txt"
                    if os.path.exists(procedure_file_path):
                        procedure_file_content = ut.read_procedure(procedure_file_path)
                        found_variables = ut.find_cell_variables(ut.find_cell_variables(procedure_file_content))
                        variables = {}
                        seen_variables = set()
                        with st.expander('Procedure Settings'):
                            for variable in found_variables:
                                if variable not in seen_variables:
                                    if variable not in variables.keys():
                                        if 'Quantity' in variable:
                                            variables[variable] = st.number_input(variable,format="%g",step=1,min_value=0,max_value=999)
                                        else:
                                            variables[variable] = st.text_input(variable)
                                        #procedure_file_content.replace(f"<{variable}>", variables[variable],inplace=True,regex=True)
                                    seen_variables.add(variable)
                                else:
                                    continue
                if (sbvalues['version'] == 'New Content' and sbvalues['procedure'] != settings.PROCEDURE_DEFAULT_TEXT and sbvalues['library'] != settings.LIBRARY_DEFAULT_TEXT and sbvalues['technology'] != settings.TECHNOLOGY_DEFAULT_TEXT):
                    with st.expander(label=settings.HOME_SIDEBAR_CONVERTER,expanded=False):
                        version_name = st.text_input('Version Name:')
                        uploaded_file = st.file_uploader("Upload an Excel File", type=['xlsx','xls'])
                        if st.button(label='Add Content'):
                            if uploaded_file is not None and version_name:
                                output_file_path = f"./templates/libraries/{sbvalues['library']}/procedures/{sbvalues['procedure']}/{sbvalues['technology']}/{version_name}.txt"
                                if not os.path.exists(output_file_path):
                                    try:
                                        df = ut.excel_to_pipe_delimited(uploaded_file)
                                        ut.pipe_delimited_to_csv(input_df=df,output_file_path=output_file_path)
                                    except Exception as e:
                                        None
                                    finally:
                                        st.info('Content Added')
                                else:
                                    st.warning("File content exsist, select a different name.")
                            else:
                                st.warning('Insert version name and upload content in the proper format.')

                if sbvalues['library'] != settings.LIBRARY_DEFAULT_TEXT and os.path.exists(procedure_path):
                    col1,col2,col3 = st.columns(3)
                    with col1:
                        sbvalues['phase'] = st.selectbox("Phase:", ['All', 'Plan', 'Prepare', 'Implement','Operate','Optimize'], key='phase')
                    with col2:
                        sbvalues['products'] = st.selectbox("Products:", ['No', 'Yes'], key='products',disabled=True)
                    with col3:
                        sbvalues['notes'] = st.selectbox("Default Notes:", ['No', 'Yes'], key='notes',disabled=True)

                    if st.session_state['debugmode']:
                        st.write(st.session_state['content'])
                    
                    existing_content_df = pd.DataFrame(st.session_state['content'])
                    existing_content_df['Select'] = False
                    column_config = {
                    "Technology": st.column_config.TextColumn(disabled=True),
                    "Version": st.column_config.TextColumn(disabled=True),
                    "Procedure": st.column_config.TextColumn(disabled=True),
                    "Phase": st.column_config.TextColumn(disabled=True),
                    "Library": None,
                    "Select": st.column_config.CheckboxColumn('Delete?', required=True, disabled=False),
                    "psettings": None
                    }
                    edited_content = st.data_editor(existing_content_df,column_config=column_config,hide_index=True,num_rows="fixed",use_container_width=True)
                    col1, col2,col3 = st.columns(3)

                    if st.session_state['debugmode']:
                        st.write(edited_content)

                    with col1:
                        if st.button('Insert Content',use_container_width=True):
                            cont = False
                            for variable in variables:
                                if variables[variable] == '':
                                    st.sidebar.warning(f"Missing value: {variable}")
                                    cont = False
                                    break
                                cont = True
                            if cont:
                                content_to_insert = {'Select' : False,'Library': sbvalues['library'], 'Technology': sbvalues['technology'],'Version': sbvalues['version'],'Procedure': sbvalues['procedure'], 'Phase': sbvalues['phase'], 'psettings': variables}
                                content_combined = pd.concat([existing_content_df, pd.DataFrame([content_to_insert])])
                                duplicate = False
                                for duplicated in content_combined.duplicated(['Technology','Procedure','Version']):
                                    if duplicated:
                                        duplicate = True
                                        st.sidebar.warning('Content already exists')
                                        break
                                if not duplicate:
                                    #client_file_path = f"./templates/clients/{dfdata['Title'].values[0]}+/{sbvalues['client']}.txt"
                                    #client_file_content = ut.read_text_file(client_file_path)
                                    procedure_file_path = f"./templates/libraries/{sbvalues['library']}/procedures/{sbvalues['procedure']}/{sbvalues['technology']}/{sbvalues['version']}.txt"
                                    procedure_file_content = ut.read_procedure(procedure_file_path)
                                    
                                    if not procedure_file_content.empty:
                                        st.session_state['content']['Library'].append(sbvalues['library'])
                                        st.session_state['content']['Technology'].append(sbvalues['technology'])
                                        st.session_state['content']['Version'].append(sbvalues['version'])
                                        st.session_state['content']['Procedure'].append(sbvalues['procedure'])
                                        st.session_state['content']['Phase'].append(sbvalues['phase'])
                                        st.session_state['content']['psettings'].append(variables)
                                        st.experimental_rerun()
                                    else:
                                        st.sidebar.warning(f'Content does not exists.')
                    with col2:
                        if st.button('Delete Content',use_container_width=True):
                            for selected in edited_content[edited_content['Select'] == True].index:
                                for key in st.session_state['content'].keys():
                                        del st.session_state['content'][key][selected]
                            st.experimental_rerun()
                    with col3:
                        reset = st.button('Reset Settings',use_container_width=True)

                    if 'Technology' in st.session_state['content']:
                        st.subheader(settings.HOME_SIDEBAR_SETTINGS_SUBHEADER)
                        if reset:
                            psettings = reset_proposal_settings(psettings,sbvalues)
                        else:
                            if os.path.exists(client_path):
                                cell_values = ut.get_variables_from_excel(path=f"./templates/clients/{sbvalues['client']}/Template.xlsx")
                                for cell_value in cell_values:
                                    if cell_value not in psettings:
                                        psettings[cell_value] = ''
                                sbvalues['settings'] = proposal_settings(psettings,sbvalues)                 
        #Warnings:
        if sbvalues['library'] == settings.LIBRARY_DEFAULT_TEXT:
            st.warning('Select a Library')
            sbvalues['continue'] = False
        elif sbvalues['client'] not in clients_list:
            st.warning('Client Template has not been added')
            sbvalues['continue'] = False
        elif not sbvalues['breq']:
            st.warning('Insert business requirements')
            sbvalues['continue'] = False
        elif not os.path.exists(procedure_path):
            st.warning('Library is empty')
            sbvalues['continue'] = False
        elif not sbvalues['pname']:
            st.warning('Insert proposal name')
            sbvalues['continue'] = False
        elif not sbvalues['pnumber']:
            st.warning('Insert a correct proposal number')
            sbvalues['continue'] = False
        elif not os.path.exists(client_path):
            st.warning('Company template does not exists')
            sbvalues['continue'] = False
        elif 'content' not in st.session_state or 'Technology' not in st.session_state['content']:
            st.warning('Insert Content')
            sbvalues['continue'] = False
        else:
            df = ut.prepare_content(sbvalues,st.session_state['content'],templates_path=settings.LIBRARY_DEFAULT_PATH)
            sbvalues['continue'] = True
    return sbvalues,df