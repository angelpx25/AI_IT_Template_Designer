#Import transformer
import torch, os
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, GenerationConfig

#Import streamlit
import streamlit as st
from streamlit_chat import message

#Import langchain
from langchain import HuggingFacePipeline
from langchain import PromptTemplate,  LLMChain
from langchain.memory import ConversationBufferMemory

#Import additional librearies
import json
import textwrap
import openai
import dotenv
import openpyxl
import io
import re

#Other Imports
import tempfile

#Training Imports
from transformers import TrainingArguments, BitsAndBytesConfig
from trl import SFTTrainer
from peft import LoraConfig, AutoPeftModelForCausalLM, PeftModel
import pandas as pd
from datasets import load_dataset

#Prompt Parameters
B_INST, E_INST = "<s>[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
DEFAULT_SYSTEM_PROMPT = """\
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information."""

#Initializers
device_map_tokenizer = 'auto'
device_map_model = 'auto'
device_map_pipe = 'auto'
device_map_training = 'auto'

#%% Prepare Dataset
def prepare_dataset(datasetfile: str, outputpath: str ='./datasets/train.csv'):
    st.write(datasetfile)
    df = pd.read_csv(datasetfile)
    st.write(df)
    df.fillna("", inplace=True)

    text_col = []
    for _, row in df.iterrows():
        prompt = ""
        instruction = str(row['instruction'])
        input_query = str(row['input'])
        response = str(row['output'])

        inst_format = f"\n<s>[INST] {instruction} [/INST]\n"

        if len(input_query.strip()) != 0:
            inst_format += f"\ninput:\n{input_query}"

        text = f"{inst_format}\n{response} </s>"
        text_col.append(text)

    df.loc[:,"text"] = text_col
    df = df.iloc[:, -1]
    df.to_csv(outputpath, index=False, sep='\t')

#%% Call tokenizer
@st.cache_resource
def load_tokenizer(llmselect):
    if selected_model == 'Trained Model':
        tokenizer = AutoTokenizer.from_pretrained(
            'meta-llama/Llama-2-7b-chat-hf',
            use_fast=True,
            device_map=device_map_tokenizer,
            trust_remote_code=True,
                                                    )
    else:
        tokenizer = AutoTokenizer.from_pretrained(
            llmselect,
            use_fast=True,
            device_map=device_map_tokenizer,
            trust_remote_code=True,
                                                    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    return tokenizer

#%% Call model
@st.cache_resource
def load_model(llmselect):
    if selected_model == 'GPT':
        return llmselect
    if selected_model == 'Trained Model':
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=False,
            )
        base_model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b-chat-hf',
                                                    device_map=device_map_model,
                                                    torch_dtype=torch.float16,
                                                    quantization_config=bnb_config,
                                                    #use_auth_token=True,
                                                    #  load_in_8bit=True,
                                                    #  load_in_4bit=True
                                                    )
        model = PeftModel.from_pretrained(base_model, llmselect)
        model = model.merge_and_unload()
    else:
        model = AutoModelForCausalLM.from_pretrained(llmselect,
                                                    device_map=device_map_model,
                                                    torch_dtype=torch.float16,
                                                    quantization_config=bnb_config,
                                                    #use_auth_token=True,
                                                    #  load_in_8bit=True,
                                                    #  load_in_4bit=True
                                                    load_in_4bit=True
                                                    )
    # don't use the cache
    model.config.use_cache = False
    return model

#%% Call pipeline
def load_pipe(temperature=0.01,top_k=30,top_p=0.10,max_tokens=512):
    #print(f" Pipe Settings: Temperature:{temperature} Top_k:{top_k} Top_p:{top_p} Max tokens:{max_tokens}")
    pipe = pipeline("text-generation",
                    model=load_model(llmselect),
                    tokenizer=load_tokenizer(),
                    torch_dtype=torch.bfloat16,
                    device_map=device_map_pipe,
                    max_new_tokens=max_tokens,
                    do_sample=True,
                    top_k=top_k,
                    top_p=top_p,
                    temperature=temperature,
                    #max_length=max_length,
                    num_return_sequences=1,
                    eos_token_id=load_tokenizer(llmselect=llmselect).eos_token_id,
                    )
    return pipe

# %% Call llm
def load_llm(pipe):     
    llm = HuggingFacePipeline( pipeline = pipe)
    return llm

