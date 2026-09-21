# AI IT Template Designer

A Streamlit web app that helps IT engineers build **proposal workplans** — Excel files that list every task, phase, and estimated hour for a project such as a firewall replacement or a switch installation. It pulls live proposal data from SharePoint (Aktis), combines reusable procedure templates into a single plan, fills in client-specific values, and exports a ready-to-use `.xlsx` workplan.

The repository also contains an experimental **AI Proposal Development** mode that drafts workplans with OpenAI GPT or a locally fine-tuned Llama 2 model, plus the scripts used to build the training dataset from past proposals.

> Built for Project Fuel LLC's Design & Delivery Engineering (DDE) team. Current version: **0.0.71**.

---

## Features

**Template Designer** (`appdata/pfdesigner/`)

- Sign-in with username/password (streamlit-authenticator), profile editing, and password reset
- Loads open proposals (`KT Complete` / `In Progress`) from the SharePoint **Proposal Queues** list, and the business requirements from the **New KT** list
- Pick a **Library → Procedure → Technology → Version** to add a block of tasks; stack several procedures into one proposal
- Filter by project phase: *Plan, Prepare, Implement, Operate, Optimize*
- Prompts for any `<placeholder>` variables found in a procedure (e.g. device counts, hostnames) and substitutes them
- Import an existing Excel workplan as a new procedure version
- Calculates total hours from each task's hours × multiplier
- Generates the workplan from the client's `Template.xlsx` and downloads it as `Proposal Name [Ticket#].xlsx`
- Debug mode toggle that shows the raw SharePoint data

**AI Proposal Development** (`app.py`, prototype)

- Chat-style workplan generation from a business requirement
- Model options: OpenAI GPT-3.5, instruction/chat Llama 2 (7B/13B), or a locally trained LoRA adapter
- Dataset preparation and fine-tuning from the UI (Hugging Face AutoTrain or TRL `SFTTrainer` with PEFT/LoRA and 4/8-bit quantization)

---

## Repository structure

```
AI_IT_Template_Designer/
├── appdata/pfdesigner/          # Main Template Designer app
│   ├── app.py                   # Entry point
│   ├── page/                    # login, main, sidebar, home views
│   ├── utils/                   # Excel, template, and SharePoint helpers
│   ├── config/                  # settings.py, config.yaml (users), page config
│   ├── src/streamlit_auth/      # Vendored/customised streamlit-authenticator
│   ├── legacy/TemplateDesigner.py
│   ├── images/
│   └── .streamlit/config.toml
├── app.py                       # AI Proposal Development prototype (Streamlit)
├── app2.py                      # Minimal Gradio GPT chatbot test
├── PFextract.py                 # Builds training data from historical workplans
├── templates/                   # Sample procedures, device lists, prompts
│   ├── procedures/{Installation,Replacement}/*.txt
│   ├── technologies/{Firewall,Switch,AWS}/...
│   ├── clients/
│   ├── Firewalls.list
│   └── Switches.list
├── data.csv / final.csv         # Generated training datasets
└── training.log
```

---

## Requirements

- Python 3.10
- Access to the SharePoint Online site with the **Proposal Queues** and **New KT** lists
- An Entra ID (Azure AD) app registration with certificate-based access to that site
- *(AI mode only)* An OpenAI API key and/or an NVIDIA GPU with CUDA for local Llama 2 models, plus Hugging Face access to `meta-llama/Llama-2-7b-chat-hf`

`requirements.txt` is currently empty. Based on the imports, the Template Designer needs:

```text
streamlit
streamlit-authenticator
pandas
openpyxl
pyyaml
Pillow
requests
msal
Office365-REST-Python-Client
```

The AI prototype additionally uses:

```text
openai
python-dotenv
langchain
streamlit-chat
gradio
torch
transformers
datasets
peft
trl
bitsandbytes
accelerate
autotrain-advanced
```

---

## Getting started

