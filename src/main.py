import os
import json
import sys
from tokenizer import Tokenizer, TokenType, ScanError
from parser import ASTParser
from semantico import SemanticAnalyzer, SemanticError
from gerador import GeradorCodigoVisitor
from utils import rules, nonterm_userdef, term_userdef

ENTRADA_1_CONTEUDO = None
caminho_script = os.path.dirname(__file__)
caminho_entrada = os.path.join(caminho_script, 'tests', sys.argv[1])
caminho_saida = os.path.join(caminho_script, 'tests', sys.argv[2])

try:
  with open(caminho_entrada, 'r', encoding="utf-8") as arquivo:
    ENTRADA_1_CONTEUDO = arquivo.read()
except FileNotFoundError:
  print(f"O arquivo de entrada não foi encontrado em: {caminho_entrada}")
except Exception as e:
  print(f"Ocorreu um erro: {e}")


# Etapa 2: Análise Sintática (Parser)
try:
  print(ENTRADA_1_CONTEUDO)
  tokenizer = Tokenizer(ENTRADA_1_CONTEUDO)
  tokens_list = []
  tok = tokenizer.obter_next_token()
  while tok.type != TokenType.EOF:
      tokens_list.append(tok)
      tok = tokenizer.obter_next_token()

  # Para o parser antigo, que usava a string
  token_string_for_parser = " ".join([t.literal if t.type in {TokenType.ATRIBUICAO, TokenType.PONTO_VIRGULA, TokenType.DOIS_PONTOS} else t.type.name.lower() for t in tokens_list])
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
  semantic_analyzer = SemanticAnalyzer(ast)
  semantic_analyzer.analyze()
  
  # Etapa 4: Geração de Código
  gerador = GeradorCodigoVisitor()
  codigo_gerado = gerador.gerar_codigo(ast)
  print("\n--- Código Gerado ---")
  print(codigo_gerado)
  with open(caminho_saida, 'w', encoding='utf-8') as f:
    f.write(codigo_gerado)
  print(f"\nCódigo salvo em {caminho_saida}")
except ScanError as e:
  print(f"Erro de Análise Léxica: {e}")
# except SyntaxError as e:
#   print(e)
except SemanticError as e:
  print(e)
# except Exception as e:
#   print(f"Ocorreu um erro durante a análise semântica: {e}")

