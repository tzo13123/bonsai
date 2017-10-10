
#Copyright (c) 2017 Andre Santos
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

###############################################################################
# Imports
###############################################################################

from ..model import *


###############################################################################
# Language Model
###############################################################################

CppEntity = CodeEntity

CppStatementGroup = CodeStatementGroup


# ----- Common Entities -------------------------------------------------------

class CppVariable(CodeVariable):
    def __init__(self, scope, parent, id, name, result):
        CodeVariable.__init__(self, scope, parent, id, name, result)
        self.full_type = result
        self.result = result[6:] if result.startswith("const ") else result


class CppFunction(CodeFunction):
    def __init__(self, scope, parent, id, name, result):
        CodeFunction.__init__(self, scope, parent, id, name, result)
        self.full_type = result
        self.result = result[6:] if result.startswith("const ") else result

    @property
    def is_constructor(self):
        return self.member_of and self.name == self.member_of.name

    # def _afterpass(self):
        # left side can be CALL_EXPR: operator[] or operator()
        # or ARRAY_SUBSCRIPT_EXPR: a[]
        # or UNARY_OPERATOR: *a
        # or PAREN_EXPR: (*a)


CppClass = CodeClass

CppNamespace = CodeNamespace

CppGlobalScope = CodeGlobalScope


# ----- Expression Entities ---------------------------------------------------

class CppExpression(CodeExpression):
    def __init__(self, scope, parent, name, result, paren = False):
        CodeExpression.__init__(self, scope, parent,
                                name, result, paren = False)
        self.full_type = result
        self.result = result[6:] if result.startswith("const ") else result


SomeCpp = SomeValue


class CppReference(CodeReference):
    def pretty_str(self, indent = 0):
        spaces = (" " * indent)
        pretty = "{}({})" if self.parenthesis else "{}{}"
        name = self.name
        if self.field_of:
            o = self.field_of
            if isinstance(o, CppFunctionCall) and o.name == "operator->":
                name = o.arguments[0].pretty_str() + "->" + self.name
            else:
                name = o.pretty_str() + "." + self.name
        return pretty.format(spaces, name)


class CppOperator(CodeOperator):
    _UNARY_TOKENS = ("+", "-", "++", "--", "*", "&", "!", "~")

    _BINARY_TOKENS = ("+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>",
                      "<", ">", "<=", ">=", "==", "!=", "&&", "||", "=",
                      "+=", "-=", "*=", "/=", "%=", "<<=", ">>=", "&=",
                      "|=", "^=", ",")

    @property
    def is_assignment(self):
        return (self.name == "=" or self.name == "+=" or self.name == "-="
                or self.name == "*=" or self.name == "/=" or self.name == "%="
                or self.name == "&=" or self.name == "|=" or self.name == "^="
                or self.name == "<<=" or self.name == ">>=")

    def pretty_str(self, indent = 0):
        indent = (" " * indent)
        pretty = "{}({})" if self.parenthesis else "{}{}"
        operator = self.name
        if self.is_unary:
            if self.name.startswith("_"):
                operator = pretty_str(self.arguments[0]) + self.name[1:]
            else:
                operator += pretty_str(self.arguments[0])
        else:
            operator = "{} {} {}".format(pretty_str(self.arguments[0]),
                                         self.name,
                                         pretty_str(self.arguments[1]))
        return pretty.format(indent, operator)


class CppFunctionCall(CodeFunctionCall):
    def __init__(self, scope, parent, name, result):
        CodeFunctionCall.__init__(self, scope, parent, name, result)
        self.template = None

    @property
    def is_constructor(self):
        result = self.result.split("::")[-1]
        if result.endswith(" *"):
            result = result[:-2]
        return result == self.name

    def _set_method(self, cppobj):
        assert isinstance(cppobj, CodeExpression)
        self.method_of = cppobj
        self.full_name = cppobj.result + "::" + self.name

    def pretty_str(self, indent = 0):
        indent = " " * indent
        pretty = "{}({})" if self.parenthesis else "{}{}"
        call = self.name
        operator = self.name[8:]
        args = [pretty_str(arg) for arg in self.arguments]
        if operator in CppOperator._BINARY_TOKENS:
            call = "{} {} {}".format(args[0], operator, args[1])
        else:
            temp = "<" + ",".join(self.template) + ">" if self.template else ""
            args = ", ".join(args)
            if self.method_of:
                o = self.method_of
                if isinstance(o, CppFunctionCall) and o.name == "operator->":
                    call = "{}->{}{}({})".format(o.arguments[0].pretty_str(),
                                                 self.name, temp, args)
                else:
                    call = "{}.{}{}({})".format(o.pretty_str(),
                                                self.name, temp, args)
            elif self.is_constructor:
                call = "new {}{}({})".format(self.name, temp, args)
            else:
                call = "{}{}({})".format(self.name, temp, args)
        return pretty.format(indent, call)

    def __repr__(self):
        temp = "<" + ",".join(self.template) + ">" if self.template else ""
        args = ", ".join([str(arg) for arg in self.arguments])
        if self.is_constructor:
            return "[{}] new {}({})".format(self.result, self.name, args)
        if self.method_of:
            return "[{}] {}.{}{}({})".format(self.result, self.method_of.name,
                                           self.name, temp, args)
        return "[{}] {}{}({})".format(self.result, self.name, temp, args)


CppDefaultArgument = CodeDefaultArgument


# ----- Statement Entities ----------------------------------------------------

CppStatement = CodeStatement

CppJumpStatement = CodeJumpStatement

CppExpressionStatement = CodeExpressionStatement

CppBlock = CodeBlock

CppDeclaration = CodeDeclaration

CppControlFlow = CodeControlFlow

CppConditional = CodeConditional


class CppLoop(CodeLoop):
    def pretty_str(self, indent = 0):
        spaces = " " * indent
        condition = pretty_str(self.condition)
        if self.name == "while":
            pretty = spaces + "while (" + condition + "):\n"
            pretty += self.body.pretty_str(indent = indent + 2)
        elif self.name == "do":
            pretty = spaces + "do:\n"
            pretty += self.body.pretty_str(indent = indent + 2)
            pretty += "\n" + spaces + "while (" + condition + ")"
        elif self.name == "for":
            v = self.declarations.pretty_str() if self.declarations else ""
            i = self.increment.pretty_str(indent = 1) if self.increment else ""
            pretty = spaces + "for ({}; {};{}):\n".format(v, condition, i)
            pretty += self.body.pretty_str(indent = indent + 2)
        return pretty


CppSwitch = CodeSwitch
