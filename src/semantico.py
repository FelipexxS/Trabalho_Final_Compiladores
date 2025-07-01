# ------------------------------------------------------------
# turtlescript_semantic.py – Infra‑estrutura de análise semântica
# para a linguagem TurtleScript usando uma AST LINEAR (única tabela)
# ------------------------------------------------------------
from __future__ import annotations

# ============================================================
# 1.  Definições básicas e Tabela de Símbolos
# ============================================================

class SemanticError(Exception):
    """Exceção usada para sinalizar erros semânticos graves."""
    pass


class EntradaTabelaSimbolos:
    """Registro de uma variável na tabela de símbolos."""

    def __init__(self, nome: str, tipo: str):
        self.nome = nome
        self.tipo = tipo

    def __repr__(self) -> str:
        return f"EntradaTabelaSimbolos({self.nome!r}, {self.tipo!r})"


class TabelaDeSimbolos:
    """Implementa uma pilha de escopos (lista de dicionários)."""

    def __init__(self):
        self._escopos: list[dict[str, EntradaTabelaSimbolos]] = [{}]  # escopo global
        self.erros: list[str] = []

    # ---------- Escopos ----------
    def abrir_escopo(self) -> None:
        self._escopos.append({})

    def fechar_escopo(self) -> None:
        self._escopos.pop()

    # ---------- Registro / busca ----------
    def declarar(self, nome: str, tipo: str, linha: int) -> None:
        escopo_atual = self._escopos[-1]
        if nome in escopo_atual:
            self._erro(f"Variável '{nome}' já declarada neste escopo", linha)
            return
        escopo_atual[nome] = EntradaTabelaSimbolos(nome, tipo)

    def buscar(self, nome: str, linha: int) -> EntradaTabelaSimbolos | None:
        for escopo in reversed(self._escopos):
            if nome in escopo:
                return escopo[nome]
        self._erro(f"Variável '{nome}' não declarada", linha)
        return None  # sinaliza erro, mas permite continuar

    # ---------- Relato de erros ----------
    def _erro(self, mensagem: str, linha: int) -> None:
        self.erros.append(f"Linha {linha}: {mensagem}")

    def possui_erros(self) -> bool:
        return bool(self.erros)

    # ---------- Depuração ----------
    def __str__(self) -> str:
        linhas = []
        for i, esc in enumerate(self._escopos):
            prefixo = "<global>" if i == 0 else f"<escopo {i}>"
            for nome, ent in esc.items():
                linhas.append(f"{prefixo}  {nome}: {ent.tipo}")
        return "\n".join(linhas) or "(Tabela vazia)"


# ============================================================
# 2.  Representação da AST como uma TABELA ÚNICA
# ============================================================

AST: list[dict] = []  # cada posição contém um nó (dict)


def novo_no(tag: str, filhos: list[int] | None = None, **attrs) -> int:
    """Cria um nó, armazena na lista global AST e devolve o índice."""
    idx = len(AST)
    AST.append({
        "tag": tag,
        "filhos": filhos or [],
        **attrs,
    })
    return idx


# ============================================================
# 3.  NodeVisitor genérico para tabela linear
# ============================================================

class NodeVisitor:
    """Despacho dinâmico baseado no campo 'tag' do nó."""

    def visit(self, idx: int):
        no = AST[idx]
        metodo = getattr(self, f"visit_{no['tag']}", self.generic_visit)
        return metodo(idx)

    def generic_visit(self, idx: int):
        raise RuntimeError(f"Nó não suportado: {AST[idx]['tag']}")


# ============================================================
# 4.  Assinaturas de comandos primitivos de TurtleScript
# ============================================================
# Exemplo enxuto – adapte conforme sua linguagem.
ASSINATURAS: dict[str, tuple[list[str], str | None]] = {
    "avancar": (["inteiro"], None),
    "definir_cor": (["texto"], None),
}


# ============================================================
# 5.  SemanticoVisitor adaptado para AST linear
# ============================================================

