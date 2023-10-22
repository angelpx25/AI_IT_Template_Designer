import openpyxl
import os
import pandas as pd

def is_cell_underlined(cell):
    """
    Check if a cell is underlined.
    """
    if cell.font.underline:
        return True
    return False

def is_cell_red(cell):
    """
    Check if a cell has red font color.
    """
    font_color = cell.font.color
    if font_color is not None:
        if font_color.rgb == "FFFF0000":
            return True
        else:
            return False
    else:
        return False
    
def is_cell_excluded(cell, excluded_values):
    """
    Check if a cell value is in the list of excluded values.
    """
    cell_value = cell.value
    return cell_value in excluded_values

def is_cell_included(cell, included_values):
    """
    Check if a cell value is in the list of excluded values.
    """
    cell_value = cell.value
    return cell_value in included_values

def extract_block_tasks(file_path,sheet_name,excluded_values,included_values):
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.worksheets[0]

        task_blocks = []
        block = [[],[]]
        breq = ""
        count = 0
        for row in sheet.iter_rows(min_col=1,max_col=1):
            for cell in row:
                if (cell.row == 2):
                    breq = cell.value
                if (cell.row < 6):
                    continue
                if  (cell.font.color == None and not is_cell_underlined(cell) and cell.value is not None and not is_cell_excluded(cell, excluded_values)):
                    task_blocks.append(cell.value)
                elif (is_cell_underlined(cell) and cell.value is not None and not is_cell_excluded(cell, excluded_values)):
                    if len(task_blocks) != 0:
                        block[count].append(task_blocks)
                        count += 1
                    block.append([])
                    block[count].append(cell.value)
                    task_blocks = []
                elif is_cell_included(cell, included_values):
                    task_blocks.append(cell.value)
        block[count].append(task_blocks)
        return block, breq


def extract_red_text_blocks(file_path, sheet_name, excluded_values, included_values):
    """
    Extract red text blocks under each underlined cell in a specific sheet in an Excel file.
    """
    try:
        return extract_block_tasks(file_path,sheet_name, excluded_values, included_values)
    except Exception:
        try:
            return extract_block_tasks(file_path,'V(1)', excluded_values, included_values)
        except Exception:
            try:
                return extract_block_tasks(file_path,'V2', excluded_values, included_values)
            except Exception:
                try:
                    return extract_block_tasks(file_path,'V3', excluded_values, included_values)
                except Exception:
                    try:
                        return extract_block_tasks(file_path,'V4', excluded_values, included_values)
                    except Exception as e:
                        print(f"Error occurred: {e} in file {file_path}")
                        return []


def consolidate_tasks(input_file):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(input_file)

    # Group the data by 'phase', 'subphase', and aggregate tasks
    grouped = df.groupby(['phase', 'subphase'])['task'].agg(list).reset_index()

    # Create a Categorical type for the 'phase' column to preserve the order
    phase_order = df['phase'].unique()
    phase_cat = pd.CategoricalDtype(categories=phase_order, ordered=True)
    grouped['phase'] = grouped['phase'].astype(phase_cat)

    # Create a Categorical type for the 'subphase' column to preserve the order
    subphase_order = df['subphase'].unique()
    subphase_cat = pd.CategoricalDtype(categories=subphase_order, ordered=True)
    grouped['subphase'] = grouped['subphase'].astype(subphase_cat)

    # Group the data by 'phase' and aggregate subphases and their tasks
    phase_grouped = grouped.groupby('phase')[['subphase', 'task']].apply(lambda x: list(zip(x['subphase'], x['task']))).reset_index(name='subphase_task')

    # Create a formatted output DataFrame
    formatted_output = pd.DataFrame(columns=['formatted_output'])
    for _, row in phase_grouped.iterrows():
        formatted_text = row['phase'] + "\n\n"
        for subphase, tasks in row['subphase_task']:
            formatted_text += subphase + "\n" + '\n'.join(tasks) + "\n\n"
        formatted_output = pd.concat([formatted_output,pd.DataFrame({'formatted_output': [formatted_text]})],ignore_index=True)

    
    consolidatedphases_text = formatted_output['formatted_output'].str.cat(sep='\n')
    consolidatedphases_df = pd.DataFrame({'joined_formatted': [consolidatedphases_text]})
    return consolidatedphases_df

