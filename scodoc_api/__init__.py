"""
scodoc-api : Bibliothèque Python pour interagir avec l'API ScoDoc (passerelle Scodoc-Notes v7:2:3).
Fournit un accès objet typé, simple et complet à l'ensemble des données de scolarité :
notes, moyennes, UEs, coefficients, rangs et assiduité.
"""

from .client import ScoDoc, LegacySSLAdapter
from .models import (
    Releve,
    Etudiant,
    UE,
    Matiere,
    Evaluation,
    StatistiquesSemestre,
    Absences,
    CreneauAbsence,
)
from .exceptions import (
    ScoDocError,
    ScoDocAuthError,
    ScoDocConnectionError,
    ScoDocAPIError,
)

__version__ = "1.0.0"

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
    "__version__",
]
