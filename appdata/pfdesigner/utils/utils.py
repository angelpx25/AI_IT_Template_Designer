#utils.py
import requests
from msal import ConfidentialClientApplication
from office365.sharepoint.client_context import ClientContext

import os
import re
import io
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from pandas import DataFrame

def number_to_letter(n):
    if 1 <= n <= 26:
        return chr(ord('a') + n - 1)
    else:
        return None  # Handle values outside the range a-z

def find_cell_variables(content):
    pattern = r'<(.*?)>'
    #pattern = r'<([^<>]+)>'
    found_cells = []
    if isinstance(content, DataFrame):
        for index, row in content.iterrows():
            for column, cell_value in row.items():
                if isinstance(cell_value, str):
                    matches = re.findall(pattern, cell_value)
                    if matches:
                        found_cells.append(cell_value)
    elif isinstance(content, Worksheet):
        for row in content.iter_rows(values_only=True):
            for cell_value in row:
                if isinstance(cell_value, str):
                    matches = re.findall(pattern, cell_value)
                    if matches:
                        found_cells.append(cell_value)
    elif isinstance(content, list):
        for word in content:
            matches = re.findall(pattern, word)
            found_cells.extend(matches)
    else:
        print('Error in function find_cell_matches')
    return found_cells

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def insert_content(pvalues):
    import streamlit as st
    content_to_insert = {'Technology': pvalues['technology'],'Version': pvalues['version'],'Procedure': pvalues['procedure']}

    content = {'Technology': st.session_state['Technology'],
               'Version': st.session_state['Version'],
               'Procedure': st.session_state['Procedure']}

    content_df = pd.DataFrame(content)

    content_combined = pd.concat([content_df, pd.DataFrame([content_to_insert])])
    for duplicated in content_combined.duplicated():
        if duplicated:
            st.warning('Content is duplicated')
            break
    content_combined = content_combined.drop_duplicates()
    if not content_combined.empty:
        st.session_state['Technology'] = content_combined['Technology'].tolist()
        st.session_state['Version'] = content_combined['Version'].tolist()
        st.session_state['Procedure'] = content_combined['Procedure'].tolist()
    else:
        st.sidebar.warning('Content to insert empty')

def replace_cell_in_coordinates(workbook : openpyxl.Workbook,new_cell_values : list):
    worksheet = workbook.active
    for cell_value in new_cell_values:
        target_value = cell_value
        for row_idx, row in enumerate(worksheet.iter_rows(values_only=True, min_row=1), start=1):
            for col_idx, cell_value in enumerate(row, start=1):
                if isinstance(cell_value, str) and target_value in cell_value:
                    cell = f"{number_to_letter(col_idx)}{row_idx}"
                    worksheet[cell] = new_cell_values[cell_value]
    return workbook

def read_text_file(file_path):
    try:
        with open(file_path, 'r') as file:
            file_content = file.read()
        return file_content
    except FileNotFoundError:
        #print(f"The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def get_variables_from_excel(path):
    workbook = openpyxl.load_workbook(path)
    worksheet = workbook.active
    cell_values = find_cell_variables(worksheet)
    workbook.close
    return cell_values

def download_template(workbook):
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output

def extract_procedure_content(content : pd.DataFrame,phase):
    try:
        phase_mapping = {
            'Plan': 'Prepare:',
            'Prepare': 'Implement:',
            'Implement': 'Operate:',
            'Operate': 'Optimize:',
            'Optimize': 'Project closure'
        }
        if phase + ':' in content['Task'].values:
            if phase in phase_mapping:
                if phase_mapping[phase] in content['Task'].values:
                    phase_index = content[content['Task'] == phase + ':'].index[0]
                    next_phase = phase_mapping[phase]
                    next_phase_index = content[content['Task'] == next_phase].index[0]
                    phase_content = content.loc[phase_index:next_phase_index-1]
                    content = phase_content.iloc[1:]
                else:
                    phase_index = content[content['Task'] == phase + ':'].index[0]
                    phase_content = content.loc[phase_index+1:]
                    content = phase_content
            return content
    except Exception as e:
        print(e)