def extract_tasks(folder_path):
    count = 0
    breq = [str]
    for file in os.listdir(folder_path):
        if file.endswith(".xlsx") or file.endswith(".xls"):
            file_path = os.path.join(folder_path, file)
            sheet_name = "V1"  # Replace with the name of the sheet containing the underlined and red text
            excluded_values = ["Total", "Time", "Multiplier"]
            included_values = ["Plan:", "Prepare:", "Implement:", "Implement & Operate:", "Operate:", "Optimize:", "Proposal Notes"]
            phase_block_breq = extract_red_text_blocks(file_path, sheet_name, excluded_values, included_values)
            breq[count] = phase_block_breq[1]
            breq.append([])
            phase_blocks = phase_block_breq[0]
            phase = "Plan:"
            data = {
                #'id' : [],
                #'workplan' : [],
                #'technology' : [],
                #'businessrequirement' : [],
                'phase' : [],
                'subphase' : [],
                'task' : []
            }
            df = pd.DataFrame(data)
            for block in phase_blocks:
                for subphase in block:
                    if subphase is not block[0]:
                        for task in subphase:
                            if task in included_values:
                                phase = task
                            else:
                                df = pd.concat([df,pd.DataFrame({'phase' : phase, 'task' : [task],'subphase' : block[0]})], ignore_index=True)
            df.to_csv(f"./Tasks/tasks{count}.csv", index=False)
            count += 1
    return count, breq

def create_combined_csv(input_dir=".",headers=None,breq=[]):
    if headers is None:
        headers = ["instruction", "input", "output"]
    
    csv_files = [file for file in os.listdir(input_dir) if file.startswith("train") and file.endswith(".csv")]

    combined_data = pd.DataFrame(columns=headers)

    for count, csv_file in enumerate(csv_files, start=0):
        df = pd.read_csv(input_dir+csv_file,header=None)
        output_column = df.iloc[:, 0]
        instruction_column = ["Create an information technology workplan with the following business requirement: "] * len(df)
        input_column = [breq[count]] * len(df)

        file_data = pd.DataFrame({
            headers[0]: instruction_column,
            headers[1]: input_column,
            headers[2]: output_column
        })
        combined_data = pd.concat([combined_data, file_data], ignore_index=True)

    combined_data.to_csv("data.csv", index=False)

def create_text_column(csvfilepath):
    df = pd.read_csv(csvfilepath)
    df = df.fillna("")

    text_col = []
    for _, row in df.iterrows():
    #prompt = "Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request"
        prompt = ""
        instruction = str(row['instruction'])
        input_query = str(row['input'])
        response = str(row['output'])

        if len(input_query.strip()) == 0:
            text = (
                prompt
                + "<s>[INST] "
                + instruction
                + " [/INST] "
                + response
                + " </s>"
            )
        else:
            text = (
                prompt
                + "<s>[INST] "
                + instruction
                + "business requirement: "
                + input_query
                + f" [/INST]\n\n"
                + response
                + " </s>"
            )
        text_col.append(text)

    df.loc[:,"text"] = text_col
    df = df.iloc[:, -1]
    df.to_csv('final.csv', index=False)

def delete_csv_files_with_prefix(folder_path, prefixes):
    """
    Deletes CSV files from a folder that start with any of the specified prefixes.

    :param folder_path: Path to the folder containing the files.
    :param prefixes: List of prefixes to match filenames against.
    """
    for filename in os.listdir(folder_path):
        if any(filename.lower().startswith(prefix.lower()) for prefix in prefixes):
            if filename.lower().endswith(".csv"):
                file_path = os.path.join(folder_path, filename)
                os.remove(file_path)
                print(f"Deleted: {file_path}")

if __name__ == "__main__":
#    result_extract_tasks = extract_tasks('./Proposals/')
#    count = result_extract_tasks[0] - 1
#    breq = result_extract_tasks[1]
    #count = 729
#    for i in range(count, -1, -1):
#        consolidatedtasks_df = consolidate_tasks(f"./Tasks/tasks{i}.csv")
#        consolidatedtasks_df.to_csv(f"./Trains/train{i}.csv",index=False,header=False)
#    create_combined_csv('./Trains/',breq=breq)
    #delete_csv_files_with_prefix(".",['train', 'tasks'])
    create_text_column('data.csv')
    
