from utils import NodeVisitor
from typing import List, Dict, Any

class GeradorCodigoVisitor(NodeVisitor):
  """
  Percorre a AST (do parser) e gera código Python para biblioteca turtle.
  """
  def __init__(self):
    self.codigo: List[str] = []
    self.indent_level: int = 0
    
    self.mapa_comandos_turtle = {
      "avancar": "turtle.forward",
      "recuar": "turtle.backward",
      "girar_direita": "turtle.right",
      "girar_esquerda": "turtle.left",
      "ir_para": "turtle.goto",
      "levantar_caneta": "turtle.penup",
      "abaixar_caneta": "turtle.pendown",
      "definir_cor": "turtle.color",
      "definir_espessura": "turtle.pensize",
      "cor_de_fundo": "turtle.bgcolor",
      "limpar_tela": "turtle.clear",
    }
  
  def gerar_codigo(self, ast_raiz: Dict[str, Any]) -> str:
    self.codigo = [
      "import turtle",
      "import math",
      "",
      "tela = turtle.Turtle()",
      "turtle.speed('fast')",
      "",
    ]
    self.visit(ast_raiz)
    self.codigo.append("\nturtle.done()")
    return "\n".join(self.codigo)
  
  def _indentador(self) -> str:
    return "    " * self.indent_level
  
  def _add_linha(self, linha: str) -> None:
    self.codigo.append(f"{self._indentador()}{linha}")

  def generic_visit(self, node: Dict[str, Any]):
    """Visita os filhos de um nó genérico."""
    for filho in node.get("filhos", []):
      self.visit(filho)

  # Handlers para a estrutura da gramática (não geram código, apenas atravessam)
  def visit_S(self, node): self.generic_visit(node)
  def visit_B(self, node): self.generic_visit(node)
  def visit_CMDS(self, node): self.generic_visit(node)
  def visit_CMD(self, node): self.generic_visit(node)
  def visit_TYPE(self, node): self.generic_visit(node)
  def visit_ATT(self, node): self.generic_visit(node)
  def visit_SE_CONT(self, node): self.generic_visit(node)
  def visit_OP_REL(self, node): self.generic_visit(node)


  def visit_DECL(self, node: Dict[str, Any]):
    type_node = node['filhos'][1]
    id_node = node['filhos'][3]
    
    var_type = type_node['filhos'][0]['tag']
    var_name = self.visit(id_node)

    valor_inicial = "None"
    if var_type == "inteiro" or var_type == "real": valor_inicial = "0"
    elif var_type == "texto": valor_inicial = '""'
    elif var_type == "logico": valor_inicial = "False"
    self._add_linha(f"{var_name} = {valor_inicial}")

  def visit_ATR(self, node: Dict[str, Any]):
    att_node = node['filhos'][0]
    var_name = self.visit(att_node['filhos'][0])
    expr_val = self.visit(att_node['filhos'][2])
    self._add_linha(f"{var_name} = {expr_val}")

  def visit_REL(self, node):
    lhs = self.visit(node['filhos'][0]) or ""
    rhs = self.visit(node['filhos'][1]) or ""
    return f"{lhs}{rhs}"
    
  def visit_REL_prime(self, node):
    if not node.get('filhos'): return ""
    op = self.visit(node['filhos'][0]) or ""
    rhs = self.visit(node['filhos'][1]) or ""
    rest = self.visit(node['filhos'][2]) or ""
    return f" {op} {rhs}{rest}"

  def visit_OP_REL(self, node):
    return node['filhos'][0].get('valor', '')

  def visit_ADD(self, node):
    lhs = self.visit(node['filhos'][0]) or ""
    rhs = self.visit(node['filhos'][1]) or ""
    return f"{lhs}{rhs}"
    
  def visit_ADD_prime(self, node):
    if not node.get('filhos'): return ""
    op = node['filhos'][0].get('valor', '')
    rhs = self.visit(node['filhos'][1]) or ""
    rest = self.visit(node['filhos'][2]) or ""
    return f" {op} {rhs}{rest}"

  def visit_MUL(self, node):
    lhs = self.visit(node['filhos'][0]) or ""
    rhs = self.visit(node['filhos'][1]) or ""
    return f"{lhs}{rhs}"

  def visit_MUL_prime(self, node):
    if not node.get('filhos'): return ""
    op = node['filhos'][0].get('valor', '')
    rhs = self.visit(node['filhos'][1]) or ""
    rest = self.visit(node['filhos'][2]) or ""
    return f" {op} {rhs}{rest}"

  def visit_FACTOR(self, node):
    child = node['filhos'][0]
    if child['tag'] == '(':
        return f"({self.visit(node['filhos'][1])})"
    else:
        return self.visit(child)

  def visit_ID(self, node): return node['filhos'][0]['valor']
  def visit_NUM(self, node): return node['filhos'][0]['valor']
  def visit_TEXT(self, node): return f"\"{node['filhos'][0]['valor']}\""
  def visit_BOOL(self, node):
    val = node['filhos'][0]['valor']
    return "True" if val == "verdadeiro" else "False"

  def _visit_simple_cmd(self, node: Dict[str, Any]):
    cmd_name = node['filhos'][0]['tag']
    turtle_cmd = self.mapa_comandos_turtle.get(cmd_name)
    if turtle_cmd:
        if len(node['filhos']) > 1 and node['filhos'][1]['tag'] == 'REL':
            arg_val = self.visit(node['filhos'][1])
            self._add_linha(f"{turtle_cmd}({arg_val})")
        else:
             self._add_linha(f"{turtle_cmd}()")
  
  visit_AV = _visit_simple_cmd
  visit_REC = _visit_simple_cmd
  visit_GD = _visit_simple_cmd
  visit_GE = _visit_simple_cmd
  visit_DC = _visit_simple_cmd
  visit_DE = _visit_simple_cmd
  visit_CDF = _visit_simple_cmd
  
  def visit_LC(self, node): self._add_linha("turtle.penup()")
  def visit_AC(self, node): self._add_linha("turtle.pendown()")
  def visit_LP(self, node): self._add_linha("turtle.clear()")
  
  def visit_IRP(self, node):
      arg1 = self.visit(node['filhos'][1])
      arg2 = self.visit(node['filhos'][2])
      self._add_linha(f"turtle.goto({arg1}, {arg2})")
      
  def visit_DSQ(self, node):
      lado = self.visit(node['filhos'][1])
      self._add_linha(f"for _ in range(4):")
      self.indent_level += 1
      self._add_linha(f"turtle.forward({lado})")
      self._add_linha(f"turtle.right(90)")
      self.indent_level -= 1

  def visit_DSC(self, node):
      raio = self.visit(node['filhos'][1])
      self._add_linha(f"turtle.circle({raio})")

  def visit_REP(self, node: Dict[str, Any]):
    num_vezes = self.visit(node['filhos'][1])
    corpo_node = node['filhos'][3]
    
    self._add_linha(f"for _ in range(int({num_vezes})):")
    self.indent_level += 1
    self.visit(corpo_node)
    self.indent_level -= 1

  def visit_SE(self, node: Dict[str, Any]):
    cond_node = node['filhos'][1]
    then_node = node['filhos'][3]
    se_cont_node = node['filhos'][4]
    
    cond_expr = self.visit(cond_node)
    self._add_linha(f"if {cond_expr}:")
    
    self.indent_level += 1
    self.visit(then_node)
    self.indent_level -= 1
    
    if len(se_cont_node['filhos']) > 2:
      else_node = se_cont_node['filhos'][1]
      self._add_linha("else:")
      self.indent_level += 1
      self.visit(else_node)
      self.indent_level -= 1
    
  def visit_ENQ(self, node: Dict[str, Any]):
    cond_node = node['filhos'][1]
    corpo_node = node['filhos'][3]
    
    cond_expr = self.visit(cond_node)
    self._add_linha(f"while {cond_expr}:")
    
    self.indent_level += 1
    self.visit(corpo_node)
    self.indent_level -= 1