def insert_dataframe_in_excel(workbook,content: pd.DataFrame):
    from openpyxl.styles import NamedStyle, Font
    from openpyxl.styles import Alignment
    standard_style = NamedStyle(name='standard')
    underlined_style = NamedStyle(name='underlined')
    number_style = NamedStyle(name='number',alignment=Alignment(horizontal='center'),number_format='0.00')
    standard_style.font =Font(name='Arial',size=12,color="800080")
    number_style.font =Font(name='Arial',size=12,color="800080")
    underlined_style.font =Font(name='Arial',size=12,color="800080",underline='single')

    phase_list = ['Plan','Prepare','Implement','Operate','Optimize']
    for phase in phase_list:
        extracted_content = extract_procedure_content(content,phase)
        if extracted_content is not None:
            target_value = phase + ':'
            worksheet = workbook.active
            target_cell = None
            for row in worksheet.iter_rows(min_row=1, max_col=1, max_row=worksheet.max_row):
                for cell in row:
                    if cell.value == target_value:
                        target_cell = cell
                        row_index = target_cell.row + 1
                        while worksheet.cell(row_index, column=target_cell.column).value is not None:
                            row_index += 1
                        row_index +=1
                        break
                if target_cell:
                    break
            if target_value and target_cell is not None:
                #row_index = target_cell.row + 1
                rows_to_insert = dataframe_to_rows(extracted_content, index=False, header=False)
                try:
                    if row_index is not None and rows_to_insert is not None:
                        for row_num, row_data in enumerate(rows_to_insert, start=row_index):
                            worksheet.insert_rows(row_num)
                            for col_num, value in enumerate(row_data, start=1):
                                if isinstance(value,str):
                                    if value[0] == '*':
                                        worksheet.insert_rows(row_num-1)
                                        worksheet.cell(row=row_num, column=col_num,value=value[1:]).style = underlined_style
                                    else:
                                        worksheet.cell(row=row_num, column=col_num,value=value).style = standard_style
                                elif isinstance(value, float):
                                    worksheet.cell(row=row_num, column=col_num+3,value=value).style = number_style
                                else:
                                    worksheet.cell(row=row_num, column=col_num,value=value).style = standard_style
                        #worksheet.insert_rows(row_num+1)       
                except Exception as e:
                    print(e)
            else:
                print(f"Cell with value '{target_value}' not found.")
    return workbook


def extract_phase(current_phase:str,content:pd.DataFrame):
    phase_mapping = {
                'Plan': 'Prepare:',
                'Prepare': 'Implement:',
                'Implement': 'Operate:',
                'Operate': '*Execute Test Plan:',
                '*Execute Test Plan': 'Optimize:',
                'Optimize': 'Project closure'
            }
    if current_phase == 'All':
        phase_content = content
    elif current_phase in phase_mapping:
        phase_index = content[content['Task'] == current_phase + ':'].index[0]
        next_phase = phase_mapping[current_phase]
        next_phase_index = content[content['Task'] == next_phase].index[0] if next_phase in content['Task'].values else len(content)
        phase_content = content.loc[phase_index:next_phase_index-1]
    else:
        phase_index = content[content['Task'] == current_phase + ':'].index[0]
        phase_content = content.loc[phase_index:]
    return phase_content

def read_procedure(procedure_file_path:str):
    procedure_file_content = read_text_file(procedure_file_path)
    test= io.StringIO(procedure_file_content)
    df = pd.read_csv(test, sep='|',skip_blank_lines=False)
    df['Task'].fillna("",inplace=True,)
    return df

