import os
import pickle
import json
import re

def load_cache(cache_file="extraction_cache.pkl"):
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    return {}

def save_cache(cache, cache_file="extraction_cache.pkl"):
    with open(cache_file, "wb") as f:
        pickle.dump(cache, f)

def extract_json_from_response(response):
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            return {}
    return {}