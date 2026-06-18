"""
================================================================================
config.py — Configuração Central do Projeto (Google Gemini)
================================================================================
Responsabilidade:
    Centralizar todas as configurações da aplicação em um único lugar.

Como obter a API Key (gratuita, sem cartão):
    1. Acesse https://aistudio.google.com
    2. Clique em "Get API Key" → "Create API Key"
    3. Cole a chave no campo API_KEY abaixo

ATENÇÃO — sobre a API Key:
    Esta versão expõe a chave diretamente no código para fins didáticos.
    Em projetos reais, use variável de ambiente:
        import os
        API_KEY = os.environ.get("GEMINI_API_KEY")
================================================================================
"""

# ── Autenticação ──────────────────────────────────────────────────────────────
API_KEY: str = "COLE_SUA_CHAVE_AQUI"


# ── Modelo ────────────────────────────────────────────────────────────────────
# Modelos com cota gratuita disponível no free tier do AI Studio:
#   "gemini-1.5-flash"   → Recomendado para free tier: cota generosa (RPM/dia)
#   "gemini-1.5-pro"     → Mais capaz, cota menor no free tier
#   "gemini-2.0-flash"   → Requer billing ativo (cota free tier = 0 em algumas regiões)
#
# Se você não adicionou cartão no Google AI Studio, use "gemini-1.5-flash".

MODEL: str = "models/gemini-2.5-flash"


# ── Limite de tokens da resposta ──────────────────────────────────────────────
MAX_TOKENS: int = 1024


# ── Temperatura ───────────────────────────────────────────────────────────────
# Escala no Gemini: 0.0 (determinístico) → 2.0 (muito criativo)
# Para uso técnico, manter entre 0.0 e 0.5.
TEMPERATURE: float = 0.3


# ── System Prompt ─────────────────────────────────────────────────────────────
# No novo SDK (google-genai), passado como system_instruction no GenerateContentConfig.
SYSTEM_PROMPT: str = """
Você é um assistente técnico especializado em Data Science e Machine Learning.
Responda de forma direta e estruturada, priorizando clareza para um profissional
de nível pleno que está consolidando conhecimentos em MLOps e integração de APIs.
Use exemplos práticos quando pertinente. Responda em português.
""".strip()
