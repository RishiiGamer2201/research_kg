from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

print("Loading model (first run downloads it, may take a minute)...")
model = SentenceTransformer('sentence-transformers/LaBSE')

sentences = {
    "meaning1_en": "The bank approved my loan application.",
    "meaning1_hi": "बैंक ने मेरे ऋण आवेदन को मंजूरी दे दी।",
    "meaning1_fr": "La banque a approuvé ma demande de prêt.",
    "meaning2_en": "The river flooded the village after heavy rain.",
}

labels = list(sentences.keys())
texts = list(sentences.values())
embeddings = model.encode(texts)
sim = cosine_similarity(embeddings)

print("\n--- Similarity Results ---")
for i in range(len(labels)):
    for j in range(i + 1, len(labels)):
        print(f"{labels[i]:15s} vs {labels[j]:15s} -> {sim[i][j]:.3f}")

print("\nExpect HIGH scores: meaning1_en/hi/fr pairs (same meaning, different language)")
print("Expect LOW scores:   meaning2_en vs any meaning1_* pair (different meaning)")
