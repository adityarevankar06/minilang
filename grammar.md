# MiniLang DSL — Language Specification

## Overview
MiniLang is a lightweight, statically-typed Domain-Specific Language designed for
basic computational tasks: arithmetic, conditionals, loops, and function definitions.

---

## Context-Free Grammar (BNF Form)

```
<program>       ::= <stmt_list>

<stmt_list>     ::= <stmt> <stmt_list>
                  | ε

<stmt>          ::= <var_decl>
                  | <assign_stmt>
                  | <if_stmt>
                  | <while_stmt>
                  | <for_stmt>
                  | <func_def>
                  | <return_stmt>
                  | <print_stmt>
                  | <expr_stmt>

<var_decl>      ::= "var" IDENTIFIER ":" <type> "=" <expr> ";"
                  | "var" IDENTIFIER ":" <type> ";"

<type>          ::= "int" | "float" | "bool" | "string"

<assign_stmt>   ::= IDENTIFIER "=" <expr> ";"

<if_stmt>       ::= "if" "(" <expr> ")" "{" <stmt_list> "}"
                  | "if" "(" <expr> ")" "{" <stmt_list> "}" "else" "{" <stmt_list> "}"

<while_stmt>    ::= "while" "(" <expr> ")" "{" <stmt_list> "}"

<for_stmt>      ::= "for" "(" <var_decl> <expr> ";" <assign_stmt_no_semi> ")" "{" <stmt_list> "}"

<func_def>      ::= "func" IDENTIFIER "(" <param_list> ")" ":" <type> "{" <stmt_list> "}"

<param_list>    ::= <param> ("," <param>)*
                  | ε

<param>         ::= IDENTIFIER ":" <type>

<return_stmt>   ::= "return" <expr> ";"

<print_stmt>    ::= "print" "(" <expr> ")" ";"

<expr_stmt>     ::= <expr> ";"

<expr>          ::= <or_expr>

<or_expr>       ::= <and_expr> ("||" <and_expr>)*

<and_expr>      ::= <eq_expr> ("&&" <eq_expr>)*

<eq_expr>       ::= <rel_expr> (("==" | "!=") <rel_expr>)*

<rel_expr>      ::= <add_expr> (("<" | ">" | "<=" | ">=") <add_expr>)*

<add_expr>      ::= <mul_expr> (("+" | "-") <mul_expr>)*

<mul_expr>      ::= <unary_expr> (("*" | "/" | "%") <unary_expr>)*

<unary_expr>    ::= "-" <unary_expr>
                  | "!" <unary_expr>
                  | <primary>

<primary>       ::= INTEGER_LITERAL
                  | FLOAT_LITERAL
                  | STRING_LITERAL
                  | BOOL_LITERAL
                  | IDENTIFIER
                  | IDENTIFIER "(" <arg_list> ")"
                  | "(" <expr> ")"

<arg_list>      ::= <expr> ("," <expr>)*
                  | ε
```

---

## Keywords
`var`, `func`, `if`, `else`, `while`, `for`, `return`, `print`,
`int`, `float`, `bool`, `string`, `true`, `false`

## Operators
`+`, `-`, `*`, `/`, `%`, `=`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `||`, `!`

## Delimiters
`(`, `)`, `{`, `}`, `:`, `,`, `;`

## Literals
- Integer: `[0-9]+`
- Float:   `[0-9]+\.[0-9]+`
- String:  `"[^"]*"`
- Bool:    `true` | `false`

## Comments
Single-line comments start with `#` and continue to end of line.
