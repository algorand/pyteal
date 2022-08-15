import ast
import astor
import pyteal as pt

tree = ast.parse("""
print(itob(3 - 1))
""")

e = pt.Log(pt.Itob(pt.Int(3) - pt.Int(1)))
pyteal_tree = ast.Module(body=[ast.Expr(value=e.__astnode__())], type_ignores=[])
ast.fix_missing_locations(pyteal_tree)


print(astor.to_source(tree))
print(astor.to_source(pyteal_tree))

#exec(compile(tree, filename="<ast>", mode="exec"))
#exec(compile(pyteal_tree, filename="<ast>", mode="exec"))

#import astpretty
#astpretty.pprint(tree)
#astpretty.pprint(pyteal_tree)