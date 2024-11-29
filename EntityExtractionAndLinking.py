import re
from llama_cpp import Llama
import spacy
from SPARQLWrapper import SPARQLWrapper, JSON
import warnings
from bs4 import GuessedAtParserWarning
import math
import logging

logging.basicConfig(filename='entity_linker.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')
warnings.filterwarnings("ignore", category=GuessedAtParserWarning)
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("The 'en_core_web_md' model is not installed. Please run 'python -m spacy download en_core_web_md' to install it.")
    exit(1)

# Define the mapping from spaCy NER labels to DBpedia types
NER_TO_DBPEDIA_TYPE = {
    'PERSON': ['dbo:Person'],
    'NORP': ['dbo:Organisation', 'dbo:Group'],
    'FAC': ['dbo:Facility'],
    'ORG': ['dbo:Organisation'],
    'GPE': ['dbo:Country', 'dbo:City', 'dbo:Region'],
    'LOC': ['dbo:Location'],
    'PRODUCT': ['dbo:Product'],
    'EVENT': ['dbo:Event'],
    'WORK_OF_ART': ['dbo:Work'],
    'LAW': ['dbo:Law'],
    'LANGUAGE': ['dbo:Language'],
    'DATE': [],
    'TIME': [],
    'PERCENT': [],
    'MONEY': [],
    'QUANTITY': [],
    'ORDINAL': [],
    'CARDINAL': [],
}

model_path = "models/llama-2-7b.Q4_K_M.gguf"
llm = Llama(model_path=model_path, verbose=False)
sparql = SPARQLWrapper("http://dbpedia.org/sparql")

def escape_sparql_regex(text):
    return text.replace('\\', '\\\\').replace('"', '\\"')

# function to extract entities and link using context
def extract_and_link_entities(text, context):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    logging.info(f"Extracted Entities: {entities}")
    linked_entities = []

    for e in entities:
        entity_text, entity_label = e
        logging.info(f'Processing entity: "{entity_text}" with label "{entity_label}"')
        try:
            # Mapping the spacy label to DBpedia types
            dbpedia_types = NER_TO_DBPEDIA_TYPE.get(entity_label)

            # depending on if there is corresponding dbpedia type, apply the apt filter
            if dbpedia_types:
                escaped_entity_text = escape_sparql_regex(entity_text)

                # adding a values clause for multiple types
                type_values = " ".join(f"<http://dbpedia.org/ontology/{dbpedia_type.split(':')[1]}>"
                                       for dbpedia_type in dbpedia_types)

                # SPARQL query with PREFIX declarations, type filtering, and exact match
                query = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                SELECT DISTINCT ?entity ?abstract WHERE {{
                    ?entity rdfs:label ?label .
                    VALUES ?type {{ {type_values} }}
                    ?entity rdf:type ?type .
                    OPTIONAL {{ ?entity dbo:abstract ?abstract . FILTER (lang(?abstract) = 'en') }}
                    FILTER (lang(?label) = 'en' && regex(str(?label), "^({escaped_entity_text})$", "i"))
                }}
                LIMIT 5
                """
            else:
                # omit the type filtering
                escaped_entity_text = escape_sparql_regex(entity_text)
                
                query = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                SELECT DISTINCT ?entity ?abstract WHERE {{
                    ?entity rdfs:label ?label .
                    OPTIONAL {{ ?entity dbo:abstract ?abstract . FILTER (lang(?abstract) = 'en') }}
                    FILTER (lang(?label) = 'en' && regex(str(?label), "^({escaped_entity_text})$", "i"))
                }}
                LIMIT 5
                """

            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            candidates = []
            for result in results["results"]["bindings"]:
                candidate_uri = result["entity"]["value"]
                candidate_abstract = result.get("abstract", {}).get("value", "")
                candidates.append((candidate_uri, candidate_abstract))
            logging.info(f"Candidates for '{entity_text}': {[uri for uri, _ in candidates]}")

            if not candidates:
                print(f"No candidates found for '{entity_text}'.")
                logging.info(f"No candidates found for '{entity_text}'.")
                continue

            # Using the  context to select the best candidate
            best_candidate = None
            best_similarity = -1
            context_doc = nlp(context)
            for candidate_uri, candidate_abstract in candidates:
                if candidate_abstract:
                    candidate_doc = nlp(candidate_abstract)
                    if context_doc.vector_norm == 0 or candidate_doc.vector_norm == 0:
                        logging.info(f"Zero vector encountered for context or candidate '{candidate_uri}'. Skipping similarity calculation.")
                        continue
                    similarity = context_doc.similarity(candidate_doc)
                    logging.info(f"Similarity between context and '{candidate_uri}': {similarity}")
                    if math.isnan(similarity):
                        logging.info(f"Similarity is NaN for candidate '{candidate_uri}'. Skipping.")
                        continue
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_candidate = candidate_uri
                else:
                    logging.info(f"No abstract available for '{candidate_uri}'. Skipping similarity calculation.")

            if best_candidate:
                print(f'Using best candidate "{best_candidate}".')
                logging.info(f'Using best candidate "{best_candidate}".')
                linked_entities.append((entity_text, best_candidate))
            else:
                print(f"Could not find a suitable candidate for '{entity_text}'.")
                logging.info(f"Could not find a suitable candidate for '{entity_text}'.")

        except Exception as ex:
            print(f'An unexpected error occurred while processing "{entity_text}": {ex}')
            logging.error(f'An unexpected error occurred while processing "{entity_text}": {ex}')

    return linked_entities

