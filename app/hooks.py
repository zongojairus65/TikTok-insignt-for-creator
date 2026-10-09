import re

PATTERNS = [
    ("question", re.compile(r"\?")),
    ("curiosité / suspense", re.compile(r"\b(attends|regarde|écoute|tu ne vas pas|personne ne|voici pourquoi|la vérité|secret|incroyable)\b", re.I)),
    ("urgence / temporalité", re.compile(r"\b(aujourd'hui|maintenant|avant de|ne passe pas|cette nuit|ce matin)\b", re.I)),
    ("adresse directe", re.compile(r"\b(tu|toi|vous|ton|ta|tes|votre|vos)\b", re.I)),
    ("émotion / foi", re.compile(r"\b(peur|pleure|joie|espoir|miracle|Dieu|Jésus|prière|amen|réussir|échec)\b", re.I)),
    ("chiffre", re.compile(r"\b\d+\b")),
]

def analyze_hook(description=None, transcript=None):
    text = " ".join(x.strip() for x in (description or "", transcript or "") if x and x.strip())
    words = re.findall(r"\b[\wÀ-ÿ'-]+\b", text)
    signals = [name for name, pattern in PATTERNS if pattern.search(text)]
    suggestions = []
    if not text:
        return {"text": "", "word_count": 0, "signals": [], "assessment": "Aucun texte fourni : impossible d'analyser le hook.", "suggestions": ["Ajoutez la phrase prononcée dans les 1 à 3 premières secondes."]}
    if len(words) > 18:
        suggestions.append("Tester une version plus courte : le hook dépasse 18 mots.")
    if not any(x in signals for x in ("question", "curiosité / suspense", "adresse directe")):
        suggestions.append("Tester une question, une promesse claire ou une adresse directe dès le début.")
    if not suggestions:
        suggestions.append("Créer une variante A/B en changeant seulement la première phrase.")
    return {"text": text, "word_count": len(words), "signals": signals,
            "assessment": "Indices linguistiques détectés; ce résultat ne mesure pas la rétention et ne prédit pas la viralité.",
            "suggestions": suggestions}
