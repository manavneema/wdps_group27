import re
from llama_cpp import Llama
import spacy
from SPARQLWrapper import SPARQLWrapper, JSON
import warnings
import math
import logging

logging.basicConfig(filename='entity_linker.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    # print("The 'en_core_web_md' model is not installed. Please run 'python -m spacy download en_core_web_md' to install it.")
    exit(1)

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

model_path = "../models/llama-2-7b.Q4_K_M.gguf"
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

            if dbpedia_types:
                escaped_entity_text = escape_sparql_regex(entity_text)
                type_values = " ".join(f"<http://dbpedia.org/ontology/{dbpedia_type.split(':')[1]}>"
                                       for dbpedia_type in dbpedia_types)
                query = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                SELECT DISTINCT ?entity ?abstract WHERE {{
                    ?entity rdfs:label ?label .
                    VALUES ?type {{ {type_values} }}
                    ?entity rdf:type ?type .
                    OPTIONAL {{ ?entity dbo:abstract ?abstract . FILTER (lang(?abstract) = 'en') }}
                    FILTER (lcase(str(?label)) = lcase("{escaped_entity_text}"))
                }}
                LIMIT 5
                """
            else:
                escaped_entity_text = escape_sparql_regex(entity_text)
                query = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX dbo: <http://dbpedia.org/ontology/>
                SELECT DISTINCT ?entity ?abstract WHERE {{
                    ?entity rdfs:label ?label .
                    OPTIONAL {{ ?entity dbo:abstract ?abstract . FILTER (lang(?abstract) = 'en') }}
                    FILTER (lcase(str(?label)) = lcase("{escaped_entity_text}"))
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
                logging.info(f"No candidates found for '{entity_text}'.")
                continue

            # Using the context to select the best candidate
            best_candidate = None
            best_similarity = -1
            context_doc = nlp(context)
            for candidate_uri, candidate_abstract in candidates:
                if candidate_abstract:
                    candidate_doc = nlp(candidate_abstract)
                    if context_doc.vector_norm == 0 or candidate_doc.vector_norm == 0:
                        logging.info(f"Zero vector encountered for context or candidate '{candidate_uri}'. Skipping.")
                        continue
                    similarity = context_doc.similarity(candidate_doc)
                    logging.info(f"Cosine Similarity between context and '{candidate_uri}': {similarity}")
                    if math.isnan(similarity):
                        logging.info(f"Cosine Similarity is NaN for candidate '{candidate_uri}'. Skipping.")
                        continue
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_candidate = candidate_uri
                else:
                    logging.info(f"No abstract available for '{candidate_uri}'. Skipping similarity calculation.")

            if best_candidate:
                logging.info(f'Using best candidate "{best_candidate}".')
                linked_entities.append((entity_text, best_candidate))
            else:
                logging.info(f"Could not find a suitable candidate for '{entity_text}'.")
        except Exception as ex:
            logging.error(f'An unexpected error occurred while processing "{entity_text}": {ex}')

    return linked_entities

def process_question(question_id, question_text):
    # Ask the question to the LLM
    logging.info(f'Asking the question "{question_text}" to {model_path} (wait, it can take some time...)')

    enhanced_prompt = f"{question_text} Answer:"
    output = llm(
          enhanced_prompt,
          max_tokens=32, 
          echo=False,
          seed=42,
          temperature=0.0,
          top_p=0.0
    ) 
    logging.info(f"LLM Output: {output['choices']}")

    if not output['choices']:
        logging.warning("No output generated by the LLM.")
        return None

    llm_output_text = output['choices'][0]['text'].strip()
    if not llm_output_text:
        logging.warning("LLM did not generate any response.")
        return None

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

    entities_list = list(unique_entities.items())
    extracted_answer = llm_output_text
    result = {
        'llm_output': llm_output_text,
        'entities': entities_list
    }
    return result

def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: python scriptname.py inputfile")
        exit(1)
    input_filename = sys.argv[1]
    output_filename = 'output.txt'

    logging.info("Program started.")
    with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
        for line in infile:
            line = line.strip()
            if not line:
                continue
            # every line is in the format: <ID question><TAB>text of the question>
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            question_id, question_text = parts
            result = process_question(question_id, question_text)
            if not result:
                continue

            # Print the LLM result
            print(f"{question_id}\tR\"{result['llm_output']}\"\n")
            outfile.write(f"{question_id}\tR\"{result['llm_output']}\"\n")

            # Convert DBpedia URI to Wikipedia URL before printing
            for entity, uri in result['entities']:
                # Check if it's a DBpedia URI and convert
                if uri.startswith("http://dbpedia.org/resource/"):
                    wikipedia_uri = uri.replace("http://dbpedia.org/resource/", "https://en.wikipedia.org/wiki/")
                else:
                    # If not standard DBpedia, just leave as is
                    wikipedia_uri = uri

                print(f"{question_id}\tE\"{entity}\"\t\"{wikipedia_uri}\"\n")
                outfile.write(f"{question_id}\tE\"{entity}\"\t\"{wikipedia_uri}\"\n")

if __name__ == "__main__":
    main()