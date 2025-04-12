# Project Title

## Description
This project is designed to facilitate legal simulations and court proceedings using advanced language models. It leverages various libraries and frameworks to provide a comprehensive environment for legal practitioners and researchers.

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