def prepare_content(sbvalues:dict,data:dict,templates_path:str):
    #client_file_path = f"./templates/clients/{client}/{client}.txt"
    #client_file_content = read_text_file(client_file_path)

    #procedure_file_path = f"./templates/procedures/{procedure}/{technology}.txt"
    #procedure_file_content = read_text_file(procedure_file_path)
    phase_mapping = {
                'Plan': 'Prepare:',
                'Prepare': 'Implement:',
                'Implement': 'Operate:',
                'Operate': '*Execute Test Plan:',
                '*Execute Test Plan': 'Optimize:',
                'Optimize': 'Project closure'
            }
    df_list = []
    df_combined = pd.DataFrame()

    for index,procedure in enumerate(data['Procedure']):
        try:
            procedure_file_path = templates_path + f"/{data['Library'][index]}/procedures/{procedure}/{data['Technology'][index]}/{data['Version'][index]}.txt"
            df_list.append(extract_phase(current_phase=data['Phase'][index],content=read_procedure(procedure_file_path)))
        except Exception as e:
            print(f"Error processing procedure {procedure}: {e}")
    for phase in phase_mapping:
        first = True
        for index,df in enumerate(df_list):
            try:
                if first:
                    if data['psettings'][index]:
                        for key, value in data['psettings'][index].items():
                            df['Task'] = df['Task'].apply(lambda x: x.replace(f"<{key}>", str(value)))
                            if key == 'Quantity':
                                df.loc[df['Time'].notna(), 'Multiplier'] = value
                            elif key == 'Onsite Service':
                                df.loc[df['Time'].notna(), 'Multiplier'] = value
                    df_combined = pd.concat([df_combined,extract_phase(current_phase=phase,content=df)])
                    first = False
                else:
                    if data['psettings'][index]:
                        for key, value in data['psettings'][index].items():
                            df['Task'] = df['Task'].apply(lambda x: x.replace(f"<{key}>", str(value)))
                            if key == 'Quantity':
                                df.loc[df['Time'].notna(), 'Multiplier'] = value
                            elif key == 'Onsite Service':
                                df.loc[df['Time'].notna(), 'Multiplier'] = value
                    df_combined = pd.concat([df_combined,extract_phase(current_phase=phase,content=df).iloc[1:]])
            except:
                None

    for item in data['psettings']:
        for option, value in item.items():
            df_combined.apply(lambda x: x.replace(f"<{option}>", str(value)))
                
    df_combined.loc[df_combined['Time'].notna() & df_combined['Multiplier'].isna(), 'Multiplier'] = 1

    return df_combined.reset_index(drop=True)

