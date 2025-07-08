from gerador import GeradorCodigoVisitor

"""Exemplo de entrada para o teste escopado do gerador de código:
  inicio
    var inteiro: lado;

    lado = 10;
    definir_cor "cyan";
    cor_de_fundo "black";

    repita 50 vezes
        avancar lado;
        girar_direita 91;
        lado = lado + 5;
    fim_repita;
  fim
"""

ast_exemplo = {
    "tag": "Bloco",
    "linha": 1,
    "filhos": [
        {
            "tag": "DeclaracaoVar",
            "linha": 2,
            "tipo": "inteiro",
            "ident": "lado",
            "filhos": []
        },
        {
            "tag": "Atribuicao",
            "linha": 4,
            "filhos": [
                {"tag": "Identificador", "linha": 4, "lexema": "lado"},
                {"tag": "Literal", "linha": 4, "tipo": "inteiro", "valor": 10}
            ]
        },
        {
            "tag": "FuncaoCall",
            "linha": 5,
            "nome": "definir_cor",
            "filhos": [
                {"tag": "Literal", "linha": 5, "tipo": "texto", "valor": "cyan"}
            ]
        },
        {
            "tag": "FuncaoCall",
            "linha": 6,
            "nome": "cor_de_fundo",
            "filhos": [
                {"tag": "Literal", "linha": 6, "tipo": "texto", "valor": "black"}
            ]
        },
        {
            "tag": "Repita",
            "linha": 8,
            "filhos": [
                {"tag": "Literal", "linha": 8, "tipo": "inteiro", "valor": 50},
                {
                    "tag": "Bloco",
                    "linha": 8,
                    "filhos": [
                        {
                            "tag": "FuncaoCall",
                            "linha": 9,
                            "nome": "avancar",
                            "filhos": [
                                {"tag": "Identificador", "linha": 9, "lexema": "lado"}
                            ]
                        },
                        {
                            "tag": "FuncaoCall",
                            "linha": 10,
                            "nome": "girar_direita",
                            "filhos": [
                                {"tag": "Literal", "linha": 10, "tipo": "inteiro", "valor": 91}
                            ]
                        },
                        {
                            "tag": "Atribuicao",
                            "linha": 11,
                            "filhos": [
                                {"tag": "Identificador", "linha": 11, "lexema": "lado"},
                                {
                                    "tag": "ExprBinaria",
                                    "linha": 11,
                                    "op": "+",
                                    "filhos": [
                                        {"tag": "Identificador", "linha": 11, "lexema": "lado"},
                                        {"tag": "Literal", "linha": 11, "tipo": "inteiro", "valor": 5}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

gerador = GeradorCodigoVisitor()

codigo_python_gerado = gerador.gerar_codigo(ast_exemplo)

print(codigo_python_gerado)

with open("D:\\Estudos-Projetos\\Projeto-Compiladores\\Trabalho_Final_Compiladores\\src\\tests\\saida_teste.py", "w", encoding="utf-8") as f:
    f.write(codigo_python_gerado)

print("\n Código salvo em 'tests/saida_teste.py'")

