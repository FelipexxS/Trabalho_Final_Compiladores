import turtle
import math

tela = turtle.Turtle()
turtle.speed('fast')

lado = 0
cor = ""
tamanho_quadrado = 0
cor_de_fundo_quadrado = ""
lado = 10
turtle.bgcolor("black")
turtle.pensize(2)
for _ in range(int(50)):
    turtle.color("cyan")
    turtle.forward(lado)
    lado = lado + 5
tamanho_quadrado = 100
cor_de_fundo_quadrado = "red"
tela.color(cor_de_fundo_quadrado)
tela.begin_fill()
for _ in range(4):
    tela.forward(tamanho_quadrado)
    tela.right(90)
tela.forward(tamanho_quadrado)
tela.end_fill()
tela.color("red", "cyan")
tela.begin_fill()
tela.circle(80)
tela.end_fill()

turtle.done()