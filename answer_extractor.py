import re
import logging
import spacy

logger = logging.getLogger(__name__)

ANSWER_TYPE_YES_NO = 'YES_NO'
ANSWER_TYPE_ENTITY = 'ENTITY'

class AnswerExtractor:
    def __init__(self):
        """
        AnswerExtractor using spaCy.
        """
        try:
            self.nlp = spacy.load("en_core_web_md")
            logger.info("Loaded spaCy model 'en_core_web_md' for AnswerExtractor.")
        except OSError:
            logger.error("The 'en_core_web_md' model is not installed.")
            raise

    def extract_answer(self, llm_output, question_text):
        """
        Extracts the answer and determines its type (YES_NO or ENTITY).

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

        # Initialize variables to store potential answers
        extracted_answer = None
        answer_type = None

        if yes_no_question:
            # Attempt to extract yes/no answer
            match = re.search(r'\b(yes|no)\b', processed_output.lower())
            if match:
                extracted_answer = match.group(1)
                answer_type = ANSWER_TYPE_YES_NO
                logger.info(f"Extracted yes/no answer: {extracted_answer}")
                return extracted_answer, answer_type
            else:
                logger.info("Yes/No question detected but no explicit yes/no answer found.")

        # Attempt to extract an entity (e.g., Wikipedia URL)
        match = re.search(r'https?://\S+', processed_output)
        if match:
            extracted_answer = match.group(0)
            answer_type = ANSWER_TYPE_ENTITY
            logger.info(f"Extracted entity answer (URL): {extracted_answer}")
            return extracted_answer, answer_type

        # If no URL, use spaCy to extract the first relevant entity
        doc = self.nlp(processed_output)
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC', 'ORG', 'PERSON']:
                extracted_answer = ent.text
                answer_type = ANSWER_TYPE_ENTITY
                logger.info(f"Extracted entity answer via spaCy: {extracted_answer}")
                return extracted_answer, answer_type

        # Fallback: Attempt to extract yes/no answer even if it's not a yes/no question
        logger.info("Attempting to extract Yes/No answer as a fallback.")
        match = re.search(r'\b(yes|no)\b', processed_output.lower())
        if match:
            extracted_answer = match.group(1)
            answer_type = ANSWER_TYPE_YES_NO
            logger.info(f"Fallback extracted yes/no answer: {extracted_answer}")
            return extracted_answer, answer_type

        # If all extraction methods fail, default to 'no' with YES_NO type
        # Alternatively, you can choose to return a default value or raise an exception
        logger.warning("Could not extract a clear answer. Defaulting to 'no' as a YES_NO answer.")
        return 'no', ANSWER_TYPE_YES_NO

    def is_yes_no_question(self, question_text):
        """
        Heuristically determine if the question is a yes/no question.

        Parameters:
            question_text (str): The original question text.

        Returns:
            bool: True if it's likely a yes/no question, False otherwise.
        """
        # Simple heuristics based on question starting words, possibly after "Question:" prefix
        yes_no_verbs = [
            'is', 'are', 'do', 'does', 'can', 'could', 'should', 'would', 'will',
            'did', 'was', 'were', 'has', 'have', 'had'
        ]
        # Pattern breakdown:
        # ^\s*                -> Start of string, followed by any number of whitespace characters
        # (?:Question:\s*)?   -> Non-capturing group for optional "Question:" prefix followed by optional whitespace
        # (is|are|do|...)     -> Capturing group for any of the yes/no verbs
        # \b                  -> Word boundary to ensure exact match
        pattern = r'^\s*(?:Question:\s*)?(' + '|'.join(yes_no_verbs) + r')\b'
        match = re.match(pattern, question_text, re.IGNORECASE)
        if match:
            logger.debug(f"Question starts with a yes/no verb: '{match.group(1)}'")
            return True
        else:
            logger.debug("Question does not start with a yes/no verb.")
            return False