import sys

class Node:
    def __init__(self, type, children=None, value=None, pos=None, operator=None, reference=None, condition=None):
        self.type = type
        self.children = children if children is not None else []
        self.value = value
        self.pos = pos
        self.operator = operator
        self.reference = reference
        self.condition = condition

    def __repr__(self):
        return self._pretty_print()

    def _pretty_print(self, level=0, prefix="Root: "):
        indent = "    " * level
        result = f"{indent}{prefix}{self.type}"
        
        if self.value is not None:
            result += f" [value: {self.value}]"
        if self.operator:
            result += f" [operator: '{self.operator}']"
        if self.reference:
            result += f" [reference: {self.reference}]"
        if self.condition is not None:
            result += f" [condition: {self.condition}]"
        if self.pos:
            result += f" [pos: {self.pos}]"
            
        result += "\n"
        
        for i, child in enumerate(self.children):
            is_last = i == len(self.children) - 1
            prefix = "└── " if is_last else "├── "
            result += child._pretty_print(level + 1, prefix)
            
        return result

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = lexer.get_next_token()
        self.symbol_table = {'MEM': 0.0}
        self.results = []
        self.line_results = {}
        self.line_count = 1
        self.call_stack = []

    def eat(self, token_type, value=None):
        if self.current_token is None:
            raise Exception(f"Esperado {token_type}, mas fim do arquivo encontrado")
            
        if self.current_token[0] == token_type:
            if value and self.current_token[1] != value:
                raise Exception(f"Esperado {value}, obtido {self.current_token[1]}")
            token = self.current_token
            self.current_token = self.lexer.get_next_token()
            return token
            
        raise Exception(f"Esperado {token_type}, obtido {self.current_token[0]}")

    def parse(self):
        nodes = []
        self.line_count = 1
        
        while self.current_token:
            if self.current_token[0] == 'NEWLINE':
                self.eat('NEWLINE')
                self.line_count += 1
                continue
            
            try:
                if self.current_token[0] == 'PARENTESE_ABRE':
                    self.eat('PARENTESE_ABRE')
                    node = self.expression()
                    self.eat('PARENTESE_FECHA')
                    
                    try:
                        node.value = self.evaluate_expression(node)
                        if node.value is not None:
                            self.results.append(node.value)
                            self.line_results[self.line_count] = node.value
                    except Exception as e:
                        raise Exception(f"Erro ao avaliar expressão: {e}")
                    
                    nodes.append(node)
                else:
                    node = self.simple_expression()
                    if node.value is not None:
                        self.results.append(node.value)
                        self.line_results[self.line_count] = node.value
                    nodes.append(node)
                
            except Exception as e:
                raise Exception(f"Erro na linha {self.line_count}: {e}")
            
            if self.current_token and self.current_token[0] == 'NEWLINE':
                self.eat('NEWLINE')
                self.line_count += 1
                
        return Node('Program', nodes)

    def expression(self):
        elements = []
        
        while self.current_token and self.current_token[0] != 'PARENTESE_FECHA':
            if self.current_token[0] == 'PARENTESE_ABRE':
                self.eat('PARENTESE_ABRE')
                sub_expr = self.expression()
                self.eat('PARENTESE_FECHA')
                elements.append(sub_expr)
            elif self.current_token[0] == 'NUMERO':
                token = self.eat('NUMERO')
                try:
                    value = float(token[1])
                    node = Node('Number', value=value, pos=token[2])
                    elements.append(node)
                except ValueError:
                    raise Exception(f"Número inválido: '{token[1]}' (linha {token[2][0]}, coluna {token[2][1]})")
            elif self.current_token[0] == 'COMANDO':
                token = self.eat('COMANDO')
                if token[1] == 'MEM':
                    node = Node('MemRead', value=self.symbol_table['MEM'], reference='MEM', pos=token[2])
                elif token[1] == 'RES':
                    node = Node('ResRead', reference='RES', pos=token[2])
                else:
                    node = Node('Command', value=token[1], pos=token[2])
                elements.append(node)
            elif self.current_token[0] == 'OPERADOR':
                token = self.eat('OPERADOR')
                node = Node('Operator', value=token[1], pos=token[2])
                elements.append(node)
            elif self.current_token[0] == 'PALAVRA_CHAVE':
                token = self.eat('PALAVRA_CHAVE')
                node = Node('Keyword', value=token[1], pos=token[2])
                elements.append(node)
            elif self.current_token[0] == 'IDENTIFICADOR':
                token = self.eat('IDENTIFICADOR')
                node = Node('Identifier', value=token[1], pos=token[2])
                elements.append(node)
            else:
                raise Exception(f"Token inesperado: '{self.current_token[1]}' (linha {self.current_token[2][0]}, coluna {self.current_token[2][1]})")
        
        return self.process_elements(elements)

    def simple_expression(self):
        if self.current_token[0] == 'NUMERO':
            token = self.eat('NUMERO')
            try:
                value = float(token[1])
                return Node('Number', value=value, pos=token[2])
            except ValueError:
                raise Exception(f"Número inválido: '{token[1]}' (linha {token[2][0]}, coluna {token[2][1]})")
        else:
            raise Exception(f"Token inesperado: '{self.current_token[1]}' (linha {self.current_token[2][0]}, coluna {self.current_token[2][1]})")

    def process_elements(self, elements):
        if len(elements) == 2:
            if elements[1].type == 'MemRead' or (hasattr(elements[1], 'value') and elements[1].value == 'MEM'):
                if elements[0].type == 'Number':
                    self.symbol_table['MEM'] = elements[0].value
                    return Node('MemStore', 
                               children=[elements[0]], 
                               value=elements[0].value,
                               reference='MEM')
                else:
                    return Node('MemRead', 
                               value=self.symbol_table['MEM'],
                               reference='MEM')
            elif elements[1].type == 'ResRead' or (hasattr(elements[1], 'value') and elements[1].value == 'RES'):
                if elements[0].type == 'Number':
                    n = int(elements[0].value)
                    if 0 <= n < len(self.results):
                        value = self.results[-(n+1)]
                        return Node('ResRead', 
                                   value=value,
                                   reference=f'line {self.line_count - n - 1}')
                    raise Exception(f"Referência RES inválida: linha {n} não existe")
                else:
                    raise Exception("RES deve ser precedido por um número")
        
        if len(elements) == 3 and elements[2].type == 'Operator':
            return Node('BinOp', 
                      children=[elements[0], elements[1]], 
                      operator=elements[2].value,
                      pos=elements[2].pos)
        
        if len(elements) >= 4 and elements[1].type == 'Keyword' and elements[1].value == 'if':
            if len(elements) >= 5 and elements[3].value == 'else':
                return Node('If', 
                          children=[elements[0], elements[2], elements[4]])
            else:
                return Node('If', 
                          children=[elements[0], elements[2]])
        
        if len(elements) >= 4 and elements[1].type == 'Keyword' and elements[1].value == 'for':
            return Node('For', 
                      children=elements[:4])
        
        return Node('Expression', children=elements)

    def evaluate_expression(self, node):
        if len(self.call_stack) > 100:
            raise Exception("Estouro de pilha: recursão muito profunda")
            
        self.call_stack.append(node)
        
        try:
            if node.type == 'Number':
                return node.value
                
            elif node.type == 'MemRead':
                return self.symbol_table['MEM']
                
            elif node.type == 'MemStore':
                return node.value
                
            elif node.type == 'ResRead':
                if node.reference and node.reference.startswith('line'):
                    try:
                        parts = node.reference.split()
                        if len(parts) >= 2:
                            n = int(parts[1])
                            if 0 <= n < len(self.results):
                                return self.results[-(n+1)]
                    except:
                        pass
                raise Exception(f"Referência RES inválida: {node.reference}")
                
            elif node.type == 'BinOp':
                left = self.evaluate_expression(node.children[0])
                right = self.evaluate_expression(node.children[1])
                return self.calculate_operation(left, right, node.operator)
                
            elif node.type == 'If':
                condition = self.evaluate_expression(node.children[0])
                if condition != 0:
                    return self.evaluate_expression(node.children[1])
                elif len(node.children) > 2:
                    return self.evaluate_expression(node.children[2])
                return None
                
            elif node.type == 'For':
                initialization = self.evaluate_expression(node.children[0])
                condition_expr = node.children[1]
                increment_expr = node.children[2]
                body = node.children[3]
                
                result = None
                current = initialization
                iteration = 0
                
                while True:
                    condition = self.evaluate_expression(condition_expr)
                    if condition == 0:
                        break
                        
                    if iteration > 1000:
                        raise Exception("Loop infinito detectado")
                    
                    result = self.evaluate_expression(body)
                    current = self.evaluate_expression(increment_expr)
                    iteration += 1
                    
                return result
                
            elif node.type == 'Expression':
                result = None
                for child in node.children:
                    result = self.evaluate_expression(child)
                return result
                
            elif node.type == 'Command':
                if node.value == 'MEM':
                    return self.symbol_table['MEM']
                elif node.value == 'RES':
                    raise Exception("Comando RES sem referência")
                else:
                    raise Exception(f"Comando desconhecido: {node.value}")
                    
            elif node.type == 'Identifier':
                raise Exception(f"Identificador não reconhecido: '{node.value}'")
                
            elif node.type == 'Operator':
                raise Exception(f"Operador '{node.value}' não pode ser avaliado isoladamente")
                
            else:
                raise Exception(f"Não é possível avaliar expressão do tipo: {node.type}")
                
        finally:
            self.call_stack.pop()

    def calculate_operation(self, left, right, op):
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise Exception(f"Operandos devem ser números: left={type(left)}, right={type(right)}")
        
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '|':
            if right == 0:
                raise Exception("Divisão por zero")
            return left / right
        elif op == '/':
            if right == 0:
                raise Exception("Divisão por zero")
            return left // right
        elif op == '%':
            if right == 0:
                raise Exception("Divisão por zero")
            return left % right
        elif op == '^':
            if right < 0:
                raise Exception("Expoente negativo não permitido")
            return left ** right
        elif op == '>':
            return 1.0 if left > right else 0.0
        elif op == '<':
            return 1.0 if left < right else 0.0
        elif op == '>=':
            return 1.0 if left >= right else 0.0
        elif op == '<=':
            return 1.0 if left <= right else 0.0
        elif op == '==':
            return 1.0 if left == right else 0.0
        elif op == '!=':
            return 1.0 if left != right else 0.0
        else:
            raise Exception(f"Operador desconhecido: '{op}'")