### 1. Install

```bash
git clone https://github.com/angelpx25/AI_IT_Template_Designer.git
cd AI_IT_Template_Designer/appdata/pfdesigner
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install streamlit streamlit-authenticator pandas openpyxl pyyaml Pillow requests msal Office365-REST-Python-Client
```

### 2. Configure SharePoint access

`Get_SharePoint_data()` in `utils/utils.py` and `config/settings.py` hold the site URL, tenant ID, client ID, certificate thumbprint, and certificate path. Point these at your own app registration and place the certificate (PEM) outside the repository, for example:

```python
import os
TENANT_ID      = os.environ["AKTIS_TENANT_ID"]
CLIENT_ID      = os.environ["AKTIS_CLIENT_ID"]
CERT_THUMBPRINT = os.environ["AKTIS_CERT_THUMBPRINT"]
CERT_PATH      = os.environ["AKTIS_CERT_PATH"]
```

### 3. Configure users

Users live in `config/config.yaml`:

```yaml
cookie:
  name: pfdesigner_auth
  key: <long random string>
  expiry_days: 7
credentials:
  usernames:
    jane@example.com:
      email: jane@example.com
      name: Jane D
      password: <bcrypt hash>
preauthorized:
  emails: []
```

Generate a password hash with:

```python
from streamlit_authenticator import Hasher
print(Hasher(["my-password"]).generate())
```

### 4. Add templates

The app reads templates from `./templates` (git-ignored inside `pfdesigner`):

```
templates/
├── clients/<Client Name>/Template.xlsx
└── libraries/<Library>/procedures/<Procedure>/<Technology>/<Version>.txt
```

### 5. Run

```bash
streamlit run app.py
```

Open http://localhost:8501.

---

## Procedure template format

Procedures are pipe-delimited text files. Phase headers end in a colon, task groups are un-prefixed lines, and individual tasks start with `-`:

```text
Task|Total Time|Hours|Multiplier

Prepare:

Define (2) New Switches for Replacement:|2.75||
-Document new proposed topology|0.16|0.04|2
-Determine VLANs (802.1q), MTU membership, IP helpers and DHCP relay|0.16|0.08|2
```

`Total Time = Hours × Multiplier`. Any text wrapped in angle brackets, such as `<Number of Switches>`, becomes an input field under **Procedure Settings** and is replaced when the content is inserted. The same `<placeholder>` convention is used in client `Template.xlsx` files for the **Advanced Settings** values.

---

## AI Proposal Development (experimental)

Run the prototype from the repository root:

```bash
# .env
OPENAI_API_KEY=sk-...

streamlit run app.py
```

Training workflow:

1. **Extract** – `PFextract.py` reads historical Excel workplans (underlined cells = task groups, red text = tasks), producing `instruction,input,output` rows in `data.csv`.
2. **Format** – `create_text_column()` wraps each row in Llama 2 `[INST] … [/INST]` format and writes `final.csv`.
3. **Train** – In the app, open **Autotrain Training**, upload the CSV, set hyperparameters, and click **Start**. Trained adapters are saved under `./projects/` and appear under **Model → Trained Model**.

---

## Roadmap

- Populate `requirements.txt` / separate requirements for the AI prototype
- Move all credentials and IDs into environment variables or a secrets store
- Merge the AI mode into the main Template Designer
- Fill in the empty technology and client templates (AWS, server replacement, etc.)

---

## Security

Do not commit certificates, private keys, API keys, cookie keys, or user files to this repository. Recommended `.gitignore` additions:

```gitignore
certs/
*.pem
*.pfx
*.key
.env
config/config.yaml
__pycache__/
*.pyc
projects/
data.csv
final.csv
```

If any of these were ever pushed, rotate them and remove them from Git history (e.g. with `git filter-repo`).

---

## Author

Angel Paruas — Project Fuel LLC. All template content is property of Project Fuel LLC.
