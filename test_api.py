"""
Script de test complet pour la bibliothèque scodoc-api.
Charge automatiquement les identifiants depuis le fichier .env
"""

import os
from dotenv import load_dotenv
from scodoc_api import ScoDoc

# 1. Chargement des variables d'environnement (.env)
load_dotenv()

SCODOC_URL = os.getenv("SCODOC_URL", "https://wscodoc.iutbeziers.fr")
USERNAME = os.getenv("SCODOC_USERNAME")
PASSWORD = os.getenv("SCODOC_PASSWORD")

if not USERNAME or not PASSWORD:
    print("[-] Erreur : SCODOC_USERNAME et SCODOC_PASSWORD doivent être définis dans le fichier .env")
    exit(1)


def main():
    print(f"[*] Connexion à ScoDoc ({SCODOC_URL}) avec l'utilisateur '{USERNAME}'...")
    client = ScoDoc(base_url=SCODOC_URL, username=USERNAME, password=PASSWORD)

    # Récupération de l'objet Releve complet
    releve = client.get_releve()
    etud = releve.etudiant

    print("\n" + "=" * 70)
    print(f"  ÉTUDIANT : {etud.prenom} {etud.nom} (NIP: {etud.code_nip})")
    print(f"  Formation: {releve.formation} (Semestre {releve.semestre_numero})")
    print(f"  Année    : {releve.annee_universitaire} | Groupes: {', '.join(releve.groupes)}")
    print("=" * 70)

    # 1. Moyenne générale et rang
    moyenne = client.get_moyenne_generale()
    rang, total = client.get_rang()
    print(f"\n[+] MOYENNE GÉNÉRALE : {moyenne} / 20")
    print(f"    - Rang : {rang} sur {total} étudiants")
    print(f"    - Promo : Moyenne={releve.stats.moy_promo} (Min: {releve.stats.min_promo} | Max: {releve.stats.max_promo})")

    # 2. Moyennes par UE
    print("\n[+] MOYENNES PAR UE :")
    print("-" * 70)
    for code, ue in releve.ues.items():
        if ue.moyenne is not None:
            print(f"  * {code:<6} : {ue.moyenne:>5.2f}/20 | Rang: {ue.rang:>2}/{ue.total_promo} | Promo: {ue.moy_promo} ({ue.titre})")
        else:
            print(f"  * {code:<6} : Non évaluée ({ue.titre})")

    # 3. Dernières évaluations reçues
    print("\n[+] DERNIÈRES ÉVALUATIONS REÇUES :")
    print("-" * 70)
    notes = client.get_notes()
    for ev in notes[:10]:
        print(f"  - [{ev.code_matiere}] {ev.description[:32]:<32} : {ev.note:>5.2f}/20 (coef: {ev.coefficient}, le {ev.date})")

    # 4. Assiduité et détails des absences
    absences = client.get_absences()
    print("\n[+] BILAN DE L'ASSIDUITÉ :")
    print("-" * 70)
    print(f"  - Total absences       : {absences.total_nb} créneau(x) ({absences.total_heures}h, soit {absences.total_demi_journees} demi-journée(s))")
    print(f"  - Absences justifiées  : {absences.justifiees_nb} créneau(x) ({absences.justifiees_heures}h)")
    print(f"  - Absences injustifiées: {absences.injustifiees_nb} créneau(x) ({absences.injustifiees_heures}h)")
    if absences.retards_nb > 0:
        print(f"  - Retards enregistrés  : {absences.retards_nb} ({absences.retards_heures}h)")

    creneaux_abs = absences.creneaux_absents
    if creneaux_abs:
        print("\n  Détail des créneaux d'absence :")
        for c in creneaux_abs:
            justif_str = "Justifiée" if c.justifie else "INJUSTIFIÉE"
            prof = f" (Prof: {c.enseignant})" if c.enseignant else ""
            print(f"  • {c.date} de {c.heure_debut} à {c.heure_fin} ({c.duree_heures}h) : [{justif_str}] {c.matiere}{prof}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