class SemanticoVisitor(NodeVisitor):
    """
    Percorre a AST linear validando regras semânticas da linguagem TurtleScript.
    Cada método `visit_<Tag>` recebe **o índice** do nó na tabela AST.
    """

    def __init__(self):
        self.tabela = TabelaDeSimbolos()

    # --------------------------------------------------
    # DECLARAÇÃO DE VARIÁVEL
    # --------------------------------------------------
    def visit_DeclaracaoVar(self, idx: int):
        no = AST[idx]
        tipo = no["tipo_lexema"]
        ident = no["ident_lexema"]
        linha = no["linha"]
        self.tabela.declarar(ident, tipo, linha)

    # --------------------------------------------------
    # USO DE IDENTIFICADOR EM EXPRESSÕES
    # --------------------------------------------------
    def visit_Identificador(self, idx: int):
        no = AST[idx]
        lexema = no["lexema"]
        linha = no["linha"]
        entrada = self.tabela.buscar(lexema, linha)
        return entrada.tipo if entrada else "indefinido"

    # --------------------------------------------------
    # ATRIBUIÇÃO
    # --------------------------------------------------
    def visit_Atribuicao(self, idx: int):
        no = AST[idx]
        linha = no["linha"]
        var_idx, expr_idx = no["filhos"]  # [lhs, rhs]

        tipo_lhs = self.visit(var_idx)
        tipo_rhs = self.visit(expr_idx)

        if tipo_lhs != "indefinido" and tipo_rhs != "indefinido":
            if not self._compat(tipo_lhs, tipo_rhs):
                self.tabela._erro(
                    f"Tipos incompatíveis em atribuição: '{tipo_lhs}' ← '{tipo_rhs}'",
                    linha,
                )

    # --------------------------------------------------
    # COMANDO PRIMITIVO
    # --------------------------------------------------
    def visit_Comando(self, idx: int):
        no = AST[idx]
        nome = no["nome"]
        linha = no["linha"]
        assinatura = ASSINATURAS.get(nome)
        if assinatura is None:
            self.tabela._erro(f"Comando desconhecido '{nome}'", linha)
            return

        tipos_args = [self.visit(i) for i in no["args"]]
        self._checar_assinatura(nome, tipos_args, assinatura, linha)

    # --------------------------------------------------
    # BLOCO – cria novo escopo
    # --------------------------------------------------
    def visit_Bloco(self, idx: int):
        no = AST[idx]
        self.tabela.abrir_escopo()
        for stmt_idx in no["stmts"]:
            self.visit(stmt_idx)
        self.tabela.fechar_escopo()

    # --------------------------------------------------
    # ------------------ AUXILIARES --------------------
    # --------------------------------------------------
    def _compat(self, tipo_lhs: str, tipo_rhs: str) -> bool:
        """Regra simples de compatibilidade de tipos."""
        if tipo_lhs == tipo_rhs:
            return True
        return tipo_lhs == "real" and tipo_rhs == "inteiro"

    def _checar_assinatura(
        self,
        nome: str,
        reais: list[str],
        esperados: tuple[list[str], str | None],
        linha: int,
    ) -> None:
        tipos_esp, _ = esperados
        # --- Aridade ---
        if len(reais) != len(tipos_esp):
            self.tabela._erro(
                f"'{nome}' espera {len(tipos_esp)} argumento(s), recebeu {len(reais)}",
                linha,
            )
            return
        # --- Tipos ---
        for i, (t_real, t_esp) in enumerate(zip(reais, tipos_esp), 1):
            if not self._compat(t_esp, t_real):
                self.tabela._erro(
                    f"Argumento {i} de '{nome}' deve ser '{t_esp}', não '{t_real}'",
                    linha,
                )


# ============================================================
# 6.  Exemplo mínimo de uso (pode ser removido em produção)
# ============================================================

def _exemplo_demo():
    """Constrói uma mini‑AST na mão para demonstração."""
    AST.clear()

    # inteiro x;
    decl_x = novo_no("DeclaracaoVar", tipo_lexema="inteiro", ident_lexema="x", linha=1)

    # x = 5;
    ident_x = novo_no("Identificador", lexema="x", linha=2)
    num_5 = novo_no("Numero", valor=5, linha=2)  # não há verificação de tipo aqui – simplificado
    atrib = novo_no("Atribuicao", filhos=[ident_x, num_5], linha=2)

    # { bloco }
    bloco = novo_no("Bloco", stmts=[decl_x, atrib], linha=0)

    sem = SemanticoVisitor()
    sem.visit(bloco)

    print("Erros encontrados:\n" + "\n".join(sem.tabela.erros) if sem.tabela.possui_erros() else "Sem erros!")
    print("\nTabela de símbolos:\n", sem.tabela)


if __name__ == "__main__":
    _exemplo_demo()
