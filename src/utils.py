from typing import Dict, Any
from typing import Dict, Any

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
        # Constrói o nome do método a partir da 'tag' do nó.
        # Ex: 'Repita' -> 'visit_Repita'
        method_name = f'visit_{node["tag"]}'
        
        # Procura o método específico (ex: visit_Repita). 
        # Se não encontrar, usa o método genérico 'generic_visit'.
        visitor = getattr(self, method_name, self.generic_visit)
        
        # Chama o método encontrado, passando o nó como argumento.
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

class SemanticASTNode:
    """ Classe base para todos os nós da AST Semântica. """
    pass

class Program(SemanticASTNode):
    """ Representa o programa inteiro como uma lista de comandos. """
    def __init__(self, statements):
        self.statements = statements

class VarDecl(SemanticASTNode):
    """ Representa uma declaração de variável (ex: var inteiro: x;). """
    def __init__(self, var_type, var_name, line):
        self.type = var_type
        self.name = var_name
        self.line = line

class Assignment(SemanticASTNode):
    """ Representa uma atribuição (ex: x = 10;). """
    def __init__(self, var_name, expression, line):
        self.name = var_name
        self.expression = expression
        self.line = line

class Command(SemanticASTNode):
    """ Representa um comando genérico da turtle (ex: avancar 100;). """
    def __init__(self, name, args, line):
        self.name = name # Nome do comando em maiúsculas (ex: 'AV')
        self.args = args
        self.line = line

class Repeat(SemanticASTNode):
    """ Representa um laço 'repita'. """
    def __init__(self, times, body, line):
        self.times = times
        self.body = body
        self.line = line

class If(SemanticASTNode):
    """ Representa uma estrutura condicional 'se/senao'. """
    def __init__(self, condition, if_body, else_body, line):
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body
        self.line = line

class While(SemanticASTNode):
    """ Representa um laço 'enquanto'. """
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body = body
        self.line = line

class BinOp(SemanticASTNode):
    """ Representa uma operação binária (ex: x + 5). """
    def __init__(self, op, left, right, line):
        self.op = op
        self.left = left
        self.right = right
        self.line = line

class Literal(SemanticASTNode):
    """ Representa um valor literal (número, texto, booleano). """
    def __init__(self, value, lit_type, line):
        self.value = value
        self.type = lit_type
        self.line = line

class Identifier(SemanticASTNode):
    """ Representa o uso de uma variável/identificador. """
    def __init__(self, name, line):
        self.name = name
        self.line = line

# =============================================================================
# VISITOR PARA TRANSFORMAÇÃO DA AST
# =============================================================================

