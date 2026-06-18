"""
================================================================================
api_client.py — Módulo de Comunicação com a API do Google Gemini
================================================================================
SDK utilizado : google-genai (substitui google.generativeai depreciado)
Instalação    : pip install google-genai

Responsabilidade:
    Encapsular toda a lógica de comunicação com a API do Gemini.
    Este módulo não sabe nada sobre interface ou apresentação —
    só sabe fazer requisições e retornar resultados.

    Funções disponíveis:
        criar_cliente()              → Instancia o cliente autenticado
        criar_config()               → Monta o GenerateContentConfig reutilizável
        chat_simples()               → Chamada única, resposta completa
        chat_streaming()             → Tokens progressivos
        chat_multi_turno()           → Histórico entre turnos via lista de Content
        chat_com_tratamento_erros()  → Wrapper com captura de exceções

Diferenças do novo SDK (google-genai) vs antigo (google.generativeai):
    ANTES  : genai.configure(api_key=) + GenerativeModel(model_name=)
    AGORA  : genai.Client(api_key=) + client.models.generate_content(model=, ...)

    ANTES  : model.generate_content(prompt)
    AGORA  : client.models.generate_content(model=MODEL, contents=prompt, config=...)

    ANTES  : model.start_chat(history=[...]) → session.send_message(...)
    AGORA  : histórico montado manualmente como lista de types.Content

    ANTES  : google.api_core.exceptions (pacote externo)
    AGORA  : google.genai.errors (embutido no SDK)
================================================================================
"""

from google import genai
from google.genai import types
from google.genai import errors as gemini_errors

from gemini_config import API_KEY, MODEL, MAX_TOKENS, TEMPERATURE, SYSTEM_PROMPT


# ════════════════════════════════════════════════════════════════════════════════
# FÁBRICA DO CLIENTE
# ════════════════════════════════════════════════════════════════════════════════

def criar_cliente() -> genai.Client:
    """
    Instancia e retorna o cliente autenticado do novo SDK google-genai.

    Mudança principal em relação ao SDK antigo:
        Antes : genai.configure(api_key=API_KEY)  →  configuração global
        Agora : genai.Client(api_key=API_KEY)      →  objeto explícito

    Retorno:
        Instância configurada de genai.Client.
    """
    return genai.Client(api_key=API_KEY)


def criar_config(**kwargs) -> types.GenerateContentConfig:
    """
    Monta e retorna o objeto de configuração de geração reutilizável.

    No novo SDK, os parâmetros (temperature, max_output_tokens, system_instruction)
    são agrupados em GenerateContentConfig e passados como `config=` em cada chamada.

    Parâmetros opcionais (**kwargs):
        Permitem sobrescrever os defaults de config.py para chamadas específicas.
        Ex: criar_config(temperature=0.9) para uma chamada mais criativa.

    Retorno:
        Instância de types.GenerateContentConfig.
    """
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=kwargs.get("temperature", TEMPERATURE),
        max_output_tokens=kwargs.get("max_output_tokens", MAX_TOKENS),
    )


# ════════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 1 — Chamada Simples (síncrona, resposta completa)
# ════════════════════════════════════════════════════════════════════════════════

def chat_simples(pergunta: str) -> str:
    """
    Envia uma mensagem única e aguarda a resposta completa antes de retornar.

    Equivalência com a Anthropic:
        Anthropic : client.messages.create(messages=[{"role":"user","content":...}])
        Gemini    : client.models.generate_content(model=MODEL, contents=pergunta, ...)

    Estrutura interna da resposta:
        response.text                    → Atalho para o texto da resposta
        response.candidates[0].content  → Objeto de conteúdo completo
        response.usage_metadata          → Tokens consumidos (prompt + resposta)

    Parâmetros:
        pergunta : Texto da mensagem do usuário (str).

    Retorno:
        Texto da resposta do modelo (str).
    """
    client = criar_cliente()
    config = criar_config()

    response = client.models.generate_content(
        model=MODEL,
        contents=pergunta,
        config=config,
    )

    return response.text


# ════════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 2 — Streaming (tokens progressivos)
# ════════════════════════════════════════════════════════════════════════════════

