# 🎓 scodoc-api

[![PyPI version](https://img.shields.io/pypi/v/scodoc-api.svg)](https://pypi.org/project/scodoc-api/)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![PyPI Downloads](https://img.shields.io/pypi/dm/scodoc-api.svg)](https://pypi.org/project/scodoc-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**`scodoc-api`** est une bibliothèque Python moderne et typée permettant de s'interfacer avec les serveurs **ScoDoc** et les passerelles **Scodoc-Notes** (version 7:2:3 / ScoDoc 9) utilisés dans les IUT et universités françaises (notamment avec authentification CAS).

> [!NOTE]
> **Projet non officiel** : Cette bibliothèque est un projet open-source communautaire indépendant. Elle n'est ni affiliée, ni approuvée, ni maintenue par les créateurs de ScoDoc, par les auteurs de la passerelle Scodoc-Notes, ou par un établissement universitaire.

---

## ✨ Fonctionnalités

- 🔐 **Authentification CAS automatique** : Supporte les serveurs CAS / Keycloak institutionnels (avec compatibilité automatique des suites TLS et anciens ciphers).
- 📊 **Moyennes & Rangs** : Récupération instantanée de la moyenne générale, du rang dans la promotion et des statistiques de promotion (min, max, moyenne de promo).
- 📝 **Notes détaillées** : Liste des évaluations pour toutes les Ressources et SAÉ (avec note, coef, date, min/max promo).
- 📈 **Distribution des notes de la promo** : Récupération de l'ensemble des notes attribuées à la promotion pour chaque devoir (`eval.get_distribution()`), idéal pour calculer médianes, quartiles et histogrammes.
- 🖼️ **Photo d'identité étudiante** : Téléchargement direct des octets JPEG de la photo officielle (`get_student_pic()`) ou au format Data-URI base64 (`get_student_pic_base64()`).
- 🕒 **Suivi de l'assiduité** : Bilan des absences justifiées et injustifiées (en heures et en nombre avec motifs et créneaux).
- ⚙️ **Sérialisation JSON** : Export complet en dictionnaire (`.to_dict()`) ou JSON (`.to_json()`) pour l'intégration dans des bots Discord, dashboards ou apps mobiles.

---

## 📦 Installation

Installez directement le module depuis **[PyPI](https://pypi.org/project/scodoc-api/)** :

```bash
pip install scodoc-api
```

*(Optionnel) Pour contribuer ou tester en mode développement local :*
```bash
git clone https://github.com/SkillFXX/scodoc-api.git
cd scodoc-api
pip install -e .
```

---

## ⚙️ Configuration (`.env`)

Créez un fichier `.env` à la racine de votre projet (voir `.env.example`) :

```ini
SCODOC_URL=https://wscodoc.iutbeziers.fr
SCODOC_USERNAME=votre.identifiant
SCODOC_PASSWORD=votre_mot_de_passe
```

> **Note :** Pensez à ajouter `.env` à votre `.gitignore` pour ne jamais exposer vos mots de passe.

---

## 🚀 Utilisation

### 1. Accès direct et rapide

```python
from dotenv import load_dotenv
from scodoc_api import ScoDoc

load_dotenv()

# Connexion automatique via les variables du .env (ou en passant les paramètres)
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

# Dernières évaluations reçues et distribution de promo
for ev in releve.notes_avec_valeur[:5]:
    print(f"[{ev.code_matiere}] {ev.description} : {ev.note}/20 (coef {ev.coefficient})")
    # Distribution de l'ensemble de la promo pour cette évaluation :
    notes_promo = ev.get_distribution()
    print(f"  -> Notes promo : min={min(notes_promo)}, max={max(notes_promo)}, moy={round(sum(notes_promo)/len(notes_promo), 2)}")

# Photo officielle de l'étudiant
photo_bytes = client.get_student_pic() # ou releve.get_student_pic()
client.save_student_pic("ma_photo.jpg")
data_uri = client.get_student_pic_base64() # data:image/jpeg;base64,...

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
