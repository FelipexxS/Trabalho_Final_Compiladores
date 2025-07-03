# -----------------------------------------------------------------
# turtlescript_semantic_v2.py – Análise semântica estendida
# para TurtleScript com condicionais, laços e funções.
# -----------------------------------------------------------------
from __future__ import annotations

# =================================================================
# 1. Definições básicas e Tabela de Símbolos Aprimorada
# =================================================================

class SemanticError(Exception):
    """Exceção usada para sinalizar erros semânticos graves."""
    pass


class EntradaTabelaSimbolos:
    """
    Registro de um símbolo (variável ou função) na tabela.
    NOVO: Adicionamos 'categoria' e campos para metadados da função.
    """
    def __init__(self, nome: str, tipo: str, categoria: str = "var", *,
                 tipos_params: list[str] | None = None, tipo_retorno: str | None = None):
        self.nome = nome
        self.tipo = tipo  # Para vars: tipo da var; Para funcs: nome da func
        self.categoria = categoria  # 'var' ou 'funcao'
        # Metadados específicos para funções
        self.tipos_params = tipos_params
        self.tipo_retorno = tipo_retorno

    def __repr__(self) -> str:
        if self.categoria == "funcao":
            return f"Funcao({self.nome}, params={self.tipos_params}, ret={self.tipo_retorno})"
        return f"Variavel({self.nome!r}, {self.tipo!r})"


class TabelaDeSimbolos:
    """Implementa uma pilha de escopos (lista de dicionários)."""
    def __init__(self):
        self._escopos: list[dict[str, EntradaTabelaSimbolos]] = [{}]  # escopo global
        self.erros: list[str] = []

    def abrir_escopo(self) -> None:
        self._escopos.append({})

    def fechar_escopo(self) -> None:
        self._escopos.pop()

    def declarar_var(self, nome: str, tipo: str, linha: int) -> None:
        """Declara uma variável no escopo atual."""
        escopo_atual = self._escopos[-1]
        if nome in escopo_atual:
            self._erro(f"Símbolo '{nome}' já declarado neste escopo", linha)
            return
        escopo_atual[nome] = EntradaTabelaSimbolos(nome, tipo, categoria="var")

    def declarar_funcao(self, nome: str, tipos_params: list[str], tipo_retorno: str, linha: int) -> None:
        """Declara uma função no escopo atual."""
        escopo_atual = self._escopos[-1]
        if nome in escopo_atual:
            self._erro(f"Símbolo '{nome}' já declarado neste escopo", linha)
            return
        escopo_atual[nome] = EntradaTabelaSimbolos(
            nome, nome, "funcao", tipos_params=tipos_params, tipo_retorno=tipo_retorno
        )

    def buscar(self, nome: str, linha: int) -> EntradaTabelaSimbolos | None:
        """Busca um símbolo (var ou func) do escopo mais interno ao mais externo."""
        for escopo in reversed(self._escopos):
            if nome in escopo:
                return escopo[nome]
        self._erro(f"Símbolo '{nome}' não declarado", linha)
        return None

    def _erro(self, mensagem: str, linha: int) -> None:
        self.erros.append(f"Linha {linha}: {mensagem}")

    def possui_erros(self) -> bool:
        return bool(self.erros)

    def __str__(self) -> str:
        linhas = []
        for i, esc in enumerate(self._escopos):
            prefixo = "<global>" if i == 0 else f"<escopo {i}>"
            for nome, ent in esc.items():
                linhas.append(f"{prefixo:12} {nome}: {ent!r}")
        return "\n".join(linhas) or "(Tabela vazia)"


# =================================================================
# 2. Representação da AST como uma TABELA ÚNICA (sem alterações)
# =================================================================

AST: list[dict] = []

def novo_no(tag: str, filhos: list[int] | None = None, **attrs) -> int:
    idx = len(AST)
    AST.append({"tag": tag, "filhos": filhos or [], **attrs})
    return idx


# =================================================================
# 3. NodeVisitor genérico (sem alterações)
# =================================================================

class NodeVisitor:
    def visit(self, idx: int):
        no = AST[idx]
        metodo = getattr(self, f"visit_{no['tag']}", self.generic_visit)
        return metodo(idx)

    def generic_visit(self, idx: int):
        raise RuntimeError(f"Nó não suportado: {AST[idx]['tag']}")


