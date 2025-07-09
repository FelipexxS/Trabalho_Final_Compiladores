from tokenizer import Tokenizer, TokenType
from parser import ASTParser
from semantico import SemanticAnalyzer, SemanticError
import json
from gerador import GeradorCodigoVisitor

ENTRADA_1_CONTEUDO = None

try:
  with open('D:\\Estudos-Projetos\\Projeto-Compiladores\\Trabalho_Final_Compiladores\\src\\tests\\entrada1.txt', 'r', encoding="utf-8") as arquivo:
    ENTRADA_1_CONTEUDO = arquivo.read()
except FileNotFoundError:
  print("O arquivo não foi encontrado.")
except Exception as e:
  print(f"Ocorreu um erro: {e}")

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
# parser = ASTParser(rules, nonterm_userdef, term_userdef, tokens)
# parser.computeAllFirsts()
# parser.start_symbol = list(parser.diction.keys())[0]
# parser.computeAllFollows()
# table, result, tab_terms = parser.createParseTable()
# ast_dict = parser.parse_with_ast(table, result, tab_terms, parser.sample_input_string)
# # 2) converte para AST semântica
# resultado_semantico = analisar_semantica(ast_dict)

# print(resultado_semantico)
tokenizer = Tokenizer(ENTRADA_1_CONTEUDO)
tokens_list = []
tok = tokenizer.obter_next_token()
while tok.type != TokenType.EOF:
    tokens_list.append(tok)
    tok = tokenizer.obter_next_token()

# Para o parser antigo, que usava a string
token_string_for_parser = " ".join([t.literal if t.type in {TokenType.ATRIBUICAO, TokenType.PONTO_VIRGULA, TokenType.DOIS_PONTOS} else t.type.name.lower() for t in tokens_list])


# Etapa 2: Análise Sintática (Parser)
parser = ASTParser(rules, nonterm_userdef, term_userdef, token_string_for_parser)
parser.computeAllFirsts()
parser.start_symbol = list(parser.diction.keys())[0]
parser.computeAllFollows()
table, result, tab_terms = parser.createParseTable()

# Geração da AST usando a lista de tokens original
print("\n--- Iniciando Geração da AST ---")
ast = parser.parse_with_ast(table, result, tab_terms, tokens_list)
print("--- AST Gerada com Sucesso! ---")
print(json.dumps(ast, indent=2)) # Imprime a AST formatada

# Etapa 3: Análise Semântica
try:
    semantic_analyzer = SemanticAnalyzer(ast)
    semantic_analyzer.analyze()
except SemanticError as e:
    print(e)
except Exception as e:
    print(f"Ocorreu um erro durante a análise semântica: {e}")

# Etapa 4: Geração de Código
gerador = GeradorCodigoVisitor()
codigo_gerado = gerador.gerar_codigo(ast)
print("\n--- Código Gerado ---")
print(codigo_gerado)