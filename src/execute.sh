#!/bin/bash

# --- Validação dos Argumentos ---
# Verifica se o número de argumentos passados para o script é diferente de 2.
# $# é uma variável especial que contém o número de argumentos.
echo "Como usar: ./executar.sh <caminho_do_arquivo_de_entrada> <caminho_do_arquivo_de_saida>"

if [ "$#" -ne 2 ]; then
    echo "Erro: Uso incorreto."
    exit 1 # Encerra o script com um código de erro
fi

ARQUIVO_ENTRADA="$1"
ARQUIVO_SAIDA="$2"

echo "Iniciando processo..."
echo "  - Lendo de: $ARQUIVO_ENTRADA"
echo "  - Escrevendo para: $ARQUIVO_SAIDA"
echo ""

python main.py "$ARQUIVO_ENTRADA" "$ARQUIVO_SAIDA"

echo ""
echo "Processo finalizado com sucesso."