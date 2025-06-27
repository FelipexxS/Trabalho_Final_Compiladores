# tokenizer.py
import re
from enum import Enum

#Tipos de tokens da nossa linguagem,

class TokenType(Enum):

    # Palavras-chave
    INICIO = "inicio"
    FIM = "fim"
    VAR = "var"
    INTEIRO = "inteiro"
    TEXTO = "texto"
    REAL = "real"
    LOGICO = "logico"
    AVANCAR = "avancar"
    RECUAR = "recuar"
    GIRAR_DIREITA = "girar_direita"
    GIRAR_ESQUERDA = "girar_esquerda"
    IR_PARA = "ir_para"
    LEVANTAR_CANETA = "levantar_caneta"
    ABAIXAR_CANETA = "abaixar_caneta"
    DEFINIR_COR = "definir_cor"
    DEFINIR_ESPESSURA = "definir_espessura"
    COR_DE_FUNDO = "cor_de_fundo"
    LIMPAR_TELA = "limpar_tela"
    REPITA = "repita"
    VEZES = "vezes"
    FIM_REPITA = "fim_repita"
    SE = "se"
    ENTAO = "entao"
    SENAO = "senao"
    FIM_SE = "fim_se"
    ENQUANTO = "enquanto"
    FACA = "faca"
    FIM_ENQUANTO = "fim_enquanto"
    VERDADEIRO = "verdadeiro"
    FALSO = "falso"

    # Identificadores e Literais
    IDENTIFICADOR = "IDENTIFICADOR"                 # nome de variável
    NUMERO_INT = "NUMERO_INT"   # Ex: 100, 5
    NUMERO_REAL = "NUMERO_REAL" # Ex: 144.0, 10.5
    LITERAL_TEXTO = "LITERAL_TEXTO" # Ex: "blue", "black"

    # Operadores e Pontuação
    ATRIBUICAO = "="
    DOIS_PONTOS = ":"
    PONTO_VIRGULA = ";"
    VIRGULA = ","
    SOMA = "+"
    SUBTRACAO = "-"
    MULTIPLICACAO = "*"
    DIVISAO = "/"
    RESTO = "%"
    IGUAL = "=="
    MENOR = "<"
    MAIOR = ">"
    PARENTESE_ESQ = "("
    PARENTESE_DIR = ")"

    # Fim do arquivo
    EOF = "EOF"


# Uma classe simples para armazenar as informações de cada token:
# o seu tipo (da Enum acima) e o seu valor literal (o texto original).
class Token:
    def __init__(self, type, literal, line):
        self.type = type
        self.literal = literal
        self.line = line

    def __repr__(self):
        return f"Token(type={self.type.name}, literal='{self.literal}', line={self.line})"


# Classe main que fará a análise do código-fonte.

