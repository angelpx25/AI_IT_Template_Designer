#page.py

import page.sidebar as sb
import streamlit as st
import utils.utils as ut
import config.settings as settings

def home():
    debugmode,pvalues,client,phase,procedure,technology,make,products,notes = sb.sidebar()
    proposal_name = pvalues['pname'] if pvalues['pname'] != '' else "Proposal Name"
    st.subheader(proposal_name, divider="grey")
    if client == 'Select a Client':
        #st.write(ut.read_text_file('./README.md'))
        st.markdown(ut.read_text_file('./README.md'), unsafe_allow_html=True)
    else:
        st.write("<b>Proposal number:</b> " + pvalues['pnumber'], unsafe_allow_html=True)
        st.write("<b>Business requirements:</b> " + pvalues['breq'], unsafe_allow_html=True)
        st.write("<b>Maintenance windows:</b> " + str(pvalues['mwin']), unsafe_allow_html=True)
        client_file_path = f"./templates/clients/{client}/{client}.txt"
        procedure_file_path = f"./templates/procedures/{procedure}/{technology}.txt"
        client_file_content = ut.read_text_file(client_file_path)
        procedure_file_content = ut.read_text_file(procedure_file_path)
        #st.write(f"{client_file_content}\n\n{procedure_file_content}")
        if client_file_content == None or procedure_file_content == None:
            content = "Content could not be found"
            st.error(content)
        else:
            try:
                content = ut.prepare_content(client,phase,procedure,technology)
                if st.toggle("Plain Text:"):
                    content = content.to_csv(index=False, header=False,sep='\t',lineterminator='\n')
                    st.code(content.replace('-', ' '))
                else:
                    found_variables = ut.find_cell_variables(content)
                    found_variables = ut.find_cell_variables(found_variables)
                    variables = {}
                    with st.sidebar.expander('Procedure Settings'):
                        for variable in found_variables:
                            if 'make' != variable:
                                if variable not in variables.keys():
                                    variables[variable] = st.text_input(variable)
                                    content.replace(f"<{variable}>", variables[variable],inplace=True,regex=True)
                        content = content.applymap(lambda x: x.lstrip('*') if isinstance(x, str) else x)
                    content.replace('<make>', make, regex=True, inplace=True)
                    content.replace('-', '   ', regex=True, inplace=True)
                    if debugmode:
                        st.write(len(content))
                    st.dataframe(content,hide_index=True,use_container_width=True,height=len(content)*settings.PROPOSAL_PAGE_WIDTH)
            except Exception as e:
                if debugmode:
                    st.error(f"Fix the following error {e}")
                else:
                    st.error('The data does not exists')