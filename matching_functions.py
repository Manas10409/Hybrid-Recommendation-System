import numpy as np
import pandas as pd
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer('all-MiniLM-L6-v2')
users_df = pd.read_csv("data/users.csv")
user_vectors = np.load("data/user_vectors.npy")


MBTI_SCORES = {
    ("INTJ","ENFP"): 1.0, ("ENFP","INTJ"): 1.0,
    ("INTP","ENTP"): 0.9, ("ENTP","INTP"): 0.9,
    ("INTJ","ENTP"): 0.9, ("ENTP","INTJ"): 0.9,
    ("INFJ","ENFP"): 0.9, ("ENFP","INFJ"): 0.9,
    ("INFP","ENFJ"): 0.9, ("ENFJ","INFP"): 0.9,
    ("ISTJ","ESTJ"): 0.8, ("ESTJ","ISTJ"): 0.8,
    ("ISFJ","ESFJ"): 0.8, ("ESFJ","ISFJ"): 0.8,
    ("ISTP","ESTP"): 0.8, ("ESTP","ISTP"): 0.8,
    ("ISFP","ESFP"): 0.8, ("ESFP","ISFP"): 0.8,
}

CITY_STATE = {
    "Bangalore": "Karnataka", "Mysuru": "Karnataka", "Coimbatore": "Karnataka",
    "Mumbai": "Maharashtra", "Pune": "Maharashtra",
    "Chennai": "Tamil Nadu", "Coimbatore": "Tamil Nadu",
    "Hyderabad": "Telangana",
    "Delhi": "Delhi", "Noida": "Delhi", "Gurugram": "Delhi",
    "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat",
    "Kochi": "Kerala",
    "Jaipur": "Rajasthan",
    "Chandigarh": "Punjab"
}

def get_location_score(user_location, candidate_location):
    if user_location == candidate_location:
        return 1.0
    
    user_state = CITY_STATE.get(user_location)
    candidate_state = CITY_STATE.get(candidate_location)
    
    if user_state and candidate_state and user_state == candidate_state:
        return 0.3
    
    return 0.0

def clean_text(text):
    doc = nlp(text)
    return ' '.join([
        word.lemma_.lower() for word in doc
        if not word.is_punct and not word.is_stop
    ])

def get_nlp_score(new_user_text):
    cleaned = clean_text(new_user_text)
    new_vector = model.encode([cleaned])
    scores = cosine_similarity(new_vector, user_vectors)[0]
    return scores

def get_mbti_score(user_mbti, candidate_mbti):
    if user_mbti == candidate_mbti:
        return 0.7
    return MBTI_SCORES.get((user_mbti, candidate_mbti), 0.4)

def get_top_matches(new_user, weights, top_n=5):
    combined = (new_user['about_me'] + " " + 
                new_user['professional_summary'] + " " + 
                new_user['interests'] + " " + 
                new_user['profession'])
    
    nlp_scores = get_nlp_score(combined)
    
    results = []
    for i, row in users_df.iterrows():
        nlp_s = float(nlp_scores[i])
        mbti_s = get_mbti_score(new_user['mbti'], row['mbti'])
        loc_s = get_location_score(new_user['location'], row['location'])
        
        total = (weights['w1'] * nlp_s + 
                 weights['w2'] * mbti_s + 
                 weights['w3'] * loc_s)
        
        results.append({
            'user_id': row['user_id'],
            'name': row['name'],
            'profession': row['profession'],
            'location': row['location'],
            'mbti': row['mbti'],
            'professional_summary': row['professional_summary'],
            'nlp_score': round(nlp_s, 3),
            'mbti_score': round(mbti_s, 3),
            'location_score': round(loc_s, 3),
            'total_score': round(total, 3)
        })
    
    results_df = pd.DataFrame(results)
    return results_df.sort_values('total_score', ascending=False).head(top_n)