# =================================================================
# 4. Assinaturas de Comandos Primitivos (estendido)
# =================================================================
ASSINATURAS_PRIMITIVAS: dict[str, tuple[list[str], str | None]] = {
    "avancar": (["inteiro"], None),
    "definir_cor": (["texto"], None),
    "imprimir": (["qualquer"], None), # NOVO: aceita qualquer tipo
}


# =================================================================
# 5. SemanticoVisitor com Novas Funcionalidades
# =================================================================

class SemanticoVisitor(NodeVisitor):
    def __init__(self):
        self.tabela = TabelaDeSimbolos()
        # NOVO: Rastreia a função atual para validar retornos
        self.funcao_atual: EntradaTabelaSimbolos | None = None

    # --- Métodos de visita de Nós ---

    def visit_Bloco(self, idx: int):
        no = AST[idx]
        self.tabela.abrir_escopo()
        for stmt_idx in no.get("filhos", []): # Usar .get para blocos vazios
            self.visit(stmt_idx)
        self.tabela.fechar_escopo()

    def visit_DeclaracaoVar(self, idx: int):
        no = AST[idx]
        tipo = no["tipo"]
        ident = no["ident"]
        linha = no["linha"]
        self.tabela.declarar_var(ident, tipo, linha)
        
        # Se houver uma expressão de inicialização, verifique a compatibilidade
        if no["filhos"]:
            expr_idx = no["filhos"][0]
            tipo_expr = self.visit(expr_idx)
            if not self._compat(tipo, tipo_expr):
                self.tabela._erro(
                    f"Tipo da expressão ('{tipo_expr}') é incompatível com o tipo da variável ('{tipo}')",
                    linha
                )

    def visit_Atribuicao(self, idx: int):
        no = AST[idx]
        linha = no["linha"]
        var_idx, expr_idx = no["filhos"]

        # O lado esquerdo deve ser um identificador válido
        no_var = AST[var_idx]
        if no_var["tag"] != "Identificador":
            self.tabela._erro("O lado esquerdo de uma atribuição deve ser uma variável", linha)
            return

        entrada_var = self.tabela.buscar(no_var["lexema"], linha)
        if entrada_var and entrada_var.categoria != "var":
            self.tabela._erro(f"Não é possível atribuir a '{no_var['lexema']}', que é uma função.", linha)
            return
            
        tipo_lhs = entrada_var.tipo if entrada_var else "indefinido"
        tipo_rhs = self.visit(expr_idx)

        if tipo_lhs != "indefinido" and tipo_rhs != "indefinido":
            if not self._compat(tipo_lhs, tipo_rhs):
                self.tabela._erro(
                    f"Tipos incompatíveis em atribuição: '{tipo_lhs}' ← '{tipo_rhs}'",
                    linha,
                )

    def visit_Identificador(self, idx: int):
        no = AST[idx]
        entrada = self.tabela.buscar(no["lexema"], no["linha"])
        if entrada and entrada.categoria == 'var':
            return entrada.tipo
        # Se for uma função usada como valor, é um erro (neste ponto)
        elif entrada and entrada.categoria == 'funcao':
             self.tabela._erro(f"Nome de função '{no['lexema']}' usado como variável.", no['linha'])
        return "indefinido"
        
    def visit_Literal(self, idx: int):
        # NOVO: Para literais como 5, "olá", verdadeiro
        return AST[idx]["tipo"]
        
    def visit_ExprBinaria(self, idx: int):
        # NOVO: Para expressões como a + b
        no = AST[idx]
        op, linha = no["op"], no["linha"]
        lhs_idx, rhs_idx = no["filhos"]

        tipo_lhs = self.visit(lhs_idx)
        tipo_rhs = self.visit(rhs_idx)

        if "indefinido" in (tipo_lhs, tipo_rhs):
            return "indefinido"

        # Regras de tipo para operadores
        if op in ('+', '-', '*', '/'): # Operadores aritméticos
            if not (self._compat("real", tipo_lhs) and self._compat("real", tipo_rhs)):
                self.tabela._erro(f"Operador '{op}' não suporta os tipos '{tipo_lhs}' e '{tipo_rhs}'", linha)
                return "indefinido"
            # Promoção de tipo: se um for real, o resultado é real
            return "real" if "real" in (tipo_lhs, tipo_rhs) else "inteiro"
        
        if op in ('>', '<', '>=', '<='): # Operadores relacionais
            if not (self._compat("real", tipo_lhs) and self._compat("real", tipo_rhs)):
                self.tabela._erro(f"Operador '{op}' não suporta os tipos '{tipo_lhs}' e '{tipo_rhs}'", linha)
                return "indefinido"
            return "booleano"

        if op in ('==', '!='): # Operadores de igualdade
            if not self._compat(tipo_lhs, tipo_rhs) and not self._compat(tipo_rhs, tipo_lhs):
                 self.tabela._erro(f"Comparação de igualdade entre tipos incompatíveis: '{tipo_lhs}' e '{tipo_rhs}'", linha)
                 return "indefinido"
            return "booleano"
        
        return "indefinido" # Operador desconhecido

    def visit_If(self, idx: int):
        # NOVO: Para o comando se-senao
        no = AST[idx]
        cond_idx, then_idx = no["filhos"][:2]
        
        tipo_cond = self.visit(cond_idx)
        if tipo_cond != "booleano" and tipo_cond != "indefinido":
            self.tabela._erro(f"Condição do 'se' deve ser do tipo 'booleano', mas é '{tipo_cond}'", no["linha"])

        self.visit(then_idx) # Visita o bloco 'then'

        if len(no["filhos"]) > 2: # Existe um bloco 'else'
            else_idx = no["filhos"][2]
            self.visit(else_idx)

    def visit_Enquanto(self, idx: int):
        # NOVO: Para o laço de repetição 'enquanto'
        no = AST[idx]
        cond_idx, corpo_idx = no["filhos"]

        tipo_cond = self.visit(cond_idx)
        if tipo_cond != "booleano" and tipo_cond != "indefinido":
            self.tabela._erro(f"Condição do 'enquanto' deve ser do tipo 'booleano', mas é '{tipo_cond}'", no["linha"])

        self.visit(corpo_idx) # Visita o corpo do laço

    # --- NOVO ---
    def visit_Repita(self, idx: int):
        """Valida o laço de repetição 'repita'."""
        no = AST[idx]
        vezes_idx, corpo_idx = no["filhos"]
        linha = no["linha"]

        # Regra: O número de repetições deve ser um LITERAL do tipo INTEIRO.
        no_vezes = AST[vezes_idx]
        if no_vezes.get("tag") != "Literal" or no_vezes.get("tipo") != "inteiro":
            self.tabela._erro(
                "O número de repetições no comando 'repita' deve ser um literal do tipo inteiro (ex: 5), não uma variável ou expressão.",
                linha
            )
        
        # Visita o corpo do laço
        self.visit(corpo_idx)

    def visit_FuncaoDecl(self, idx: int):
        # NOVO: Para declaração de funções
        no = AST[idx]
        nome, tipo_retorno, linha = no["nome"], no["tipo_retorno"], no["linha"]
        
        # Extrai os tipos dos parâmetros
        params_info = no.get("params", []) # Lista de tuplas (nome, tipo)
        tipos_params = [p[1] for p in params_info]
        
        # Declara a função no escopo atual
        self.tabela.declarar_funcao(nome, tipos_params, tipo_retorno, linha)
        
        # Guarda a função atual para validar os 'retorne'
        funcao_anterior = self.funcao_atual
        self.funcao_atual = self.tabela.buscar(nome, linha)

        # Abre novo escopo para o corpo da função
        self.tabela.abrir_escopo()
        
        # Declara os parâmetros como variáveis locais
        for nome_param, tipo_param in params_info:
            self.tabela.declarar_var(nome_param, tipo_param, linha)
        
        # Visita o corpo da função
        corpo_idx = no["filhos"][0]
        self.visit(corpo_idx)
        
        # Restaura o contexto
        self.tabela.fechar_escopo()
        self.funcao_atual = funcao_anterior

    def visit_FuncaoCall(self, idx: int):
        # NOVO: Para chamada de funções
        no = AST[idx]
        nome, linha = no["nome"], no["linha"]
        
        # Checa se é um comando primitivo
        if nome in ASSINATURAS_PRIMITIVAS:
            assinatura = ASSINATURAS_PRIMITIVAS[nome]
            tipos_args = [self.visit(i) for i in no["filhos"]]
            self._checar_assinatura(nome, tipos_args, assinatura, linha)
            return assinatura[1] # Retorna o tipo de retorno do primitivo (geralmente None)

        # Senão, busca a função na tabela de símbolos
        entrada = self.tabela.buscar(nome, linha)
        if not entrada:
            return "indefinido" # Erro já foi reportado por 'buscar'
        if entrada.categoria != "funcao":
            self.tabela._erro(f"'{nome}' não é uma função, não pode ser chamado", linha)
            return "indefinido"
        
        tipos_args = [self.visit(i) for i in no["filhos"]]
        assinatura = (entrada.tipos_params, entrada.tipo_retorno)
        self._checar_assinatura(nome, tipos_args, assinatura, linha)
        
        return entrada.tipo_retorno

    def visit_Retorno(self, idx: int):
        # NOVO: Para o comando 'retorne'
        no = AST[idx]
        linha = no["linha"]

        if not self.funcao_atual:
            self.tabela._erro("Comando 'retorne' só pode ser usado dentro de uma função", linha)
            return
        
        tipo_retorno_esperado = self.funcao_atual.tipo_retorno
        
        if no["filhos"]: # retorne <expressao>
            expr_idx = no["filhos"][0]
            tipo_retorno_real = self.visit(expr_idx)

            if tipo_retorno_esperado == "vazio":
                 self.tabela._erro(f"Função com retorno 'vazio' não pode retornar um valor", linha)
            elif not self._compat(tipo_retorno_esperado, tipo_retorno_real):
                self.tabela._erro(f"Tipo de retorno incompatível. Esperado '{tipo_retorno_esperado}', recebido '{tipo_retorno_real}'", linha)
        else: # retorne;
            if tipo_retorno_esperado != "vazio":
                self.tabela._erro(f"Retorno vazio em função que espera '{tipo_retorno_esperado}'", linha)

    # --- Métodos Auxiliares ---
    
    def _compat(self, tipo_lhs: str, tipo_rhs: str) -> bool:
        """Regra de compatibilidade de tipos."""
        if tipo_lhs == "qualquer" or tipo_rhs == "qualquer":
            return True
        if tipo_lhs == tipo_rhs:
            return True
        # Permite atribuir inteiro a real
        return tipo_lhs == "real" and tipo_rhs == "inteiro"

    def _checar_assinatura(self, nome: str, reais: list[str], esperados: tuple, linha: int):
        """Valida argumentos de uma chamada de função."""
        tipos_esp, _ = esperados
        # Aridade (número de argumentos)
        if len(reais) != len(tipos_esp):
            self.tabela._erro(
                f"Função '{nome}' espera {len(tipos_esp)} argumento(s), mas recebeu {len(reais)}",
                linha,
            )
            return
        # Tipos
        for i, (t_real, t_esp) in enumerate(zip(reais, tipos_esp), 1):
            if not self._compat(t_esp, t_real) and "indefinido" not in (t_real, t_esp):
                self.tabela._erro(
                    f"Argumento {i} de '{nome}': esperado '{t_esp}', mas recebeu '{t_real}'",
                    linha,
                )

