from utils import NodeVisitor

class GeradorCodigoVisitor(NodeVisitor):
  """
  Percorre a AST (após análise semântica) e gera código Python para biblioteca turtle.
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
      "desenhar_quadrado": "desenhar_quadrado",
      "desenhar_circulo": "desenhar_circulo"
    }
    
  def gerar_codigo(self, ast_raiz: Dict[str, Any]) -> str:
    """
    Método principal para iniciar a geração de código.
    """
    self.codigo = [
      "import turtle",
      "import math",
      "",
      "tela = turtle.screen()",
      "turtle.speed('fast')",
      "",
    ]
    self.visit(ast_raiz)
    self.codigo.append("\ntela.exitonclick()")
    return "\n".join(self.codigo)
  
  def _indentador(self) -> str:
    """
    Retorna a string de indentação atual.
    """
    return "    " * self.indent_level
  
  def _add_linha(self, linha: str) -> None:
    """
    Adiciona uma linha de código ao código
    """
    self.codigo.append(f"{self._indentador()}{linha}")
  
  def visit_Bloco(self, node: Dict[str, Any]):
    for filho in node.get("filhos", []):
      self.visit(filho)
  
  def visit_DeclaracaoVar(self, node: Dict[str, Any]):
    tipo = node["tipo"]
    ident = node["ident"]
    valor_inicial = "None"
    if tipo in ("inteiro", "real"):
      valor_inicial = "0"
    elif tipo == "texto":
      valor_inicial = "\"\""
    elif tipo == "logico":
      valor_inicial = "False"

    self._add_linha(f"{ident} = {valor_inicial}")
    
    if node.get("filhos"):
      expr_node = node["filhos"][0]
      valor_expr = self.visit(expr_node)
      self._add_linha(f"{ident} = {valor_expr}")
  
  def visit_Atribuicao(self, node: Dict[str, Any]):
    var_node, expr_node = node["filhos"]
    nome_var = self.visit(var_node)
    valor_expr = self.visit(var_node)
    self._add_linha(f"{nome_var} = {valor_expr}")
  
  def visit_ExprBinaria(self, node: Dict[str, Any]):
    lhs = self.visit(node["filhos"][0])
    rhs = self.visit(node["filhos"][1])
    op = node["op"]
    return f"{lhs} {op} {rhs}"
  
  def visit_Identificador(self, node: Dict[str, Any]):
    return node["lexema"]
  
  def visit_Literal(self, node: Dict[str, Any]):
    tipo = node["tipo"]
    valor = node["valor"]
    if tipo == "texto":
      return f'"{valor}"'
    if tipo == "logico":
      return "True" if valor == "verdadeiro" else "False"
    return str(valor)
  
  def visit_FuncaoCall(self, node: Dict[str, Any]):
    nome_funcao = node["nome"]
    
    if nome_funcao in self.mapa_comandos:
      nome_turtle = self.mapa_comandos[nome_funcao]
      args = [str(self.visit(arg)) for arg in node.get("filhos", [])]
      self._add_linha(f"{nome_turtle}({', '.join(args)})")
    else:
      pass
  
  def visit_Repita(self, node: Dict[str, Any]):
    vezes_node, corpo_node = node["filhos"]
    num_vezes = self.visit(vezes_node)
    
    self._add_linha(f"for _ in range({num_vezes}):")
    self.indent_level += 1
    self.visit(corpo_node)
    self.indent_level -= 1

  def visit_se(self, node: Dict[str, Any]):
    filhos = node["filhos"]
    cond_node, then_node = filhos[0], filhos[1]
    
    cond_expr = self.visit(cond_node)
    self._add_linha(f"if {cond_expr}:")
    
    self.indent_level += 1
    self.visit(then_node)
    self.indent_level -= 1
    
    if len(filhos) > 2:
      else_node = filhos[2]
      self._add_linha("else:")
      self.indent_level += 1
      self.visit(else_node)
      self.indent_level -= 1
    
  def visit_Enquanto(self, node: Dict[str, Any]):
    cond_node, corpo_node = node["filhos"]
    
    cond_expr = self.visit(cond_node)
    self._add_linha(f"while {cond_expr}:")
    
    self.indent_level += 1
    self.visit(corpo_node)
    self.indent_level -= 1
