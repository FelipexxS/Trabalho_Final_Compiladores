# Definição de uma classe para a entrada da Tabela de Símbolos
# Esta classe armazena os atributos de cada identificador.
class EntradaTabelaSimbolos:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo

    def __repr__(self):
        return f"EntradaTabelaSimbolos(nome='{self.nome}', tipo='{self.tipo}')"
class TabelaDeSimbolos:
    def __init__(self):
        self._tabela = {}
        print("Tabela de Símbolos inicializada.")

    def inserir(self, nome, tipo):
        """
        Insere um novo símbolo na tabela.
        Verifica se o símbolo já foi declarado para evitar redeclaração.
        """
        if nome in self._tabela:
            print(f"Erro Semântico: Variável '{nome}' já declarada.")
            return False
        else:
            self._tabela[nome] = EntradaTabelaSimbolos(nome, tipo)
            print(f"Inserido: {self._tabela[nome]}")
            return True

    def consultar(self, nome):
        """
        Consulta um símbolo na tabela e retorna sua entrada.
        Reporta um erro se a variável não foi declarada.
        """
        if nome not in self._tabela:
            print(f"Erro Semântico: Variável '{nome}' não declarada.")
            return None
        else:
            print(f"Consultado '{nome}': {self._tabela[nome]}")
            return self._tabela[nome]

    def __str__(self):
        """
        Retorna uma representação em string da tabela para visualização.
        """
        if not self._tabela:
            return "  (Tabela vazia)"
        return "\n".join([f"  '{nome}': {entrada}" for nome, entrada in self._tabela.items()])
