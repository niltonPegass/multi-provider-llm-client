"""
================================================================================
🚀 GEMINI_MAIN.PY — Orquestração e Interface com o Usuário
================================================================================

🎯 PROPÓSITO:
    Ponto de entrada da aplicação. Orquestra a execução dos diferentes modos
    de demonstração da API Gemini e exibe os resultados para o usuário.

🏗️  PADRÃO DE DESIGN (Separação de Responsabilidades):
    
    ✓ gemini_config.py  → APENAS parâmetros e configurações
    ✓ gemini_api_client.py → APENAS lógica de comunicação com API
    ✓ gemini_main.py → APENAS orquestração e UI/UX (você está aqui)
    
    Benefício: Cada módulo tem UMA responsabilidade clara.
    • Fácil de testar (cada parte isolada)
    • Fácil de reutilizar (import gemini_api_client em outro projeto)
    • Fácil de manter (mudança em um lugar afeta pouco os outros)

📖 CONCEITO-CHAVE:
    Este arquivo é AGNÓSTICO ao provedor. Se quisermos trocar Gemini por
    OpenAI ou Anthropic, precisamos apenas trocar o import e os nomes
    das funções. O resto do main.py continua igual!
    
    Por isso é idêntico à versão anthropic_main.py — só mudou o import.

🎮 MODOS DE USO (3 demonstrações):
    
    1️⃣  Chamada Simples
        └─ Uma pergunta, resposta completa
        └─ chat_com_tratamento_erros()
    
    2️⃣  Streaming
        └─ Uma pergunta, resposta progressiva
        └─ chat_streaming_com_tratamento_erros()
    
    3️⃣  Multi-turno (Chat)
        └─ Conversa com histórico
        └─ chat_multi_turno_com_tratamento_erros()

================================================================================
"""

from gemini_api_client import (
    chat_com_tratamento_erros,
    chat_streaming_com_tratamento_erros,
    chat_multi_turno_com_tratamento_erros,
)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  HELPERS DE APRESENTAÇÃO — Formatting de Output                            ║
# ║  (Funções que deixam a saída visual mais legível)                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def cabecalho(titulo: str) -> None:
    """
    🎨 Imprime um cabeçalho visualmente destacado.
    
    ◆ O QUE FAZ:
        Cria uma linha de separação com título centralizado.
        Melhora a legibilidade visual entre diferentes modos.
    
    ◆ PADRÃO:
        ============================================================
          DEMO 1 — Chamada Simples
        ============================================================
    
    ◆ PARÂMETRO:
        titulo (str): Texto do cabeçalho
        
    ◆ EXEMPLO DE USO:
        cabecalho("DEMO 1 — Chamada Simples")
    """
    # Imprime uma linha de 60 caracteres "="
    # 60 é um bom tamanho para terminais típicos (80 colunas total)
    # Deixa espaço para caracteres de margin/borda
    print(f"\n{'=' * 60}")
    
    # Imprime o título com espaçamento (2 espaços antes para centralizar)
    # Isso deixa o titulo como "  DEMO 1 — Chamada Simples"
    # em vez de colado no lado esquerdo, melhorando a legibilidade
    print(f"  {titulo}")
    
    # Outra linha de separação para "fechar" o cabeçalho visualmente
    # Este duplo-separador (antes e depois) delimita bem a seção
    print(f"{'=' * 60}")


