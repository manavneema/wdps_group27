import requests
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class FactChecker:
    def __init__(self):
        """
        Initializes the FactChecker with the triplet extractor pipeline.
        """
        try:
            self.triplet_extractor = pipeline('text2text-generation', model='Babelscape/rebel-large', tokenizer='Babelscape/rebel-large')
            logger.info("Initialized triplet extractor pipeline.")
        except Exception as e:
            logger.error(f"Failed to initialize triplet extractor: {e}")
            raise

    def extract_triplets(self, text):
        """
        Extract triplets from text using the rebel model.

        Parameters:
            text (str): The text to extract triplets from.

        Returns:
            list: A list of triplet dictionaries with 'head', 'type', 'tail'.
        """
        logger.info(f"Extracting triplets from text: {text}")
        triplets = []
        relation, subject, object_ = '', '', ''
        text = text.strip()
        current = 'x'
        tokens = text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split()
        for token in tokens:
            if token == "<triplet>":
                current = 't'
                if relation != '':
                    triplets.append({'head': subject.strip(), 'type': relation.strip(), 'tail': object_.strip()})
                    relation = ''
                subject = ''
            elif token == "<subj>":
                current = 's'
                if relation != '':
                    triplets.append({'head': subject.strip(), 'type': relation.strip(), 'tail': object_.strip()})
                object_ = ''
            elif token == "<obj>":
                current = 'o'
                relation = ''
            else:
                if current == 't':
                    subject += ' ' + token
                elif current == 's':
                    object_ += ' ' + token
                elif current == 'o':
                    relation += ' ' + token
        if subject != '' and relation != '' and object_ != '':
            triplets.append({'head': subject.strip(), 'type': relation.strip(), 'tail': object_.strip()})
        logger.info(f"Extracted Triplets: {triplets}")
        return triplets

    def get_entity_id(self, entity):
        """
        Fetch the Wikidata ID of the entity.

        Parameters:
            entity (str): The name of the entity.

        Returns:
            str or None: The Wikidata ID of the entity, or None if not found.
        """
        url = 'https://www.wikidata.org/w/api.php'
        params = {
            'action': 'wbsearchentities',
            'format': 'json',
            'search': entity,
            'language': 'en',
            'type': 'item',
        }

        try:
            data = requests.get(url, params=params)
            data = data.json()
            entity_id = data['search'][0]['id'] if 'search' in data and data['search'] else None
            logger.info(f"Fetched entity ID for '{entity}': {entity_id}")
            return entity_id
        except Exception as e:
            logger.error(f"Fetching entity ID failed for '{entity}': {e}")
            return None

    def get_wikidata_relations(self, subj, obj):
        """
        Perform a SPARQL query to get the relation between entities from Wikidata.

        Parameters:
            subj (str): Subject entity name.
            obj (str): Object entity name.

        Returns:
            set: A set of relation labels.
        """

        logger.info(f"Getting wikidata relations for subject: '{subj}': object: {obj}")
        if not subj or not obj:
            return set()

        subj_id, obj_id = self.get_entity_id(subj), self.get_entity_id(obj)
        if not subj_id or not obj_id:
            return set()

        query = f"""
        SELECT ?wdLabel
        WHERE {{
          VALUES (?s) {{(wd:{subj_id})}}
          VALUES (?o) {{(wd:{obj_id})}}
          ?s ?wdt ?o .
          ?wd wikibase:directClaim ?wdt .
          ?wd rdfs:label ?wdLabel .
          FILTER (lang(?wdLabel) = "en")
        }} 
        ORDER BY xsd:integer(STRAFTER(STR(?wd), "http://www.wikidata.org/entity/P"))
        """

        url = 'https://query.wikidata.org/sparql'

        try:
            r = requests.get(url, params={'format': 'json', 'query': query})
            data = r.json()
            if not data['results']['bindings']:
                logger.info(f"No relations found between '{subj}' and '{obj}'.")
                return set()

            relations = set()
            for binding in data['results']['bindings']:
                relations.add(binding['wdLabel']['value'])

            logger.info(f"Retrieved relations between '{subj}' and '{obj}': {relations}")
            return relations

        except Exception as e:
            logger.error(f"SPARQL query to Wikidata failed: {e}")
            return set()

    def validate_answer(self, prompt, answer_tuple):
        """
        Validate the extracted answer.

        Parameters:
            prompt (str): The question prompt.
            answer_tuple (tuple): A tuple containing the answer and entity name.

        Returns:
            str: 'correct' or 'incorrect'.
        """
        answer = answer_tuple[0]
        entity_name = answer_tuple[1]

        # Extract triplets from the raw output
        try:
            generated = self.triplet_extractor("".join((prompt, entity_name)), return_tensors=True, return_text=False)
            extracted_text = self.triplet_extractor.tokenizer.decode(generated[0]["generated_token_ids"])
            extracted_triplets = self.extract_triplets(extracted_text)
        except Exception as e:
            logger.error(f"Triplet extraction failed: {e}")
            return 'incorrect'

        logger.info(f"Extracted Triplets: {extracted_triplets}")

        # If yes/no answer
        if answer.lower() in ("yes", "no"):
            for triplet in extracted_triplets:
                relations = set()

                # Get relations from Wikidata
                relations.update(self.get_wikidata_relations(triplet['head'], triplet['tail']))

                logger.debug(f"Relations List: {relations}")

                # There is a relation, the answer was YES => correct
                if triplet['type'] in relations and answer.lower() == 'yes':
                    return 'correct'

                # There is a relation, the answer was NO  => incorrect
                elif triplet['type'] in relations and answer.lower() == 'no':
                    return 'incorrect'

            # No relation, the answer was YES  => incorrect
            if answer.lower() == 'yes':
                return 'incorrect'
            # No relation, the answer was NO  => correct
            else:
                return 'correct'

        # If entity answer
        else:
            for triplet in extracted_triplets:
                relations = set()

                # Get relations from Wikidata
                relations.update(self.get_wikidata_relations(triplet['head'], entity_name))
                relations.update(self.get_wikidata_relations(entity_name, triplet['tail']))

                logger.info(f"Relations List: {relations}")

                # There is a relation => correct
                if triplet['type'] in relations:
                    return 'correct'

            # No relation => incorrect
            return 'incorrect'

    def check_correctness(self, question_text, extracted_answer, answer_type):
        """
        Check the correctness of the extracted answer based on its type.

        Parameters:
            question_text (str): The original question text.
            extracted_answer (str): The extracted answer.
            answer_type (str): The type of the answer ('YES_NO', 'ENTITY', etc.).

        Returns:
            str: 'correct' or 'incorrect'.
        """
        if answer_type == 'YES_NO':
            return self.validate_answer(question_text, (extracted_answer, None))
        elif answer_type == 'ENTITY':
            # Extract entity name from the URL or the answer
            if extracted_answer.startswith("https://"):
                entity_name = extracted_answer.split('/')[-1].replace('_', ' ')
            else:
                entity_name = extracted_answer
            return self.validate_answer(question_text, (extracted_answer, entity_name))
        else:
            return 'incorrect'