# =================================================================
# 6. Exemplo de Uso Abrangente
# =================================================================

def _exemplo_demo_avancado():
    """Constrói uma AST complexa para demonstrar as novas funcionalidades."""
    AST.clear()

    # --- Código fonte de exemplo para guiar a construção da AST ---
    #
    # funcao inteiro fatorial(inteiro n) {
    #     se (n < 2) {
    #         retorne 1;
    #     }
    #     retorne n * fatorial(n - 1);
    # }
    #
    # imprimir(fatorial(5));
    #
    # // --- Erros semânticos intencionais ---
    #
    # inteiro x = "texto"; // Erro: tipo incompatível na inicialização
    #
    # funcao texto saudacao(real nome) { // "nome" deveria ser texto
    #     retorne 123; // Erro: tipo de retorno incorreto
    # }
    #
    # fatorial("cinco"); // Erro: tipo de argumento incorreto
    # y = 10;           // Erro: 'y' não declarado
    #
    # repita "dez" vezes {} // Erro: 'repita' com literal não inteiro
    # var inteiro: i = 5;
    # repita i vezes {} // Erro: 'repita' com variável
    
    # --- Construção da AST para a função fatorial ---
    # Corpo da função: se (n < 2) { retorne 1; } retorne n * fatorial(n - 1);
    n_ident1 = novo_no("Identificador", lexema="n", linha=2)
    lit_2 = novo_no("Literal", tipo="inteiro", valor=2, linha=2)
    cond_if = novo_no("ExprBinaria", op='<', filhos=[n_ident1, lit_2], linha=2)
    ret_1 = novo_no("Retorno", filhos=[novo_no("Literal", tipo="inteiro", valor=1, linha=3)], linha=3)
    bloco_if = novo_no("Bloco", filhos=[ret_1])
    no_if = novo_no("If", filhos=[cond_if, bloco_if], linha=2)

    n_ident2 = novo_no("Identificador", lexema="n", linha=5)
    n_ident3 = novo_no("Identificador", lexema="n", linha=5)
    lit_1 = novo_no("Literal", tipo="inteiro", valor=1, linha=5)
    n_minus_1 = novo_no("ExprBinaria", op='-', filhos=[n_ident3, lit_1], linha=5)
    chamada_rec = novo_no("FuncaoCall", nome="fatorial", filhos=[n_minus_1], linha=5)
    expr_mult = novo_no("ExprBinaria", op='*', filhos=[n_ident2, chamada_rec], linha=5)
    ret_final = novo_no("Retorno", filhos=[expr_mult], linha=5)
    
    corpo_fatorial = novo_no("Bloco", filhos=[no_if, ret_final])
    decl_fatorial = novo_no(
        "FuncaoDecl",
        nome="fatorial",
        params=[("n", "inteiro")],
        tipo_retorno="inteiro",
        filhos=[corpo_fatorial],
        linha=1
    )

    # --- Chamada: imprimir(fatorial(5)); ---
    chamada_fatorial5 = novo_no("FuncaoCall", nome="fatorial", filhos=[novo_no("Literal", tipo="inteiro", valor=5, linha=8)], linha=8)
    chamada_imprimir = novo_no("FuncaoCall", nome="imprimir", filhos=[chamada_fatorial5], linha=8)

    # --- Bloco de erros ---
    err_decl_x = novo_no("DeclaracaoVar", tipo="inteiro", ident="x", filhos=[novo_no("Literal", tipo="texto", valor="texto", linha=12)], linha=12)
    err_ret_saudacao = novo_no("Retorno", filhos=[novo_no("Literal", tipo="inteiro", valor=123, linha=15)], linha=15)
    err_corpo_saudacao = novo_no("Bloco", filhos=[err_ret_saudacao])
    err_decl_saudacao = novo_no("FuncaoDecl", nome="saudacao", params=[("nome", "real")], tipo_retorno="texto", filhos=[err_corpo_saudacao], linha=14)
    err_chamada_fatorial = novo_no("FuncaoCall", nome="fatorial", filhos=[novo_no("Literal", tipo="texto", valor="cinco", linha=18)], linha=18)
    err_atrib_y = novo_no("Atribuicao", filhos=[novo_no("Identificador", lexema="y", linha=19), novo_no("Literal", tipo="inteiro", valor=10, linha=19)], linha=19)

    # --- MODIFICADO: Bloco de erros para 'repita' ---
    repita_corpo_vazio = novo_no("Bloco", filhos=[])
    # Erro 1: Usando um literal do tipo 'texto'
    err_repita_tipo_lit = novo_no("Literal", tipo="texto", valor="dez", linha=21)
    err_repita1 = novo_no("Repita", filhos=[err_repita_tipo_lit, repita_corpo_vazio], linha=21)
    
    # Erro 2: Usando uma variável em vez de um literal
    decl_i = novo_no("DeclaracaoVar", tipo="inteiro", ident="i", linha=22)
    ident_i = novo_no("Identificador", lexema="i", linha=23)
    err_repita2 = novo_no("Repita", filhos=[ident_i, repita_corpo_vazio], linha=23)
    
    # --- MODIFICADO: Programa Principal (AST raiz) ---
    programa = novo_no("Bloco", filhos=[
        decl_fatorial, 
        chamada_imprimir,
        err_decl_x,
        err_decl_saudacao,
        err_chamada_fatorial,
        err_atrib_y,
        err_repita1, # Erro de 'repita' com tipo errado
        decl_i,      # Declaração de 'i' para o próximo erro
        err_repita2, # Erro de 'repita' com variável
    ])

    # --- Executar a análise ---
    sem = SemanticoVisitor()
    sem.visit(programa)

    print("--- ANÁLISE SEMÂNTICA CONCLUÍDA ---")
    if sem.tabela.possui_erros():
        print("\nErros encontrados:")
        for erro in sem.tabela.erros:
            print(f"  - {erro}")
    else:
        print("\nSem erros semânticos encontrados!")
    
    print("\nEstado final da Tabela de Símbolos (escopo global):")
    print(sem.tabela)


if __name__ == "__main__":
    _exemplo_demo_avancado()
