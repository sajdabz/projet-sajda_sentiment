from transformers import pipeline

classifier = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment"
)

textes = [
    "J'adore ce produit, il est vraiment excellent!",
    "C'est nul, je suis très déçu.",
    "C'est correct, sans plus."
]

for texte in textes:
    resultat = classifier(texte)
    print(f"Texte: {texte}")
    print(f"Résultat: {resultat}\n")