#%% Load Dataset
#@st.cache_data
def load_datasets(tmp_file_path):
    os.rename(tmp_file_path, os.path.dirname(tmp_file_path) + "/train.csv")
    datasetpath = os.path.dirname(tmp_file_path) + "/train.csv"
    dataset = load_dataset('csv', data_files=datasetpath)
    dataset = dataset['train']
    #st.write(dataset['text'][0])
    return dataset

#%% Training Arguments
@st.cache_data
def load_training_arguments():
        training_arguments = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=overwrite_output_dir,
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=per_device_train_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        #gradient_checkpointing=gradient_checkpointing,
        optim=optim,
        save_steps=save_steps,
        logging_steps=logging_steps,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        fp16=fp16,
        bf16=bf16,
        max_grad_norm=max_grad_norm,
        max_steps=max_steps,
        warmup_ratio=warmup_ratio,
        group_by_length=group_by_length,
        lr_scheduler_type=lr_scheduler_type,
        )
        training_arguments = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=5,      # uses the number of epochs earlier
            per_device_train_batch_size=4,          # 4 seems reasonable
            gradient_accumulation_steps=2,          # 2 is fine, as we're a small batch
            optim="paged_adamw_32bit",              # default optimizer
            save_steps=0,                           # we're not gonna save
            logging_steps=1,                       # same value as used by Meta
            learning_rate=2e-4,                     # standard learning rate
            weight_decay=0.001,                     # standard weight decay 0.001
            fp16=False,                             # set to true for A100
            bf16=False,                             # set to true for A100
            max_grad_norm=0.3,                      # standard setting
            max_steps=-1,                           # needs to be -1, otherwise overrides epochs
            warmup_ratio=0.03,                      # standard warmup ratio
            group_by_length=True,
            #auto_find_batch_size=False,
            #dataloader_drop_last=True,
            #remove_unused_columns=False,                  # speeds up the training
            lr_scheduler_type="cosine"              # constant seems better than cosine
            )
        return training_arguments

@st.cache_data
def load_loraconfig():
    peft_config = LoraConfig(
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        r=lora_r,
        bias=bias,
        task_type=task_type,
    )
    return peft_config

def prepare_trainer(datasetpath):
    trainer = SFTTrainer(
        model=load_model(llmselect),
        train_dataset=load_datasets(datasetpath),
        peft_config=load_loraconfig(),
        dataset_text_field="text",
        max_seq_length=4096,
        tokenizer=load_tokenizer(llmselect=llmselect),
        args=load_training_arguments(),
        packing=packing,
    )
    return trainer

def start_training(trainer):
    trainer.train()

def save_trained_model(trainer):
    trainer.model.save_pretrained(output_dir)

#%% Auto-Train
def autotrain(**kwargs):
    os.system(f"autotrain llm --train --project_name {kwargs.get('project_name')} --model {kwargs.get('at_model')} \
              --data_path '{kwargs.get('data_path')}' --text_column {kwargs.get('text_column')} {kwargs.get('use_peft')} \
                {kwargs.get('bnb')} --learning_rate {kwargs.get('learning_rate')} --train_batch_size {kwargs.get('train_batch_size')} \
                    --num_train_epochs {kwargs.get('num_train_epochs')} --trainer {kwargs.get('trainer')} > training.log")
                        #--model_max_length {kwargs.get('model_max_length')}  --block_size {kwargs.get('block_size')} > training.log")

def load_autotrain_arguments(tmp_file_path):
    at_kwargs = {'project_name': at_project_name, 'at_model': llmselect, 'data_path': tmp_file_path, 'text_column': at_text_column,\
                     'use_peft': at_use_peft, 'bnb': at_bnb, 'learning_rate': at_learning_rate, 'train_batch_size': at_train_batch_size,\
                        'num_train_epochs': at_num_train_epochs, 'trainer': at_trainer, 'model_max_length': at_model_max_length,\
                            'block_size': at_block_size}
    return at_kwargs

def projects_in_folder():
    folder_count = 0
    for item in os.listdir('./projects'):
        item_path = os.path.join('./projects', item)
        if os.path.isdir(item_path):
            folder_count += 1
    return folder_count

