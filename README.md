# AgenticMootCourt

## Description
This project is a human-in-the-loop simulation of Indian constitutional moot courts using Large Language Models (LLMs) that is designed to aid law students in preparing for oral rounds. The system simulates real Indian moot court dynamics with AI agents acting as the judge, respondent, and reviewer, while the user plays the role of the petitioner.

**Key Features:**

- Realistic simulation of oral rounds in moot courts.
- AI agents powered by LLMs and Indian legal texts (Constitution, BNS, landmark cases).
- Judge agent asks questions dynamically based on arguments.
- Respondent agent presents structured arguments and responds to judicial queries.
- Reviewer agent scores and gives feedback based on standard moot court rubrics.

**Technologies Used:**

* LangChain, FAISS, Python
* Google Vertex AI (Gemini models)
* InLegalBERT, MiniLM for semantic similarity

## File Structure
```
.
├── EvalutionDataset
│   ├── 150_lawergpt_dataset_qna_v1_train.jsonl
│   ├── Articles_Constitution_3300_Instruction_Set.jsonl
│   ├── constitution_qa.json
│   ├── crpc_qa.json
│   ├── indian_constitution.csv
│   ├── ipc_qa.json
│   └── ipc_sections.csv
├── mootcourtVenv
│   ├── bin
│   ├── include
│   ├── lib
│   ├── lib64 -> lib
│   ├── pyvenv.cfg
│   └── share
├── Processed_Data
│   ├── Laws_Constitution
│   └── PreviousCases
├── pyproject.toml
├── Raw_data
│   └── 100LandmarkCases.docx
├── README.md
├── requirements.txt
├── Results
│   ├── ArticlesConstitution_filtered_results.csv
│   ├── ArticlesConstitution_incremental_results.csv
│   ├── IndianConstitution_filtered_results.csv
│   ├── IndianConstitution_incremental_results.csv
│   ├── IPC_incremental_filtered_results.csv
│   ├── IPC_incremental_results.csv
│   ├── ResultProcessing2.ipynb
│   ├── ResultProcessing3.ipynb
│   ├── ResultProcessing.ipynb
│   └── Results.md
├── src
│   └── mootcourt
│       ├── argsumm_test.py
│       ├── cached_datasets
│       ├── CaseDetails.py
│       ├── court_agent_cot.py
│       ├── court_agent_old.py
│       ├── court_agent_react.py
│       ├── DataPreprocessing
│       ├── Evalution
│       ├── EvalutionHelper.py
│       ├── EvalutionInitilise.py
│       ├── EvalutionMatrices.py
│       ├── Evalution.py
│       ├── flow.py
│       ├── gold_answer_embeddings
│       ├── Initlise.py
│       ├── main.py
│       ├── moot_court_log.txt
│       ├── openrouter.py
│       ├── Prompts_cot.py
│       ├── Prompts_react.py
│       ├── __pycache__
│       ├── store_gen.py
│       ├── test_agent.py
│       └── tools
├── uv.lock
├── vector_database
│   ├── faiss_bns
│   ├── faiss_constitution
│   ├── faiss_landmark_cases
│   └── faiss_supreme_court_csv
└── WorkingDemos
    ├── moot_court_log_1.txt
    └── moot_court_log_2.txt
```


## Installation
To set up the project, follow these steps:

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
To run the project, execute the following command:
```bash
python src/mootcourt/main.py
```
## Drive Link for Results
https://drive.google.com/drive/folders/1NLCf7bYVQRIUZJEStQJ59KjiTy2t5XFh?usp=sharing


## Collaborators
- Ishan Gupta(https://github.com/Ishan-1)
- Harsh Gupta(https://github.com/harsh-gupta10)


