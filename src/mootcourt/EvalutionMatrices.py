import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.tokenize import word_tokenize
from rouge import Rouge
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from pathlib import Path
from sentence_transformers import SentenceTransformer, models




# Initialize NLTK components
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


nltk.download('punkt_tab')

# Set device to CPU explicitly
device = torch.device("cpu")

# Initialize sentence transformer model for semantic similarity
# tokenizer = AutoTokenizer.from_pretrained("law-ai/InLegalBERT")
# # model = AutoModel.from_pretrained("law-ai/InLegalBERT").to(device)


# Load InLegalBERT with mean pooling
word_embedding_model = models.Transformer("law-ai/InLegalBERT", max_seq_length=512)
pooling_model = models.Pooling(     
    word_embedding_model.get_word_embedding_dimension(),
    pooling_mode_mean_tokens=True,
    pooling_mode_cls_token=False,
    pooling_mode_max_tokens=False
)
legal_sentence_model = SentenceTransformer(modules=[word_embedding_model, pooling_model])



rouge = Rouge()

def calculate_bleu(generated, reference):
    """Calculate BLEU score"""
    if not generated or not reference:
        return 0
    reference_tokens = [word_tokenize(reference.lower())]
    generated_tokens = word_tokenize(generated.lower())
    return sentence_bleu(reference_tokens, generated_tokens)

def calculate_rouge(generated, reference):
    """Calculate ROUGE scores"""
    if not generated or not reference:
        return {'rouge-1': 0, 'rouge-2': 0, 'rouge-l': 0}
    try:
        scores = rouge.get_scores(generated, reference)[0]
        return {
            'rouge-1': scores['rouge-1']['f'],
            'rouge-2': scores['rouge-2']['f'],
            'rouge-l': scores['rouge-l']['f']
        }
    except:
        return {'rouge-1': 0, 'rouge-2': 0, 'rouge-l': 0}





# def compute_embedding(text):
#     """Compute embedding for a given text"""
#     if not text:
#         # Return a zero embedding for empty text
#         return torch.zeros((1, 768), device=device)
    
#     encoded_input = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
#     encoded_input = {k: v.to(device) for k, v in encoded_input.items()}
    
#     with torch.no_grad():
#         output = model(**encoded_input)
    
#     # Extract CLS token embedding
#     embedding = output.last_hidden_state[:, 0, :]  # Shape: (1, 768)
#     return embedding

# def calculate_embedding_similarity(generated, gold_answer):
#     """Calculate cosine similarity between generated text and gold answer"""
#     # Compute embeddings
#     gen_embedding = compute_embedding(generated)
#     gold_embedding = compute_embedding(gold_answer)
    
#     # Normalize embeddings
#     gen_embedding = F.normalize(gen_embedding, p=2, dim=1)
#     gold_embedding = F.normalize(gold_embedding, p=2, dim=1)
    
#     # Compute cosine similarity
#     similarity = torch.mm(gen_embedding, gold_embedding.T).item()
    
#     return similarity




def compute_embedding(text):
    """Compute sentence embedding using SentenceTransformer-wrapped InLegalBERT"""
    if not text:
        return torch.zeros((768,), device=legal_sentence_model.device)
    
    # Return tensor embedding (convert_to_tensor=True keeps it on device)
    embedding = legal_sentence_model.encode(text, convert_to_tensor=True)
    return embedding


def calculate_embedding_similarity(generated, gold_answer):
    """Calculate cosine similarity between two texts"""
    # Compute embeddings
    gen_embedding = compute_embedding(generated)
    gold_embedding = compute_embedding(gold_answer)

    # Normalize and compute cosine similarity
    similarity = F.cosine_similarity(gen_embedding, gold_embedding, dim=0).item()
    
    return similarity


def evaluate_legal_qa(questions, generated_answers, gold_answers, domain, question_ids=None):
    """Evaluate legal QA performance"""
    results = []
    
    for i in range(len(questions)):
        question = questions[i]
        generated = generated_answers[i]
        gold = gold_answers[i]
        
        # Calculate lexical similarity
        bleu_score = calculate_bleu(generated, gold)
        
        # Calculate ROUGE scores
        rouge_scores = calculate_rouge(generated, gold)
        
        # Calculate semantic similarity
        embedding_similarity = calculate_embedding_similarity(generated, gold)
        
        result = {
            'domain': domain,
            'question': question,
            'generated_answer': generated,
            'gold_answer': gold,
            'bleu': bleu_score,
            'rouge-1': rouge_scores['rouge-1'],
            'rouge-2': rouge_scores['rouge-2'],
            'rouge-l': rouge_scores['rouge-l'],
            'embedding_similarity': embedding_similarity
        }
        
        # Add question_id if provided
        if question_ids is not None:
            result['question_id'] = question_ids[i]
            
        results.append(result)
    
    return results



# # Load model and tokenizer
# tokenizer = AutoTokenizer.from_pretrained('law-ai/InLegalBERT')
# model = AutoModel.from_pretrained('law-ai/InLegalBERT')

# # Function to get embeddings
# def get_embeddings(texts):
#     # Tokenize
#     encoded_input = tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
    
#     # Get model output
#     with torch.no_grad():
#         model_output = model(**encoded_input)
    
#     # Mean Pooling - take attention mask into account for correct averaging
#     attention_mask = encoded_input['attention_mask']
#     input_mask_expanded = attention_mask.unsqueeze(-1).expand(model_output.last_hidden_state.size()).float()
#     sum_embeddings = torch.sum(model_output.last_hidden_state * input_mask_expanded, 1)
#     sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
#     embeddings = sum_embeddings / sum_mask
    
#     # Normalize
#     embeddings = F.normalize(embeddings, p=2, dim=1)
    
#     return embeddings

# # Calculate similarity
# def similarity(text1, text2):
#     embeddings = get_embeddings([text1, text2])
#     return torch.cosine_similarity(embeddings[0], embeddings[1], dim=0).item()