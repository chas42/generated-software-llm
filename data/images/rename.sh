#!/bin/bash

# Diretório contendo os arquivos
DIR="/home/chas/Downloads/images/Bengal"

# Definir o prefixo do novo nome dos arquivos
PREFIXO="Bengal"

# Contador para numerar os arquivos
CONTADOR=1

# Loop para percorrer os arquivos no diretório
for ARQ in "$DIR"/*; do
    # Verifica se é um arquivo
    if [[ -f "$ARQ" ]]; then
        # Obtém a extensão do arquivo
        EXT="${ARQ##*.}"
        
        # Define o novo nome do arquivo
        NOVO_NOME="${DIR}/${PREFIXO}_test_${CONTADOR}.${EXT}"
        
        # Renomeia o arquivo
        mv "$ARQ" "$NOVO_NOME"
        
        # Incrementa o contador
        ((CONTADOR++))
    fi
done

echo "Arquivos renomeados com sucesso!"
