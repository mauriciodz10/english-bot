"""
bedrock_generator.py
Genera las explicaciones de inglés usando Amazon Bedrock (Amazon Nova Micro).
"""

import json
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

IRREGULAR_VERB_PROMPT = """Eres un profesor de inglés cercano y motivador. Crea una cápsula de aprendizaje diaria para un hispanohablante de nivel intermedio.

Verbos de hoy: {verbs}

Para CADA verbo usa este formato:

🔹 *VERBO* — traducción
🔊 Pronunciación: escribe cómo suena en español aproximado
_(Ej: "go" → "gou" | "went" → "uent" | "gone" → "gon")_
📝 *Formas:* base form | past simple | past participle
_(IMPORTANTE: escribe siempre las 3 formas reales. Ej: go | went | gone)_

⏱ *En acción:*
• 🟢 Present: oración corta
• 🟡 Past: oración corta
• 🔵 Present perfect: oración corta
• 🟠 Past continuous: oración corta
• 🔴 Future: oración corta

⚠️ *Error común:* describe el error + explica brevemente por qué ocurre y cómo evitarlo

---

Reglas:
- Oraciones de máximo 8 palabras
- La pronunciación usa letras españolas para aproximar el sonido real
- Sin introducciones ni despedidas
- El texto completo no debe superar 1200 caracteres."""

PHRASAL_VERB_PROMPT = """Eres un profesor de inglés cercano y motivador. Crea una cápsula de aprendizaje diaria para un hispanohablante de nivel intermedio.

Phrasal verbs de hoy: {verbs}

Para CADA phrasal verb usa este formato:

🔹 *PHRASAL VERB* — traducción
🔊 Pronunciación: escribe cómo suena en español aproximado
_(Ej: "break down" → "breik daun")_
📌 Cuándo usarlo: una línea corta

💬 *Ejemplos:*
• 💼 Trabajo: oración corta
• 🏠 Cotidiano: oración corta
• 😄 Informal: oración corta

⚠️ *Error común:* describe el error + explica brevemente por qué ocurre y cómo evitarlo
🔗 *Similar:* 1 expresión relacionada

---

Reglas:
- Ejemplos de máximo 8 palabras
- La pronunciación usa letras españolas para aproximar el sonido real
- Sin introducciones ni despedidas
- El texto completo no debe superar 1200 caracteres."""

VOCABULARY_PROMPT = """Eres un profesor de inglés cercano y motivador. Crea una cápsula de vocabulario para un hispanohablante que quiere alcanzar nivel B2-C1.

Palabras de hoy: {words}

Para CADA palabra usa este formato:

🔹 *PALABRA* — traducción
🔊 Pronunciación: escribe cómo suena en español aproximado
_(Ej: "achieve" → "a-CHIIV" | "nuance" → "NIU-ans")_
📌 Nivel: B2 / C1
💬 Cuándo usarlo: una línea corta
• Ejemplo: oración natural en inglés

⚠️ *Error común:* describe el error + explica brevemente por qué ocurre y cómo evitarlo

---

Reglas:
- Ejemplos de máximo 10 palabras
- La pronunciación usa letras españolas para aproximar el sonido real
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
            "irregular_verbs": "🇬🇧 *Verbos del día* 📚",
            "phrasal_verbs":   "🇬🇧 *Phrasal Verbs del día* 💬",
            "vocabulary":      "🇬🇧 *Vocabulario del día — B2/C1* 🧠",
        }
        header        = headers.get(lesson_type, "🇬🇧 *Inglés del día*")
        verbs_display = " & ".join(f"*{v}*" for v in verbs)

        return (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📌 Hoy: {verbs_display}\n\n"
            f"{lesson_content}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"_Ciclo {cycle} • English Bot 🤖_"
        )