from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import numpy as np
import spacy

# spacy processing
nlp = spacy.load("en_core_web_sm")

#main processing
def preprocess(text):
    doc = nlp(text.lower())
    return " ".join([t.lemma_ for t in doc if t.is_alpha and not t.is_stop])

#load from csv
df = pd.read_csv("triage_data.csv")

# Clean text
df["cleaned"] = df["text"].apply(preprocess)
X = df["cleaned"].tolist()
y = df["severity"].tolist()

#embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Convert sentences to embeddings
X_embeddings = embedder.encode(X, show_progress_bar=True)

#classifier of embeddings
X_train, X_test, y_train, y_test = train_test_split(X_embeddings, y, test_size=0.2, random_state=42)

clf = LogisticRegression(max_iter=2000)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print("\n🔍 Classification Report:\n")
print(classification_report(y_test, y_pred))

#triage loop
print("\n🩺 MEDICAL TRIAGE BOT — SEMANTIC SEVERITY CLASSIFIER")
print("Type 'exit' to quit\n")

while True:
    user_input = input("Describe your condition: ").strip()
    if user_input.lower() == "exit":
        break

    cleaned = preprocess(user_input)
    user_vec = embedder.encode([cleaned])

    pred = clf.predict(user_vec)[0]
    probs = clf.predict_proba(user_vec)[0]
    conf = np.max(probs)

    if conf < 0.4:
        print(f"🤔 Uncertain result (confidence {conf:.2f}). Please consult a professional.\n")
    else:
        print(f"Predicted severity: {pred.upper()} (confidence: {conf:.2f})\n")
