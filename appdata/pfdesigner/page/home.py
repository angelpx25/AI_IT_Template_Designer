#page.py

import page.sidebar as sb
import streamlit as st
import utils.utils as ut
import config.settings as settings

def home():
    sbvalues,df = sb.sidebar()
    proposal_name = sbvalues['pname'] if sbvalues['pname'] != '' else "Proposal Name"
    if not sbvalues['continue']:
        st.subheader('HOW TO USE THE TOOL', divider="grey")
        st.markdown(ut.read_text_file('./README.md'), unsafe_allow_html=True)
    else:
        st.subheader(proposal_name, divider="grey")
        st.write("<b>Proposal number:</b> " + sbvalues['pnumber'], unsafe_allow_html=True)
        st.write("<b>Business requirements:</b> " + sbvalues['breq'], unsafe_allow_html=True)
        st.write("<b>Maintenance windows:</b> " + str(sbvalues['mwin']), unsafe_allow_html=True)

        #st.write(f"{client_file_content}\n\n{procedure_file_content}")
        if df.empty:
            content = "Content could not be found"
            st.error(content)
        else:
            try:
                content = df
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
                    content.replace('<make>', sbvalues['make'], regex=True, inplace=True)
                    content.replace('-', '   ', regex=True, inplace=True)
                    if st.session_state['debugmode']:
                        st.write(len(content))
                    new_df = st.data_editor(content,hide_index=True,use_container_width=True,height=len(content)*settings.PROPOSAL_PAGE_WIDTH)
            except Exception as e:
                if st.session_state['debugmode']:
                    st.error(f"Fix the following error {e}")
                else:
                    st.error('The data does not exists')