def rodape(info: str = "") -> None:
    """
    🎨 Imprime um rodapé com informação (opcional) e linha separadora.
    
    ◆ O QUE FAZ:
        Encerra uma seção com uma linha tracejada.
        Opcionalmente exibe uma informação adicional.
    
    ◆ PADRÃO:
        (sem informação)
        ────────────────────────────────────────────────────────
        
        (com informação)
        
          ℹ Total de mensagens: 6
        ────────────────────────────────────────────────────────
    
    ◆ PARÂMETRO:
        info (str, opcional): Informação extra para exibir
        
    ◆ EXEMPLO DE USO:
        rodape()  # Apenas linha
        rodape("Histórico acumulado: 10 mensagens")
    """
    # Se houver informação, imprime com um ícone "ℹ" indicando informação
    # O condicional if info garante que não imprime linha vazia se info não for fornecido
    if info:
        print(f"\n  ℹ {info}")
    
    # Imprime linha tracejada de 60 caracteres usando "─" (travessão unicode)
    # Este é mais refinado visualmente que "-" comum
    # Marca o fim de uma seção de forma clara
    # Alternativas:
    #   - "─" * 60  (travessão unicode — sofisticado)
    #   - "-" * 60  (hífen simples — clássico)
    #   - "•" * 60  (bullet — visual)
    print("─" * 60)


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  DEMONSTRAÇÃO 1 — Chamada Simples                                          ║
# ║  (Uma pergunta, resposta completa, sem contexto anterior)                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def demo_chamada_simples() -> None:
    """
    💬 DEMO 1 — Modo de Pergunta Simples e Isolada.
    
    ◆ QUANDO USAR:
        • Perguntas únicas, sem contexto anterior
        • Exemplos: "Qual é a capital?", "Explique ML"
        • Não é uma conversa — é uma consulta
    
    ◆ FLUXO:
        1. Exibe cabeçalho
        2. Loop até o usuário digitar "sair":
           a. Lê pergunta do console
           b. Chama chat_com_tratamento_erros()
           c. Verifica se sucesso ou erro
           d. Exibe resposta ou mensagem de erro
        3. Exibe rodapé
    
    ◆ TRATAMENTO DE ERROS:
        Se algo der errado (503, 429, 403, etc.):
        ├─ Não lança exceção
        ├─ Exibe mensagem amigável
        └─ Permite tentar novamente
    
    ◆ ESTRUTURA DE RESPOSTA:
        resultado = {
            "sucesso": bool,
            "resposta": str,
            "erro_tipo": str|None
        }
    
    ◆ EXEMPLO DE FLUXO:
        Usuário: "Explique embeddings"
        Bot: "Embeddings são representações numéricas..."
        Usuário: "Como usar em PyTorch?"
        Bot: "Em PyTorch, use torch.nn.Embedding..."
        Usuário: "sair"
        [Encerra]
    
    ◆ PARTICULARIDADE:
        Cada pergunta é INDEPENDENTE. O bot não "lembra" da pergunta anterior.
        Para conversa com contexto, use demo_multi_turno().
    """
    # Exibe cabeçalho visual para delimitar este demo
    cabecalho("DEMO 1 — Chamada Simples")

    # Loop infinito que continua até o usuário digitar "sair"
    while True:
        # Lê input do usuário
        pergunta = input("\nDigite sua pergunta (ou 'sair' para encerrar): ")
        
        # Verifica se o usuário quer sair
        # .strip() remove espaços em branco das pontas
        # .lower() converte para minúsculas para comparação case-insensitive
        # Alternativas para sair: "quit", "exit", "q" (adicione com "or")
        if pergunta.strip().lower() == "sair":
            break
        
        # Exibe a pergunta formatada para confirmar
        # Espaçamento com "\n" e "  " melhora legibilidade
        print(f"\nPergunta:\n  {pergunta}\n")

        # Executa a pergunta COM TRATAMENTO DE ERROS integrado
        # A função chat_com_tratamento_erros() nunca lança exceção
        # Sempre retorna um dicionário com sucesso/erro/tipo
        resultado = chat_com_tratamento_erros(pergunta)

        # Verifica se foi bem-sucedido
        if resultado["sucesso"]:
            # Se sucesso=True, exibe a resposta
            print(f"Resposta:\n{resultado['resposta']}")
        else:
            # Se sucesso=False, exibe tipo de erro e mensagem de erro
            # erro_tipo pode ser: "ClientError_403", "ServerError_503", "ClientError_429", etc.
            # Útil para debug ou log
            print(f"Erro [{resultado['erro_tipo']}]: {resultado['resposta']}")

    # Ao sair do loop, exibe rodapé para encerrar a seção visualmente
    rodape()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  DEMONSTRAÇÃO 2 — Streaming                                                ║
