from typing import Dict, Any
from typing import Dict, Any


# tokens = lista_tokens(ENTRADA_1_CONTEUDO)
rules = [
        "S -> inicio B fim",
        "B -> CMDS",
        "CMDS -> CMD CMDS | #",
        "CMD -> AV | REC | GD | GE | IRP | LC | AC | DC | DE | CDF | LP | DECL | REP | ENQ | SE | ATR | DSQ | DSC",
        "ATR -> ATT ;",
        "AV -> avancar REL ;",
        "REC -> recuar REL ;",
        "GD -> girar_direita REL ;",
        "GE -> girar_esquerda REL ;",
        "IRP -> ir_para REL REL ;",
        "LC -> levantar_caneta ;",
        "AC -> abaixar_caneta ;",
        "DC -> definir_cor REL ;",
        "DE -> definir_espessura REL ;",
        "CDF -> cor_de_fundo REL ;",
        "LP -> limpar_tela ;",
        "DSQ -> desenhar_quadrado REL REL ;",
        "DSC -> desenhar_circulo REL REL REL ;",
        "DECL -> var TYPE : ID ;",
        "TYPE -> inteiro | texto | real | logico",
        "ATT -> ID = REL",
        "REP -> repita REL vezes CMDS fim_repita ;",
        "ENQ -> enquanto REL faca CMDS fim_enquanto ;",
        "SE -> se REL entao CMDS SE_CONT",
        "SE_CONT -> senao CMDS fim_se ; | fim_se ;",
        "REL -> ADD REL'",
        "REL' -> OP_REL ADD REL' | #",
        "OP_REL -> == | != | > | < | >= | <=",
        "ADD -> MUL ADD'",
        "ADD' -> + MUL ADD' | - MUL ADD' | #",
        "MUL -> FACTOR MUL'",
        "MUL' -> * FACTOR MUL' | / FACTOR MUL' | #",
        "FACTOR -> ( REL ) | ID | NUM | TEXT | BOOL",
        "ID -> identificador",
        "NUM -> numero_inteiro | numero_real",
        "TEXT -> literal_texto",
        "BOOL -> verdadeiro | falso"
]

nonterm_userdef = ['S', 'B','CMDS', 'CMD', 'ATR', 'AV', 'REC', 'GD', 'GE', 'IRP', 'LC', 'AC', 'DC', 'DE', 'CDF', 'LP', 'DSQ', 'DSC',
                       'DECL', 'TYPE', 'ATT', 'REP', 'ENQ', 'SE', 'SE_CONT', 'REL', 'REL\'', 'OP_REL', 'ADD', 'ADD\'', 'MUL', 'MUL\'', 'FACTOR', 'ID', 'NUM', 'TEXT', 'BOOL']

term_userdef = [
        'inicio', 'fim', 'avancar', 'recuar', 'girar_direita', 'girar_esquerda', 'ir_para', 'levantar_caneta',
        'abaixar_caneta', 'definir_cor', 'definir_espessura', 'cor_de_fundo', 'limpar_tela', 'desenhar_quadrado',
        'desenhar_circulo', 'var', 'inteiro', 'texto', 'real', 'logico', '=', ';', ':', ',', 'repita', 'vezes', 'fim_repita',
        'enquanto', 'faca', 'fim_enquanto', 'se', 'entao', 'senao', 'fim_se', '#',
        '+', '-', '*', '/', '(', ')', '<=', '<', '>=', '>', '==', '!=', 'identificador', 'literal_texto',
        'numero_inteiro', 'numero_real', 'verdadeiro', 'falso'
]
class NodeVisitor:
    """
    Uma classe base para percorrer uma Árvore Sintática Abstrata (AST).
    Utiliza o padrão de projeto Visitor, onde para cada tipo de nó na árvore,
    um método 'visit_TIPO_DO_NO' é chamado.
    """
    def visit(self, node: Dict[str, Any]):
        """
        Inicia a visita a um nó. Atua como um despachante que chama o método
        visitante específico para o tipo do nó.
        
        Por exemplo, se node['tag'] for 'Repita', este método tentará chamar
        self.visit_Repita(node).
        """
        
        method_name = f'visit_{node["tag"]}'
        
        visitor = getattr(self, method_name, self.generic_visit)
        
        return visitor(node)

    def generic_visit(self, node: Dict[str, Any]):
        """
        Método chamado se nenhum método visitante específico for encontrado para um nó.
        A ação padrão é visitar todos os filhos do nó atual.
        """
        # A implementação padrão de um nó genérico é visitar seus filhos.
        # Útil para nós estruturais como 'BlocoDeComandos' que não têm
        # lógica própria, mas contêm outros nós a serem processados.
        for child_node in node.get('filhos', []):
            self.visit(child_node)
