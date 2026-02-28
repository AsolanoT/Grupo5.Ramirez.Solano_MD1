#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import os

if not os.path.exists("data/superheroes.csv"):
    print("Primero ejecuta extractor.py")
    exit()

df = pd.read_csv("data/superheroes.csv")

plt.figure(figsize=(10,6))
plt.bar(df["nombre"], df["poder"])
plt.title("Nivel de Poder por Superhéroe")
plt.xticks(rotation=45)
plt.ylabel("Poder")
plt.tight_layout()
plt.savefig("data/superheroes_analysis.png")
plt.show()

print("Gráfica guardada en data/superheroes_analysis.png")