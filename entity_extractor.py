# entity_extractor.py
import re
import math
import logging
from SPARQLWrapper import SPARQLWrapper, JSON
import spacy

# Obtain a logger for this module
logger = logging.getLogger(__name__)

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

class EntityExtractor:
    def __init__(self):
        """
        Initializes the EntityExtractor with spaCy and SPARQL settings.
        """
        try:
            self.nlp = spacy.load("en_core_web_md")
            logger.info("Loaded spaCy model 'en_core_web_md'.")
        except OSError:
            logger.error("The 'en_core_web_md' model is not installed.")
            raise

        self.sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        logger.info("Initialized SPARQLWrapper with DBpedia endpoint.")

    def escape_sparql_regex(self, text):
        """
        Escapes special characters in text for SPARQL queries.

        Parameters:
            text (str): The text to escape.

        Returns:
            str: The escaped text.
        """
        return text.replace('\\', '\\\\').replace('"', '\\"')

    def extract_and_link_entities(self, text, context):
        """
        Extracts entities from the given text and links them to DBpedia URIs.

        Parameters:
            text (str): The text to extract entities from.
            context (str): The context to use for similarity calculations.

        Returns:
            list: A list of tuples containing entity text and their DBpedia URIs.
        """
        doc = self.nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        logger.info(f"Extracted Entities: {entities}")
        linked_entities = []

        for e in entities:
            entity_text, entity_label = e
            logger.info(f'Processing entity: "{entity_text}" with label "{entity_label}"')
            try:
                # Mapping the spaCy label to DBpedia types
                dbpedia_types = NER_TO_DBPEDIA_TYPE.get(entity_label)

                if dbpedia_types:
                    escaped_entity_text = self.escape_sparql_regex(entity_text)
                    type_values = " ".join(
                        f"<http://dbpedia.org/ontology/{dbpedia_type.split(':')[1]}>"
                        for dbpedia_type in dbpedia_types
                    )
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
                    escaped_entity_text = self.escape_sparql_regex(entity_text)
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

                self.sparql.setQuery(query)
                self.sparql.setReturnFormat(JSON)
                results = self.sparql.query().convert()
                candidates = []
                for result in results["results"]["bindings"]:
                    candidate_uri = result["entity"]["value"]
                    candidate_abstract = result.get("abstract", {}).get("value", "")
                    candidates.append((candidate_uri, candidate_abstract))
                logger.info(f"Candidates for '{entity_text}': {[uri for uri, _ in candidates]}")

                if not candidates:
                    logger.info(f"No candidates found for '{entity_text}'.")
                    continue

                # Using the context to select the best candidate
                best_candidate = None
                best_similarity = -1
                context_doc = self.nlp(context)
                for candidate_uri, candidate_abstract in candidates:
                    if candidate_abstract:
                        candidate_doc = self.nlp(candidate_abstract)
                        if context_doc.vector_norm == 0 or candidate_doc.vector_norm == 0:
                            logger.info(f"Zero vector encountered for context or candidate '{candidate_uri}'. Skipping.")
                            continue
                        similarity = context_doc.similarity(candidate_doc)
                        logger.info(f"Cosine Similarity between context and '{candidate_uri}': {similarity}")
                        if math.isnan(similarity):
                            logger.info(f"Cosine Similarity is NaN for candidate '{candidate_uri}'. Skipping.")
                            continue
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_candidate = candidate_uri
                    else:
                        logger.info(f"No abstract available for '{candidate_uri}'. Skipping similarity calculation.")

                if best_candidate:
                    logger.info(f'Using best candidate "{best_candidate}".')
                    linked_entities.append((entity_text, best_candidate))
                else:
                    logger.info(f"Could not find a suitable candidate for '{entity_text}'.")

            except Exception as ex:
                logger.error(f'An unexpected error occurred while processing "{entity_text}": {ex}')

        return linked_entities