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
            "tag": "FuncaoCall",
            "linha": 7,
            "nome": "desenhar_quadrado",
            "filhos": [
                { "tag": "Literal", "linha": 7, "tipo": "inteiro", "valor": 100 },
                { "tag": "Literal", "linha": 7, "tipo": "inteiro", "valor": 90 },
                { "tag": "Literal", "linha": 7, "tipo": "texto", "valor": "cyan" },
            ]
        },
    ]
}

gerador = GeradorCodigoVisitor()

codigo_python_gerado = gerador.gerar_codigo(ast_exemplo)

print(codigo_python_gerado)

with open("D:\\Estudos-Projetos\\Projeto-Compiladores\\Trabalho_Final_Compiladores\\src\\tests\\saida_teste.py", "w", encoding="utf-8") as f:
    f.write(codigo_python_gerado)

print("\n Código salvo em 'tests/saida_teste.py'")

