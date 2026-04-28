"""
bedrock_generator.py
Genera las explicaciones de inglés usando Amazon Bedrock (Amazon Nova Micro).

Nota: Amazon Nova usa un formato de request diferente al de Anthropic.
  - messages[].content es una lista de objetos: [{"text": "..."}]
  - inferenceConfig en lugar de max_tokens al nivel raíz
  - Response en body["output"]["message"]["content"][0]["text"]
  - Tokens en body["usage"]["inputTokens"] / "outputTokens"
"""

import json
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

IRREGULAR_VERB_PROMPT = """Eres un profesor de inglés experto. Genera una lección diaria de inglés para un estudiante hispanohablante de nivel intermedio.

Crea una explicación para los siguientes verbos irregulares en inglés: {verbs}

Para CADA verbo incluye:
1. *Verbo:* forma base | past simple | past participle
2. *Significado:* traducción al español en una línea
3. Los siguientes tiempos con UN ejemplo cada uno:
   - *Present simple:* (oración afirmativa)
   - *Past simple:* (oración afirmativa)
   - *Present perfect:* (con have/has)
   - *Past continuous:* (con was/were + ing)
   - *Future simple:* (con will)

Formato de salida:
- Usa *texto* para negrita
- Usa emojis para hacer la lección más visual
- Separa cada verbo con una línea de guiones ---
- Al final agrega un tip de uso común en inglés cotidiano

Responde SOLO con el contenido de la lección, sin introducciones ni despedidas.
IMPORTANTE: el texto completo no debe superar 1200 caracteres."""

PHRASAL_VERB_PROMPT = """Eres un profesor de inglés experto. Genera una lección diaria de inglés para un estudiante hispanohablante de nivel intermedio.

Crea una explicación para los siguientes phrasal verbs en inglés: {verbs}

Para CADA phrasal verb incluye:
1. *Phrasal verb:* en negrita
2. *Significado:* traducción al español + explicación breve de cuándo usarlo
3. *3 ejemplos en inglés* en diferentes contextos (formal, informal, laboral)
4. *Expresiones relacionadas:* 1 o 2 frases similares

Formato de salida:
- Usa *texto* para negrita
- Usa emojis para hacer la lección más visual
- Separa cada phrasal verb con una línea de guiones ---
- Al final agrega una nota sobre registro (formal/informal)

Responde SOLO con el contenido de la lección, sin introducciones ni despedidas.
IMPORTANTE: el texto completo no debe superar 1200 caracteres."""


VOCABULARY_PROMPT = """Eres un profesor de inglés cercano y motivador. Crea una cápsula de vocabulario para un estudiante hispanohablante que quiere alcanzar nivel B2-C1.

Palabras de hoy: {words}

Para CADA palabra usa exactamente este formato:

🔹 *PALABRA* — traducción
📌 Nivel: B2 / C1
💬 Uso: una línea corta explicando en qué contexto se usa
• Ejemplo: oración natural en inglés

Separa cada palabra con ---

Reglas:
- Ejemplos de máximo 10 palabras
- Palabras sofisticadas pero de uso real (no arcaicas)
- Sin introducciones ni despedidas
- El texto completo no debe superar 1200 caracteres."""

class BedrockGenerator:
    def __init__(self, model_id: str, aws_region: str):
        self.client   = boto3.client("bedrock-runtime", region_name=aws_region)
        self.model_id = model_id

    def _build_prompt(self, lesson_type: str, verbs: list[str]) -> str:
        verbs_str = " | ".join(verbs)
        if lesson_type == "irregular_verbs":
            return IRREGULAR_VERB_PROMPT.format(verbs=verbs_str)
        elif lesson_type == "phrasal_verbs":
            return PHRASAL_VERB_PROMPT.format(verbs=verbs_str)
        elif lesson_type == "vocabulary":
            return VOCABULARY_PROMPT.format(words=verbs_str)
        else:
            raise ValueError(f"lesson_type inválido: {lesson_type}")

    def generate(self, lesson_type: str, verbs: list[str]) -> str:
        prompt = self._build_prompt(lesson_type, verbs)

        logger.info(
            "Llamando a Bedrock — modelo: %s | tipo: %s | verbos: %s",
            self.model_id, lesson_type, verbs,
        )

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "inferenceConfig": {
                        "max_new_tokens": 900,
                        "temperature":    0.7,
                    },
                }),
            )

            body    = json.loads(response["body"].read())
            content = body["output"]["message"]["content"][0]["text"]

            logger.info(
                "Bedrock respondió — tokens entrada: %d | tokens salida: %d | chars: %d",
                body["usage"]["inputTokens"],
                body["usage"]["outputTokens"],
                len(content),
            )

            return content

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error("Error Bedrock (%s): %s", error_code, e)
            raise

    def build_whatsapp_message(
        self,
        lesson_type: str,
        verbs: list[str],
        lesson_content: str,
        cycle: int,
    ) -> str:
        headers = {
            "irregular_verbs": "🇬🇧 *Lección de hoy — Verbos Irregulares* 📚",
            "phrasal_verbs":   "🇬🇧 *Lección de hoy — Phrasal Verbs* 💬",
            "vocabulary":      "🇬🇧 *Vocabulario del día — B2/C1* 🧠",
        }
        header        = headers.get(lesson_type, "🇬🇧 *Lección de inglés*")
        verbs_display = " & ".join(f"*{v}*" for v in verbs)

        return (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📌 Hoy: {verbs_display}\n\n"
            f"{lesson_content}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"_Ciclo {cycle} • English Bot 🤖_"
        )
