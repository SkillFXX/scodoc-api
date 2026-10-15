# 🎓 scodoc-api

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**`scodoc-api`** est une bibliothèque Python moderne et typée permettant de s'interfacer avec les serveurs **ScoDoc** et les passerelles **Scodoc-Notes** (version 7:2:3 / ScoDoc 9) utilisés dans les IUT et universités françaises (notamment avec authentification CAS).

> [!NOTE]
> **Projet non officiel** : Cette bibliothèque est un projet open-source communautaire indépendant. Elle n'est ni affiliée, ni approuvée, ni maintenue par les créateurs de ScoDoc, par les auteurs de la passerelle Scodoc-Notes, ou par un établissement universitaire.

---

## ✨ Fonctionnalités

- 🔐 **Authentification CAS automatique** : Supporte les serveurs CAS / Keycloak institutionnels (avec compatibilité automatique des suites TLS et anciens ciphers).
- 📊 **Moyennes & Rangs** : Récupération instantanée de la moyenne générale, du rang dans la promotion et des statistiques de promotion (min, max, moyenne de promo).
- 🎯 **Détail par UE & Compétences** : Moyennes individuelles pour chaque UE (UE1.1, UE1.2, etc.), ECTS associés et coefficients.
- 📝 **Notes détaillées** : Liste des évaluations pour toutes les Ressources et SAÉ (avec note, coef, date, min/max promo).
- 🕒 **Suivi de l'assiduité** : Bilan des absences justifiées et injustifiées (en heures et en nombre).
- ⚙️ **Sérialisation JSON** : Export complet en dictionnaire (`.to_dict()`) ou JSON (`.to_json()`) pour l'intégration dans des bots Discord, dashboards ou apps mobiles.

---

## 📦 Installation

Clonez le dépôt ou installez les dépendances :

```bash
git clone https://github.com/votre-compte/scodoc-api.git
cd scodoc-api
pip install -r requirements.txt
```

Ou installation en mode développement :
```bash
pip install -e .
```

---

## ⚙️ Configuration (`.env`)

Créez un fichier `.env` à la racine du projet à partir de `.env.example` :

```bash
cp .env.example .env
```

Renseignez vos identifiants :
```ini
SCODOC_URL=https://wscodoc.iutbeziers.fr
SCODOC_USERNAME=votre.identifiant
SCODOC_PASSWORD=votre_mot_de_passe
```

> **Note :** Le fichier `.env` est déjà listé dans `.gitignore` pour ne jamais exposer vos mots de passe sur GitHub.

---

## 🚀 Utilisation

### 1. Accès direct et rapide

```python
from dotenv import load_dotenv
from scodoc_api import ScoDoc

load_dotenv()

# Connexion automatique via les variables du .env
client = ScoDoc()

print("Moyenne générale :", client.get_moyenne_generale())
rang, total = client.get_rang()
print(f"Rang dans la promo : {rang} sur {total} étudiants")
```

---

### 2. Récupération de l'objet complet `Releve`

```python
from scodoc_api import ScoDoc

client = ScoDoc("https://wscodoc.iutbeziers.fr", "mon_identifiant", "mon_mot_de_passe")
releve = client.get_releve()

# Profil étudiant
print(releve.etudiant.prenom, releve.etudiant.nom)
print("Formation :", releve.formation)

# Moyennes par UE
for code, ue in releve.ues.items():
    if ue.moyenne is not None:
        print(f"[{code}] {ue.titre} : {ue.moyenne}/20 (Rang: {ue.rang}/{ue.total_promo})")

# Dernières évaluations reçues
for ev in releve.notes_avec_valeur:
    print(f"[{ev.code_matiere}] {ev.description} : {ev.note}/20 (coef {ev.coefficient}, le {ev.date})")

# Bilan d'assiduité et liste des absences
print(f"Absences : {releve.absences.total_nb} créneau(x) ({releve.absences.total_heures}h)")
for c in releve.absences.creneaux_absents:
    justif = "Justifiée" if c.justifie else "Injustifiée"
    print(f"• {c.date} ({c.heure_debut}-{c.heure_fin}) : [{justif}] {c.matiere} (Prof: {c.enseignant})")

# Export en JSON complet
json_complet = releve.to_json(indent=2)
```

---

## 🧪 Lancer les tests

```bash
python test_api.py
```

---

## ⚠️ Avertissement (Disclaimer)

Ce projet est développé à des fins d'interopérabilité et d'automatisation personnelle. Il s'appuie sur les endpoints web de la passerelle *Scodoc-Notes*. Utilisez-le de manière responsable, dans le respect de la charte informatique de votre établissement (pas de requêtes abusives ou d'inondation de requêtes).

---

## 📄 Licence

Ce projet est sous licence MIT.
