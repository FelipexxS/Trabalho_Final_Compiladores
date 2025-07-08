import turtle
import math

tela = turtle.screen()
turtle.speed('fast')

lado = 0
lado = 10
turtle.color("cyan")
turtle.bgcolor("black")
for _ in range(50):
    turtle.forward(lado)
    turtle.right(91)
    lado = lado + 5

tela.exitonclick()