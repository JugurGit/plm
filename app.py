from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file
import io
import os

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_pour_flash'

data = {
    'id_parfum': [1, 2],
    'nom': ['Chanel No. 5', 'Dior Sauvage'],
    'prix': ['100', '80'],
    'sexe': ['Femme', 'Homme'],
    'description': ['Parfum iconique', 'Parfum frais et boisé'],
    'etat': ['Dispo', 'Dispo']
}
parfums = pd.DataFrame(data)



@app.route('/')
def login():
    return render_template('login.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    user_id = request.form.get('username')
    password = request.form.get('password')
    
    df = pd.read_csv('utilisateurs.txt', sep=';')
    
    if df["id_user"].str.contains(user_id, na=False).any() and df["mot_de_passe"].str.contains(password, na=False).any():
        row = df.loc[df["id_user"] == user_id]
        user_name = row["nom"].iloc[0]
        user_type = row["type"].iloc[0]

        # Stocker les informations utilisateur dans la session
        session['user_name'] = user_name
        session['user_type'] = user_type

        if user_type == "Manager":
            return redirect(url_for('manager'))
        if user_type == "Commercial":
            return redirect(url_for('commercial'))
        if user_type == "Scientifique":
            return redirect(url_for('scientifique'))
        if user_type == "Partenaire":
            return redirect(url_for('commercial'))

        return redirect(url_for('success'))
    else:
        flash("Identifiant ou mot de passe incorrect.")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Vous avez été déconnecté avec succès.")
    return redirect(url_for('login'))

@app.route('/download_pdf/<int:id_parfum>')
def download_pdf(id_parfum):
    # Charger les données des composants
    composants = pd.read_csv('composants.txt', sep=';')
    composants_parfum = composants[composants['id_parfum'] == id_parfum]

    if composants_parfum.empty:
        flash("Aucun composant trouvé pour ce parfum.")
        return redirect(url_for('scientifique'))

    # Créer un buffer pour le fichier PDF
    buffer = io.BytesIO()

    # Créer un PDF
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 750, f"Composants du Parfum ID: {id_parfum}")
    pdf.drawString(100, 730, "ID Composant | Nom | Quantité | Version")

    # Ajouter les composants dans le PDF
    y_position = 710
    for _, composant in composants_parfum.iterrows():
        pdf.drawString(
            100, y_position,
            f"{composant['id_componant']} | {composant['nom']} | {composant['quantité']} | {composant['version']}"
        )
        y_position -= 20

    pdf.save()
    buffer.seek(0)

    # Retourner le fichier PDF
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"composants_parfum_{id_parfum}.pdf",
        mimetype='application/pdf'
    )

@app.route('/success')
def success():
    return render_template('success.html')

def load_parfums():
    return pd.read_csv('parfums.txt', sep=';')

@app.route('/manager', methods=['GET', 'POST'])
def manager():
    parfum_info = None  # Variable pour stocker les informations du parfum trouvé
    parfums = load_parfums()  # Charger les parfums depuis le fichier à chaque requête
    
    if request.method == 'POST':
        parfum_id = request.form.get('parfum_id')
        
        # Vérifier si l'ID est valide et existe dans le DataFrame
        if parfum_id and parfum_id.isdigit():
            # Rechercher l'ID dans le DataFrame
            parfum_info = parfums[parfums['id_parfum'] == int(parfum_id)]
            
            if parfum_info.empty:
                parfum_info = "Parfum non trouvé."
            else:
                parfum_info = parfum_info.iloc[0].to_dict()  # Convertir la ligne en dictionnaire

        elif parfum_id:
            parfum_info = "Parfum non trouvé."
        
        # Si le formulaire de modification est soumis, on met à jour le parfum
        if 'modifier' in request.form and parfum_info and isinstance(parfum_info, dict):
            # Modifier les informations dans le DataFrame
            nom = request.form.get('nom')
            prix = request.form.get('prix')
            sexe = request.form.get('sexe')
            description = request.form.get('description')
            etat = request.form.get('etat')

            # Modifier les informations du parfum dans le DataFrame
            parfums.loc[parfums['id_parfum'] == int(parfum_id), ['nom', 'prix', 'sexe', 'description', 'etat']] = [
                nom, prix, sexe, description, etat
            ]
            
            # Sauvegarder les modifications dans le fichier CSV
            parfums.to_csv('parfums.txt', sep=';', index=False)
            
            parfum_info = "Parfum modifié avec succès."

    return render_template('manager.html', parfum_info=parfum_info)


