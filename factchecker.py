
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification


def  validate_claim(claim, evidence):
# Load the tokenizer and model
  tokenizer = RobertaTokenizer.from_pretrained('Dzeniks/roberta-nei-fact-check')
  model = RobertaForSequenceClassification.from_pretrained('Dzeniks/roberta-nei-fact-check')

  # Define the claim with evidence to classify
  claim = "Albert Einstein work in the field of computer science"
  evidence = "Albert Einstein was a German-born theoretical physicist, widely acknowledged to be one of the greatest and most influential physicists of all time."

  # Tokenize the claim with evidence
  x = tokenizer.encode_plus(claim, evidence, return_tensors="pt")

  model.eval()
  with torch.no_grad():
    prediction = model(**x)

  label = torch.argmax(prediction[0]).item()

  if label == 0:
    return True
  else :
    return False
