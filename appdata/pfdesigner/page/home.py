#page.py

import page.sidebar as sb
import streamlit as st
import utils.utils as ut
import config.settings as settings

def home():
    sbvalues,df = sb.sidebar()
    proposal_name = sbvalues['pname'] if sbvalues['pname'] != '' else "Proposal Name"
    if not sbvalues['continue'] or df.empty:
        st.subheader('HOW TO USE THE TOOL', divider="grey")
        st.markdown(ut.read_text_file('./README.md'), unsafe_allow_html=True)
    else:
        df = ut.calculate_proposal_time(df)
        content = ut.add_spaces_to_df_subphases(df)
        st.subheader(proposal_name, divider="grey")
        st.write("<b>Proposal number:</b> " + sbvalues['pnumber'], unsafe_allow_html=True)
        st.write("<b>Business requirements:</b> " + sbvalues['breq'], unsafe_allow_html=True)
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            st.write("<b>Maintenance windows:</b> " + str(sbvalues['mwin']), unsafe_allow_html=True)
        with col2:
            st.write("<b>Standby Time:</b> " + str(sbvalues['standbytime']), unsafe_allow_html=True)
        with col3:
            st.write("<b>Closure Time:</b> " + str(sbvalues['closuretime']), unsafe_allow_html=True)
        with col4:
            st.write("<b>Total Time:</b> " + str(content['Hours'].sum()), unsafe_allow_html=True)

        #st.write(f"{client_file_content}\n\n{procedure_file_content}")
        if df.empty:
            content = "Content could not be found"
            st.error(content)
        else:
            try:
                col1, col2 = st.columns(2)
                with col1:
                    phases = ['All', 'Prepare','Implement','Operate', 'Execute Test Plan','Optimize']
                    current_phase = st.selectbox(label='Phase:',options=phases)
                    current_phase = '*Execute Test Plan' if current_phase == 'Execute Test Plan' else current_phase
                    content = ut.extract_phase(current_phase=current_phase,content=content)
                with col2:
                    view_mode_list = ['Normal', 'Text']
                    view_mode = st.selectbox(label='View Mode', options=view_mode_list)

                if view_mode == 'Text':
                    content = content.to_csv(index=False, header=False,sep='\t',lineterminator='\n')
                    st.code(content.replace('-', ' '))
                else:
                    #content = df.applymap(lambda x: x.lstrip('*') if isinstance(x, str) else x)
                    #content = content.loc[content['Task'] != '']
                    #content = content.applymap(lambda x: x.replace('*','  ') if isinstance(x, str) else x)

                    
                                    #content = pd.concat([content.iloc[:index-1], pd.DataFrame({'Task': ['']}), content.iloc[index:]]).reset_index(drop=True)

                    content.replace('-', '    ', regex=True, inplace=True)
                    content['Select'] = False
                    

                if st.session_state['debugmode']:
                    st.write(len(content))

                column_config = {
                    "Task": st.column_config.TextColumn(disabled=False),
                    "Hours": st.column_config.NumberColumn(disabled=True,default=float()),
                    "Total": st.column_config.NumberColumn(disabled=True,default=float()),
                    "Time": st.column_config.NumberColumn(disabled=True,default=float()),
                    "Multiplier": st.column_config.NumberColumn(disabled=False,default=int()),
                    "Select": st.column_config.CheckboxColumn('Select', required=True, disabled=False),
                    }

                new_df = st.data_editor(content,column_config=column_config,hide_index=True,use_container_width=True,height=len(content)*settings.PROPOSAL_PAGE_WIDTH)

                col31,col32 = st.columns(2)
                with col31:
                    st.button(label='Insert Lines Below',use_container_width=True)
                with col32:
                    st.button(label='Delete Selected Lines',use_container_width=True)

                col1,col2,col3,col4,col5 = st.columns(5)
                with col1:
                    start_index = new_df.loc[new_df['Task'] == 'Prepare:'].index
                    end_index = new_df.loc[new_df['Task'] == 'Implement:'].index
                    if not start_index.empty and not end_index.empty:
                        start_index = start_index[0]
                        end_index = end_index[0]
                        PrepareTime = new_df.loc[start_index + 1 : end_index - 1, 'Hours'].sum()
                        st.write(f"<h5>Prepare Time: {str((PrepareTime).round(2))} </h5>", unsafe_allow_html=True)
                    else:
                        st.write(f"<h5>Prepare Time: N/A </h5>", unsafe_allow_html=True)
                with col2:
                    start_index = new_df.loc[new_df['Task'] == 'Implement:'].index
                    end_index = new_df.loc[new_df['Task'] == 'Operate:'].index
                    if not start_index.empty and not end_index.empty:
                        start_index = start_index[0]
                        end_index = end_index[0]
                        ImplementTime = new_df.loc[start_index + 1 : end_index - 1, 'Hours'].sum()
                        st.write(f"<h5>Implement Time: {str((ImplementTime).round(2))} </h5>", unsafe_allow_html=True)
                    else:
                        st.write(f"<h5>Implement Time: N/A </h5>", unsafe_allow_html=True)
                with col3:
                    start_index = new_df.loc[new_df['Task'] == 'Operate:'].index
                    end_index = new_df.loc[new_df['Task'] == '*Execute Test Plan:'].index
                    if not start_index.empty and not end_index.empty:
                        start_index = start_index[0]
                        end_index = end_index[0]
                        OperateTime = new_df.loc[start_index + 1 : end_index - 1, 'Hours'].sum()
                        st.write(f"<h5>Operate Time: {str((OperateTime).round(2))} </h5>", unsafe_allow_html=True)
                    else:
                        st.write(f"<h5>Operate Time: N/A </h5>", unsafe_allow_html=True)
                with col4:
                    start_index = new_df.loc[new_df['Task'] == '*Execute Test Plan:'].index
                    if not start_index.empty:
                        start_index = start_index[0]
                        OptimizeTime = new_df.loc[start_index + 1 :, 'Hours'].sum()
                        st.write(f"<h5>Optimize Time: {str((OptimizeTime).round(2))} </h5>", unsafe_allow_html=True)
                    else:
                        st.write(f"<h5>Optimize Time: N/A </h5>", unsafe_allow_html=True)
                with col5:
                    st.write(f"<h5>Total Time: {str((new_df['Hours'].sum()).round(2))} </h5>", unsafe_allow_html=True)
            except Exception as e:
                if st.session_state['debugmode']:
                    st.error(f"Fix the following error {e}")
                else:
                    st.error('The data does not exists')
    if st.session_state['debugmode']:
        st.write(st.session_state['content'])
    with st.sidebar:
        if sbvalues['continue']:
            col1,col2,col3 = st.columns(3)
            with col1:     
                prepared = False
                if st.button("Prepare",use_container_width=True,disabled=not st.session_state['content']['Technology']):
                    import openpyxl
                    with st.spinner():
                        workbook = openpyxl.load_workbook(f"./templates/clients/{sbvalues['client']}/Template.xlsx")
                        workbook = ut.replace_cell_in_coordinates(workbook,sbvalues['settings'])
                        new_df = new_df[new_df.applymap(lambda x: x != '')]
                        #new_df = new_df.applymap(lambda x: x.replace('  ','*') if isinstance(x, str) else x)
                        workbook = ut.insert_dataframe_in_excel(workbook, new_df)
                        data = ut.download_template(workbook)
                        prepared = True
            with col2:
                if prepared:
                    st.download_button(label="Download", data=data, file_name=f"{sbvalues['pname']} [{sbvalues['pnumber']}].xlsx", key='download',use_container_width=True,disabled=False)
                    workbook.close
                else:
                    st.button(label="Download",use_container_width=True,disabled=True)
            with col3:
                st.button(label='Restart',use_container_width=True)