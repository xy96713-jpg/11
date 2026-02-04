import ast
import sys

filename = 'enhanced_harmonic_set_sorter.py'
with open(filename, 'r', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)

class LoopWrapper(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        if node.name == 'enhanced_harmonic_sort':
            # Find the main while loop: while has_unused_tracks() ...
            for i, child in enumerate(node.body):
                if isinstance(child, ast.While):
                    # Found the loop! 
                    # Now find the inner loop: for track in candidate_tracks:
                    inner_loop = None
                    for subchild in child.body:
                        if isinstance(subchild, ast.For) and getattr(subchild.target, 'id', '') == 'track':
                             inner_loop = subchild
                             break
                    
                    if inner_loop:
                        # Wrap the body of the inner loop in Try
                        # try:
                        #    original_body
                        # except Exception:
                        #    continue
                        
                        try_node = ast.Try(
                            body=inner_loop.body,
                            handlers=[
                                ast.ExceptHandler(
                                    type=ast.Name(id='Exception', ctx=ast.Load()),
                                    name=None,
                                    body=[ast.Continue()]
                                )
                            ],
                            orelse=[],
                            finalbody=[]
                        )
                        inner_loop.body = [try_node]
                        print("Wrapped inner loop in enhanced_harmonic_sort")
        return node

optimizer = LoopWrapper()
new_tree = optimizer.visit(tree)
ast.fix_missing_locations(new_tree)

# Generate code
import ast
# Python's ast module doesn't convert back to code easily in 3.8 (unparse came in 3.9)
# Assuming user environment has python 3.9+ ? 
# If not, we fall back to line string manipulation which we already tried.

try:
    source_code = ast.unparse(new_tree)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(source_code)
    print("Success using AST unparse.")
except AttributeError:
    print("ast.unparse not available. Manual fallback required.")
    
