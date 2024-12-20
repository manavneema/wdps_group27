# answer_extractor.py
import re
import logging
import spacy

logger = logging.getLogger(__name__)

# Define constants for answer types
ANSWER_TYPE_YES_NO = 'YES_NO'
ANSWER_TYPE_ENTITY = 'ENTITY'
ANSWER_TYPE_UNKNOWN = 'UNKNOWN'

class AnswerExtractor:
    def __init__(self):
        """
        Initializes the AnswerExtractor with spaCy.
        """
        try:
            self.nlp = spacy.load("en_core_web_md")
            logger.info("Loaded spaCy model 'en_core_web_md' for AnswerExtractor.")
        except OSError:
            logger.error("The 'en_core_web_md' model is not installed.")
            raise

    def extract_answer(self, llm_output, question_text):
        """
        Extracts the answer and determines its type (YES_NO, ENTITY, UNKNOWN).

        Parameters:
            llm_output (str): The raw output from the LLM.
            question_text (str): The original question text.

        Returns:
            tuple: (extracted_answer, answer_type)
        """
        # Preprocess LLM output: Replace newlines with spaces
        processed_output = llm_output.replace('\n', ' ').strip()
        logger.info(f"Processed LLM Output: {processed_output}")

        # Determine if the question expects a yes/no answer
        yes_no_question = self.is_yes_no_question(question_text)
        logger.info(f"Is yes/no question: {yes_no_question}")

        if yes_no_question:
            # Attempt to extract yes/no
            match = re.search(r'\b(yes|no)\b', processed_output.lower())
            if match:
                answer = match.group(1)
                logger.info(f"Extracted yes/no answer: {answer}")
                return answer, ANSWER_TYPE_YES_NO

        # Otherwise, attempt to extract an entity (e.g., Wikipedia URL)
        # Extract the first URL
        match = re.search(r'https?://\S+', processed_output)
        if match:
            answer = match.group(0)
            logger.info(f"Extracted entity answer (URL): {answer}")
            return answer, ANSWER_TYPE_ENTITY

        # If no URL, use spaCy to extract the first GPE entity
        doc = self.nlp(processed_output)
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC', 'ORG', 'PERSON']:
                answer = ent.text
                logger.info(f"Extracted entity answer via spaCy: {answer}")
                return answer, ANSWER_TYPE_ENTITY

        # Fallback if no clear answer is found
        logger.warning("Could not extract a clear answer.")
        return 'unknown', ANSWER_TYPE_UNKNOWN

    def is_yes_no_question(self, question_text):
        """
        Heuristically determine if the question is a yes/no question.

        Parameters:
            question_text (str): The original question text.

        Returns:
            bool: True if it's likely a yes/no question, False otherwise.
        """
        # Simple heuristics based on question starting words
        yes_no_verbs = ['is', 'are', 'do', 'does', 'can', 'could', 'should', 'would', 'will', 'did', 'was', 'were', 'has', 'have', 'had']
        pattern = r'^\s*(Is|Are|Do|Does|Can|Could|Should|Would|Will|Did|Was|Were|Has|Have|Had)\b'
        return re.match(pattern, question_text, re.IGNORECASE) is not None