@app.route('/commercial', methods=['GET', 'POST'])
def commercial():
    parfum_info = None
    parfums = pd.read_csv('parfums.txt', sep=';')

    if request.method == 'POST':
        parfum_id = request.form.get('parfum_id')  # Récupère l'ID du parfum
        if parfum_id and parfum_id.isdigit():  # Vérifie que l'ID est valide
            # Trouver le parfum par ID
            parfum_info = parfums[parfums['id_parfum'] == int(parfum_id)]
            if parfum_info.empty:
                parfum_info = "Parfum non trouvé."
            else:
                parfum_info = parfum_info.iloc[0].to_dict()  # Convertir la ligne en dictionnaire

    return render_template('commercial.html', parfum_info=parfum_info)

@app.route('/forgot-password')
def forgot_password():
    flash("Veuillez contacter service-client@cosmetic-factory.com pour récupérer votre mot de passe.")
    return redirect(url_for('login'))


@app.route('/update_parfum', methods=['POST'])
def update_parfum():
    # Charger le fichier parfums.txt
    parfums = pd.read_csv('parfums.txt', sep=';')

    # Parcourir les données envoyées via le formulaire
    for key, value in request.form.items():
        parts = key.split('_')
        
        # Vérifier que la clé contient bien un ID numérique avant de l'utiliser
        if len(parts) > 1 and parts[1].isdigit():  # Vérifier que la deuxième partie de la clé est un ID numérique
            id_parfum = int(parts[1])

            if key.startswith('nom_'):
                parfums.loc[parfums['id_parfum'] == id_parfum, 'nom'] = value
            elif key.startswith('prix_'):
                parfums.loc[parfums['id_parfum'] == id_parfum, 'prix'] = float(value)
            elif key.startswith('sexe_'):
                parfums.loc[parfums['id_parfum'] == id_parfum, 'sexe'] = value
            elif key.startswith('description_'):
                parfums.loc[parfums['id_parfum'] == id_parfum, 'description'] = value
            elif key.startswith('etat_projet_'):
                parfums.loc[parfums['id_parfum'] == id_parfum, 'etat du projet'] = value

    # Sauvegarder les modifications dans le fichier parfums.txt
    parfums.to_csv('parfums.txt', sep=';', index=False)

    # Rediriger vers une page appropriée
    return redirect('/manager')


@app.route('/scientifique', methods=['GET', 'POST'])
def scientifique():
    choice = request.form.get('choice')  # "parfum" ou "composant"
    id_parfum = request.form.get('id_parfum')  # ID du parfum
    nom_composant = request.form.get('nom_composant')  # Nom du composant
    # Débogage pour vérifier les données reçues
    print("Choice:", choice)
    print("ID Parfum:", id_parfum)
    print("Nom Composant:", nom_composant)

    # Charger les fichiers
    parfums = pd.read_csv('parfums.txt', sep=';')
    composants = pd.read_csv('composants.txt', sep=';')

    if choice == 'parfum' and id_parfum:
        # Filtrer les composants correspondant à l'ID du parfum
        composants_parfum = composants[composants['id_parfum'] == int(id_parfum)].to_dict(orient='records')
        print(composants_parfum)
        return render_template('scientifique.html', choice='parfum', id_parfum=id_parfum, composants=composants_parfum)
    elif choice == 'composant' and nom_composant:
        # Filtrer les parfums contenant ce composant
        composants_filtered = composants[composants['nom'].str.contains(nom_composant, case=False, na=False)]
        print(composants_filtered)
        parfums_ids = composants_filtered['id_parfum'].unique()
        parfums_composant = parfums[parfums['id_parfum'].isin(parfums_ids)].to_dict(orient='records')
        print(parfums_composant)
        return render_template('scientifique.html', choice='composant', nom_composant=nom_composant, parfums=parfums_composant)
    else:
        return render_template('scientifique.html')
    

@app.route('/update_composants', methods=['POST'])
def update_composants():
    composants = pd.read_csv('composants.txt', sep=';')

    for key, value in request.form.items():
        if key.startswith('quantité_'):
            id_componant = int(key.split('_')[1])
            composants.loc[composants['id_componant'] == id_componant, 'quantité'] = int(value)
        elif key.startswith('version_'):
            id_componant = int(key.split('_')[1])
            composants.loc[composants['id_componant'] == id_componant, 'version'] = float(value)

    composants.to_csv('composants.txt', sep=';', index=False)
    return redirect('/scientifique')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)