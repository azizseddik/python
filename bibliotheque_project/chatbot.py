import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is None:
        key = os.getenv('GEMINI_API_KEY', '')
        if not key:
            raise ValueError(
                "GEMINI_API_KEY manquant dans le fichier .env\n"
                "Ajoutez : GEMINI_API_KEY=votre_clé\n"
                "Obtenez une clé gratuite sur : https://aistudio.google.com/app/apikey"
            )
        _client = genai.Client(api_key=key)
    return _client


def _build_context(livres: list) -> str:
    if not livres:
        return "La bibliothèque est vide."
    lines = ["Inventaire actuel de la bibliothèque :"]
    for l in livres:
        lines.append(
            f"  ID {l['id_livre']} | \"{l['titre']}\" par {l['auteur']}"
            f" | {l['categorie']} | {l['annee_publication']}"
            f" | Qté: {l['quantite_disponible']} | Statut: {l['statut']}"
        )
    return "\n".join(lines)


SYSTEM_TEMPLATE = """\
Tu es un assistant bibliothécaire intelligent et sympathique.
Tu réponds TOUJOURS en français, de façon claire et bien formatée.
Tu bases tes réponses UNIQUEMENT sur les données réelles de la bibliothèque fournies ci-dessous.

{context}

Règles :
- Si on demande un livre par ID, cherche cet ID exact dans les données.
- Pour la disponibilité, indique le statut et la quantité disponible.
- Pour les recommandations, propose des livres de la catégorie demandée (de préférence 'disponible').
- Si un livre n'existe pas dans la base, dis-le clairement.
- Si la question ne concerne pas la bibliothèque, réponds poliment que tu es spécialisé
  dans la gestion de bibliothèque.
- Formate tes réponses lisiblement (utilise des tirets ou numéros si tu listes des livres).\
"""


def ask_chatbot(user_message: str, livres: list, history: list | None = None) -> tuple[str, list]:
    """
    history: list of {"role": "user"|"model", "parts": [{"text": ...}]} dicts.
    Returns (reply_text, updated_history).
    """
    context    = _build_context(livres)
    system     = SYSTEM_TEMPLATE.format(context=context)
    model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    client     = _get_client()

    current_history = list(history or [])
    contents = current_history + [
        {'role': 'user', 'parts': [{'text': user_message}]}
    ]

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=1024,
        ),
    )

    reply = response.text
    updated_history = current_history + [
        {'role': 'user',  'parts': [{'text': user_message}]},
        {'role': 'model', 'parts': [{'text': reply}]},
    ]
    return reply, updated_history
