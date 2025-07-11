"""
# semantic.py  – adicional para detectar 3  erros ainda não detecáveis:

- Operandos aritméticos incompatíveis (+ - * /)
- Operandos relacionais incompatíveis e garante que o resultado de uma comparação é logico
- Operador desconhecido (qualquer símbolo fora dos conjuntos permitidos)
(as demais regras já existentes foram mantidas)

- adicional para Varredura em escopo de Funções e verificação de retornos
- Escopo local para função (SymbolTable.abrir_escopo_local/fechar_escopo_local).
- Symbol agora distingue categorias e armazena assinatura de função.
______Visitors novos
______visit_FuncDecl — registra função, abre escopo local, exige retorno.
______visit_Retorno — valida tipo e contexto.
______visit_Call — verifica aridade e tipos dos argumentos, devolve tipo de retorno.
______Expressões refatoradas para validar operadores aritméticos/relacionais e apontar desconhecidos.
# --------------------------------------------------------------
"""
class SemanticError(Exception):
    """Exceção levantada pelo analisador semântico."""
    def __init__(self, msg, line=None):
        prefix = "Erro Semântico"
        if line:
            prefix += f" (linha {line})"
        super().__init__(f"{prefix}: {msg}")


# =================================================================
# 1. Tabela de símbolos (escopo global + escopo local de função)
# =================================================================
class Symbol:
    def __init__(
        self,
        name: str,
        category: str,            # "var" | "funcao"
        tipo: str | None = None,  # para variáveis
        tipos_params: list[str] | None = None,
        tipo_retorno: str | None = None,
    ):
        self.name = name
        self.category = category
        self.tipo = tipo
        self.tipos_params = tipos_params or []
        self.tipo_retorno = tipo_retorno
        self.houve_retorno = False


class SymbolTable:
    """Dois níveis apenas: global e local‐de‐função."""
    def __init__(self):
        self.global_scope: dict[str, Symbol] = {}
        self.local_scope: dict[str, Symbol] | None = None  # None quando fora de função

    # -------- lookup / define --------
    def _current(self):
        return self.local_scope if self.local_scope is not None else self.global_scope

    def define(self, sym: Symbol, line=None):
        scope = self._current()
        if sym.name in scope:
            raise SemanticError(f"Símbolo '{sym.name}' já declarado neste escopo.", line)
        scope[sym.name] = sym

    def lookup(self, name: str, line=None) -> Symbol:
        if self.local_scope and name in self.local_scope:
            return self.local_scope[name]
        if name in self.global_scope:
            return self.global_scope[name]
        raise SemanticError(f"Símbolo '{name}' não declarado.", line)

    # -------- controle de escopo local --------
    def abrir_escopo_local(self):
        self.local_scope = {}

    def fechar_escopo_local(self):
        self.local_scope = None