class Tokenizer:
    def __init__(self, source_code):
        self.source = source_code
        self.pos = 0  # Posição atual no código-fonte
        if self.pos < len(self.source):
            self.current_char = self.source[self.pos]
        else:
            self.current_char = None
        self.line = 1 # Contador de linha para mensagens de erro

        # Mapeamento de palavras-chave para seus tipos de token
        self.keywords = {
            "inicio": TokenType.INICIO,
            "fim": TokenType.FIM,
            "var": TokenType.VAR,
            "inteiro": TokenType.INTEIRO,
            "texto": TokenType.TEXTO,
            "real": TokenType.REAL,
            "logico": TokenType.LOGICO,
            "avancar": TokenType.AVANCAR,
            "recuar": TokenType.RECUAR,
            "girar_direita": TokenType.GIRAR_DIREITA,
            "girar_esquerda": TokenType.GIRAR_ESQUERDA,
            "ir_para": TokenType.IR_PARA,
            "levantar_caneta": TokenType.LEVANTAR_CANETA,
            "abaixar_caneta": TokenType.ABAIXAR_CANETA,
            "definir_cor": TokenType.DEFINIR_COR,
            "definir_espessura": TokenType.DEFINIR_ESPESSURA,
            "cor_de_fundo": TokenType.COR_DE_FUNDO,
            "limpar_tela": TokenType.LIMPAR_TELA,
            "repita": TokenType.REPITA,
            "vezes": TokenType.VEZES,
            "fim_repita": TokenType.FIM_REPITA,
            "se": TokenType.SE,
            "entao": TokenType.ENTAO,
            "senao": TokenType.SENAO,
            "fim_se": TokenType.FIM_SE,
            "enquanto": TokenType.ENQUANTO,
            "faca": TokenType.FACA,
            "fim_enquanto": TokenType.FIM_ENQUANTO,
            "verdadeiro": TokenType.VERDADEIRO,
            "falso": TokenType.FALSO,
        }

    # -- Métodos auxiliares --

    def advance(self):
        """Avança o ponteiro para o próximo caractere no código."""
        if self.current_char == '\n':
            self.line += 1
        
        self.pos += 1
        if self.pos < len(self.source):
            self.current_char = self.source[self.pos]
        else:
            self.current_char = None # Fim do arquivo

    def peek(self):
        """Espia o próximo caractere sem consumir o atual."""
        peek_pos = self.pos + 1
        if peek_pos < len(self.source):
            return self.source[peek_pos]
        return None

    def skip_whitespace(self):
        """Pula espaços em branco, tabulações e quebras de linha."""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        """Pula comentários de linha única (iniciados com //)."""
        if self.current_char == '/' and self.peek() == '/':
            while self.current_char is not None and self.current_char != '\n':
                self.advance()
            self.skip_whitespace() # Pula a quebra de linha após o comentário

    # -- Métodos de reconhecimento de tokens --

    def number(self):
        """Reconhece números inteiros ou de ponto flutuante (real)."""
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()

        if self.current_char == '.':
            result += '.'
            self.advance()
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()
            return Token(TokenType.NUMERO_REAL, float(result), self.line)
        else:
            return Token(TokenType.NUMERO_INT, int(result), self.line)

    def identifier(self):
        """Reconhece identificadores (variáveis) e palavras-chave."""
        result = ''
        # Um identificador pode começar com uma letra ou _
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        # Verifica se é uma palavra-chave ou um ID comum.
        token_type = self.keywords.get(result, TokenType.IDENTIFICADOR)
        return Token(token_type, result, self.line)

    def string_literal(self):
        """Reconhece literais de texto (strings) entre aspas duplas."""
        self.advance() # Pula a aspa inicial
        result = ''
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        
        if self.current_char is None:
            raise Exception(f"Erro Léxico: String não terminada na linha {self.line}")

        self.advance() # Pula a aspa final
        return Token(TokenType.LITERAL_TEXTO, result, self.line)

    # -- Método Principal --

    def obter_next_token(self):
        """
        O core no nosso analisador léxico. Consome o código-fonte e retorna
        o próximo token encontrado.
        """
        while self.current_char is not None:
            
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            if self.current_char == '/' and self.peek() == '/':
                self.skip_comment()
                continue

            # Reconhecimento de números
            if self.current_char.isdigit():
                return self.number()

            # Reconhecimento de identificadores e palavras-chave
            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()
            
            # Reconhecimento de literais de texto
            if self.current_char == '"':
                return self.string_literal()
            
            # Reconhecimento de operadores de dois caracteres
            if self.current_char == '=' and self.peek() == '=':
                self.advance()
                self.advance()
                return Token(TokenType.IGUAL, '==', self.line)

            # Reconhecimento de operadores e pontuação de um caractere
            # Ou no caso de potenciais erros de não correspondência de tokens
            try:
                # Tentamos encontrar o caractere na Enum para tokens de um caractere
                token_type = TokenType(self.current_char)
                token = Token(token_type, self.current_char, self.line)
                self.advance()
                return token
            except ValueError:
                # Se não for um token válido, lança um erro
                char = self.current_char
                self.advance()
                raise Exception(f"Erro Léxico: Caractere inesperado '{char}' na linha {self.line}")

        # Se o loop terminar, chegamos ao fim do arquivo
        return Token(TokenType.EOF, None, self.line)


def lista_tokens(source_code):

  
    classes_gram = []

    tokenizer = Tokenizer(source_code)
    
    token = tokenizer.obter_next_token()

    while token.type != TokenType.EOF:
        classes_gram.append(token.type.name)
        token = tokenizer.obter_next_token()
    
    return classes_gram



#Exemplo de código

source_code = """
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


#Exemplo com retorno de tokens 

tokens = lista_tokens(source_code)


