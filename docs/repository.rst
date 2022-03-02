PyTeal Repository Structure
===========================

The main PyTeal codebase is logically organized as follows:


pyteal/ast
~~~~~~~~~~

Code for the basic PyTeal building blocks: expressions which define an Abstract Syntax Tree (AST) .


pyteal/compiler
~~~~~~~~~~~~~~~

The basic compilation algorithms.

pyteal/ir
~~~~~~~~~

Code for PyTeal's Intermediate Representation (IR) which the compiler generates midway from the AST before finally converting to TEAL.
