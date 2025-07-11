# semantic.py

class SemanticError(Exception):
    """Classe de exceção para erros semânticos."""
    def __init__(self, message, line=None):
        full_message = f"Erro Semântico"
        if line:
            full_message += f" (linha {line})"
        full_message += f": {message}"
        super().__init__(full_message)

class Symbol:
    def __init__(self, name, type):
        self.name = name
        self.type = type

class SymbolTable:
    """
    Tabela de Símbolos para armazenar informações sobre variáveis (tipo, etc.).
    Para esta linguagem, um único escopo global é suficiente.
    """
    def __init__(self):
        self._symbols = {}

    def define(self, name, type):
        """Define uma nova variável na tabela."""
        if name in self._symbols:
            raise SemanticError(f"Variável '{name}' já foi declarada.")
        self._symbols[name] = Symbol(name, type)

    def lookup(self, name):
        """Busca por uma variável na tabela."""
        symbol = self._symbols.get(name)
        if not symbol:
            raise SemanticError(f"Variável '{name}' não foi declarada.")
        return symbol

class SemanticAnalyzer:
    """
    Percorre a AST para realizar a análise semântica.
    Utiliza o padrão de projeto Visitor.
    """
    def __init__(self, ast_tree):
        self.ast = ast_tree
        self.symbol_table = SymbolTable()

    def analyze(self):
        """Método principal para iniciar a análise."""
        print("\n--- Iniciando Análise Semântica ---")
        self.visit(self.ast)
        print("--- Análise Semântica Concluída com Sucesso! ---")

    def visit(self, node):
        """Método visitante genérico que despacha para o método específico do nó."""
        method_name = f'visit_{node["tag"]}'
        visitor = getattr(self, method_name, self.generic_visit)
        # Passa o nó inteiro para o método visitante
        return visitor(node)

    def generic_visit(self, node):
        """Método para visitar nós que não têm uma regra específica."""
        if 'filhos' in node:
            for child in node['filhos']:
                self.visit(child)

    # --- Métodos de Visita Específicos para cada tipo de nó da AST ---

    def visit_Bloco(self, node):
        # O bloco principal apenas contém uma lista de comandos
        self.generic_visit(node)

    def visit_DECL(self, node):
        """Processa a declaração de uma variável."""
        # Estrutura do nó DECL: [var, TYPE, :, ID, ;]
        var_type_node = node['filhos'][1] # Nó TYPE
        var_type = var_type_node['filhos'][0]['tag'] # 'inteiro', 'texto', etc.

        var_id_node = node['filhos'][3] # Nó ID
        var_name = var_id_node['filhos'][0]['tag'] # 'identificador'
        
        # O nome real do identificador está no valor literal, que não está na AST.
        # Para simplificar, vamos assumir que o nome é "identificador" para fins de exemplo
        # ou ajustar o parser para incluir o valor literal.
        # Por simplicidade aqui, vamos usar o nome 'identificador' como placeholder.
        # Idealmente, o tokenizer/parser deveria anexar o valor literal ao nó.
        # Assumindo que o nome do identificador é seu valor:
        var_name = var_id_node['filhos'][0]['valor'] if 'valor' in var_id_node['filhos'][0] else 'identificador_desconhecido'

        print(f"Declarando variável '{var_name}' do tipo '{var_type}' na linha {node['linha']}.")
        self.symbol_table.define(var_name, var_type)
    
    def visit_ATR(self, node):
        """Processa uma atribuição (ATT -> ID = REL)."""
        # Nó ATT: filhos [ID, =, REL]
        att_node = node['filhos'][0] 
        var_name_node = att_node['filhos'][0]['filhos'][0]
        var_name = var_name_node['valor'] # Assumindo que o parser adiciona o valor
        
        # Verifica se a variável foi declarada
        symbol = self.symbol_table.lookup(var_name)
        
        # Avalia o tipo da expressão à direita
        expr_type = self.visit(att_node['filhos'][2]) # Visita o nó REL
        
        print(f"Verificando atribuição para '{var_name}' na linha {node['linha']}. Tipo esperado: '{symbol.type}', Tipo encontrado: '{expr_type}'.")

        # Regra de verificação de tipo
        # Permite atribuir inteiro a real, mas não o contrário sem coerção.
        if symbol.type == 'real' and expr_type == 'inteiro':
            pass # Válido
        elif symbol.type != expr_type:
            raise SemanticError(f"Não é possível atribuir um valor do tipo '{expr_type}' à variável '{var_name}' do tipo '{symbol.type}'.", node['linha'])

    def visit_REL(self, node):
        # Para expressões, o tipo da expressão é o tipo do seu primeiro operando.
        # Uma análise mais completa resolveria o tipo resultante da operação.
        return self.visit(node['filhos'][0])

    def visit_ADD(self, node):
        return self.visit(node['filhos'][0])
    
    def visit_MUL(self, node):
        return self.visit(node['filhos'][0])

    def visit_FACTOR(self, node):
        """Retorna o tipo de um fator base da expressão."""
        factor_child = node['filhos'][0]
        tag = factor_child['tag']
        
        if tag == 'NUM':
            num_type = factor_child['filhos'][0]['tag'] # numero_inteiro ou numero_real
            return 'inteiro' if num_type == 'numero_inteiro' else 'real'
        elif tag == 'TEXT':
            return 'texto'
        elif tag == 'BOOL':
            return 'logico'
        elif tag == 'ID':
            var_name = factor_child['filhos'][0]['valor'] # Assumindo que o parser adiciona o valor
            return self.symbol_table.lookup(var_name).type
        elif tag == '(': # ( REL )
            return self.visit(factor_child['filhos'][1]) # Visita o nó REL interno
        else:
            # Para nós como 'avancar', 'recuar' que podem estar aqui por erro de gramática
            raise SemanticError(f"Fator inesperado na expressão: {tag}", node['linha'])

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