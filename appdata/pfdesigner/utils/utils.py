#utils.py
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
    import streamlit as st
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
    
def get_variables_from_excel(client):
    pattern = r'<(.*?)>'
    workbook = openpyxl.load_workbook(f"./templates/clients/{client}/Template.xlsx")
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
    
def prepare_content(client,phase,procedure,technology):
    client_file_path = f"./templates/clients/{client}/{client}.txt"
    procedure_file_path = f"./templates/procedures/{procedure}/{technology}.txt"
    client_file_content = read_text_file(client_file_path)
    procedure_file_content = read_text_file(procedure_file_path)
    try:
        content = pd.read_csv(io.StringIO(procedure_file_content), sep='|')
        phase_mapping = {
            'Plan': 'Prepare:',
            'Prepare': 'Implement:',
            'Implement': 'Operate:',
            'Operate': 'Optimize:',
            'Optimize': 'Project closure'
        }
        if phase == 'All':
            phase_content = content
        elif phase in phase_mapping:
            phase_index = content[content['Task'] == phase + ':'].index[0]
            next_phase = phase_mapping[phase]
            next_phase_index = content[content['Task'] == next_phase].index[0]
            phase_content = content.loc[phase_index:next_phase_index-1]
        else:
            phase_index = content[content['Task'] == phase + ':'].index[0]
            phase_content = content.loc[phase_index:]
        content = phase_content
        #content = content.replace('-', ' ')
        return content
    except Exception as e:
        print(e)