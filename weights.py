import json
import os
import uuid

STORE_FILE = 'data/user_store.json'

def load_store():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_store(store):
    with open(STORE_FILE, 'w') as f:
        json.dump(store, f, indent=2)

def create_user(profile):
    store = load_store()
    user_id = str(uuid.uuid4())[:8]
    store[user_id] = {
        "profile": profile,
        "weights": {
            "w1": 0.5,
            "w2": 0.3,
            "w3": 0.2,
            "interactions": 0
        }
    }
    save_store(store)
    return user_id

def get_user(user_id):
    store = load_store()
    return store.get(user_id, None)

def update_weights(user_id, action, nlp_s, mbti_s, loc_s):
    store = load_store()
    if user_id not in store:
        return None

    w = store[user_id]['weights']
    n = w['interactions']

    # Learning rate decay
    lr = 0.1 / (1 + 0.05 * n)

    # Gradient descent
    pred = w['w1']*nlp_s + w['w2']*mbti_s + w['w3']*loc_s
    err = action - pred

    w['w1'] += lr * err * nlp_s
    w['w2'] += lr * err * mbti_s
    w['w3'] += lr * err * loc_s
    w['interactions'] += 1

    # Keep weights positive
    w['w1'] = max(0.05, w['w1'])
    w['w2'] = max(0.05, w['w2'])
    w['w3'] = max(0.05, w['w3'])

    # Normalize so they sum to 1
    total = w['w1'] + w['w2'] + w['w3']
    w['w1'] = round(w['w1'] / total, 4)
    w['w2'] = round(w['w2'] / total, 4)
    w['w3'] = round(w['w3'] / total, 4)

    store[user_id]['weights'] = w
    save_store(store)
    return w