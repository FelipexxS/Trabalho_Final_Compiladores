"""turtlescript_semantic_ast_dict.py
--------------------------------------------------
Versão reformulada do analisador semântico para TurtleScript.
Agora ele recebe, do parser, uma AST **inteiramente** formada por
objetos‐dicionário aninhados (sem índices numéricos globais).
Cada nó possui:
    tag      – string com o tipo do nó (e.g. "Identificador")
    filhos   – *lista* de nós‑filhos (pode estar ausente ou vazia)
Além disso, cada subtipo traz campos específicos (lexema, linha, etc.)
 
O núcleo de verificação semântica permanece o mesmo, mas todo o
código foi refatorado para operar diretamente sobre esses dicionários.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional

# ================================================================
# 1. Exceções e Tabela de Símbolos
# ================================================================

class SemanticError(Exception):
    """Exceção lançada para erros semânticos graves (interrompe compilação)."""
    pass


class EntradaTabelaSimbolos:
    """Registro de variável ou função na tabela de símbolos."""

    def __init__(
        self,
        nome: str,
        tipo: str,
        categoria: str = "var",  # "var" | "funcao"
        *,
        tipos_params: Optional[List[str]] = None,
        tipo_retorno: Optional[str] = None,
    ) -> None:
        self.nome = nome
        self.tipo = tipo
        self.categoria = categoria
        self.tipos_params = tipos_params or []
        self.tipo_retorno = tipo_retorno

    # ------------------------------------------------------------
    # Representação amigável para depuração
    # ------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        if self.categoria == "funcao":
            return f"Funcao({self.nome}, params={self.tipos_params}, ret={self.tipo_retorno})"
        return f"Variavel({self.nome!r}, {self.tipo!r})"


class TabelaDeSimbolos:
    """Pilha de escopos implementada como lista de dicionários."""

    def __init__(self) -> None:
        self._escopos: List[Dict[str, EntradaTabelaSimbolos]] = [{}]  # escopo global
        self.erros: List[str] = []

    # ------------------------------------------------------------
    # Operações sobre escopos
    # ------------------------------------------------------------
    def abrir_escopo(self) -> None:
        self._escopos.append({})

    def fechar_escopo(self) -> None:
        self._escopos.pop()

    # ------------------------------------------------------------
    # Declaração de símbolos
    # ------------------------------------------------------------
    def _declarar(self, nome: str, entrada: EntradaTabelaSimbolos, linha: int) -> None:
        escopo_atual = self._escopos[-1]
        if nome in escopo_atual:
            self._erro(f"Símbolo '{nome}' já declarado neste escopo", linha)
            return
        escopo_atual[nome] = entrada

    def declarar_var(self, nome: str, tipo: str, linha: int) -> None:
        self._declarar(nome, EntradaTabelaSimbolos(nome, tipo, "var"), linha)

    def declarar_funcao(
        self,
        nome: str,
        tipos_params: List[str],
        tipo_retorno: str,
        linha: int,
    ) -> None:
        self._declarar(
            nome,
            EntradaTabelaSimbolos(
                nome,
                nome,  # campo "tipo" não é usado para funções
                "funcao",
                tipos_params=tipos_params,
                tipo_retorno=tipo_retorno,
            ),
            linha,
        )

    # ------------------------------------------------------------
    # Busca de símbolos
    # ------------------------------------------------------------
    def buscar(self, nome: str, linha: int) -> Optional[EntradaTabelaSimbolos]:
        for escopo in reversed(self._escopos):
            if nome in escopo:
                return escopo[nome]
        self._erro(f"Símbolo '{nome}' não declarado", linha)
        return None

    # ------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------
    def _erro(self, mensagem: str, linha: int) -> None:
        self.erros.append(f"Linha {linha}: {mensagem}")

    def possui_erros(self) -> bool:
        return bool(self.erros)

    def __str__(self) -> str:  # pragma: no cover
        linhas: List[str] = []
        for i, esc in enumerate(self._escopos):
            prefixo = "<global>" if i == 0 else f"<escopo {i}>"
            for nome, ent in esc.items():
                linhas.append(f"{prefixo:12} {nome}: {ent!r}")
        return "\n".join(linhas) or "(Tabela vazia)"


# ================================================================
# 2. NodeVisitor genérico (agora recebe o próprio nó‑dicionário)
# ================================================================

class NodeVisitor:
    """Classe base para percorrer recursivamente uma AST de dicionários."""

    def visit(self, node: Dict[str, Any]):
        metodo = getattr(self, f"visit_{node['tag']}", self.generic_visit)
        return metodo(node)

    def generic_visit(self, node: Dict[str, Any]):  # pragma: no cover
        raise RuntimeError(f"Nó não suportado: {node['tag']}")


# ================================================================
# 3. Assinaturas de comandos primitivos (inalterado)
# ================================================================
ASSINATURAS_PRIMITIVAS: Dict[str, Tuple[List[str], Optional[str]]] = {
    "avancar": (["inteiro"], None),
    "definir_cor": (["texto"], None),
    "imprimir": (["qualquer"], None),  # aceita qualquer tipo
}


# ================================================================
# 4. SemanticoVisitor – varredura e verificação
# ================================================================

class SemanticoVisitor(NodeVisitor):
    """Percorre a AST e acumula erros semânticos."""

    def __init__(self):
        self.tabela = TabelaDeSimbolos()
        self.funcao_atual: Optional[EntradaTabelaSimbolos] = None  # p/ validar 'retorne'

    # ------------------------------------------------------------
    # Blocos e escopos
    # ------------------------------------------------------------
    def visit_Bloco(self, node):
        self.tabela.abrir_escopo()
        for filho in node.get("filhos", []):
            self.visit(filho)
        self.tabela.fechar_escopo()

    # ------------------------------------------------------------
    # Declarações
    # ------------------------------------------------------------
    def visit_DeclaracaoVar(self, node):
        tipo = node["tipo"]
        ident = node["ident"]
        linha = node["linha"]
        self.tabela.declarar_var(ident, tipo, linha)

        # Inicialização opcional
        if node.get("filhos"):
            expr_node = node["filhos"][0]
            tipo_expr = self.visit(expr_node)
            if not self._compat(tipo, tipo_expr):
                self.tabela._erro(
                    f"Tipo da expressão ('{tipo_expr}') é incompatível com o tipo da variável ('{tipo}')",
                    linha,
                )

    def visit_FuncaoDecl(self, node):
        nome, tipo_retorno, linha = node["nome"], node["tipo_retorno"], node["linha"]
        params_info: List[Tuple[str, str]] = node.get("params", [])
        tipos_params = [t for _n, t in params_info]

        # Declara a função no escopo atual
        self.tabela.declarar_funcao(nome, tipos_params, tipo_retorno, linha)

        # Prepara contexto para corpo
        funcao_anterior = self.funcao_atual
        self.funcao_atual = self.tabela.buscar(nome, linha)

        self.tabela.abrir_escopo()
        for nome_param, tipo_param in params_info:
            self.tabela.declarar_var(nome_param, tipo_param, linha)

        self.visit(node["filhos"][0])  # corpo da função

        self.tabela.fechar_escopo()
        self.funcao_atual = funcao_anterior

    # ------------------------------------------------------------
    # Atribuição e uso de identificadores
    # ------------------------------------------------------------
    def visit_Atribuicao(self, node):
        linha = node["linha"]
        var_node, expr_node = node["filhos"]

        if var_node["tag"] != "Identificador":
            self.tabela._erro("O lado esquerdo de uma atribuição deve ser uma variável", linha)
            return

        entrada_var = self.tabela.buscar(var_node["lexema"], linha)
        if entrada_var and entrada_var.categoria != "var":
            self.tabela._erro(
                f"Não é possível atribuir a '{var_node['lexema']}', que é uma função.", linha
            )
            return

        tipo_lhs = entrada_var.tipo if entrada_var else "indefinido"
        tipo_rhs = self.visit(expr_node)

        if "indefinido" not in (tipo_lhs, tipo_rhs) and not self._compat(tipo_lhs, tipo_rhs):
            self.tabela._erro(
                f"Tipos incompatíveis em atribuição: '{tipo_lhs}' ← '{tipo_rhs}'", linha
            )

    def visit_Identificador(self, node):
        entrada = self.tabela.buscar(node["lexema"], node["linha"])
        if not entrada:
            return "indefinido"  # erro já reportado
        if entrada.categoria == "funcao":
            self.tabela._erro(
                f"Nome de função '{node['lexema']}' usado como variável.", node["linha"]
            )
            return "indefinido"
        return entrada.tipo

    # ------------------------------------------------------------
    # Literais e expressões
    # ------------------------------------------------------------
    def visit_Literal(self, node):
        return node["tipo"]

    def visit_ExprBinaria(self, node):
        op, linha = node["op"], node["linha"]
        lhs_node, rhs_node = node["filhos"]
        tipo_lhs = self.visit(lhs_node)
        tipo_rhs = self.visit(rhs_node)

        if "indefinido" in (tipo_lhs, tipo_rhs):
            return "indefinido"

        # ------------------ operadores aritméticos -----------------
        if op in {"+", "-", "*", "/"}:
            if not (self._compat("real", tipo_lhs) and self._compat("real", tipo_rhs)):
                self.tabela._erro(
                    f"Operador '{op}' não suporta os tipos '{tipo_lhs}' e '{tipo_rhs}'", linha
                )
                return "indefinido"
            return "real" if "real" in (tipo_lhs, tipo_rhs) else "inteiro"

        # ------------------ operadores relacionais -----------------
        if op in {">", "<", ">=", "<="}:
            if not (self._compat("real", tipo_lhs) and self._compat("real", tipo_rhs)):
                self.tabela._erro(
                    f"Operador '{op}' não suporta os tipos '{tipo_lhs}' e '{tipo_rhs}'", linha
                )
                return "indefinido"
            return "booleano"

        # ------------------ igualdade -----------------------------
        if op in {"==", "!="}:
            if not (self._compat(tipo_lhs, tipo_rhs) or self._compat(tipo_rhs, tipo_lhs)):
                self.tabela._erro(
                    f"Comparação de igualdade entre tipos incompatíveis: '{tipo_lhs}' e '{tipo_rhs}'",
                    linha,
                )
                return "indefinido"
            return "booleano"

        self.tabela._erro(f"Operador desconhecido '{op}'", linha)
        return "indefinido"

    # ------------------------------------------------------------
    # Estruturas de controle
    # ------------------------------------------------------------
    def visit_If(self, node):
        linha = node["linha"]
        cond_node, then_node = node["filhos"][:2]
        tipo_cond = self.visit(cond_node)
        if tipo_cond not in {"booleano", "indefinido"}:
            self.tabela._erro(
                f"Condição do 'se' deve ser 'booleano', mas é '{tipo_cond}'", linha
            )
        self.visit(then_node)
        # opcional else
        if len(node["filhos"]) > 2:
            self.visit(node["filhos"][2])

    def visit_Enquanto(self, node):
        linha = node["linha"]
        cond_node, corpo_node = node["filhos"]
        tipo_cond = self.visit(cond_node)
        if tipo_cond not in {"booleano", "indefinido"}:
            self.tabela._erro(
                f"Condição do 'enquanto' deve ser 'booleano', mas é '{tipo_cond}'", linha
            )
        self.visit(corpo_node)

    def visit_Repita(self, node):
        # Regra: literal inteiro obrigatório
        linha = node["linha"]
        vezes_node, corpo_node = node["filhos"]
        if not (vezes_node.get("tag") == "Literal" and vezes_node.get("tipo") == "inteiro"):
            self.tabela._erro(
                "O número de repetições no 'repita' deve ser literal inteiro (ex: 5)", linha
            )
        self.visit(corpo_node)

    # ------------------------------------------------------------
    # Chamadas de função e retorno
    # ------------------------------------------------------------
    def visit_FuncaoCall(self, node):
        nome, linha = node["nome"], node["linha"]
        tipos_args = [self.visit(arg) for arg in node.get("filhos", [])]

        # Comando primitivo?
        if nome in ASSINATURAS_PRIMITIVAS:
            assinatura = ASSINATURAS_PRIMITIVAS[nome]
            self._checar_assinatura(nome, tipos_args, assinatura, linha)
            return assinatura[1]

        # Procura função declarada
        entrada = self.tabela.buscar(nome, linha)
        if not entrada:
            return "indefinido"
        if entrada.categoria != "funcao":
            self.tabela._erro(f"'{nome}' não é uma função", linha)
            return "indefinido"

        assinatura = (entrada.tipos_params, entrada.tipo_retorno)
        self._checar_assinatura(nome, tipos_args, assinatura, linha)
        return entrada.tipo_retorno

    def visit_Retorno(self, node):
        linha = node["linha"]
        if not self.funcao_atual:
            self.tabela._erro("'retorne' só pode aparecer dentro de função", linha)
            return

        esperado = self.funcao_atual.tipo_retorno
        tem_expr = bool(node.get("filhos"))

        if not tem_expr and esperado != "vazio":
            self.tabela._erro(
                f"Retorno vazio em função que espera '{esperado}'", linha
            )
            return

        if tem_expr:
            real = self.visit(node["filhos"][0])
            if esperado == "vazio":
                self.tabela._erro("Função 'vazio' não pode retornar valor", linha)
            elif not self._compat(esperado, real):
                self.tabela._erro(
                    f"Tipo de retorno incompatível: esperado '{esperado}', recebeu '{real}'",
                    linha,
                )

    # ============================================================
    # 5. Auxiliares de tipagem
    # ============================================================
    @staticmethod
    def _compat(tipo_lhs: str, tipo_rhs: str) -> bool:
        if "qualquer" in (tipo_lhs, tipo_rhs):
            return True
        if tipo_lhs == tipo_rhs:
            return True
        return tipo_lhs == "real" and tipo_rhs == "inteiro"

    def _checar_assinatura(
        self,
        nome: str,
        reais: List[str],
        esperados: Tuple[List[str], Optional[str]],
        linha: int,
    ) -> None:
        tipos_esp, _ = esperados
        if len(reais) != len(tipos_esp):
            self.tabela._erro(
                f"Função '{nome}' espera {len(tipos_esp)} arg(s), mas recebeu {len(reais)}",
                linha,
            )
            return
        for i, (t_real, t_esp) in enumerate(zip(reais, tipos_esp), 1):
            if "indefinido" in (t_real, t_esp):
                continue  # erro já reportado
            if not self._compat(t_esp, t_real):
                self.tabela._erro(
                    f"Arg {i} de '{nome}': esperado '{t_esp}', recebeu '{t_real}'",
                    linha,
                )


# ================================================================
# 6. Função utilitária para o pipeline
# ================================================================

def analisar_semantica(ast_raiz: Dict[str, Any]) -> List[str]:
    """Executa o analisador e devolve a lista de erros (vazia se OK)."""
    sem = SemanticoVisitor()
    sem.visit(ast_raiz)
    return sem.tabela.erros


# ================================================================
# 7. Pequeno teste manual (pode remover em produção)
# ================================================================
if __name__ == "__main__":  # pragma: no cover
    # Demo mínimo: var inteiro x = 5 + 3;
    ast_demo = {
        "tag": "Bloco",
        "filhos": [
            {
                "tag": "DeclaracaoVar",
                "tipo": "inteiro",
                "ident": "x",
                "linha": 1,
                "filhos": [
                    {
                        "tag": "ExprBinaria",
                        "op": "+",
                        "linha": 1,
                        "filhos": [
                            {"tag": "Literal", "tipo": "inteiro", "valor": 5, "linha": 1},
                            {"tag": "Literal", "tipo": "inteiro", "valor": 3, "linha": 1},
                        ],
                    }
                ],
            }
        ],
    }
    erros = analisar_semantica(ast_demo)
    print("Erros:" if erros else "Sem erros.")
    for e in erros:
        print(" -", e)