#%% Text Prompt
@st.cache_data
def get_prompt(instruction, new_system_prompt=DEFAULT_SYSTEM_PROMPT ):
    SYSTEM_PROMPT = B_SYS + new_system_prompt + E_SYS
    prompt_template =  B_INST + SYSTEM_PROMPT + instruction + E_INST
    return prompt_template

#%% Load prompt
@st.cache_data
def load_prompt():
    instruction = "Chat History:\n\n{chat_history} \n\nUser: {user_input}"
    #system_prompt = "My name is DDE. You are Fuely, an IT workplan writer, you always only answer for the assistant then you stop. your purpose is create IT workplans for the company Project Fuel. read the chat history to get context"
    system_prompt = "My name is DDE. You are Fuely, an IT workplan writer. Your purpose is to create IT workplans for the company Project Fuel, read the chat history to get context"
    
    #template = get_prompt(instruction, system_prompt)
    
    template = B_INST + " {user_input} " + E_INST
    prompt = PromptTemplate(
        #input_variables=["chat_history", "user_input"], template=template
        input_variables=["user_input"], template=template
    )
    return prompt

#%% Load Memory
@st.cache_resource
def load_memory():
    memory = ConversationBufferMemory(memory_key="chat_history")
    return memory

#%% Clear history
def clear_chat_history():
    if selected_model == 'GPT':
        st.session_state.messages = [{"role": "system", "content": "An IT workplan is divided in (4) phases. Prepare, Implement, Operate, Optimize.You are Fuely, an IT workplan writer for Project Fuel LLC"},
                                 {"role": "assistant", "content": "Hello DDE, What IT workplan can I write for you today?"}
                                 ]
    else:
        memory=load_memory()
        memory.clear()
        st.session_state.messages = [{"role": "system", "content": "An IT workplan is divided in (4) phases. Prepare, Implement, Operate, Optimize. You are Fuely, an IT workplan writer for Project Fuel LLC"},
                                 {"role": "assistant", "content": "Hello DDE, What IT workplan can I write for you today?"}
                                 ]
def number_to_letter(n):
    if 1 <= n <= 26:
        return chr(ord('a') + n - 1)
    else:
        return None  # Handle values outside the range a-z

def find_cell_matches(match,worksheet):
    found_cells = []
    for row in worksheet.iter_rows(values_only=True):
        for cell_value in row:
            if isinstance(cell_value, str):
                matches = re.findall(match, cell_value)
                if matches:
                    found_cells.append(cell_value)
    return found_cells

def replace_cell_in_coordinates(worksheet,new_cell_values):
    for cell_value in new_cell_values:
        target_value = cell_value
        for row_idx, row in enumerate(worksheet.iter_rows(values_only=True, min_row=1), start=1):
            for col_idx, cell_value in enumerate(row, start=1):
                if isinstance(cell_value, str) and target_value in cell_value:
                    cell = f"{number_to_letter(col_idx)}{row_idx}"
                    worksheet[cell] = new_cell_values[cell_value]
    return worksheet

def DownloadTemplate(workbook,cell_values):
    worksheet = workbook.active
    worksheet = replace_cell_in_coordinates(worksheet=worksheet,new_cell_values=cell_values)
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output

#%% Generate text
def generate_text(user_input: str):
    config = dotenv.dotenv_values(".env")
    openai.api_key=config['OPENAI_API_KEY']
    if selected_model =='GPT':
        completions = openai.ChatCompletion.create(model=load_model(llmselect="gpt-3.5-turbo-0613"),temperature=temperature, messages=st.session_state.messages)
        msg = completions.choices[0].message
        return msg.content

    if selected_model == 'Trained Model':
        prompt = B_INST + f" {user_input} " + E_INST
        tokenizer = load_tokenizer(llmselect)
        inputs = tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].cuda()
        generation_output = load_model(llmselect).generate(
            input_ids=input_ids,
            generation_config=GenerationConfig(temperature=0.2, top_p=0.75, num_beams=4),
            return_dict_in_generate=True,
            output_scores=True,
            max_new_tokens=max_tokens
        )
        generated_output = []
        for seq in generation_output.sequences:
            output = tokenizer.decode(seq)
            generated_output.append(output)
        
        return "\n".join(generated_output)
        #    print("Respuesta:", output.split("### Response:")[1].strip())
    else:
        pipe = load_pipe(temperature=temperature,top_k=top_k,top_p=top_p,max_tokens=max_tokens)
        llm=load_llm(pipe)
        memory=load_memory()
        print(f'modeltype: {selected_model}')
        if selected_model == 'Instruction':
            system_prompt = "My name is DDE. You are Fuely, an IT workplan writer. Your purpose is to create IT workplans for the company Project Fuel."
            prompt = system_prompt + "\n\n {user_input}"
            prompt = PromptTemplate(input_variables=["user_input"], template=prompt)
            llm_chain = LLMChain(
                llm=llm,
                prompt=prompt,
                verbose=False,
            )
            text = llm_chain.run(user_input=user_input)
        else:
            prompt = load_prompt()
            llm_chain = LLMChain(
                llm=llm,
                prompt=prompt,
                verbose=False,
                memory=memory,
            )
            text = llm_chain.predict(user_input=user_input)
        return text
    

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