def chat_streaming(pergunta: str, callback=None) -> str:
    """
    Envia uma mensagem e recebe os tokens progressivamente (streaming).

    Como funciona no novo SDK:
        client.models.generate_content_stream() retorna um iterável de chunks.
        Cada chunk tem um atributo .text com o fragmento de token recebido.

    Parâmetro `callback`:
        Função opcional chamada a cada fragmento. Se não fornecida,
        os fragmentos são impressos diretamente no stdout.
        Assinatura esperada: callback(fragmento: str) -> None

    Parâmetros:
        pergunta : Texto da mensagem do usuário (str).
        callback : Função opcional para processar cada fragmento.

    Retorno:
        Texto completo acumulado (str).
    """
    client = criar_cliente()
    config = criar_config()

    texto_completo = ""

    for chunk in client.models.generate_content_stream(
        model=MODEL,
        contents=pergunta,
        config=config,
    ):
        fragmento = chunk.text
        texto_completo += fragmento

        if callback:
            callback(fragmento)
        else:
            print(fragmento, end="", flush=True)

    return texto_completo


# ════════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 3 — Conversa Multi-turno (histórico manual)
# ════════════════════════════════════════════════════════════════════════════════

def chat_multi_turno(historico: list, nova_mensagem: str) -> tuple[str, list]:
    """
    Gerencia uma conversa com múltiplos turnos reenviando o histórico completo.

    Estrutura de um turno (types.Content):
        types.Content(
            role="user",                           # "user" ou "model"
            parts=[types.Part(text="mensagem")]
        )
        Atenção: no Gemini o papel do assistente é "model" (vs "assistant" na Anthropic).

    A API continua STATELESS: cada chamada recebe o histórico completo.

    Parâmetros:
        historico     : Lista de types.Content anteriores. Passe [] para iniciar.
        nova_mensagem : Texto da nova mensagem do usuário.

    Retorno:
        Tupla (resposta_str, historico_atualizado).
    """
    client = criar_cliente()
    config = criar_config()

    historico.append(
        types.Content(role="user", parts=[types.Part(text=nova_mensagem)])
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=historico,
        config=config,
    )

    resposta_texto = response.text

    historico.append(
        types.Content(role="model", parts=[types.Part(text=resposta_texto)])
    )

    return resposta_texto, historico


# ════════════════════════════════════════════════════════════════════════════════
# FUNÇÃO 4 — Wrapper com Tratamento de Erros
# ════════════════════════════════════════════════════════════════════════════════

def chat_com_tratamento_erros(pergunta: str) -> dict:
    """
    Executa chat_simples() com captura estruturada das exceções da API Gemini.

    Hierarquia de erros do novo SDK (google.genai.errors):
        APIError          → classe base para todos os erros da API
        ├── ClientError   → erros 4xx (problema na requisição do cliente)
        │     • 400 → argumento inválido, model inexistente
        │     • 403 → API Key inválida, sem permissão
        │     • 429 → rate limit ou cota atingida
        └── ServerError   → erros 5xx (problema no servidor do Google)
              • 503 → serviço temporariamente indisponível

    Diferença em relação ao SDK antigo:
        Antes : google.api_core.exceptions (pacote separado, precisava instalar)
        Agora : google.genai.errors (embutido — sem dependência extra)

    Retorno:
        dict com campos:
            "sucesso"   : bool
            "resposta"  : str (texto do modelo ou mensagem de erro)
            "erro_tipo" : str | None
    """
    try:
        texto = chat_simples(pergunta)
        return {"sucesso": True, "resposta": texto, "erro_tipo": None}

    except gemini_errors.ClientError as e:
        codigo = str(e)

        if "403" in codigo or "PERMISSION_DENIED" in codigo:
            return {
                "sucesso": False,
                "resposta": "❌ Erro de autenticação: verifique sua API_KEY em config.py.",
                "erro_tipo": "ClientError_403"
            }
        elif "429" in codigo or "RESOURCE_EXHAUSTED" in codigo:
            return {
                "sucesso": False,
                "resposta": (
                    "⏳ Cota ou rate limit atingido.\n"
                    "   → Aguarde alguns segundos e tente novamente.\n"
                    "   → Se persistir, verifique os limites em https://ai.dev/rate-limit"
                ),
                "erro_tipo": "ClientError_429"
            }
        else:
            return {
                "sucesso": False,
                "resposta": f"❌ Erro na requisição (4xx): {str(e)}",
                "erro_tipo": "ClientError"
            }

    except gemini_errors.ServerError as e:
        return {
            "sucesso": False,
            "resposta": f"❌ Erro no servidor Google (5xx): {str(e)}",
            "erro_tipo": "ServerError"
        }

    except gemini_errors.APIError as e:
        return {
            "sucesso": False,
            "resposta": f"❌ Erro da API Gemini: {str(e)}",
            "erro_tipo": "APIError"
        }
