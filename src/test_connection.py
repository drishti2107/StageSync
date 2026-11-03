from db import run

rows, _ = run("SELECT version();", fetch=True)
print(rows[0][0])