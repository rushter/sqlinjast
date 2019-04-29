import ast
import astor
import re

SQL_FUNCTIONS = {
    'execute',
    'executemany',
}
SQL_OPERATORS = re.compile('SELECT|UPDATE|INSERT|DELETE', re.IGNORECASE)


class ASTWalker(ast.NodeVisitor):
    def __init__(self):
        self.candidates = []
        self.variables = {}

    def visit_Call(self, node):
        # Search for function calls with attributes, e.g. cursor.execute
        if isinstance(node.func, ast.Attribute) and node.func.attr in SQL_FUNCTIONS:
            self._check_function_call(node)
        # Traverse child nodes
        self.generic_visit(node)

    def visit_Assign(self, node):
        if not isinstance(node.targets[0], ast.Name):
            return self.generic_visit(node)

        variable, value = node.targets[0].id, node.value
        # Some variable assignments can store SQL queries with string formatting.
        # Save them for later.
        if isinstance(value, (ast.Call, ast.BinOp, ast.Mod)):
            self.variables[variable] = node.value
        self.generic_visit(node)

    def _check_function_call(self, node):
        if not node.args:
            return
        first_argument = node.args[0]
        query = self._check_function_argument(first_argument)
        if query and re.search(SQL_OPERATORS, query):
            self.candidates.append(node)

    def _check_function_argument(self, argument):
        query = None
        if isinstance(argument, ast.Call) and argument.func.attr == 'format':
            # Formatting using .format
            query = argument.func.value.s
        elif isinstance(argument, ast.BinOp) and isinstance(argument.op, ast.Mod):
            # Old-style formatting, .e.g. '%s' % 'string'
            query = argument.left.s
        elif isinstance(argument, ast.JoinedStr) and len(argument.values) > 1:
            # New style f-strings
            query = argument.values[0].s
        elif isinstance(argument, ast.Name) and argument.id in self.variables:
            # If execute function takes a variable as an argument, try to track its real value.
            query = self._check_function_argument(self.variables[argument.id])
        return query


if __name__ == '__main__':
    code = open('webapp.py', 'r').read()
    tree = ast.parse(code)
    ast_walker = ASTWalker()
    ast_walker.visit(tree)

    for candidate in ast_walker.candidates:
        print(astor.to_source(candidate).strip())
