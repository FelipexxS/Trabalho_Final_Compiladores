# 🐢 TurtleScript Compiler 2025.1

## Descrição do Projeto

Este projeto consiste no desenvolvimento de um compilador para a **TurtleScript**, uma linguagem didática personalizada, com foco nas etapas de análise léxica, sintática, semântica e geração de código. O objetivo principal é traduzir programas escritos em TurtleScript para scripts Python funcionais que utilizam a biblioteca **Turtle Graphics**, permitindo a simulação visual de comandos de desenho.

O desenvolvimento foi realizado em Python, e a implementação seguiu os princípios de construção de compiladores, como discutido em obras de referência como "Engineering a Compiler" de Cooper e Torczon, que aborda desde a estrutura do compilador até técnicas de otimização e representações intermediárias.

## Visão Geral da Linguagem TurtleScript

TurtleScript é uma linguagem de programação simples, projetada para controlar uma "tartaruga" virtual em uma tela bidimensional para criar desenhos vetoriais. A linguagem suporta:

### Tipos de Dados
*   `inteiro`: Para valores numéricos inteiros, usado em movimentos, rotações e repetições.
*   `texto`: Para strings, essencial para definir cores por nome.
*   `real`: Para números de ponto flutuante, permitindo maior precisão em distâncias e ângulos.
*   `logico`: Para valores booleanos (`verdadeiro` ou `falso`), base para estruturas de controle condicionais.

### Estrutura do Programa
Todo programa é delimitado por `inicio` e `fim`.