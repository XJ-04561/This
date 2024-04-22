


from typing import Any, Self, Callable
from types import MethodType, FunctionType
import itertools, ast

def fformat(a : tuple, d : dict, sep : str=", "):
	return sep.join(itertools.chain(map(str, a), map("{0[0]}={0[1]}".format, d.items())))

class ASTNode:
	def add(self, node : ast.AST):
		self.value = node

class Index(ast.Subscript,ASTNode):
	def __init__(self, key):
		super().__init__(value=self, slice=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=key, ctx=ast.Load()), ctx=ast.Load())

class Call(ast.Call):
	def __init__(self, args, kwargs):
		super().__init__(func=None, args=[ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=x, ctx=ast.Load()) for x in args], keywords=[ast.keyword(arg=name, value=ast.Constant(value=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr=kwargs[name], ctx=ast.Load()))) for name in kwargs])
	
	def add(self, node : ast.AST):
		self.func = node

class Attribute(ast.Attribute,ASTNode):
	def __init__(self, attrName : str):
		super().__init__(value=None, attr=attrName, ctx=ast.Load())

class ThisCallable:
	
	__callback__ : FunctionType
	def __init__(self, docstring : str, node, __dict__):
		self.__doc__ = docstring
		exec(compile(
			ast.Module(
				body=[
					ast.FunctionDef(
						name="__callback__",
						args=ast.arguments(
							args=[
								ast.arg(arg="self", annotation=ast.Name(id="Self", ctx=ast.Load())),
								ast.arg(arg="obj", annotation=None)
							]),
						body=[
							ast.Expr(value=ast.Constant(value=docstring)),
							node
						])],
				info_types=[]
			), filename="this-callback-creation", mode="exec"), __dict__)
		self.__dict__ |= __dict__
	
	def __call__(self : Self, obj : Any) -> Any:
		try:
			return self.__callback__(self, obj)
		except Exception as e:
			e.add_note(self.__doc__)
			raise e
	

oGet = object.__getattribute__

class this:
	"""A `this` statement (class) that acts like the `this` statement in JavaScript.
	When you need a function/lambda/callback to be called by a mapper (like `map`) that accesses each object's attributes
	and methods, then simply put `this` there and do on it what you would want done on each object in your iterable. But
	you must finish it by putting star/asterisk (`*`) in front of it, that makes it return a callable that accesses the
	attributes and calls the methods you want.
	If you want it to try, but skip objects that raise an Exception, then use two stars and pass the resulting map through
	a filter that removes `None`-objects from an iterable/iterator.
	Example:
	```python
	class this: ... # Not part of the example, just here to make the markdown colour it as a class.

	myList = ["Apple", "Lion", "Tennis"]
	myMixedList = ["Apple", 12, b"\x03Oo"]
	for item in map(*this.lower(), myList):
		print(item)
	# apple
	# lion
	# tennis

	for item in map(*this.lower(), myMixedList):
		print(item)
	# AttributeError: 'int' object has no attribute 'lower'

	for item in filter(*this, map(**this.lower(), myMixedList)):
		print(item)
	# apple
	# b'\x03oo'
	```
	"""
	pass
class ThisBase:
	"""A `this` statement (class) that acts like the `this` statement in JavaScript.
	When you need a function/lambda/callback to be called by a mapper (like `map`) that accesses each object's attributes
	and methods, then simply put `this` there and do on it what you would want done on each object in your iterable. But
	you must finish it by putting star/asterisk (`*`) in front of it, that makes it return a callable that accesses the
	attributes and calls the methods you want.
	If you want it to try, but skip objects that raise an Exception, then use two stars and pass the resulting map through
	a filter that removes `None`-objects from an iterable/iterator.
	Example:
	```python
	class this: ... # Not part of the example, just here to make the markdown colour it as a class.

	myList = ["Apple", "Lion", "Tennis"]
	myMixedList = ["Apple", 12, b"\x03Oo"]
	for item in map(*this.lower(), myList):
		print(item)
	# apple
	# lion
	# tennis

	for item in map(*this.lower(), myMixedList):
		print(item)
	# AttributeError: 'int' object has no attribute 'lower'

	for item in filter(*this, map(**this.lower(), myMixedList)):
		print(item)
	# apple
	# b'\x03oo'
	```
	"""
	__name__ : str
	nodeTree : ast.AST
	values : dict
	valuesLength : int
	def __new__(cls) -> None:
		self = super().__new__(cls)
		self.__name__ = "this"
		self.nodeTree = ast.Name(id="obj", ctx=ast.Load())
		self.values = {}
		self.valuesLength = 0
		return self
	
	def __iter__(self):
		yield ThisCallable(oGet(self, '__name__'), oGet(self, 'nodeTree'), oGet(self, 'values'))
	def __next__(self):
		return ThisCallable(oGet(self, '__name__'), oGet(self, 'nodeTree'), oGet(self, 'values'))
	
	def __repr__(self):
		return f"<{oGet(self, '__name__')} at {hex(id(self))}>"

	def __getattribute__(self, name: str) -> Self:
		node = Attribute(name)
		self.__name__ = oGet(self, "__name__") + f".{name}"
		oGet(self, "nodeTree").add(node)
		self.nodeTree = node
		return self
	def __call__(self, *args, **kwargs) -> Self:
		argNames, kwargNames = [], []
		d = oGet(self, "values")
		v = oGet(self, "valuesLength")
		for arg in args:
			name = f"arg{v}"
			d[name] = arg
			argNames.append(name)
			v += 1
		for kwarg in kwargs.values():
			name = f"kwarg{v}"
			d[name] = kwarg
			kwargNames.append(name)
			v += 1
		self.valuesLength = v
		node = Call(args=argNames, kwargs=kwargNames)
		self.__name__ = oGet(self, "__name__") + f"({fformat(args, kwargs)})"
		oGet(self, "nodeTree").add(node)
		self.nodeTree = node
		return self
	def __getitem__(self, key: Any) -> Self:
		name = f"key{oGet(self, 'valuesLength')}"
		oGet(self, "values")[name] = key
		node = Index(name)
		self.__name__ = oGet(self, "__name__") + f"[{key}]"
		oGet(self, "nodeTree").add(node)
		self.nodeTree = node
		return self

class ThisType(type):
	def __getattribute__(self, name: str) -> this:
		obj = oGet(ThisBase, "__new__")(self)
		return oGet(obj, "__getattribute__")(name)
	def __call__(self, *args: Any, **kwds: Any) -> this:
		obj = oGet(ThisBase, "__new__")(self)
		return obj(*args, **kwds)
	def __getitem__(self, key: Any) -> this:
		obj = oGet(ThisBase, "__new__")(self)
		return obj[key]
	def __repr__(self):
		return "<'this' - A Magical Class>"


this = ThisType("this", (ThisBase,), {"__doc__" : ThisBase.__doc__})

if __name__ == "__main__":
	
	class Test:
		def __init__(self, i):
			self._d = {"*":i}
		def wow(self, x):
			return {key:value*x for key,value in self._d.items()}
	
	print(this)
	print(this.att)
	print(this(1,2,h=8))
	print(this[1,3])
	print(this.att(1,2,h=8)[1,3])

	for item in map(*this.wow(2)["*"], [Test(i) for i in range(10)]):
		print(item)
		

	for item in map(next(next(this.wow(2)["*"])), [Test(0), Test(0), "asda", Test(4)]):
		print(item)