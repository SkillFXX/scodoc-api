"""
Client principal pour interagir avec l'API ScoDoc / Scodoc-Notes.
"""

from __future__ import annotations
import os
import ssl
import urllib.parse
from typing import Optional, Dict, List, Tuple, Any
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
import urllib3

from .exceptions import ScoDocError, ScoDocAuthError, ScoDocConnectionError, ScoDocAPIError
from .models import Releve, Etudiant, UE, Evaluation, Absences

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class LegacySSLAdapter(HTTPAdapter):
    """
    Adaptateur SSL pour autoriser les protocoles et suites de chiffrement anciens (SECLEVEL=1)
    requis par les serveurs CAS institutionnels (comme cas.iutbeziers.fr:8443).
    """
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        except ssl.SSLError:
            pass
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


class ScoDoc:
    """
    Interface principale pour interroger l'API ScoDoc et récupérer vos notes,
    moyennes, rangs, coefficients et absences.

    Utilisation :
    >>> from scodoc_api import ScoDoc
    >>> client = ScoDoc("https://wscodoc.iutbeziers.fr", "mon_identifiant", "mon_mot_de_passe")
    >>> releve = client.get_releve()
    >>> print(releve.moyenne_generale, releve.rang)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        auto_login: bool = True,
    ):
        self.base_url = (base_url or os.getenv("SCODOC_URL") or "https://wscodoc.iutbeziers.fr").rstrip("/")
        self.username = username or os.getenv("SCODOC_USERNAME")
        self.password = password or os.getenv("SCODOC_PASSWORD")

        self.session = requests.Session()
        self.session.mount("https://", LegacySSLAdapter())
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        self._cached_data: Optional[Dict[str, Any]] = None
        self._cached_releve: Optional[Releve] = None

        if auto_login and self.username and self.password:
            self.login(self.username, self.password)

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Authentifie la session auprès du service CAS (Central Authentication Service).
        """
        user = username or self.username
        pwd = password or self.password

        if not user or not pwd:
            raise ScoDocAuthError("Nom d'utilisateur et mot de passe requis pour la connexion.")

        auth_url = f"{self.base_url}/services/doAuth.php"
        try:
            resp = self.session.get(auth_url, verify=False, allow_redirects=True, timeout=15)
        except requests.RequestException as e:
            raise ScoDocConnectionError(f"Impossible de joindre la passerelle ScoDoc : {e}") from e

        # Déjà connecté ?
        if "login" not in resp.url and "cas" not in resp.url:
            return True

        # Parsing de la page CAS
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form")
        if not form:
            raise ScoDocAuthError(f"Formulaire CAS introuvable sur {resp.url}")

        action = form.get("action", "")
        action_url = urllib.parse.urljoin(resp.url, action)

        payload = {"username": user, "password": pwd}
        for inp in form.find_all("input"):
            name = inp.get("name")
            if name and name not in payload:
                payload[name] = inp.get("value", "")

        try:
            login_resp = self.session.post(action_url, data=payload, verify=False, allow_redirects=True, timeout=15)
        except requests.RequestException as e:
            raise ScoDocConnectionError(f"Erreur de communication avec le serveur CAS : {e}") from e

        if "wscodoc" in login_resp.url or "scodoc" in login_resp.url:
            # Réinitialiser le cache après une nouvelle connexion
            self._cached_data = None
            self._cached_releve = None
            return True

        # Détection de l'erreur dans la page CAS retournée
        err_soup = BeautifulSoup(login_resp.text, "html.parser")
        alert = err_soup.find(class_=lambda c: c and any(w in c for w in ["alert", "error", "feedback"]))
        msg = alert.get_text(strip=True) if alert else "Identifiants invalides ou échec d'authentification CAS."
        raise ScoDocAuthError(f"Échec de l'authentification : {msg}")

    def fetch_raw_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Appelle la route API 'dataPremièreConnexion' et retourne le JSON complet.
        """
        if self._cached_data and not force_refresh:
            return self._cached_data

        endpoint = f"{self.base_url}/services/data.php?q=dataPremi%C3%A8reConnexion"
        try:
            resp = self.session.get(endpoint, verify=False, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise ScoDocConnectionError(f"Erreur lors de la requête API ScoDoc : {e}") from e
        except ValueError as e:
            raise ScoDocAPIError("La réponse du serveur ScoDoc n'est pas un JSON valide.") from e

        if data.get("redirect"):
            raise ScoDocAuthError("Session expirée. Veuillez vous reconnecter.")

        self._cached_data = data
        self._cached_releve = Releve.from_api_response(data, base_url=self.base_url, client=self)
        return data

    def get_releve(self, force_refresh: bool = False) -> Releve:
        """
        Retourne l'objet complet `Releve` contenant l'ensemble des données
        structurées (moyennes, rang, UEs, notes, absences, etc.).
        """
        if self._cached_releve and not force_refresh:
            return self._cached_releve
        self.fetch_raw_data(force_refresh=force_refresh)
        assert self._cached_releve is not None
        return self._cached_releve

    def get_moyenne_generale(self) -> Optional[float]:
        """Retourne directement la moyenne générale actuelle."""
        return self.get_releve().moyenne_generale

    def get_rang(self) -> Tuple[Optional[int], Optional[int]]:
        """Retourne un tuple (rang, effectif_total) dans la promotion."""
        rel = self.get_releve()
        return (rel.rang, rel.total_promo)

    def get_ues(self) -> Dict[str, UE]:
        """Retourne le dictionnaire des UEs/Compétences avec leurs moyennes et rangs."""
        return self.get_releve().ues

    def get_notes(self) -> List[Evaluation]:
        """Retourne toutes les notes évaluées triées par date la plus récente."""
        return self.get_releve().notes_avec_valeur

    def get_absences(self) -> Absences:
        """Retourne le bilan des absences et assiduité."""
        return self.get_releve().absences

    def get_etudiant(self) -> Etudiant:
        """Retourne le profil de l'étudiant connecté."""
        return self.get_releve().etudiant

    def get_student_pic(self, nip: Optional[str] = None) -> bytes:
        """
        Télécharge et retourne les octets (JPEG) de la photo officielle de l'étudiant.
        Si nip n'est pas fourni, utilise la session de l'étudiant connecté.
        """
        url = f"{self.base_url}/services/data.php?q=getStudentPic"
        if nip:
            url += f"&nip={nip}"
        try:
            resp = self.session.get(url, verify=False, timeout=15)
            resp.raise_for_status()
            if "image" not in resp.headers.get("Content-Type", ""):
                raise ScoDocAPIError("Le serveur n'a pas renvoyé d'image valide pour cet étudiant.")
            return resp.content
        except requests.RequestException as e:
            raise ScoDocConnectionError(f"Erreur lors de la récupération de la photo : {e}") from e

    def save_student_pic(self, destination_path: str, nip: Optional[str] = None) -> str:
        """
        Télécharge et enregistre la photo de l'étudiant dans un fichier local.
        """
        content = self.get_student_pic(nip=nip)
        with open(destination_path, "wb") as f:
            f.write(content)
        return destination_path

    def get_student_pic_base64(self, nip: Optional[str] = None) -> str:
        """
        Retourne la photo de l'étudiant sous forme d'URI data base64 (format data:image/jpeg;base64,...).
        """
        import base64
        content = self.get_student_pic(nip=nip)
        b64 = base64.b64encode(content).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    def get_evaluation_distribution(self, evaluation_id: int) -> List[float]:
        """
        Récupère la distribution complète de toutes les notes de la promo pour une évaluation donnée (q=listeNotes).
        Retourne la liste des notes numériques attribuées à l'ensemble de la promotion.
        """
        url = f"{self.base_url}/services/data.php?q=listeNotes&eval={evaluation_id}"
        try:
            resp = self.session.get(url, verify=False, timeout=15)
            resp.raise_for_status()
            raw_list = resp.json()
            if isinstance(raw_list, list):
                from .models import _parse_float
                return [val for x in raw_list if (val := _parse_float(x)) is not None]
            return []
        except requests.RequestException as e:
            raise ScoDocConnectionError(f"Erreur lors de la récupération des notes de l'évaluation : {e}") from e
        except ValueError as e:
            raise ScoDocAPIError("Réponse invalide du serveur pour la distribution des notes.") from e

    def get_semestres(self) -> List[Dict[str, Any]]:
        """Retourne la liste des semestres suivis."""
        data = self.fetch_raw_data()
        return data.get("semestres") or []

