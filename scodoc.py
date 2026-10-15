"""
Wrapper de compatibilité pour scodoc.py.
Importe directement depuis le package scodoc_api.
"""

from scodoc_api import (
    ScoDoc,
    LegacySSLAdapter,
    Releve,
    Etudiant,
    UE,
    Matiere,
    Evaluation,
    StatistiquesSemestre,
    Absences,
    CreneauAbsence,
    ScoDocError,
    ScoDocAuthError,
    ScoDocConnectionError,
    ScoDocAPIError,
)

__all__ = [
    "ScoDoc",
    "LegacySSLAdapter",
    "Releve",
    "Etudiant",
    "UE",
    "Matiere",
    "Evaluation",
    "StatistiquesSemestre",
    "Absences",
    "CreneauAbsence",
    "ScoDocError",
    "ScoDocAuthError",
    "ScoDocConnectionError",
    "ScoDocAPIError",
]

if __name__ == "__main__":
    from test_api import main
    main()
