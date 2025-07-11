from tokenizer import TokenType, Token, lista_tokens


class Parser:
    def __init__(self, rules, nonterm_userdef, term_userdef, sample_input_string=None):
        self.rules = rules
        self.nonterm_userdef = nonterm_userdef
        self.term_userdef = term_userdef
        self.sample_input_string = sample_input_string
        self.diction = {}
        self.firsts = {}
        self.follows = {}
        self.start_symbol = None

    def removeLeftRecursion(self, rulesDiction):
        store = {}
        for lhs in rulesDiction:
            alphaRules = []
            betaRules = []
            allrhs = rulesDiction[lhs]
            for subrhs in allrhs:
                if subrhs[0] == lhs:
                    alphaRules.append(subrhs[1:])
                else:
                    betaRules.append(subrhs)
            if len(alphaRules) != 0:
                lhs_ = lhs + "_prime"
                while (lhs_ in rulesDiction.keys()) or (lhs_ in store.keys()):
                    lhs_ += "_prime"
                for b in range(0, len(betaRules)):
                    betaRules[b].append(lhs_)
                rulesDiction[lhs] = betaRules
                for a in range(0, len(alphaRules)):
                    alphaRules[a].append(lhs_)
                alphaRules.append(['#'])
                store[lhs_] = alphaRules
        for left in store:
            rulesDiction[left] = store[left]
        self.diction = rulesDiction

    def LeftFactoring(self, rulesDiction):
        newDict = {}
        for lhs in rulesDiction:
            allrhs = rulesDiction[lhs]
            temp = dict()
            for subrhs in allrhs:
                if subrhs[0] not in list(temp.keys()):
                    temp[subrhs[0]] = [subrhs]
                else:
                    temp[subrhs[0]].append(subrhs)
            new_rule = []
            tempo_dict = {}
            for term_key in temp:
                allStartingWithTermKey = temp[term_key]
                if len(allStartingWithTermKey) > 1:
                    lhs_ = lhs + "_prime"
                    while (lhs_ in rulesDiction.keys()) or (lhs_ in tempo_dict.keys()):
                        lhs_ += "_prime"
                    new_rule.append([term_key, lhs_])
                    ex_rules = []
                    for g in temp[term_key]:
                        ex_rules.append(g[1:])
                    tempo_dict[lhs_] = ex_rules
                else:
                    new_rule.append(allStartingWithTermKey[0])
            newDict[lhs] = new_rule
            for key in tempo_dict:
                newDict[key] = tempo_dict[key]
        self.diction = newDict

    def first(self, rule):
        if len(rule) != 0 and (rule is not None):
            if rule[0] in self.term_userdef:
                return rule[0]
            elif rule[0] == '#':
                return '#'
        if len(rule) != 0:
            if rule[0] in list(self.diction.keys()):
                fres = []
                rhs_rules = self.diction[rule[0]]
                for itr in rhs_rules:
                    indivRes = self.first(itr)
                    if indivRes is None:
                        continue  # <-- ignora None
                    if type(indivRes) is list:
                        for i in indivRes:
                            fres.append(i)
                    else:
                        fres.append(indivRes)
                if '#' not in fres:
                    return fres
                else:
                    newList = []
                    fres.remove('#')
                    if len(rule) > 1:
                        ansNew = self.first(rule[1:])
                        if ansNew is not None:
                            if type(ansNew) is list:
                                newList = fres + ansNew
                            else:
                                newList = fres + [ansNew]
                        else:
                            newList = fres
                        return newList
                    fres.append('#')
                    return fres
        return []  # <-- garante que nunca retorna None

    def follow(self, nt):
        solset = set()
        if nt == self.start_symbol:
            solset.add('$')
        for curNT in self.diction:
            rhs = self.diction[curNT]
            for subrule in rhs:
                if nt in subrule:
                    while nt in subrule:
                        index_nt = subrule.index(nt)
                        subrule = subrule[index_nt + 1:]
                        if len(subrule) != 0:
                            res = self.first(subrule)
                            if '#' in res:
                                newList = []
                                res = list(res)
                                res.remove('#')
                                ansNew = self.follow(curNT)
                                if ansNew is not None:
                                    if type(ansNew) is list:
                                        newList = res + ansNew
                                    else:
                                        newList = res + [ansNew]
                                else:
                                    newList = res
                                res = newList
                        else:
                            if nt != curNT:
                                res = self.follow(curNT)
                        if res is not None:
                            if type(res) is list:
                                for g in res:
                                    solset.add(g)
                            else:
                                solset.add(res)
        return list(solset)

    def computeAllFirsts(self):
        for rule in self.rules:
            k = rule.split("->")
            k[0] = k[0].strip()
            k[1] = k[1].strip()
            rhs = k[1]
            multirhs = rhs.split('|')
            for i in range(len(multirhs)):
                multirhs[i] = multirhs[i].strip()
                multirhs[i] = multirhs[i].split()
            self.diction[k[0]] = multirhs

        print(f"\nRules: \n")
        for y in self.diction:
            print(f"{y}->{self.diction[y]}")
        print(f"\nAfter elimination of left recursion:\n")

        self.removeLeftRecursion(self.diction)
        for y in self.diction:
            print(f"{y}->{self.diction[y]}")
        print("\nAfter left factoring:\n")

        self.LeftFactoring(self.diction)
        for y in self.diction:
            print(f"{y}->{self.diction[y]}")

        for y in list(self.diction.keys()):
            t = set()
            for sub in self.diction.get(y):
                res = self.first(sub)
                if res is not None:
                    if type(res) is list:
                        for u in res:
                            t.add(u)
                    else:
                        t.add(res)
            self.firsts[y] = t

        print("\nCalculated firsts: ")
        key_list = list(self.firsts.keys())
        index = 0
        for gg in self.firsts:
            print(f"first({key_list[index]}) => {self.firsts.get(gg)}")
            index += 1

    def computeAllFollows(self):
        for NT in self.diction:
            solset = set()
            sol = self.follow(NT)
            if sol is not None:
                for g in sol:
                    solset.add(g)
            self.follows[NT] = solset

        print("\nCalculated follows: ")
        key_list = list(self.follows.keys())
        index = 0
        for gg in self.follows:
            print(f"follow({key_list[index]}) => {self.follows[gg]}")
            index += 1

    def createParseTable(self):
        import copy
        print("\nFirsts and Follow Result table\n")
        mx_len_first = 0
        mx_len_fol = 0
        for u in self.diction:
            k1 = len(str(self.firsts[u]))
            k2 = len(str(self.follows[u]))
            if k1 > mx_len_first:
                mx_len_first = k1
            if k2 > mx_len_fol:
                mx_len_fol = k2

        print(f"{{:<{10}}} {{:<{mx_len_first + 5}}} {{:<{mx_len_fol + 5}}}".format("Non-T", "FIRST", "FOLLOW"))
        for u in self.diction:
            print(f"{{:<{10}}} {{:<{mx_len_first + 5}}} {{:<{mx_len_fol + 5}}}".format(u, str(self.firsts[u]), str(self.follows[u])))

        ntlist = list(self.diction.keys())
        terminals = copy.deepcopy(self.term_userdef)
        terminals.append('$')

        mat = []
        for x in self.diction:
            row = []
            for y in terminals:
                row.append('')
            mat.append(row)

        grammar_is_LL = True

        for lhs in self.diction:
            rhs = self.diction[lhs]
            for y in rhs:
                res = self.first(y)
                if '#' in res:
                    if type(res) == str:
                        firstFollow = []
                        fol_op = self.follows[lhs]
                        if isinstance(fol_op, str):
                            firstFollow.append(fol_op)
                        else:
                            for u in fol_op:
                                firstFollow.append(u)
                        res = firstFollow
                    else:
                        res = list(res)
                        res.remove('#')
                        res = list(res) + list(self.follows[lhs])
                ttemp = []
                if type(res) is str:
                    ttemp.append(res)
                    res = copy.deepcopy(ttemp)
                for c in res:
                    xnt = ntlist.index(lhs)
                    yt = terminals.index(c)
                    if mat[xnt][yt] == '':
                        mat[xnt][yt] = mat[xnt][yt] + f"{lhs}->{' '.join(y)}"
                    else:
                        if f"{lhs}->{y}" in mat[xnt][yt]:
                            continue
                        else:
                            grammar_is_LL = False
                            mat[xnt][yt] = mat[xnt][yt] + f",{lhs}->{' '.join(y)}"

        print("\nGenerated parsing table:\n")
        frmt = "{:>12}" * len(terminals)
        print(frmt.format(*terminals))

        j = 0
        for y in mat:
            frmt1 = "{:>12}" * len(y)
            print(f"{ntlist[j]} {frmt1.format(*y)}")
            j += 1

        return (mat, grammar_is_LL, terminals)

    def validateStringUsingStackBuffer(self, parsing_table, grammarll1, table_term_list, input_string):
        print(f"\nValidate String => {input_string}\n")
        if grammarll1 == False:
            return f"\nInput String = \"{input_string}\"\nGrammar is not LL(1)"
        stack = [self.start_symbol, '$']
        input_string = input_string.split()
        input_string.reverse()
        buffer = ['$'] + input_string

        print("{:>20} {:>20} {:>20}".format("Buffer", "Stack", "Action"))

        while True:
            if stack == ['$'] and buffer == ['$']:
                print("{:>20} {:>20} {:>20}".format(' '.join(buffer), ' '.join(stack), "Valid"))
                return "\nValid String!"
            elif stack[0] not in self.term_userdef:
                x = list(self.diction.keys()).index(stack[0])
                y = table_term_list.index(buffer[-1])
                if parsing_table[x][y] != '':
                    entry = parsing_table[x][y]
                    print("{:>20} {:>20} {:>25}".format(' '.join(buffer), ' '.join(stack), f"T[{stack[0]}][{buffer[-1]}] = {entry}"))
                    lhs_rhs = entry.split("->")
                    lhs_rhs[1] = lhs_rhs[1].replace('#', '').strip()
                    entryrhs = lhs_rhs[1].split()
                    stack = entryrhs + stack[1:]
                else:
                    return f"\nInvalid String! No rule at Table[{stack[0]}][{buffer[-1]}]."
            else:
                if stack[0] == buffer[-1]:
                    print("{:>20} {:>20} {:>20}".format(' '.join(buffer), ' '.join(stack), f"Matched:{stack[0]}"))
                    buffer = buffer[:-1]
                    stack = stack[1:]
                else:
                    return "\nInvalid String! Unmatched terminal symbols"

    def run(self):
        self.computeAllFirsts()
        self.start_symbol = list(self.diction.keys())[0]
        self.computeAllFollows()
        parsing_table, result, tabTerm = self.createParseTable()
        if self.sample_input_string is not None:
            validity = self.validateStringUsingStackBuffer(parsing_table, result, tabTerm, self.sample_input_string)
            print(validity)
        else:
            print("\nNo input String detected")

