# MiniLang Compiler Front-End

MiniLang is a lightweight statically typed Domain-Specific Language (DSL) and compiler front-end implemented in Python. The project demonstrates the complete compilation pipeline used in modern compilers, including lexical analysis, parsing, abstract syntax tree (AST) construction, semantic analysis, symbol table management, and intermediate code generation using Three-Address Code (TAC).

The compiler supports core programming language constructs such as:

* Variable declarations and assignments
* Arithmetic and boolean expressions
* Conditional statements (`if` / `else`)
* Iterative constructs (`while`, `for`)
* Functions with parameters and return types
* Recursive function calls
* Nested scopes and block structures
* Type checking and semantic validation

## Compiler Pipeline

```text
Source Code
   ↓
Lexer
   ↓
Tokens
   ↓
Parser
   ↓
Abstract Syntax Tree (AST)
   ↓
Semantic Analyzer + Symbol Table
   ↓
Three-Address Code (TAC)
```

## Project Features

* Handwritten lexer for tokenization
* Recursive-descent parser with operator precedence handling
* AST-based compiler architecture
* Scoped symbol table implementation
* Static type checking and semantic validation
* Error recovery in lexer and parser phases
* Intermediate representation generation using TAC
* Comprehensive automated test suite
* Sample MiniLang programs demonstrating language features

## Technologies Used

* Python 3
* Dataclasses
* Object-Oriented Design
* Visitor Pattern
* Compiler Design Concepts

## Modules

| Module         | Purpose                                       |
| -------------- | --------------------------------------------- |
| `lexer.py`     | Lexical analysis and token generation         |
| `parser.py`    | Recursive-descent parser and AST construction |
| `ast_nodes.py` | AST node definitions                          |
| `semantic.py`  | Semantic analysis and symbol table management |
| `tac_gen.py`   | Three-Address Code generation                 |
| `compiler.py`  | Main compiler driver                          |
| `tests.py`     | Automated testing framework                   |
| `grammar.md`   | MiniLang language grammar specification       |

## Educational Objectives

This project was developed to demonstrate fundamental compiler construction concepts including:

* Language grammar design
* Lexical and syntax analysis
* Abstract syntax tree generation
* Static semantic analysis
* Scope resolution and symbol tables
* Intermediate code generation
* Compiler error handling and recovery

## Future Enhancements

Possible future improvements include:

* Optimization passes
* Bytecode or assembly generation
* Virtual machine implementation
* Arrays and advanced data structures
* Object-oriented language features
* REPL and IDE tooling support

This project serves as an educational compiler implementation and a practical demonstration of programming language processing techniques.