def print_entities(entities):
    for entity, uri in entities:
        print(f'{entity}\t{uri}')
        logging.info(f'{entity}\t{uri}')

def process_question(question_text):
    print(f'Asking the question "{question_text}" to {model_path} (wait, it can take some time...)')
    logging.info(f'Asking the question "{question_text}" to {model_path} (wait, it can take some time...)')

    enhanced_prompt = f"{question_text} Answer:"
    output = llm(
          enhanced_prompt,
          max_tokens=64, 
          echo=False,      # don't echo the question in the response
          seed=42,
          temperature=0.0,
          top_p=0.0
    ) # set a seed value for non-random output, temperature=0, top_p=0 for minimal variance in output
    logging.info(f"LLM Output: {output['choices']}")

    if not output['choices']:
        print("No output generated by the LLM.")
        logging.warning("No output generated by the LLM.")
        return

    # Extract the text from the first choice
    llm_output_text = output['choices'][0]['text'].strip()
    if not llm_output_text:
        print("LLM did not generate any response.")
        logging.warning("LLM did not generate any response.")
        return

    print(f'\nProcessed LLM Output: "{llm_output_text}"')
    logging.info(f'Processed LLM Output: "{llm_output_text}"')

    # Combine question and LLM output for richer context
    combined_context = f"{question_text} {llm_output_text}"
    
    input_entities = extract_and_link_entities(question_text, context=combined_context)
    output_entities = extract_and_link_entities(llm_output_text, context=combined_context)
    all_entities = input_entities + output_entities
    unique_entities = {}
    for entity, uri in all_entities:
        if entity not in unique_entities:
            unique_entities[entity] = uri

    print("\n--- Combined Unique Entities ---")
    logging.info("--- Combined Unique Entities ---")
    print_entities(unique_entities.items())

def main():
    print("Enter your questions below. Type 'exit' or 'quit' to terminate the program.\n")
    logging.info("Program started.")

    question_counter = 1
    while True:
        user_input = input("Enter your question: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting the program. Goodbye!")
            logging.info("Program terminated by user.")
            break

        if not user_input:
            print("Empty input. Please enter a valid question.")
            logging.warning("User entered an empty question.")
            continue

        process_question(user_input)
        print("\n")
        question_counter += 1

if __name__ == "__main__":
    main()