def generate_prompt():
    client_file_path = f"./templates/clients/{selected_client}/{selected_client}.txt"
    procedure_file_path = f"./templates/{procedure}/{technology}.txt"
    client_file_content = read_text_file(client_file_path)
    procedure_file_content = read_text_file(procedure_file_path)
    #st.write(f"{client_file_content}\n\n{procedure_file_content}")
    if client_file_content == None or procedure_file_content == None:
        prompt = "Content could not be found"
    else:
        if selected_phase == 'All':
            prompt = f"1.Create an IT workplan using the following business requirement:\n\n{pvalues['breq']}.\n\n"\
                    f"2.Change the existing and new firewalls multiplier quantity from the business requirement\n\n"\
                    f"3.Calculate the Total multiplying Hours and Mutiplier.\n\n"\
                    f"4.Present content as table and provide the output without any additional comments.\n\n"\
                    f"5.{client_file_content}.\n\n"\
                    f"6.Use this template with '|' as separator to create it:\n\n{procedure_file_content}.\n"
        else:
            prompt = f"1.Provide only the {selected_phase} phase.\n\n"\
                    f"2.Create an IT workplan using the following business requirement:\n\n{pvalues['breq']}.\n\n"\
                    f"3.Change the existing and new firewalls multiplier quantity from the business requirement.\n\n"\
                    f"4.Calculate the Total multiplying Hours and Mutiplier.\n\n"\
                    f"5.Present content as table and provide the output without any additional comments.\n\n"\
                    f"6.{client_file_content}.\n\n"\
                    f"7.Use this template with '|' as separator to create it:\n\n{procedure_file_content}.\n"
    return prompt