# =================================================================
# 2. Analisador
# =================================================================
class SemanticAnalyzer:
    ARIT_OPS = {"+", "-", "*", "/"}
    REL_OPS  = {"==", "!=", ">", "<", ">=", "<="}

    def __init__(self, ast_tree):
        self.ast = ast_tree
        self.table = SymbolTable()
        self.funcao_atual: Symbol | None = None  # aponta símbolo da função corrente

    # ---------------- API ----------------
    def analyze(self):
        self.visit(self.ast)

    # ---------------- visitor dispatcher ----------------
    def visit(self, node):
        meth = getattr(self, f"visit_{node['tag']}", self.generic_visit)
        return meth(node)

    def generic_visit(self, node):
        for child in node.get("filhos", []):
            self.visit(child)

    # ====================================================
    # 3. Helpers de tipagem
    # ====================================================
    def _compat_numeric(self, t1, t2):
        if t1 == t2 == "inteiro":
            return "inteiro"
        if {t1, t2} <= {"inteiro", "real"}:
            return "real"
        raise SemanticError(f"Operandos numéricos incompatíveis: '{t1}' e '{t2}'")

    # ====================================================
    # 4. Declaração de variável
    # ====================================================
    def visit_DECL(self, node):
        tipo = node["filhos"][1]["filhos"][0]["tag"]       # TYPE
        ident_node = node["filhos"][3]["filhos"][0]
        nome = ident_node.get("valor", ident_node["tag"])
        self.table.define(Symbol(nome, "var", tipo), node["linha"])

    # ====================================================
    # 5. Funções
    # ====================================================
    def visit_FuncDecl(self, node):
        """
        Nó esperado:
          tag = 'FuncDecl'
          campos: nome, tipo_retorno, params (lista de (nome,tipo)), filhos = corpo (CMDS)
        """
        nome = node["nome"]
        tipo_ret = node["tipo_retorno"]
        tipos_params = [t for _n, t in node["params"]]

        # declara na tabela global
        self.table.define(
            Symbol(nome, "funcao", tipos_params=tipos_params, tipo_retorno=tipo_ret),
            node["linha"],
        )
        func_sym = self.table.lookup(nome)

        # novo contexto
        prev_func = self.funcao_atual
        self.funcao_atual = func_sym
        self.table.abrir_escopo_local()

        # parâmetros como variáveis locais
        for (param_nome, param_tipo) in node["params"]:
            self.table.define(Symbol(param_nome, "var", param_tipo), node["linha"])

        # visita corpo
        for cmd in node["filhos"]:
            self.visit(cmd)

        # garante retorno presente
        if not func_sym.houve_retorno and tipo_ret != "void":
            raise SemanticError(
                f"Função '{nome}' termina sem instrução 'retorne'.", node["linha"]
            )

        # restaura contexto
        self.table.fechar_escopo_local()
        self.funcao_atual = prev_func

    def visit_Retorno(self, node):
        if self.funcao_atual is None:
            raise SemanticError("'retorne' fora de uma função.", node["linha"])

        expr_type = self.visit(node["filhos"][1])   # REL
        esperado = self.funcao_atual.tipo_retorno
        if esperado == "real" and expr_type == "inteiro":
            pass
        elif expr_type != esperado:
            raise SemanticError(
                f"'retorne' devolve '{expr_type}', mas a função espera '{esperado}'.",
                node["linha"],
            )
        self.funcao_atual.houve_retorno = True

    # chamadas: nó 'Call' => filhos [ID, args*]
    def visit_Call(self, node):
        nome = node["ident"]
        sym = self.table.lookup(nome, node["linha"])
        if sym.category != "funcao":
            raise SemanticError(f"'{nome}' não é função.", node["linha"])

        if len(node["args"]) != len(sym.tipos_params):
            raise SemanticError(
                f"Função '{nome}' espera {len(sym.tipos_params)} argumento(s), "
                f"mas recebeu {len(node['args'])}.", node["linha"]
            )
        for arg_node, esperado in zip(node["args"], sym.tipos_params):
            tipo_arg = self.visit(arg_node)
            if esperado == "real" and tipo_arg == "inteiro":
                continue
            if tipo_arg != esperado:
                raise SemanticError(
                    f"Argumento de '{nome}' deve ser '{esperado}', recebeu '{tipo_arg}'.",
                    node["linha"],
                )
        return sym.tipo_retorno

    # ====================================================
    # 6. Atribuição
    # ====================================================
    def visit_ATR(self, node):
        ident = node["filhos"][0]["filhos"][0]["valor"]
        sym = self.table.lookup(ident, node["linha"])
        expr_type = self.visit(node["filhos"][2])
        if sym.tipo == "real" and expr_type == "inteiro":
            return
        if sym.tipo != expr_type:
            raise SemanticError(
                f"Não pode atribuir '{expr_type}' a variável '{ident}' do tipo '{sym.tipo}'.",
                node["linha"],
            )

    # ====================================================
    # 7. Expressões (REL, ADD, MUL, FACTOR)
    # ====================================================
    def visit_REL(self, node):
        left = self.visit(node["filhos"][0])
        if len(node["filhos"]) == 1:
            return left
        op = node["filhos"][1]["filhos"][0]["tag"]
        if op not in self.REL_OPS:
            raise SemanticError(f"Operador relacional desconhecido '{op}'.", node["linha"])
        right = self.visit(node["filhos"][1]["filhos"][1])
        # compatibilidade
        if (left == right == "texto") or \
           (left in {"inteiro", "real"} and right in {"inteiro", "real"}):
            return "logico"
        raise SemanticError(
            f"Comparação entre tipos incompatíveis '{left}' e '{right}'.", node["linha"]
        )

    def visit_ADD(self, node):
        tipo = self.visit(node["filhos"][0])
        idx = 1
        while idx < len(node["filhos"]):
            op = node["filhos"][idx]["tag"]
            if op not in self.ARIT_OPS:
                raise SemanticError(f"Operador aritmético desconhecido '{op}'.", node["linha"])
            tipo2 = self.visit(node["filhos"][idx + 1])
            tipo = self._compat_numeric(tipo, tipo2)
            idx += 2
        return tipo

    def visit_MUL(self, node):
        tipo = self.visit(node["filhos"][0])
        idx = 1
        while idx < len(node["filhos"]):
            op = node["filhos"][idx]["tag"]
            if op not in {"*", "/"}:
                raise SemanticError(f"Operador aritmético desconhecido '{op}'.", node["linha"])
            tipo2 = self.visit(node["filhos"][idx + 1])
            tipo = self._compat_numeric(tipo, tipo2)
            idx += 2
        return tipo

    def visit_FACTOR(self, node):
        child = node["filhos"][0]
        tag = child["tag"]
        if tag == "NUM":
            num_tag = child["filhos"][0]["tag"]
            return "inteiro" if num_tag == "numero_inteiro" else "real"
        if tag == "TEXT":
            return "texto"
        if tag == "BOOL":
            return "logico"
        if tag == "ID":
            nome = child["filhos"][0]["valor"]
            return self.table.lookup(nome, child["linha"]).tipo
        if tag == "(":
            return self.visit(child["filhos"][1])  # expressão dentro de parênteses
        if tag == "Call":
            return self.visit_Call(child)
        raise SemanticError(f"Fator inesperado na expressão: {tag}", node["linha"])


    def visit_AV(self, node):
        """Verifica o comando 'avancar'."""
        arg_type = self.visit(node['filhos'][1]) # Visita o nó REL
        if arg_type not in ['inteiro', 'real']:
            raise SemanticError(f"O comando 'avancar' espera um argumento numérico (inteiro ou real), mas recebeu '{arg_type}'.", node['linha'])
            
    def visit_definir_cor(self, node):
        """Verifica o comando 'definir_cor'."""
        arg_type = self.visit(node['filhos'][1]) # Visita o nó REL
        if arg_type != 'texto':
            raise SemanticError(f"O comando 'definir_cor' espera um argumento do tipo texto, mas recebeu '{arg_type}'.", node['linha'])
            
    # Adicione métodos 'visit_*' para outros comandos (REC, GD, GE, etc.) seguindo o mesmo padrão.
    def visit_REC(self, node):
        arg_type = self.visit(node['filhos'][1])
        if arg_type not in ['inteiro', 'real']:
            raise SemanticError(f"O comando 'recuar' espera um argumento numérico, mas recebeu '{arg_type}'.", node['linha'])

    def visit_SE(self, node):
        """Verifica a condição de um comando 'se'."""
        condition_type = self.visit(node['filhos'][1]) # Nó REL
        if condition_type != 'logico':
            raise SemanticError(f"A condição do 'se' deve ser do tipo logico, mas é '{condition_type}'.", node['linha'])
        # Visita os blocos 'entao' e 'senao'
        self.visit(node['filhos'][3]) # Nó CMDS (entao)
        self.visit(node['filhos'][4]) # Nó SE_CONT (senao/fim_se)
        
    def visit_ENQ(self, node):
        """Verifica a condição de um comando 'enquanto'."""
        condition_type = self.visit(node['filhos'][1]) # Nó REL
        if condition_type != 'logico':
            raise SemanticError(f"A condição do 'enquanto' deve ser do tipo logico, mas é '{condition_type}'.", node['linha'])
        self.visit(node['filhos'][3]) # Nó CMDS (faca)
        
    def visit_REP(self, node):
        """Verifica o contador de um comando 'repita'."""
        counter_type = self.visit(node['filhos'][1]) # Nó REL
        if counter_type != 'inteiro':
            raise SemanticError(f"O contador do 'repita' deve ser do tipo inteiro, mas é '{counter_type}'.", node['linha'])
        self.visit(node['filhos'][3]) # Nó CMDS
    
    def generic_visit(self, node):
        """Método para visitar nós que não têm uma regra específica."""
        if 'filhos' in node:
            for child in node['filhos']:
                self.visit(child)
    
    # Adicione este método dentro da classe SemanticAnalyzer em semantic.py

    def visit_GE(self, node):
        """Verifica o comando 'girar_esquerda'."""
        # O nó GE tem como filhos [girar_esquerda, REL, ;]
        # O argumento está no segundo filho (índice 1)
        arg_type = self.visit(node['filhos'][1]) # Visita o nó REL para obter seu tipo
        
        if arg_type not in ['inteiro', 'real']:
            raise SemanticError(
                f"O comando 'girar_esquerda' espera um argumento numérico (inteiro ou real), mas recebeu '{arg_type}'.", 
                node['linha']
            )
    
    # Adicione também estes métodos ao semantic.py

    def visit_GD(self, node):
        """Verifica o comando 'girar_direita'."""
        arg_type = self.visit(node['filhos'][1])
        if arg_type not in ['inteiro', 'real']:
            raise SemanticError(
                f"O comando 'girar_direita' espera um argumento numérico (inteiro ou real), mas recebeu '{arg_type}'.", 
                node['linha']
            )

    def visit_DE(self, node):
        """Verifica o comando 'definir_espessura'."""
        arg_type = self.visit(node['filhos'][1])
        if arg_type not in ['inteiro', 'real']:
            raise SemanticError(
                f"O comando 'definir_espessura' espera um argumento numérico (inteiro ou real), mas recebeu '{arg_type}'.", 
                node['linha']
            )
    
    # Adicione estes métodos à classe SemanticAnalyzer em semantic.py

    def visit_DC(self, node):
        """Verifica o comando 'definir_cor'."""
        # Gramática: DC -> definir_cor REL ;
        arg_type = self.visit(node['filhos'][1]) # Visita o nó REL
        if arg_type != 'texto':
            raise SemanticError(
                f"O comando 'definir_cor' espera um argumento do tipo texto, mas recebeu '{arg_type}'.", 
                node['linha']
            )

    def visit_CDF(self, node):
        """Verifica o comando 'cor_de_fundo'."""
        # Gramática: CDF -> cor_de_fundo REL ;
        arg_type = self.visit(node['filhos'][1])
        if arg_type != 'texto':
            raise SemanticError(
                f"O comando 'cor_de_fundo' espera um argumento do tipo texto, mas recebeu '{arg_type}'.", 
                node['linha']
            )

    def visit_DSQ(self, node):
        """Verifica o comando 'desenhar_quadrado'."""
        # Gramática: DSQ -> desenhar_quadrado REL ;
        arg_type = self.visit(node['filhos'][1])
        if arg_type not in ['inteiro', 'real']:
            raise SemanticError(
                f"O comando 'desenhar_quadrado' espera um argumento numérico, mas recebeu '{arg_type}'.", 
                node['linha']
            )

    def visit_DSC(self, node):
        """Verifica o comando 'desenhar_circulo'."""
        # Gramática: DSC -> desenhar_circulo REL ;
        arg_type = self.visit(node['filhos'][1])
        if arg_type not in ['inteiro', 'real']:
            raise SemanticError(
                f"O comando 'desenhar_circulo' espera um argumento numérico, mas recebeu '{arg_type}'.", 
                node['linha']
            )

    def visit_IRP(self, node):
        """Verifica o comando 'ir_para', que possui dois argumentos."""
        # Gramática: IRP -> ir_para REL REL ;
        # Os filhos do nó são [ir_para, REL, REL, ;]
        arg1_type = self.visit(node['filhos'][1]) # Primeiro argumento REL
        arg2_type = self.visit(node['filhos'][2]) # Segundo argumento REL

        if arg1_type not in ['inteiro', 'real']:
            raise SemanticError(
                f"O primeiro argumento do comando 'ir_para' (coordenada x) deve ser numérico, mas recebeu '{arg1_type}'.",
                node['linha']
            )
        
        if arg2_type not in ['inteiro', 'real']:
            raise SemanticError(
                f"O segundo argumento do comando 'ir_para' (coordenada y) deve ser numérico, mas recebeu '{arg2_type}'.",
                node['linha']
            )