class Concrete2Semantic(NodeVisitor):
    """
    Constrói uma AST semântica (com objetos) a partir da árvore concreta (dicionários)
    gerada pelo parser LL(1).
    """
    def visit_S(self, n):
        # S -> inicio B fim
        corpo = self.visit(n["filhos"][1]) # 'B'
        return corpo

    def visit_B(self, n):
        # B -> CMDS
        return self.visit(n["filhos"][0])

    def visit_CMDS(self, n):
        # CMDS -> CMD CMDS | #
        statements = []
        if 'filhos' in n:
            cmd = self.visit(n['filhos'][0])
            if cmd: statements.append(cmd)
            if len(n['filhos']) > 1:
                remaining_cmds = self.visit(n['filhos'][1])
                if remaining_cmds:
                    # Se o retorno for um Program, pegamos suas statements
                    if isinstance(remaining_cmds, Program):
                        statements.extend(remaining_cmds.statements)
                    else: # Caso seja uma lista de comandos
                        statements.extend(remaining_cmds)
        return Program(statements)

    def visit_CMD(self, node):
        return self.visit(node['filhos'][0])

    def visit_DECL(self, n): # DECL -> var TYPE : ID ;
        var_type = self.visit(n['filhos'][1])
        var_name = n['filhos'][3]['filhos'][0]['tag'] # Extrai o nome do identificador
        return VarDecl(var_type, var_name, n['linha'])

    def visit_TYPE(self, node):
        return node['filhos'][0]['tag']

    def visit_ATR(self, n): # ATR -> ATT ;
        return self.visit(n['filhos'][0])

    def visit_ATT(self, n): # ATT -> ID = REL
        var_name = n['filhos'][0]['filhos'][0]['tag']
        expression = self.visit(n['filhos'][2])
        return Assignment(var_name, expression, n['linha'])

    # Comandos (AV, REC, etc.)
    def _handle_command(self, n, expected_args):
        cmd_name = n['tag']
        line = n['linha']
        args = [self.visit(n['filhos'][i]) for i in range(expected_args)]

        if len(args) == 0: return Command(cmd_name, None, line)
        if len(args) == 1: return Command(cmd_name, args[0], line)
        return Command(cmd_name, args, line)

    def visit_AV(self, n): return self._handle_command(n, 1)
    def visit_REC(self, n): return self._handle_command(n, 1)
    def visit_GD(self, n): return self._handle_command(n, 1)
    def visit_GE(self, n): return self._handle_command(n, 1)
    def visit_DC(self, n): return self._handle_command(n, 1)
    def visit_DE(self, n): return self._handle_command(n, 1)
    def visit_CDF(self, n): return self._handle_command(n, 1)
    def visit_DSQ(self, n): return self._handle_command(n, 1)
    def visit_DSC(self, n): return self._handle_command(n, 1)
    def visit_IRP(self, n): return self._handle_command(n, 2)
    def visit_LC(self, n): return self._handle_command(n, 0)
    def visit_AC(self, n): return self._handle_command(n, 0)
    def visit_LP(self, n): return self._handle_command(n, 0)

    def visit_REP(self, n): # REP -> repita REL vezes CMDS fim_repita ;
        times_expr = self.visit(n['filhos'][1])
        body_program = self.visit(n['filhos'][3])
        return Repeat(times_expr, body_program.statements, n['linha'])

    def visit_ENQ(self, n): # ENQ -> enquanto REL faca CMDS fim_enquanto ;
        condition = self.visit(n['filhos'][1])
        body_program = self.visit(n['filhos'][3])
        return While(condition, body_program.statements, n['linha'])

    def visit_SE(self, n): # SE -> se REL entao CMDS SE_CONT
        condition = self.visit(n['filhos'][1])
        if_body_program = self.visit(n['filhos'][3])
        else_body = self.visit(n['filhos'][4]) # Pode ser None
        return If(condition, if_body_program.statements, else_body, n['linha'])

    def visit_SE_CONT(self, n): # SE_CONT -> senao CMDS fim_se ; | fim_se ;
        if 'filhos' in n and n['filhos'][0]['tag'] == 'senao':
            program_node = self.visit(n['filhos'][1])
            return program_node.statements
        return None # Representa a ausência de um bloco 'senao'

    def _build_binary_op_chain(self, left, op_chain, line):
        if not op_chain:
            return left
        op = op_chain[0]['op']
        right = op_chain[0]['right']
        current_op = BinOp(op, left, right, line)
        remaining_ops = op_chain[1:]
        return self._build_binary_op_chain(current_op, remaining_ops, line)

    def _visit_expr_chain(self, n):
        if 'filhos' in n and len(n['filhos']) > 0:
            op = n['filhos'][0]['filhos'][0]['tag'] if n['filhos'][0]['tag'] == 'OP_REL' else n['filhos'][0]['tag']
            right = self.visit(n['filhos'][1])
            rest = self._visit_expr_chain(n['filhos'][2])
            current_link = [{'op': op, 'right': right}]
            return current_link + rest if rest else current_link
        return None

    def visit_REL(self, n): return self._build_binary_op_chain(self.visit(n['filhos'][0]), self._visit_expr_chain(n['filhos'][1]), n['linha'])
    def visit_ADD(self, n): return self._build_binary_op_chain(self.visit(n['filhos'][0]), self._visit_expr_chain(n['filhos'][1]), n['linha'])
    def visit_MUL(self, n): return self._build_binary_op_chain(self.visit(n['filhos'][0]), self._visit_expr_chain(n['filhos'][1]), n['linha'])

    def visit_REL_(self, n): return self._visit_expr_chain(n)
    def visit_ADD_(self, n): return self._visit_expr_chain(n)
    def visit_MUL_(self, n): return self._visit_expr_chain(n)

    def visit_FACTOR(self, n):
        child = n['filhos'][0]
        return self.visit(n['filhos'][1]) if child['tag'] == '(' else self.visit(child)

    def visit_NUM(self, n): return self.visit(n['filhos'][0])
    def visit_TEXT(self, n): return self.visit(n['filhos'][0])
    def visit_BOOL(self, n): return self.visit(n['filhos'][0])
    def visit_ID(self, n): return self.visit(n['filhos'][0])

    def visit_identificador(self, n): return Identifier(n['valor'], n['linha'])
    def visit_numero_inteiro(self, n): return Literal(int(n['valor']), 'inteiro', n['linha'])
    def visit_numero_real(self, n): return Literal(float(n['valor']), 'real', n['linha'])
    def visit_literal_texto(self, n): return Literal(str(n['valor']), 'texto', n['linha'])
    def visit_verdadeiro(self, n): return Literal(True, 'logico', n['linha'])
    def visit_falso(self, n): return Literal(False, 'logico', n['linha'])