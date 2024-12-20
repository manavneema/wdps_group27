## Entity Linking Implementation

The entity linking process is executed through the following steps:

1. **Entity Extraction**: Uses spaCy's `en_core_web_md` model to identify and extract entities from the input text.

2. **SPARQL Querying**: Constructs SPARQL queries from the entity texts to retrieve potential DBpedia candidates.

3. **Candidate Retrieval**: Executes the queries against DBpedia's SPARQL endpoint to fetch candidate entities and their abstracts.

4. **Contextual Similarity**: We calculate cosine similarity between the provided context and each candidate's abstract, selecting the best match.


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
python3 entitylinker.py input.txt
```


For Windows:
```bash
cd app
python -m venv venv #not required if done already
source venv/bin/activate

chmod +x setup.sh
bash setup.sh
pip3 install -r requirements.txt
python3 entitylinker.py input.txt
```



### **Explanation of the Code**

1. **Imports and Setup**:
    - The script begins by importing necessary libraries such as `llama_cpp` for interacting with the LLM, `spacy` for Named Entity Recognition (NER), `SPARQLWrapper` for querying DBpedia, and `transformers` for the fact-checking pipeline.
    - Logging is configured to record detailed information to `entity_linker.log` for debugging purposes.
    - The Spacy model `en_core_web_md` is loaded for NER tasks.

2. **Constants and Mappings**:
    - A dictionary `NER_TO_DBPEDIA_TYPE` maps Spacy's NER labels to corresponding DBpedia ontology types, facilitating accurate entity linking.

3. **Entity Extraction and Linking (`extract_and_link_entities`)**:
    - This function extracts entities from a given text using Spacy's NER.
    - For each entity, it constructs a SPARQL query to DBpedia to find matching resources based on the entity's label and type.
    - It selects the best candidate by computing the cosine similarity between the context and the entity's abstract to ensure relevance.
    - Linked entities are returned as a list of tuples containing the entity text and its corresponding Wikipedia URL.

4. **Answer Extraction (`extract_clean_answer`)**:
    - Determines whether the question expects a **yes/no** answer or an **entity-based** answer using simple heuristics based on the question's starting words.
    - For **yes/no** questions, it uses regular expressions to extract "yes" or "no" from the LLM's output.
    - For **entity-based** questions, it extracts the most probable entity using NER.

5. **DBpedia to Wikipedia URI Conversion (`convert_dbpedia_to_wikipedia`)**:
    - Converts DBpedia URIs to their corresponding Wikipedia URLs for standardized output.

6. **Fact-Checking (`validate_answer_fact_checking` and related functions)**:
    - Utilizes the provided fact-checking reference code to validate the extracted answers.
    - **Triplet Extraction (`extract_triplets`)**: Parses the LLM-generated text to extract subject-relation-object triplets.
    - **Entity ID Retrieval (`get_entity_id`)**: Fetches Wikidata IDs for entities using Wikidata's API.
    - **Relation Retrieval (`get_wikidata_relations`)**: Queries Wikidata to find relations between entities.
    - **Validation**:
        - For **yes/no** answers, it checks if the extracted triplets support the answer.
        - For **entity-based** answers, it verifies the relationship between the extracted answer and other entities.

7. **Processing Each Question (`process_question`)**:
    - Queries the LLM with the given question and retrieves the raw output.
    - Extracts and links entities from both the question and the LLM's output.
    - Extracts a clean answer based on the expected answer type.
    - Fact-checks the extracted answer to determine its correctness.
    - Compiles all results into a dictionary for output.

8. **Main Execution (`main`)**:
    - Reads the input file specified as a command-line argument.
    - Processes each question line by line, invoking `process_question` for each.
    - Writes the results to `output.txt` in the required format:
        - **Raw LLM Output**: Prefixed with `R"`.
        - **Entities**: Prefixed with `E"`.
        - **Extracted Answer and Correctness**: Prefixed with `A"`.
    - Also prints the results to the console for immediate visibility.

9. **Error Handling**:
    - Comprehensive error handling ensures that issues like missing input files, failed API requests, or unexpected LLM outputs are logged and do not crash the program.

### **Example Output**

Given the provided `input.txt`, the `output.txt` will contain entries similar to:

### **Notes and Considerations**

- **LLM Model Path**: Ensure that the `model_path` variable correctly points to the location of the LLaMA 2 7B model on your system.

- **Fact-Checking Pipeline**: The fact-checking relies on the `Babelscape/rebel-large` model. Ensure that this model is accessible and properly downloaded.

- **Performance**: Fact-checking involves multiple API calls to Wikidata, which may slow down processing for large input files. Consider implementing caching or asynchronous requests for optimization.

- **Answer Extraction Heuristics**: The current implementation uses simple heuristics to determine the answer type. For more complex scenarios, consider using more advanced NLP techniques or training a classifier.

- **Error Handling**: While comprehensive, there may still be edge cases that cause unexpected behavior. Regularly monitor the `entity_linker.log` for issues.

- **Extensibility**: The modular design allows for easy addition of new features, such as supporting more answer types or integrating additional knowledge bases for fact-checking.

### **Conclusion**

This script provides a comprehensive solution to post-process LLM outputs by extracting and linking entities, extracting clean answers, and validating their correctness using external knowledge bases. Its modular design ensures maintainability and ease of future enhancements.