def print_ast(node, level=0):
    indent = "    " * level
    print(f"{indent}{node.type}", end="")
    
    if node.value is not None:
        print(f" [value: {node.value}]", end="")
    if node.operator:
        print(f" [operator: '{node.operator}']", end="")
    if node.reference:
        print(f" [reference: {node.reference}]", end="")
    if node.condition is not None:
        print(f" [condition: {node.condition}]", end="")
    if node.pos:
        print(f" [pos: {node.pos}]", end="")
    
    print()
    
    for child in node.children:
        print_ast(child, level + 1)

if __name__ == "__main__":
    from Lexer import Lexer
    
    if len(sys.argv) != 2:
        print("Uso: python parser.py <arquivo>")
        sys.exit(1)
    
    try:
        with open(sys.argv[1], 'r') as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo '{sys.argv[1]}' não encontrado")
        sys.exit(1)
    
    lexer = Lexer(code)
    parser = Parser(lexer)
    
    try:
        ast = parser.parse()
        print("\nÁrvore Sintática Abstrata (AST):")
        print(ast)  # Usa a representação personalizada
        
        print("\nResultados por linha:")
        for line, result in parser.line_results.items():
            print(f"Linha {line}: {result}")
        
        print(f"\nValor final de MEM: {parser.symbol_table['MEM']}")
        
    except Exception as e:
        print(f"\nErro durante análise sintática:\n{e}")
        sys.exit(1)