#%% Set streamlit page configuration
st.set_page_config(page_title="PF Proposal Writer", page_icon=":pencil:", layout="wide")
#Website Structure
with st.sidebar:

    st.title("Project Fuel Template Designer")
    st.header("Proposal Settings:")

    selected_function = st.selectbox("Application mode:", options=['Proposal Template Designer', 'AI Proposal Development'], placeholder='Select Mode')
    pvalues= {}
    pvalues['pname'] = st.text_input("Proposal Name:",value='')
    pvalues['breq'] = st.text_input("Business Requirements:", value='')

    col1,col2 = st.columns(2)
    with col1:
        file_paths = os.listdir("./templates/clients")
        clients_list = file_paths
        selected_client = st.selectbox("Client:", clients_list, key='client',disabled=False)
    with col2:
        pvalues['pnumber'] = st.text_input("Proposal Number:", value='')
    
    psettings = {}
    pattern = r'<(.*?)>'
    workbook = openpyxl.load_workbook(f"./templates/clients/{selected_client}/Template.xlsx")
    worksheet = workbook.active
    cell_values = find_cell_matches(match=pattern,worksheet=worksheet)

    col1,col2,col3 = st.columns(3)
    with col1:
        selected_phase = st.selectbox("Phase:", ['All', 'Plan', 'Prepare', 'Implement','Operate','Optimize'], key='phase')
    with col2:
        selected_products = st.selectbox("Products:", ['No', 'Yes'], key='products',disabled=True)
    with col3:
        selected_notes = st.selectbox("Default Notes:", ['No', 'Yes'], key='notes',disabled=True)

    col1,col2,col3 = st.columns(3)
    with col1:
        technology_list = os.listdir("./templates/technologies")
        technology = st.selectbox("Techonology:", technology_list, key='technology')
    with col2:
        brand_list = os.listdir("./templates/technologies/" + technology) 
        brand = st.selectbox("Make:", brand_list, key='brand')
    with col3:
        procedure_list = os.listdir("./templates/procedures")
        procedure = st.selectbox("Procedure:", procedure_list, key='procedure')

    col1, col2 = st.columns(2)
    with col1:
        st.button('New Proposal',use_container_width=True)
            #st.download_button(label="Download", data=DownloadTemplate(workbook=workbook,cell_values=psettings), file_name=f"{pvalues['pname']} [{pvalues['pnumber']}].xlsx", key='download',use_container_width=True)
    with col2:
        reset = st.button('Reset Settings',use_container_width=True)

    if selected_function == 'AI Proposal Development':
        selected_model = st.selectbox("Model:", ['GPT', 'Instruction','Trained Model', 'Chat','Chat-13B'],key='selected_model')
        if selected_model == 'GPT':
            llmselect = 'meta-llama/Llama-2-13b-chat-hf'
        elif selected_model == 'Chat-13B':
            llmselect = 'meta-llama/Llama-2-13b-chat-hf'
        elif selected_model == 'Chat':
            llmselect = 'meta-llama/Llama-2-7b-chat-hf'
        elif selected_model == 'Trained Model':
            llmselect = "./projects/" + st.selectbox('Projects', [item for item in os.listdir('./projects')if os.path.isdir(os.path.join('./projects', item))])
        else:
            llmselect = 'meta-llama/Llama-2-7b-hf'
        st.subheader("Options:")
        if selected_model == 'GPT':
            col1, col2,col3 = st.columns(3)
            with col1:
                if st.button("Write Proposal"):
                    prompt = generate_prompt()
                    if prompt == "Content could not be found":
                        st.error("Error locating the content")
                    else:
                        st.session_state.messages.append({"role": "user", "content": prompt})
            with col2:
                if st.button("Clear Content"):
                    clear_chat_history()
            with col3:
                if st.button("Regenerate"):
                    st.session_state.messages.pop()
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button('Load'):
                    torch.cuda.empty_cache()
                    st.cache_resource.clear()
                    model = load_model(llmselect)
            with col2:
                if st.button('Clear'):
                    clear_chat_history()
            with col3:
                if st.button('Reset'):
                    if 'model' in globals():
                        del model
                    torch.cuda.empty_cache()
                    st.cache_resource.clear()
                    clear_chat_history()

            with st.expander("Prepare Dataset"):
                st.write("The csv file should have instruction|input|output")
                dataset_uploaded_file = st.file_uploader("Upload Dataset", type="csv",key='dataset_uploaded_file')
                trainfile_output = st.text_input('Trainfile Output', value='./datasets/train.csv')
                if st.button("Prepare Dataset"):
                    if dataset_uploaded_file:
                        with tempfile.NamedTemporaryFile(delete=True,dir="./tmp",suffix=".csv") as tmp_file:
                            tmp_file.write(dataset_uploaded_file.getvalue())
                            with st.spinner("Preparing..."):
                                try:
                                    prepare_dataset(datasetfile=tmp_file.name,outputpath=trainfile_output)
                                except Exception as e:
                                    st.error(f"Error preparing the dataset {e}")
                                else:
                                    st.success("Trainfile ready!")
                                    with open(trainfile_output) as file:
                                        st.download_button(label='Download',data=file,file_name='train_'+dataset_uploaded_file.name,mime='text/csv')
                    else:
                        st.error("Upload a dataset")

            with st.expander("Device Mapping"):
                device_map_tokenizer = st.selectbox("Tokenizer", ['auto','cuda', 'cpu'], key='device_map_tokenizer')
                device_map_model = st.selectbox("Model", ['cuda','auto', 'cpu'], key='device_map_model')
                device_map_pipe = st.selectbox("Pipeline", ['auto','cuda', 'cpu'], key='device_map_pipe')
                device_map_training = st.selectbox("Traning", ['auto','cuda', 'cpu'], key='device_map_training')

            with st.expander("Autotrain Traning"):
                st.subheader('Autotrain Configuration')
                at_project_name = st.text_input('project_name',value=f"Fuely{projects_in_folder()}")
                at_text_column = st.text_input('text_column',value="text")
                at_use_peft = st.text_input('use_peft',value="--use_peft")
                at_learning_rate = (st.slider('learning_rate', min_value=1, max_value=1000, value=200, step=1,key='at_learning_rate')) / 1000000
                at_train_batch_size = st.slider('train_batch_size', min_value=1, max_value=128, value=2, step=1, key='at_train_batch_size')
                at_num_train_epochs = st.slider('num_train_epochs', min_value=1, max_value=100, value=15, step=1, key='at_num_train_epochs')
                at_trainer = st.text_input('trainer',value="sft")
                at_model_max_length = st.slider('model_max_length', min_value=16, max_value=2048, value=2048, step=16, key='at_model_max_length')
                at_block_size = st.slider('block_size', min_value=16, max_value=2048, value=2048, step=16, key='at_block_size')
                at_fp16 = st.selectbox("fp16", [True,False], key='at_fp16')
                at_bnb = st.selectbox("BnB Config", ['', '--use_int8','--use_int4'], key='at_bnb')

                st.write('Not working yet')
                at_gradient_accumulation_steps = st.slider('at_gradient_accumulation_steps', min_value=1, max_value=128, value=1, step=1)
                at_warmup_ratio = st.slider('at_warmup_ratio', min_value=0.0, max_value=0.2, value=0.1, step=0.01)
                at_lora_alpha = st.slider('at_lora_alpha', min_value=1, max_value=16, value=16, step=1)
                at_lora_dropout = st.slider('at_lora_dropout', min_value=0.0, max_value=0.5, value=0.1, step=0.05)
                at_lora_r= st.slider('at_lora_r', min_value=8, max_value=64, value=64, step=8)
                at_uploaded_file = st.file_uploader("Upload your Train file", type="csv",key='at_uploaded_file')
                if st.button("Start"):
                    if at_uploaded_file:
                        try:
                            with tempfile.NamedTemporaryFile(delete=False,dir="./tmp") as tmp_file:
                                tmp_file.write(at_uploaded_file.getvalue())
                                tmp_file_path = tmp_file.name
                                os.rename(tmp_file_path, os.path.dirname(tmp_file_path) + "/train.csv")
                                tmp_folder_path = os.path.dirname(tmp_file_path)
                                with st.spinner("Training..."):
                                    st.session_state.messages.append({"role": "assistant", "content": "Please wait while I exercise my brain."})
                                    autotrain(**load_autotrain_arguments(tmp_folder_path)) 
                        except:
                            st.error("Error training with Autotrain")
                        else:
                            st.success("Training was successful")
                            st.session_state.messages.append({"role": "assistant", "content": "I am ready, ask me anything."})
                    else:
                        st.error("Upload a file to start training")
            with st.expander("SFT Traning"):
                st.subheader('Training Arguments')
                output_dir = "./projects/" + st.text_input('Output_dir',value=f"Fuely{projects_in_folder()}")
                overwrite_output_dir = st.selectbox("overwrite_output_dir", [True,False], key='overwrite_output_dir')
                num_train_epochs = st.slider('num_train_epochs', min_value=1, max_value=100, value=30, step=1)
                per_device_train_batch_size = st.slider('lper_device_train_batch_size', min_value=1, max_value=128, value=4, step=1)
                gradient_accumulation_steps = st.slider('gradient_accumulation_steps', min_value=1, max_value=128, value=2, step=1)
                gradient_checkpointing = st.selectbox("gradient_checkpointing", [True,False], key='gradient_checkpointing')
                optim = st.selectbox('optim', ['paged_adamw_32bit','adamw_torch', 'adam_torch','sgd'])
                save_steps = st.slider('save_steps', min_value=0, max_value=2000, value=100, step=10)
                logging_steps = st.slider('logging_steps', min_value=0, max_value=500, value=50, step=10)
                learning_rate = (st.slider('learning_rate', min_value=1, max_value=1000, value=200, step=1))/ 1000000
                weight_decay = st.slider('weight_decay', min_value=0.00, max_value=0.1, value=0.001, step=0.001)
                fp16 = st.selectbox("fp16", [False,True], key='fp16')
                bf16 = st.selectbox("bf16", [False,True], key='bf16')
                max_grad_norm = st.slider('max_grad_norm', min_value=0.0, max_value=1.0, value=0.3, step=0.1)
                if_max_seq_length = st.selectbox("if_max_seq_length", [False,True], key='if_max_seq_length')
                if if_max_seq_length:
                    max_seq_length = st.slider('max_seq_length', min_value=16, max_value=512, value=128, step=16)
                else:
                    max_seq_length = None
                max_steps = st.slider('max_steps', min_value=-1, max_value=100000, value=-1, step=100)  
                warmup_ratio = st.slider('warmup_ratio', min_value=0.0, max_value=0.2, value=0.03, step=0.01)
                group_by_length = st.selectbox('group_by_length', [True, False])
                lr_scheduler_type = st.selectbox('lr_scheduler_type', ['cosine', 'linear', 'constant'])
                packing = st.selectbox("packing", [False,True], key='packing')
                st.subheader('Peft Config')
                lora_alpha = st.slider('lora_alpha', min_value=1, max_value=16, value=16, step=1)
                lora_dropout = st.slider('lora_dropout', min_value=0.0, max_value=0.5, value=0.1, step=0.05)
                lora_r= st.slider('lora_r', min_value=8, max_value=64, value=64, step=8)
                bias = st.selectbox("Bias", ['none','all','lora_only'], key='bias')
                task_type = st.selectbox("Task Type", ['CAUSAL_LM','SEQ_2_SEQ_LM'], key='task_type')
                st.subheader('Upload File')
                uploaded_file = st.file_uploader("Upload your Train file", type="csv",key='uploaded_file')
                if st.button("Start SFT Training"):
                    if uploaded_file:
                        try:
                            with tempfile.NamedTemporaryFile(delete=False,dir="./tmp") as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_file_path = tmp_file.name
                                with st.spinner("Training..."):
                                    st.session_state.messages.append({"role": "assistant", "content": "Please wait while I exercise my brain."})
                                    trainerready = prepare_trainer(datasetpath=tmp_file_path)
                                    start_training(trainerready)
                                    st.button(f"Save Model in {output_dir}", on_click=save_trained_model(trainerready))
                        except Exception as e:
                            st.error(f"Error training with SFT {e}")
                        else:
                            st.success("Training was successful")
                            st.session_state.messages.append({"role": "assistant", "content": "I am ready, ask me anything."})
                    else:
                        st.warning("Upload a file to start training")

        with st.expander("Inference Settings"):
            st.subheader("Inference Settings:")
            temperature = st.slider('temperature', min_value=0.00, max_value=1.0, value=0.00, step=0.01)
            top_k = st.slider('top_k', min_value=10, max_value=100, value=30, step=1)
            top_p = st.slider('top_p', min_value=0.1, max_value=1.0, value=0.8, step=0.1)
            max_tokens = st.slider('max_tokens', min_value=1, max_value=2048, value=512, step=8)

    else: #TEMPLATE DESIGNER
        if pvalues['pname']:
            for cell_value in cell_values:
                if cell_value not in psettings:
                    psettings[cell_value] = ''
            if reset:
                pvalues['mwin'] = st.slider(label='Maintenace Windows',min_value=0,max_value=10,step=1,value=0)
                psettings['Proposal Name [Ticket]'] = f"{pvalues['pname']} [{pvalues['pnumber']}]"
                psettings['Enter Business Requirements'] = pvalues['breq']
                psettings['Day Prior to Maintenance Window'] = f"Day Prior to Maintenance Window ({pvalues['mwin']})"
                psettings['mtime1'] = int(pvalues['mwin']) * 0.25
                psettings['15 Minutes Prior to Maintenance Window'] = f"15 Minutes Prior to Maintenance Window ({pvalues['mwin']})"
                psettings['mtime2'] = int(pvalues['mwin']) * 0.16
                psettings['Maintenance Window Has Ended'] = f"Maintenance Window Has Ended ({pvalues['mwin']})"
                psettings['mtime3'] = int(pvalues['mwin']) * 0.08
                with st.expander(label='Template Settings'):
                        for key,value in psettings.items():
                            psettings[key] = st.text_input(label=key,value=' ',disabled=True)
                        
            # with st.expander(label='Advanced Settings'):
            else:
                pvalues['mwin'] = st.slider(label='Maintenace Windows',min_value=0,max_value=10,step=1)
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
            col1,col2 = st.columns(2)
            with col1:
                    st.download_button(label="Download", data=DownloadTemplate(workbook=workbook,cell_values=psettings), file_name=f"{pvalues['pname']} [{pvalues['pnumber']}].xlsx", key='download',use_container_width=True)
            with col2:
                debugmode = st.toggle(label="Debug Mode")
        else:
            pvalues['mwin'] = 0
