## Entity Linking Implementation

The entity linking process is executed through the following steps:

1. **Entity Extraction**: Uses spaCy's `en_core_web_md` model to identify and extract entities from the input text.

2. **Type Mapping**: Translates spaCy NER labels to corresponding DBpedia ontology types to categorize entities accurately.

3. **SPARQL Querying**: Constructs SPARQL queries based on the mapped types and entity texts to retrieve potential DBpedia candidates.

4. **Candidate Retrieval**: Executes the queries against DBpedia's SPARQL endpoint to fetch candidate entities and their abstracts.

5. **Contextual Similarity**: Utilizes spaCy's vector representations to calculate similarity between the provided context and each candidate's abstract, selecting the best match.

6. **Logging & Error Handling**: Logs each step and handles exceptions to ensure robust and traceable entity linking. This is between 


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
python -m venv venv
source venv/bin/activate

chmod +x setup.sh
./setup.sh
pip3 install -r requirements.txt
python3 entitylinker.py input.txt
```


For Windows:
```bash
cd app
python -m venv venv
source venv/bin/activate

chmod +x setup.sh
bash setup.sh
pip3 install -r requirements.txt
python3 entitylinker.py input.txt
```



