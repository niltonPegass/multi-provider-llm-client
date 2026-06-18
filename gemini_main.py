"""
================================================================================
main.py — Ponto de Entrada da Aplicação
================================================================================
Responsabilidade:
    Orquestrar a execução dos diferentes modos de uso da API.
    Este módulo não contém lógica de negócio nem de comunicação —
    apenas chama as funções do api_client e exibe os resultados.

    NOTA: Este arquivo é idêntico ao da versão Anthropic.
    A troca de provedor (Anthropic → Gemini) não exigiu nenhuma alteração aqui.
    Isso demonstra na prática o benefício da modularização: o main.py é
    agnóstico ao provedor de IA utilizado.

Estrutura do projeto:
    gemini_project/
    ├── config.py        → API Key e parâmetros (modelo, temperatura, system prompt)
    ├── api_client.py    → Funções de comunicação com a API do Gemini
    ├── main.py          → Ponto de entrada: orquestra e exibe os resultados  ← você está aqui
    └── requirements.txt → Dependências do projeto

Como executar:
    python main.py
================================================================================
"""

from gemini_api_client import (
    chat_com_tratamento_erros,
    chat_streaming,
    chat_multi_turno,
)


# ── Helpers de apresentação ───────────────────────────────────────────────────

def cabecalho(titulo: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {titulo}")
    print(f"{'=' * 60}")


def rodape(info: str = "") -> None:
    if info:
        print(f"\n  ℹ {info}")
    print("─" * 60)


# ════════════════════════════════════════════════════════════════════════════════
# DEMO 1 — Chamada Simples com Tratamento de Erros
# ════════════════════════════════════════════════════════════════════════════════

def demo_chamada_simples() -> None:
    cabecalho("DEMO 1 — Chamada Simples")

    pergunta = "O que é temperature em modelos de linguagem e como ela afeta as respostas?"
    print(f"\nPergunta:\n  {pergunta}\n")

    resultado = chat_com_tratamento_erros(pergunta)

    if resultado["sucesso"]:
        print(f"Resposta:\n{resultado['resposta']}")
    else:
        print(f"Erro [{resultado['erro_tipo']}]: {resultado['resposta']}")

    rodape()


# ════════════════════════════════════════════════════════════════════════════════
# DEMO 2 — Streaming de Tokens
# ════════════════════════════════════════════════════════════════════════════════

def demo_streaming() -> None:
    cabecalho("DEMO 2 — Streaming de Tokens")

    pergunta = "Em três frases, explique o que é um endpoint de API REST."
    print(f"\nPergunta:\n  {pergunta}\n")
    print("Resposta (tokens chegando progressivamente):\n")

    chat_streaming(pergunta)

    rodape("Cada fragmento acima foi recebido e impresso individualmente.")


# ════════════════════════════════════════════════════════════════════════════════
# DEMO 3 — Conversa Multi-turno
# ════════════════════════════════════════════════════════════════════════════════

def demo_multi_turno() -> None:
    cabecalho("DEMO 3 — Conversa Multi-turno")

    historico = []

    pergunta_1 = "O que é XGBoost?"
    print(f"\n[Turno 1]\nUsuário: {pergunta_1}\n")
    resposta_1, historico = chat_multi_turno(historico, pergunta_1)
    print(f"Gemini : {resposta_1}")

    pergunta_2 = "Qual é a diferença principal em relação ao Random Forest?"
    print(f"\n[Turno 2]\nUsuário: {pergunta_2}\n")
    resposta_2, historico = chat_multi_turno(historico, pergunta_2)
    print(f"Gemini : {resposta_2}")

    rodape(f"Histórico acumulado: {len(historico)} mensagens gerenciadas pelo ChatSession.")


# ════════════════════════════════════════════════════════════════════════════════
# EXECUÇÃO
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("  CLIENTE API GEMINI — DEMONSTRAÇÃO MODULAR")
    print("=" * 60)

    demo_chamada_simples()
    demo_streaming()
    demo_multi_turno()

    print("\nDemonstração concluída.\n")
