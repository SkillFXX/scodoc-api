"""
Exceptions personnalisées pour le module scodoc-api.
"""

class ScoDocError(Exception):
    """Exception de base pour toutes les erreurs ScoDoc."""
    pass


class ScoDocAuthError(ScoDocError):
    """Levée lors d'un échec d'authentification (CAS ou session expirée)."""
    pass


class ScoDocConnectionError(ScoDocError):
    """Levée lors d'un problème de réseau ou SSL."""
    pass


class ScoDocAPIError(ScoDocError):
    """Levée lorsque l'API ScoDoc renvoie un statut d'erreur ou des données inattendues."""
    pass