st.sidebar.markdown('Version: 0.01 By Angel Paruas')

if selected_function == 'AI Proposal Development':
    st.markdown("<p style='text-align: center; color: black;'>Fuely Proposal Writer</p>", unsafe_allow_html=True)
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "system", "content": "An IT workplan is divided in (4) phases. Prepare, Implement, Operate, Optimize. You are Fuely, an IT workplan writer for Project Fuel LLC"},
                                    {"role": "assistant", "content": "Hello DDE, What IT workplan can I write for you today?"}
                                    ]
    for index,message in enumerate(st.session_state.messages):
        if (st.session_state.messages[index]["role"] != "system"):  
            #if (st.session_state.messages[index]["content"]).startswith("Write an IT workplan to:"):
            #    continue
            #if (st.session_state.messages[index-3]["content"]).startswith("Write an IT workplan to:"):
            #    st.session_state.messages.pop(index-3)
            #else:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
    if userinput := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": userinput})
            with st.chat_message("user"):
                st.write(userinput)
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            placeholder = st.empty()
            if selected_model =='GPT':
                report = []
                config = dotenv.dotenv_values(".env")
                openai.api_key=config['OPENAI_API_KEY']
                for resp in openai.ChatCompletion.create(model=load_model(llmselect="gpt-3.5-turbo-0613"),temperature=temperature,stream=True,messages=st.session_state.messages):
                    try:
                        report.append(resp.choices[0].delta.content)
                        result = "".join(report).strip()
                        placeholder.markdown(f'*{result}*')
                        message = {"role": "assistant", "content": result}
                    except:
                        continue
            else:
                with st.spinner("Thinking..."):
                    response = generate_text(user_input=userinput)
                    full_response = ''
                    for item in response:
                        full_response += item
                        placeholder.markdown(full_response)
                    placeholder.markdown(full_response)
                    message = {"role": "assistant", "content": full_response}
            st.session_state.messages.append(message)
            st.download_button(label='Download CSV', data=message['content'], file_name=f"{pvalues['pname']}.csv", mime='text/csv')
