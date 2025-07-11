import turtle
import math

tela = turtle.Turtle()
turtle.speed('fast')

lado = 0
cor = ""
lado = 5
turtle.bgcolor("black")
turtle.pensize(2)
for _ in range(int(50)):
    turtle.color("cyan")
    turtle.forward(lado)
    turtle.right(90)
    lado = lado + 5

turtle.done()