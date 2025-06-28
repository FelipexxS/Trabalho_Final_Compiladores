class SemanticoVisitor(NodeVisitor):
    """
    Percorre a Árvore de Sintaxe Abstrata (AST) validando as regras semânticas da
    linguagem TurtleScript. Cada método `visit_<NomeDoNodo>` é invocado
    automaticamente pelo modelo *visitor* quando um nodo desse tipo é encontrado.
    O método deve:

      1. Verificar se o uso do constructo está semanticamente correto
      2. Registrar erros através de `self.tabela._erro()` sem abortar a execução
      3. (quase sempre) devolver o *tipo* da sub-árvore para que o pai possa
         continuar checando compatibilidade de tipos amontoados.
    """

    def __init__(self):
        # Uma instância de TabelaDeSimbolos — responsável por:
        # • pilha de escopos          (open / close)
        # • registro de variáveis     (declarar / buscar)
        # • coleta de mensagens de erro semântico
      
        self.tabela = TabelaDeSimbolos()

    # ------------------------------------------------------------------
    # DECLARAÇÃO DE VARIÁVEL
    # ------------------------------------------------------------------
  
    def visit_DeclaracaoVar(self, node):
        """
        Nodo produzido pelo parser ao reconhecer algo como:
            inteiro x;
        O parser já armazenou:
            node.tipo_lexema → "inteiro"
            node.ident_lexema → "x"
            node.linha        → nº da linha no código-fonte

        A semântica exige:
          • Inserir 'x' na tabela no *escopo atual*
          • Sinalizar erro se 'x' já existir neste escopo
        """
        tipo = node.tipo_lexema
        ident = node.ident_lexema
        self.tabela.declarar(ident, tipo, node.linha)

    # ------------------------------------------------------------------
    # USO DE IDENTIFICADOR EM EXPRESSÕES
    # ------------------------------------------------------------------
  
    def visit_Identificador(self, node):
        """
        Nodo que representa uma variável aparecendo em uma expressão ou comando.
        Precisamos validar *uso antes da declaração*.

        Retornamos o tipo encontrado — isso permite que o pai verifique
        compatibilidade (ex.: atribuição, chamada de comando).
        """
        entrada = self.tabela.buscar(node.lexema, node.linha)
        return entrada.tipo if entrada else "indefinido"

    # ------------------------------------------------------------------
    # ATRIBUIÇÃO
    # ------------------------------------------------------------------

    def visit_Atribuicao(self, node):
        """
        Nodo semelhante a:
            x = expr;
        O parser garantiu estrutura sintática, mas agora checamos semântica:

          1. O lado esquerdo (variável) deve existir → `visit(node.var)`
          2. O lado direito (expressão) precisa ser avaliado para conhecer seu tipo
          3. Os tipos devem ser compatíveis segundo _compat()
        """
      
        tipo_lhs = self.visit(node.var)   # Tipo da variável alvo, Left-Hand Side (lado esquerdo). 
        tipo_rhs = self.visit(node.expr)  # Tipo do valor atribuído, Right-Hand Side (lado direito).

        # Se qualquer lado é "indefinido" já houve erro de variável não declarada,
        # então só checamos compatibilidade quando ambos são válidos.
      
        if tipo_lhs != "indefinido" and tipo_rhs != "indefinido":
            if not self._compat(tipo_lhs, tipo_rhs):
                self.tabela._erro(
                    f"Tipos incompatíveis em atribuição: '{tipo_lhs}' ← '{tipo_rhs}'",
                    node.linha
                )

    # ------------------------------------------------------------------
    # COMANDO PRIMITIVO DA LINGUAGEM
    # ------------------------------------------------------------------
    def visit_Comando(self, node):
        """
        Nodo que representa chamadas como:
            avancar(10);
            definir_cor("blue");

        Precisamos:
          • Conhecer a assinatura estática do comando (tabela global ASSINATURAS)
          • Visitar cada argumento para descobrir seu tipo real
          • Conferir quantidade e compatibilidade via _checar_assinatura()
        """
        assinatura = ASSINATURAS[node.nome]        # p.ex. (["inteiro"], None)
        tipos_args = [self.visit(arg) for arg in node.args]
        self._checar_assinatura(node.nome, tipos_args, assinatura, node.linha)

    # ------------------------------------------------------------------
    # BLOCO (ou futuro corpo de função)
    # ------------------------------------------------------------------
    def visit_Bloco(self, node):
        """
        Nodo que envolve uma lista de instruções, potencialmente delimitando
        um novo escopo (ex.: corpo do laço `repita`, função futura, etc.).

        Passos:
          • Empilha um novo dicionário na Tabela de Símbolos
          • Visita cada instrução, propagando verificações
          • Desempilha o escopo ao final
        """
        self.tabela.abrir_escopo()
        for stmt in node.stmts:
            self.visit(stmt)
        self.tabela.fechar_escopo()

    # ------------------------------------------------------------------
    # ---------- MÉTODOS AUXILIARES INTERNOS (não visitam AST) ----------
    # ------------------------------------------------------------------
    def _compat(self, tipo_lhs: str, tipo_rhs: str) -> bool:
        """
        Decide se `tipo_rhs` pode ser atribuído a uma variável de `tipo_lhs`.

        Regras atuais:
          • Mesmos tipos → OK
          • Inteiro → Real → OK (promoção implícita)
          • Qualquer outro caso → Erro
        """
        if tipo_lhs == tipo_rhs:
            return True
        # Inteiro se encaixa em real
        return tipo_lhs == "real" and tipo_rhs == "inteiro"

    def _checar_assinatura(
        self,
        nome: str,
        reais: list[str],
        esperados: tuple[list[str], None],
        linha: int
    ):
        """
        Valida chamada de comando em dois níveis:

          1. Aridade  – nº de argumentos deve bater.
          2. Tipagem  – cada argumento conforme assinatura.

        Parâmetros
        ----------
        nome       : nome do comando (ex.: 'avancar')
        reais      : lista dos tipos *avaliados* dos argumentos
        esperados  : tupla (tipos_esperados, retorno) retirada de ASSINATURAS
        linha      : nº da linha original (para mensagem de erro)
        """
        tipos_esp, _ = esperados

        # --- 1. Aridade ---
        if len(reais) != len(tipos_esp):
            self.tabela._erro(
                f"'{nome}' espera {len(tipos_esp)} argumento(s), recebeu {len(reais)}",
                linha
            )
            return  # não siga para check de tipos

        # --- 2. Tipagem ---
        for i, (t_real, t_esp) in enumerate(zip(reais, tipos_esp), start=1):
            if not self._compat(t_esp, t_real):
                self.tabela._erro(
                    f"Argumento {i} de '{nome}' deve ser '{t_esp}', não '{t_real}'",
                    linha
                )
