class NodeVisitor:
    """Classe base para percorrer recursivamente uma AST de dicionários."""

    def visit(self, node: Dict[str, Any]):
        metodo = getattr(self, f"visit_{node['tag']}", self.generic_visit)
        return metodo(node)

    def generic_visit(self, node: Dict[str, Any]):  # pragma: no cover
        raise RuntimeError(f"Nó não suportado: {node['tag']}")