# Application Al Madaniyya — parcours élèves

## Installation Windows
1. Installe Python 3.10 ou plus récent.
2. Décompresse le dossier.
3. Double-clique sur `demarrer_windows.bat`.
4. Au premier lancement, ouvre `http://127.0.0.1:5000/premier-demarrage`.
5. Crée ton compte professeur avec un mot de passe d'au moins 12 caractères.

## Fonctionnement
- 12 étapes correspondant aux 12 vidéos de la playlist fournie.
- Chaque chapitre contient un accès à la playlist vidéo et un QCM.
- Validation à 80 % minimum ; le chapitre suivant se débloque après validation.
- Comptes élèves créés depuis l'espace professeur.
- Les résultats et comptes sont conservés dans `qaida.db`.

## Important sur le contenu pédagogique
Les QCM de démonstration sont construits à partir des notions et objectifs retrouvés dans le PDF `madania.pdf` et des titres de la playlist. Les questions de lecture orale et les exercices détaillés doivent être complétés/validés par l'enseignant à partir des pages et exemples du manuel. L'application n'évalue pas encore la prononciation audio.

## Lancement manuel
Dans le dossier du projet :
```bash
pip install -r requirements.txt
python app.py
```
Puis ouvre http://127.0.0.1:5000

La base `qaida.db` contient les comptes et progressions : ne la supprime pas si tu veux conserver les données.
Pour un déploiement sur Internet, définir une variable `SECRET_KEY` longue et privée et activer HTTPS.