# ║  (Uma pergunta, resposta progressiva em tempo real)                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def demo_streaming() -> None:
    """
    🌊 DEMO 2 — Modo de Streaming (Resposta Progressiva).
    
    ◆ QUANDO USAR:
        • Respostas longas (melhor UX — vê progressão)
        • Conversas em tempo real
        • Interfaces que precisam de feedback visual
    
    ◆ DIFERENÇA vs DEMO 1:
        
        Demo 1 (Simples):
        Espera... Espera... [3 segundos depois] Resposta completa!
        
        Demo 2 (Streaming):
        "Embedding" → "s são" → " representações" → ...
        (visualiza em tempo real)
    
    ◆ FLUXO:
        1. Exibe cabeçalho
        2. Loop até o usuário digitar "sair":
           a. Lê pergunta do console
           b. Instrui o usuário a digitar "sair"
           c. Chama chat_streaming_com_tratamento_erros()
           d. A resposta é impressa progressivamente (chunk por chunk)
           e. Exibe resultado completo ao final
        3. Exibe rodapé
    
    ◆ COMO FUNCIONA INTERNAMENTE:
        A função chat_streaming() usa generate_content_stream():
        
        for chunk in stream:
            print(chunk.text, end="", flush=True)  ← Imprime imediatamente
        
        flush=True garante que não fica na buffer — mostra JÁ!
    
    ◆ TRATAMENTO DE ERROS:
        Se erro durante streaming:
        ├─ Captura exceção
        ├─ Para de receber chunks
        ├─ Exibe mensagem de erro
        └─ Permite tentar novamente
    
    ◆ EXEMPLO DE FLUXO:
        Usuário: "Explique RL"
        Bot: "Reinforcement Learning é um paradigma..." [streaming]
        Usuário: "sair"
        [Encerra]
    
    ◆ PARTICULARIDADE:
        Como Demo 1, também é stateless — cada pergunta é independente.
        Não mantém histórico entre perguntas.
    """
    # Exibe cabeçalho visual
    cabecalho("DEMO 2 — Streaming de Tokens")

    while True:
        # Lê pergunta do usuário
        pergunta = input("\nDigite sua pergunta: ")
        
        # Exibe instruções sobre como sair
        # Isso é importante porque em streaming, a saída é contínua
        # Se não avisar antes de iniciar streaming, fica confuso
        print('Para finalizar o demo de streaming, digite "sair".\n')

        # Verifica se é pedido para sair
        if pergunta.strip().lower() == "sair":
            print("\nEncerrando demo de streaming...")
            break

        # Exibe a pergunta formatada
        print(f"\nPergunta:\n  {pergunta}\n")

        # Executa streaming com tratamento de erros
        # Não passa callback — usa comportamento padrão (imprime progressivamente)
        # 
        # Internamente, chat_streaming_com_tratamento_erros() chama:
        #   chat_streaming(pergunta, callback=None)
        # 
        # Sem callback, a função usa o comportamento padrão:
        #   print(fragmento, end="", flush=True)
        # 
        # Isso imprime cada chunk imediatamente sem quebra de linha
        resultado = chat_streaming_com_tratamento_erros(pergunta)

        # Verifica se foi bem-sucedido
        if resultado["sucesso"]:
            # A resposta já foi impressa durante o streaming (chunk por chunk)
            # Aqui apenas formatamos um rodapé
            # Exibimos a resposta completa para referência
            print(f"\nResposta completa:\n{resultado['resposta']}")
        else:
            # Se houve erro, exibe a mensagem de erro
            # Isso pode ocorrer antes do streaming começar ou durante
            print(f"\nErro [{resultado['erro_tipo']}]: {resultado['resposta']}")

    # Exibe rodapé para encerrar a seção
    rodape()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  DEMONSTRAÇÃO 3 — Multi-turno (Chat com Histórico)                         ║
# ║  (Conversa onde o bot "lembra" de mensagens anteriores)                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

