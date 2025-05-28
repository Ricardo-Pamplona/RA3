import sys

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None
        self.line = 1
        self.column = 1
        self.current_state = "S0"
        self.buffer = ""
        self.start_pos = (self.line, self.column)

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.column = 0
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
            self.column += 1
        else:
            self.current_char = None

    def reset_state(self):
        self.current_state = "S0"
        self.buffer = ""
        self.start_pos = (self.line, self.column)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_state == "S0":
                token = self.state_S0()
                if token: return token
            elif self.current_state == "S1":
                token = self.state_S1()
                if token: return token
            elif self.current_state == "S2":
                token = self.state_S2()
                if token: return token
            elif self.current_state == "S3":
                token = self.state_S3()
                if token: return token
            elif self.current_state == "S4":
                token = self.state_S4()
                if token: return token
            elif self.current_state == "S5":
                self.state_S5()
        return None

    # ---------------------------------------------
    # S0: Estado Inicial
    # ---------------------------------------------
    def state_S0(self):
        self.start_pos = (self.line, self.column)
        self.buffer = ""

        # Identifica quebras de linha
        if self.current_char == '\n':
            token = ('NEWLINE', '\n', self.start_pos)
            self.advance()
            return token

        # Ignora espaços em branco
        if self.current_char.isspace():
            self.advance()
            return None

        # Ignora comentários
        if self.current_char == '#':
            while self.current_char not in ('\n', None):
                self.advance()
            if self.current_char == '\n':
                self.advance()
            return None

        # Parênteses
        if self.current_char in '()':
            token_type = 'PARENTESE_ABRE' if self.current_char == '(' else 'PARENTESE_FECHA'
            token = (token_type, self.current_char, self.start_pos)
            self.advance()
            return token

        # Operadores (incluindo operadores de comparação)
        elif self.current_char in '+-*/|%^><=':
            self.current_state = "S3"
            self.buffer = self.current_char
            self.advance()
            # Verificar se é operador composto (>=, <=, ==)
            if self.current_char == '=' and self.buffer in ['>', '<', '=']:
                self.buffer += self.current_char
                self.advance()
            return None

        # Números (inteiros e decimais)
        elif self.current_char.isdigit() or self.current_char == '.':
            self.current_state = "S1"
            self.buffer += self.current_char
            self.advance()
            return None

        # Identificadores
        elif self.current_char.isalpha() or self.current_char == '_':
            self.current_state = "S2"
            self.buffer += self.current_char
            self.advance()
            return None

        # Caractere inválido
        else:
            raise Exception(f"Caractere inválido: '{self.current_char}' (linha {self.line}, coluna {self.column})")

    # ---------------------------------------------
    # S1: Processando Números
    # ---------------------------------------------
    def state_S1(self):
        decimal_point_count = self.buffer.count('.')
        
        if self.current_char == '.':
            if decimal_point_count == 0:
                self.buffer += self.current_char
                self.advance()
                return None
            else:
                # Já tem ponto decimal, erro
                self.current_state = "S5"
                return None
                
        elif self.current_char.isdigit():
            self.buffer += self.current_char
            self.advance()
            return None
            
        else:
            # Verifica se é número válido
            if '.' in self.buffer:
                if self.buffer.startswith('.') or self.buffer.endswith('.'):
                    self.current_state = "S5"
                    return None
                    
            token = ('NUMERO', self.buffer, self.start_pos)
            self.reset_state()
            return token

    # ---------------------------------------------
    # S2: Processando Identificadores
    # ---------------------------------------------
    def state_S2(self):
        if self.current_char.isalpha() or self.current_char == '_' or self.current_char.isdigit():
            self.buffer += self.current_char
            self.advance()
            return None
        else:
            # Identifica palavras-chave e comandos
            if self.buffer.upper() in ['RES', 'MEM']:
                token = ('COMANDO', self.buffer.upper(), self.start_pos)
            elif self.buffer in ['if', 'then', 'else', 'for']:
                token = ('PALAVRA_CHAVE', self.buffer, self.start_pos)
            else:
                token = ('IDENTIFICADOR', self.buffer, self.start_pos)
            self.reset_state()
            return token

    # ---------------------------------------------
    # S3: Processando Operadores
    # ---------------------------------------------
    def state_S3(self):
        token = ('OPERADOR', self.buffer, self.start_pos)
        self.reset_state()
        return token

    # ---------------------------------------------
    # S5: Erro de Número Inválido
    # ---------------------------------------------
    def state_S5(self):
        raise Exception(f"Número inválido: '{self.buffer}' (linha {self.start_pos[0]}, coluna {self.start_pos[1]})")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python lexer.py <arquivo_de_teste>")
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo '{sys.argv[1]}' não encontrado")
        sys.exit(1)

    lexer = Lexer(code)
    
    try:
        while True:
            token = lexer.get_next_token()
            if token is None: break
            print(f"{token[0]:<15} | Valor: {token[1]:<6} | Posição: {token[2]}")
    except Exception as e:
        print(f"\nErro durante análise léxica:\n{e}")
        sys.exit(1)