def get_microsoft_lists_data():
    certificate_path='certs/AKTISFLOWS.pem'
    tenant_id='1629059d-1b1e-4108-bee7-f509b4c6e6ff'
    client_id='09b4038a-b7ed-4784-99ef-09fcfe12eaef'
    site_id='6b836720-11bd-422b-9a40-c86d69f7cdc8,ad83eab1-7d92-42fc-a66b-c6638ea73605'
    list_id='273f2e45-131d-4b30-8c58-4d57aae31021'
    thumbprint='440FC2B08CC7586C815CACE316B72C79C7FDDE21'
    
    with open(certificate_path, 'rb') as cert_file:
        cert_data = cert_file.read()

    # Build the MSAL confidential client application
    authority = f'https://login.microsoftonline.com/{tenant_id}'
    app = ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential={'thumbprint': thumbprint, 'private_key': cert_data}
    )

    # Get the access token
    #token_response = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
    token_response = {}
    token_response["access_token"] = 'eyJ0eXAiOiJKV1QiLCJub25jZSI6Ijc3b2lxdlJRYmFwLTNTcDBoNnNuSnJabWRfRnVYYjBpajNrcmRfZENSRTgiLCJhbGciOiJSUzI1NiIsIng1dCI6IlQxU3QtZExUdnlXUmd4Ql82NzZ1OGtyWFMtSSIsImtpZCI6IlQxU3QtZExUdnlXUmd4Ql82NzZ1OGtyWFMtSSJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8xNjI5MDU5ZC0xYjFlLTQxMDgtYmVlNy1mNTA5YjRjNmU2ZmYvIiwiaWF0IjoxNzAyMjY4NDMzLCJuYmYiOjE3MDIyNjg0MzMsImV4cCI6MTcwMjI3MjMzMywiYWlvIjoiRTJWZ1lOZ3JMcjlWUHJqdnFaaHA4SlRqUzBPUEF3QT0iLCJhcHBfZGlzcGxheW5hbWUiOiJBS1RJU0ZMT1dTIiwiYXBwaWQiOiIwOWI0MDM4YS1iN2VkLTQ3ODQtOTllZi0wOWZjZmUxMmVhZWYiLCJhcHBpZGFjciI6IjIiLCJpZHAiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8xNjI5MDU5ZC0xYjFlLTQxMDgtYmVlNy1mNTA5YjRjNmU2ZmYvIiwiaWR0eXAiOiJhcHAiLCJvaWQiOiI2NzExMGY2Zi1lYTVlLTQ4OTgtYmFiZC1iZDU5ZjAwNzA3MDgiLCJyaCI6IjAuQVN3QW5RVXBGaDRiQ0VHLTVfVUp0TWJtX3dNQUFBQUFBQUFBd0FBQUFBQUFBQUQyQUFBLiIsInJvbGVzIjpbIlVzZXIuUmVhZFdyaXRlLkFsbCIsIkdyb3VwLlJlYWRXcml0ZS5BbGwiXSwic3ViIjoiNjcxMTBmNmYtZWE1ZS00ODk4LWJhYmQtYmQ1OWYwMDcwNzA4IiwidGVuYW50X3JlZ2lvbl9zY29wZSI6Ik5BIiwidGlkIjoiMTYyOTA1OWQtMWIxZS00MTA4LWJlZTctZjUwOWI0YzZlNmZmIiwidXRpIjoiQ01jbWdFZDhpMEd3b2d4V0hWcElBQSIsInZlciI6IjEuMCIsIndpZHMiOlsiMDk5N2ExZDAtMGQxZC00YWNiLWI0MDgtZDVjYTczMTIxZTkwIl0sInhtc190Y2R0IjoxNTI5NTM5Mzg3fQ.SeyndSDCmTUNz_k2X5cXB8jO7OVGROsPZjGvXYr56h5IH-fUPyeQRmT0XkAvKHlD-Fdd0ee0mAG2azk7wpcGgdJTsV_oKQCFzAkPlw9qo0B2CdTIHn0jbwU7-LBFpsmXis1BMzMH-4vAJsuRp1-Z2xo1fnsV9fpnteoUWX1TRm80bT4D-NzvZtPfBsFNxgnTrobB3ORHyg3KXtZrCGuBYAlgh-0QRIJx9g_eoQTT0hfvjTc8M6ZJMdR0HLGxPkkbuEd-Y1E6Jw1yOjzPfIcR0HjPEsopRC9b5AXurPyqq2bbFe6lG-WfaDYnfsv4UxpbcgGB4oNl0hzy5o3flv6NTw'

    filter_query="TicketStatus eq Complete"
    # Make request to Microsoft Graph API
    endpoint_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?expand=fields(select=Title,TicketNumber,KTNumber,TicketStatus,ClientName,ProposalName_x0028_TicketSummary,ProposalVersion)&filter=fields/{filter_query}'
    headers = {
        'Authorization': f'Bearer {token_response["access_token"]}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.get(endpoint_url, headers=headers)

    if response.status_code == 200:
        data = [item['fields'] for item in response.json()['value']]
        df = pd.DataFrame(data)
        return df
    else:
        return f'Error: {response.status_code} - {response.text}'
    

def print_progress(items):
    # type: (ListItemCollection) -> None
    print("Items read: {0}".format(len(items)))


def query_large_list(target_list):
    # type: (List) -> None
    paged_items = (
        target_list.items.paged(500, page_loaded=print_progress).get().execute_query()
    )
    #for index, item in enumerate(paged_items):  # type: int, ListItem
    #    print("{0}: {1}".format(index, item.id))
    # all_items = [item for item in paged_items]
    # print("Total items count: {0}".format(len(all_items)))
    return paged_items

def excel_to_pipe_delimited(input_file):
    df = pd.read_excel(input_file)
    # Combine the columns with '|' separator
    #df = df['Task'].astype(str) + '|' + df['Time'].astype(str)
    return df

def pipe_delimited_to_csv(input_df,output_file_path):
    # Save the new DataFrame to a pipe-delimited text file
    input_df.to_csv(output_file_path, sep='|', index=False, header=True, na_rep='')

def get_total_count(target_list):
    # type: (List) -> None
    all_items = target_list.items.get_all(5000, print_progress).execute_query()
    print("Total items count: {0}".format(len(all_items)))


def Get_SharePoint_data(sp_list:str,filter:str):
    site_url='https://projectfuelnow.sharepoint.com/sites/Fuelnow'

    cert_credentials = {
        "tenant" : '1629059d-1b1e-4108-bee7-f509b4c6e6ff',
        "client_id" : '09b4038a-b7ed-4784-99ef-09fcfe12eaef',
        "thumbprint": '440FC2B08CC7586C815CACE316B72C79C7FDDE21',
        "cert_path": 'certs/AKTISFLOWS.pem'
    }

    ctx = ClientContext(site_url).with_client_certificate(**cert_credentials)

    sp_lists = ctx.web.lists
    s_list = sp_lists.get_by_title(sp_list)

    if filter == '*':
        l_items = query_large_list(s_list)
    else:
        l_items = s_list.items.filter(filter).get()
    list_fields = s_list.fields
    ctx.load(list_fields)
    ctx.execute_query()
    #column_names = [field.properties['Title'] for field in list_fields]
    #print(column_names)

    internal_names = [field.properties['InternalName'] for field in list_fields]
    #print(internal_names)
 
    data_dict_list = []
    for item in l_items:
        item_data_dict = {}
        for property_name in internal_names:
            # Use try-except to handle cases where the property may not exist
            try:
                property_value = item.properties[property_name]
            except KeyError:
                property_value = None  # or any default value you want to assign
            item_data_dict[property_name] = property_value
        data_dict_list.append(item_data_dict)

    return data_dict_list

def calculate_proposal_time(df: pd.DataFrame):
    #df.loc[df['Time'].notna(), 'Multiplier'] = Quantity
    df['Total'] = df.apply(lambda row: row['Time'] * row['Multiplier'] if row['Time'] != '' and row['Multiplier'] != '' else None,axis=1)

    last_column = df.columns[-1]
    columns = [col for col in df.columns if col != 'Total']
    columns.insert(1,last_column)
    df = df[columns]

    rounding_series = [0.02, 0.04, 0.08, 0.16, 0.25, 0.33, 0.50, 0.75]
    asterisk_indices = df[df['Task'].str.startswith('*')].index

    for i in range(len(asterisk_indices) - 1):
        start_index = asterisk_indices[i]
        end_index = asterisk_indices[i + 1]
        
        total_sum = df.loc[start_index+1:end_index-1, 'Total'].sum()
        decimal_part = total_sum % 1
        whole_part = total_sum // 1
        rounded_sum = whole_part + min(rounding_series, key=lambda x: abs(x - decimal_part))

        df.at[start_index, 'Hours'] = rounded_sum
    
    last_column = df.columns[-1]
    columns = [col for col in df.columns if col != 'Hours']
    columns.insert(1,last_column)
    df = df[columns]

    return df


def add_spaces_to_df_phases(df: pd.DataFrame):
    trigger_values = ['Prepare:','Implement:', 'Operate:', '*Execute Test Plan:', 'Optimize:']

    for trigger_value in trigger_values:
        if trigger_value == 'Prepare:':
            continue
        else:
            mask = df['Task'] == trigger_value
            indices_to_insert = df.index[mask]  # Get indices where the trigger value is found

            for idx in indices_to_insert:
                df = pd.concat([df.loc[:idx-1], pd.DataFrame({'Task': ['']}), df.loc[idx:]]).reset_index(drop=True)

def add_spaces_to_df_subphases(df: pd.DataFrame):
    phases_values = ['Prepare:','Implement:', 'Operate:', '*Execute Test Plan:', 'Optimize:']
    count_starts_with_asterisk = len(df[df['Task'].str.startswith('*')])
    for idx in range(count_starts_with_asterisk):
        for index, row in df.iterrows():
            if row['Task'].startswith('*'):
                if df.loc[index-1, 'Task'] == '':
                    continue
                elif index > 0 and df.loc[index-1, 'Task'] in phases_values:
                    continue
                else:
                    new_row = pd.DataFrame({'Task': ['']}, index=[index])
                    df = pd.concat([df.iloc[:index], new_row, df.iloc[index:]]).reset_index(drop=True)
                    break
    return df