def demo_multi_turno() -> None:
    """
    🔄 DEMO 3 — Modo Multi-turno (Chat com Contexto).
    
    ◆ QUANDO USAR:
        • Conversas longas
        • Referências a mensagens anteriores
        • Refinamento iterativo ("explique melhor")
        • Chat interativo natural
    
    ◆ DIFERENÇA vs DEMO 1:
        
        Demo 1 (Simples, 3 turnos):
        Bot: "O que é RL?"
        Bot: "Como funciona?" ← Não lembra da pergunta anterior
        
        Demo 3 (Multi-turno, 3 turnos):
        Bot: "O que é RL?"
        Bot: "Como funciona?" ← LEMBRA! Contextualiza
        Bot: "Exemplos?" ← AINDA LEMBRA dos 2 anteriores!
    
    ◆ FLUXO:
        1. Exibe cabeçalho
        2. Inicializa histórico vazio: historico = []
        3. Loop até o usuário digitar "sair":
           a. Lê mensagem do console ("Usuário: ")
           b. Chama chat_multi_turno_com_tratamento_erros()
           c. API recebe HISTÓRICO COMPLETO (todas mensagens anteriores)
           d. Bot responde considerando contexto
           e. Atualiza histórico com nova mensagem + resposta
           f. Exibe resposta ("Gemini: ")
        4. Exibe rodapé com total de mensagens
    
    ◆ COMO FUNCIONA COM HISTÓRICO:
        
        Turno 1:
        historico = []
        nova_msg = "O que é RL?"
        API recebe: [msg_usuario]
        resposta = "RL é..."
        historico = [msg_usuario, msg_bot]
        
        Turno 2:
        nova_msg = "Como funciona?"
        API recebe: [msg_usuario_1, msg_bot_1, msg_usuario_2]
                     ↑ CONTEXTO! Bot sabe que estamos falando de RL
        resposta = "Para funcionar, RL usa..."
        historico = [..., msg_usuario_2, msg_bot_2]
        
        Turno 3:
        nova_msg = "Exemplos?"
        API recebe: [...todos os turnos anteriores...]
        resposta = "Exemplos de RL: AlphaGo, ..."
    
    ◆ TRATAMENTO DE ERROS:
        Se erro durante um turno:
        ├─ Captura exceção
        ├─ NÃO adiciona ao histórico (reversível)
        ├─ Exibe mensagem de erro
        ├─ Histórico permanece consistente
        └─ Pode tentar novamente
    
    ◆ EXEMPLO DE FLUXO REAL:
        
        Usuário: Explique o que é transformers
        Gemini: Transformers são arquiteturas de redes neurais...
        
        Usuário: Como eles diferem de RNNs?
        Gemini: [Compara transformers com RNNs, considerando o contexto]
        
        Usuário: Qual é o mecanismo chave?
        Gemini: [Explica attention, sabendo que estamos falando de transformers]
        
        Usuário: sair
        [Histórico acumulado: 6 mensagens (3 usuario + 3 gemini)]
    
    ◆ PARTICULARIDADES:
        • historico é MUTÁVEL — modificado em cada turno
        • Total de tokens aumenta a cada turno (histórico todo é enviado)
        • Melhor experiência UX, mas mais caro em tokens
        • Para conversas MUUUITO longas, considere resumos
    """
    # Exibe cabeçalho visual
    cabecalho("DEMO 3 — Conversa Multi-turno")

    # Inicializa histórico vazio
    # Este será preenchido a cada turno com mensagens do usuário e do bot
    # Estrutura: [Content(role="user", ...), Content(role="model", ...), ...]
    historico = []
    
    # Exibe mensagem informativa
    print("\nIniciando conversa multi-turno. Digite 'sair' para encerrar.\n")

    while True:
        # Lê input do usuário com prefix "Usuário: " para deixar claro quem fala
        pergunta = input("Usuário: ")
        
        # Verifica se é pedido para sair
        if pergunta.strip().lower() == "sair":
            break

        # Executa chat multi-turno COM HISTÓRICO ACUMULADO
        # A função chat_multi_turno_com_tratamento_erros():
        #   1. Adiciona pergunta ao histórico
        #   2. Reenvia TODO o histórico à API
        #   3. Recebe resposta e adiciona ao histórico
        #   4. Retorna: {"sucesso": bool, "resposta": str, "historico": lista_atualizada}
        resultado = chat_multi_turno_com_tratamento_erros(historico, pergunta)

        # Verifica se sucesso ou erro
        if resultado["sucesso"]:
            # Se bem-sucedido, ATUALIZA o histórico com a nova conversa
            # Isso é crucial: sem isso, não acumulamos contexto
            # 
            # Estrutura de resultado["historico"] após sucesso:
            #   [msg_user_1, msg_bot_1, msg_user_2, msg_bot_2, ...]
            # 
            # Se falhasse, esta linha não executaria e o histórico permaneceria igual
            historico = resultado["historico"]
            
            # Exibe a resposta com prefix "Gemini: " para deixar claro quem respondeu
            # Isso cria o padrão de chat visual:
            #   Usuário: Pergunta
            #   Gemini: Resposta
            #   Usuário: Próxima pergunta
            #   Gemini: Próxima resposta
            print(f"Gemini : {resultado['resposta']}\n")
        else:
            # Se erro, o histórico NÃO é modificado
            # Exibe mensagem de erro e permite tentar novamente
            # Isso é importante para garantir consistência: se a API falhar,
            # não queremos adicionar mensagens incompletas ou erradas ao histórico
            print(f"Erro [{resultado['erro_tipo']}]: {resultado['resposta']}\n")

    # Ao sair do loop, exibe estatística sobre a conversa
    # len(historico) é o total de Content objects (usuario + bot)
    # Se historico tem 6 elementos, significa 3 turnos (3 usuario + 3 bot)
    rodape(f"Histórico acumulado: {len(historico)} mensagens gerenciadas.")


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  PONTO DE ENTRADA — main()                                                 ║
# ╚════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    """
    🚀 PONTO DE ENTRADA — Execução Principal da Aplicação.
    
    ◆ O QUE FAZ:
        1. Exibe menu com 3 opções de demonstração
        2. Lê escolha do usuário
        3. Executa a demonstração escolhida
        4. Exibe mensagem de encerramento
    
    ◆ FLUXO:
        
        if __name__ == "__main__":
        ├─ Exibe menu
        ├─ Lê input (1, 2 ou 3)
        ├─ Procura função correspondente em switch
        ├─ Executa a função (demo_*)
        └─ Exibe "Execução finalizada"
    
    ◆ POR QUE if __name__ == "__main__"?
        
        Este padrão garante que o código só executa se o arquivo é
        executado DIRETAMENTE:
        
        ✅ EXECUTA:
        python gemini_main.py  ← Você está rodando este arquivo
        
        ❌ NÃO EXECUTA:
        from gemini_main import demo_chamada_simples  ← Importando em outro arquivo
        
        Permite reutilizar as funções (demo_*) em outros scripts!
    
    ◆ PADRÃO SWITCH (if-elif-else vs dicionário):
        
        ❌ FORMA ANTIGA (menos elegante):
        if escolha == "1":
            demo_chamada_simples()
        elif escolha == "2":
            demo_streaming()
        elif escolha == "3":
            demo_multi_turno()
        
        ✅ FORMA NOVA (mais elegante):
        switch = {
            "1": demo_chamada_simples,
            "2": demo_streaming,
            "3": demo_multi_turno,
        }
        if escolha in switch:
            switch[escolha]()  ← Chama a função armazenada no dict
    
    ◆ EXEMPLO DE EXECUÇÃO:
        
        $ python gemini_main.py
        
        ============================================================
          CLIENTE API GEMINI — DEMONSTRAÇÃO MODULAR
        ============================================================
        
        Which demo would you like to run?
        1. Chamada Simples
        2. Streaming de Tokens
        3. Conversa Multi-turno
        
        Digite o número do demo que deseja executar: 1
        
        [Executa demo_chamada_simples()]
    """
    # Exibe cabeçalho principal com título visual
    print("\n" + "=" * 60)
    print("  CLIENTE API GEMINI — DEMONSTRAÇÃO MODULAR")
    print("=" * 60)

    # Menu de opções
    # Explica claramente o que cada opção faz
    print("\nWhich demo would you like to run?")
    print("1. Chamada Simples")       # ← Uma pergunta, resposta completa
    print("2. Streaming de Tokens")   # ← Uma pergunta, resposta progressiva
    print("3. Conversa Multi-turno")  # ← Conversa com contexto

    # Lê a escolha do usuário
    # input() retorna sempre string, então "1" é diferente de 1
    escolha = input("\nDigite o número do demo que deseja executar: ")

    # PADRÃO SWITCH COM DICIONÁRIO
    # Em vez de if-elif-else (verboso), usa dict que mapeia entrada → função
    # 
    # switch["1"] retorna a FUNÇÃO demo_chamada_simples (não a chamada)
    # Por isso usamos switch[escolha]() — o () no final chama a função
    # 
    # Vantagens:
    #   - Mais limpo e conciso
    #   - Fácil adicionar novas opções (só adiciona ao dict)
    #   - Melhor performance (lookup vs múltiplas comparações)
    # 
    # Alternativas:
    #   - getattr(sys.modules[__name__], f"demo_{escolha}") (dinâmico, mais riscado)
    #   - match-case (Python 3.10+, similar a switch tradicional)
    switch = {
        "1": demo_chamada_simples,
        "2": demo_streaming,
        "3": demo_multi_turno,
    }

    # Executa a função correspondente
    # if escolha in switch: verifica se a chave existe no dicionário
    # Se existir, switch[escolha] retorna a função (referência, não chamada)
    # switch[escolha]() chama a função com parênteses
    if escolha in switch:
        # Executa a função selecionada
        switch[escolha]()
    else:
        # Se entrada inválida, informa o usuário
        # Sem lançar exceção — apenas avisar e sair graciosamente
        print("Escolha inválida.")

    # Mensagem de encerramento
    print("\nExecução finalizada.\n")
