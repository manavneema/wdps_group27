## Overview

This project implements a question-answering and fact-checking system that processes input questions and provides comprehensive outputs, including:

1. **LLM Response (B):** Raw text generated by a large language model.
2. **Entities Extracted:** Entities extracted from both the input question and the LLM response, linked to their respective Wikipedia URLs.
3. **Extracted Answer:** The answer extracted from the LLM response, categorized as either a Yes/No response or a Wikipedia entity.
4. **Correctness of the Answer:** Validation of the extracted answer as “correct” or “incorrect” based on fact-checking mechanisms.

The system leverages various technologies, including Llama 2 for language modeling, spaCy for Named Entity Recognition (NER), SPARQL for querying DBpedia and Wikidata, and transformer models for triplet extraction in fact-checking.

## Technologies Used
    •   Python 3.8+
    •   Llama 2 (llama_cpp_python): For generating responses to input questions.
    •   spaCy: For Named Entity Recognition (NER) and entity extraction.
    •   SPARQLWrapper: To query DBpedia and Wikidata for entity linking and relation extraction.
    •   Transformers (Hugging Face): Specifically the Babelscape/rebel-large model for triplet extraction.
    •   Textacy: For additional text processing needs.
    •   Other Libraries: stanza, cython, transformers, etc.

## How to Run

### Setup the Git Repository Locally
```bash

git clone https://github.com/manavneema/wdps_group27.git
```

### Run the following:
For Mac/Linux:
```bash
cd wdps_group27
docker run -it -v ./:/home/user/app/ karmaresearch/wdps2
```

For Windows:
Use working directory path of your local for -v argument
``` bash
cd wdps_group27
docker run --platform linux/arm64 -it -v ./C:/Users/neema/OneDrive/Documents/Repos/wdps_group27/:/home/user/app/ karmaresearch/wdps2
```

### Inside the container follow the below steps:
For Mac:
```bash
cd app
python -m venv venv #not required if done already
source venv/bin/activate

chmod +x setup.sh
./setup.sh
pip3 install -r requirements.txt
python3 main.py input.txt
```


For Windows:
```bash
cd app
python -m venv venv #not required if done already
source venv/bin/activate

chmod +x setup.sh
bash setup.sh
pip3 install -r requirements.txt
python3 main.py input.txt
```