class ASTNode:
    def __init__(self, tag, linha, valor=None, **kwargs): # Adicione 'valor'
        self.tag = tag
        self.linha = linha
        self.valor = valor # Adicione esta linha
        self.children = []
        for k, v in kwargs.items():
            setattr(self, k, v)
    def to_dict(self):
        base = {"tag": self.tag, "linha": self.linha}
        if self.valor is not None: # Adicione esta condição
            base["valor"] = self.valor
        base.update({k: v for k, v in self.__dict__.items() if k not in ["tag", "linha", "children", "valor"]})
        if self.children:
            base["filhos"] = [child.to_dict() for child in self.children]
        return base

class ASTParser(Parser):
    # ... (init, next_token, peek_token não mudam) ...
    def init(self, rules, nonterm_userdef, term_userdef, sample_input_string=None):
        super().init(rules, nonterm_userdef, term_userdef, sample_input_string)
        self.input_tokens = []
        self.current_token_index = 0

    def next_token(self):
        if self.current_token_index < len(self.input_tokens):
            tok = self.input_tokens[self.current_token_index]
            self.current_token_index += 1
            return tok
        return ('$','EOF')

    def peek_token(self):
        if self.current_token_index < len(self.input_tokens):
            return self.input_tokens[self.current_token_index]
        return ('$','EOF')

    def parse_with_ast(self, parsing_table, grammarll1, table_term_list, input_string):
        if not grammarll1:
            raise ValueError("Grammar is not LL(1)")

    def parse_with_ast(self, parsing_table, grammarll1, table_term_list, input_tokens):
        if not grammarll1:
            raise ValueError("Grammar is not LL(1)")
        
        # O input agora deve ser a lista de Tokens do tokenizer, não a string
        self.input_tokens = input_tokens + [Token(TokenType.EOF, '$', -1)]
        self.current_token_index = 0

        stack = [self.start_symbol]
        root = ASTNode("Bloco", 1) 
        node_stack = [root]
        
        # Mapeia nome do token para o tipo de token literal do tokenizer
        token_map = {t.name.lower(): t for t in TokenType}
        
        # ---------- FUNÇÃO AUXILIAR ----------
        def _tag_ok(simbolo: str) -> str:
            """
            Converte nomes de não-terminais com apóstrofo para algo compatível
            com identificadores Python.  Ex.:  ADD' -> ADD_prime
            """
            return simbolo.replace("'", "_prime")

        while stack:
            # ... (lógica inicial do loop) ...
            top = stack.pop(0)
            current_node = node_stack.pop(0) if node_stack else None

            # Obter o token atual do tokenizer
            tok_obj = self.peek_token()
            tok_type_name = tok_obj.type.name.lower()
            
            # Mapeia token de pontuação para seu próprio literal
            if tok_obj.type in {
                TokenType.ATRIBUICAO, TokenType.PONTO_VIRGULA, TokenType.DOIS_PONTOS,
                TokenType.VIRGULA, TokenType.SOMA, TokenType.SUBTRACAO,
                TokenType.MULTIPLICACAO, TokenType.DIVISAO, TokenType.RESTO,
                TokenType.IGUAL, TokenType.MENOR, TokenType.MAIOR,
                TokenType.PARENTESE_ESQ, TokenType.PARENTESE_DIR
            }:
                tok_type_name = tok_obj.literal

            if tok_obj.type == TokenType.EOF:
                tok_type_name = '$'

            if top == '#':
                continue
            elif top in self.term_userdef:
                if top == tok_type_name:
                    # Se for um terminal, atualiza o nó atual com seu valor e linha.
                    # Nós terminais são folhas e não terão filhos.
                    if current_node:
                       current_node.valor = tok_obj.literal
                       current_node.linha = tok_obj.line
                    self.next_token()
                else:
                    raise SyntaxError(f"Erro de Sintaxe: Esperado '{top}', mas encontrou '{tok_type_name}' na linha {tok_obj.line}")
            elif top in self.nonterm_userdef:
                # Lógica para não-terminais (consulta à tabela de parsing)
                x = list(self.diction.keys()).index(top)
                y = table_term_list.index(tok_type_name)
                rule = parsing_table[x][y]

                if rule == '':
                    raise SyntaxError(f"Erro de Sintaxe: Token inesperado '{tok_type_name}' para a regra '{top}' na linha {tok_obj.line}")

                lhs, rhs_str = rule.split("->")
                rhs_symbols = [sym for sym in rhs_str.strip().split() if sym != '#']

                # Atualiza o nó atual com a regra que está sendo aplicada
                current_node.tag = _tag_ok(lhs)
                
                children_nodes = [
                    ASTNode(tag=_tag_ok(sym), linha=tok_obj.line) for sym in rhs_symbols
                ]
                current_node.children.extend(children_nodes)

                stack = rhs_symbols + stack
                node_stack = children_nodes + node_stack
        
        return root.to_dict()



# Exemplo de uso:
if __name__ == "__main__":

    


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
        "DSQ -> desenhar_quadrado REL ;",
        "DSC -> desenhar_circulo REL ;",
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
    
    code = source_code = """
    inicio
        var inteiro: lado;
        var texto: cor;

        lado = 5;
        cor_de_fundo "black";
        definir_espessura 2;

        // Laço para desenhar a espiral
        repita 50 vezes
            definir_cor "cyan"; // Muda a cor da linha a cada iteração
            
            avancar lado;
            girar_direita 90;

            lado = lado + 5;
        fim_repita;
    fim
    """
    
    sample_input_string = lista_tokens(code)
     # Para usar: substitua parser.run() por:
    parser = ASTParser(rules, nonterm_userdef, term_userdef, sample_input_string)
    parser.computeAllFirsts()
    parser.start_symbol = list(parser.diction.keys())[0]
    parser.computeAllFollows()
    table, result, tab_terms = parser.createParseTable()
    ast_dict = parser.parse_with_ast(table, result, tab_terms, parser.sample_input_string)
    print(ast_dict)  # Já é um dicionário Python pronto para uso