else:
    proposal_name = pvalues['pname'] if pvalues['pname'] != '' else "Proposal Name"
    st.subheader(proposal_name, divider="grey")
    st.write("<b>Proposal number:</b> " + pvalues['pnumber'], unsafe_allow_html=True)
    st.write("<b>Business requirements:</b> " + pvalues['breq'], unsafe_allow_html=True)
    st.write("<b>Maintenance windows:</b> " + str(pvalues['mwin']), unsafe_allow_html=True)
    client_file_path = f"./templates/clients/{selected_client}/{selected_client}.txt"
    procedure_file_path = f"./templates/procedures/{procedure}/{technology}.txt"
    client_file_content = read_text_file(client_file_path)
    procedure_file_content = read_text_file(procedure_file_path)
    #st.write(f"{client_file_content}\n\n{procedure_file_content}")
    if client_file_content == None or procedure_file_content == None:
        content = "Content could not be found"
        st.error(content)
    else:
        try:
            content = pd.read_csv(io.StringIO(procedure_file_content), sep='|')
            phase_mapping = {
                'Plan': 'Prepare:',
                'Prepare': 'Implement:',
                'Implement': 'Operate:',
                'Operate': 'Optimize:',
                'Optimize': 'Project closure'
            }
            if selected_phase == 'All':
                phase_content = content
            elif selected_phase in phase_mapping:
                phase_index = content[content['Task'] == selected_phase + ':'].index[0]
                next_phase = phase_mapping[selected_phase]
                next_phase_index = content[content['Task'] == next_phase].index[0]
                phase_content = content.loc[phase_index:next_phase_index-1]
            else:
                phase_index = content[content['Task'] == selected_phase + ':'].index[0]
                phase_content = content.loc[phase_index:]
            content = phase_content
            if st.toggle("Plain Text:"):
                content = content.to_csv(index=False, header=False,sep='\t',lineterminator='\n')
                st.code(content.replace('-', ' '))
            else:
                content = content.replace('-', ' ', regex=True)
                st.table(content)
        except Exception as e:
            if debugmode:
                st.error(f"Fix the following error {e}")
            else:
                st.error('The data does not exists')

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
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
# %%
