import pandas as pd

user_id = "id1"
df = pd.read_csv('utilisateurs.txt', sep=';')
row = df.loc[df["id_user"] == user_id]
user_type = row["type"].item()
print(user_type)
if user_type == "Manager":
    print("ok")