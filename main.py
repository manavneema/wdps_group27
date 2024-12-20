# main.py
import sys
import logging

from llm import LLMInterface
from entity_extractor import EntityExtractor
from answer_extractor import AnswerExtractor, ANSWER_TYPE_YES_NO, ANSWER_TYPE_ENTITY
from fact_checker import FactChecker

# Configure logging once in main.py
logging.basicConfig(
    filename='main.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    filemode='w'  # Overwrite log file each run; remove or change as needed
)

logger = logging.getLogger(__name__)

def convert_dbpedia_to_wikipedia(uri):
    """
    Converts a DBpedia URI to its corresponding Wikipedia URL.

    Parameters:
        uri (str): The DBpedia URI.

    Returns:
        str: The corresponding Wikipedia URL.
    """
    if uri.startswith("http://dbpedia.org/resource/"):
        return uri.replace("http://dbpedia.org/resource/", "https://en.wikipedia.org/wiki/")
    else:
        return uri

def process_question(question_id, question_text, llm_interface, entity_extractor, answer_extractor, fact_checker):
    """
    Processes a single question by generating an answer, extracting entities, and fact-checking.

    Parameters:
        question_id (str): The unique identifier for the question.
        question_text (str): The text of the question.
        llm_interface (LLMInterface): Instance of LLMInterface.
        entity_extractor (EntityExtractor): Instance of EntityExtractor.
        answer_extractor (AnswerExtractor): Instance of AnswerExtractor.
        fact_checker (FactChecker): Instance of FactChecker.

    Returns:
        dict: A dictionary containing the results for the question.
    """
    logger.info(f"Processing question ID: {question_id}, Text: {question_text}")

    # Generate LLM response
    prompt = f"{question_text} Answer:"
    llm_output = llm_interface.get_response(prompt)
    if not llm_output:
        logger.warning(f"No LLM output for question ID: {question_id}")
        return None

    # Combine question and LLM output for context
    combined_context = f"{question_text} {llm_output}"

    # Extract entities from question and LLM output
    input_entities = entity_extractor.extract_and_link_entities(question_text, context=combined_context)
    output_entities = entity_extractor.extract_and_link_entities(llm_output, context=combined_context)
    all_entities = input_entities + output_entities

    # Remove duplicate entities
    unique_entities = {}
    for entity, uri in all_entities:
        if entity not in unique_entities:
            unique_entities[entity] = uri

    entities_list = list(unique_entities.items())

    # Extract answer and its type
    extracted_answer, answer_type = answer_extractor.extract_answer(llm_output, question_text)
    logger.info(f"Extracted answer: {extracted_answer}, Type: {answer_type}")

    # Check correctness of the answer
    correctness = fact_checker.check_correctness(question_text, extracted_answer, answer_type)
    logger.info(f"Answer correctness: {correctness}")

    # Build result dictionary
    result = {
        'llm_output': llm_output,
        'entities': entities_list,
        'extracted_answer': extracted_answer,
        'correctness': correctness
    }

    return result

def main():
    """
    Main function to execute the workflow.
    """
    if len(sys.argv) != 2:
        print("Usage: python main.py inputfile")
        sys.exit(1)

    input_filename = sys.argv[1]
    output_filename = 'output.txt'

    logger.info("Program started.")

    # Initialize modules
    model_path = "../models/llama-2-7b.Q4_K_M.gguf"  # Update the path as necessary
    try:
        llm_interface = LLMInterface(model_path=model_path)
    except Exception as e:
        logger.error(f"Failed to initialize LLMInterface: {e}")
        sys.exit(1)

    try:
        entity_extractor = EntityExtractor()
    except Exception as e:
        logger.error(f"Failed to initialize EntityExtractor: {e}")
        sys.exit(1)

    answer_extractor = AnswerExtractor()
    fact_checker = FactChecker()

    try:
        with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                # Each line is in the format: <ID><TAB>text of the question>
                parts = line.split('\t')
                if len(parts) != 2:
                    logger.warning(f"Invalid input line format: {line}")
                    continue
                question_id, question_text = parts
                result = process_question(question_id, question_text, llm_interface, entity_extractor, answer_extractor, fact_checker)
                if not result:
                    continue

                # Write the LLM output
                outfile.write(f"{question_id}\tR\"{result['llm_output']}\"\n")

                # Write extracted answer and correctness
                outfile.write(f"{question_id}\tA\"{result['extracted_answer']}\"\n")
                outfile.write(f"{question_id}\tC\"{result['correctness']}\"\n")

                # Convert DBpedia URIs to Wikipedia URLs and write entities
                for entity, uri in result['entities']:
                    wikipedia_uri = convert_dbpedia_to_wikipedia(uri)
                    outfile.write(f"{question_id}\tE\"{entity}\"\t\"{wikipedia_uri}\"\n")


                # Optionally, print to console as per the original code
                print(f"{question_id}\tR\"{result['llm_output']}\"\n")
                for entity, uri in result['entities']:
                    wikipedia_uri = convert_dbpedia_to_wikipedia(uri)
                    print(f"{question_id}\tE\"{entity}\"\t\"{wikipedia_uri}\"\n")
                print(f"{question_id}\tA\"{result['extracted_answer']}\"\n")
                print(f"{question_id}\tC\"{result['correctness']}\"\n")

    except FileNotFoundError:
        logger.error(f"Input file '{input_filename}' not found.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

    logger.info("Program finished.")

if __name__ == "__main__":
    main()