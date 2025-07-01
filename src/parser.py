# Definição de uma classe para a entrada da Tabela de Símbolos
# Esta classe armazena os atributos de cada identificador.

class SemanticError(Exception):
    """Exceção customizada para erros semânticos."""
    pass

class EntradaTabelaSimbolos:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo

    def __repr__(self):
        return f"EntradaTabelaSimbolos(nome='{self.nome}', tipo='{self.tipo}')"
class TabelaDeSimbolos:
    def __init__(self):
        self._symbols = {}

    def inserir(self, nome, tipo):
        """
        Insere um novo símbolo na tabela.
        Verifica se o símbolo já foi declarado para evitar redeclaração.
        Lança um SemanticError em caso de redeclaração.
        """
        if nome in self._symbols:
            raise SemanticError(f"Variável '{nome}' já declarada.")
        
        self._symbols[nome] = EntradaTabelaSimbolos(nome, tipo)
        return self._symbols[nome]

    def consultar(self, nome):
        """
        Consulta um símbolo na tabela e retorna sua entrada.
        Lança um SemanticError se a variável não foi declarada.
        """
        entry = self._symbols.get(nome)
        if entry is None:
            raise SemanticError(f"Variável '{nome}' não declarada.")
        return entry

    def __str__(self):
        """
        Retorna uma representação em string da tabela para visualização.
        """
        if not self._symbols:
            return "  (Tabela vazia)"
        return "\n".join([f"  '{nome}': {entrada}" for nome, entrada in self._symbols.items()])
    