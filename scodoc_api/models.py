"""
Modèles de données pour le module scodoc-api.
Structure toutes les informations de scolarité : profil étudiant,
semestre, UEs, ressources, SAÉ, évaluations et assiduité complète.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
import json


def _parse_float(val: Any) -> Optional[float]:
    """Convertit une chaîne ou valeur numérique en float, renvoie None si indisponible."""
    if val is None or val == "" or val == "~":
        return None
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _parse_int(val: Any) -> Optional[int]:
    """Convertit une chaîne ou valeur en entier, renvoie None si indisponible."""
    if val is None or val == "" or val == "~":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _format_heure(val: Optional[float]) -> str:
    """Convertit une heure décimale (ex: 10.75) en chaîne 'HH:MM' (ex: '10:45')."""
    if val is None:
        return ""
    h = int(val)
    m = int(round((val % 1) * 60))
    if m >= 60:
        h += 1
        m = 0
    return f"{h:02d}:{m:02d}"


@dataclass
class Etudiant:
    """Informations administratives et personnelles sur l'étudiant."""
    id: int
    nom: str
    prenom: str
    email: str
    email_perso: Optional[str] = None
    code_nip: Optional[str] = None
    code_ine: Optional[str] = None
    date_naissance: Optional[str] = None
    telephone: Optional[str] = None
    departement: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    photo_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], base_url: str = "") -> Etudiant:
        photo = data.get("photo_url")
        if photo and photo.startswith("/") and base_url:
            photo = f"{base_url.rstrip('/')}{photo}"
        elif not photo and base_url:
            nip = data.get("code_nip")
            photo = f"{base_url.rstrip('/')}/services/data.php?q=getStudentPic" + (f"&nip={nip}" if nip else "")

        return cls(
            id=_parse_int(data.get("id") or data.get("etudid")) or 0,
            nom=data.get("nom", ""),
            prenom=data.get("prenom", ""),
            email=data.get("email", ""),
            email_perso=data.get("emailperso"),
            code_nip=data.get("code_nip"),
            code_ine=data.get("code_ine"),
            date_naissance=data.get("date_naissance"),
            telephone=data.get("telephonemobile") or data.get("telephone"),
            departement=data.get("dept_acronym"),
            ville=data.get("villedomicile"),
            code_postal=data.get("codepostaldomicile"),
            photo_url=photo,
        )


@dataclass
class Evaluation:
    """Détail d'une évaluation ou devoir dans une matière (Ressource / SAÉ)."""
    id: int
    description: str
    code_matiere: str
    titre_matiere: str
    note: Optional[float]
    coefficient: float = 1.0
    date: Optional[str] = None
    min_promo: Optional[float] = None
    moy_promo: Optional[float] = None
    max_promo: Optional[float] = None
    poids_par_ue: Dict[str, float] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    _client: Optional[Any] = field(default=None, repr=False, compare=False)

    def get_distribution(self) -> List[float]:
        """
        Récupère la distribution complète de toutes les notes de la promo pour cette évaluation.
        Nécessite que l'évaluation provienne d'un relevé interrogé avec un client ScoDoc actif.
        """
        if not self._client:
            raise RuntimeError("Cette évaluation n'est pas rattachée à un client ScoDoc connecté.")
        return self._client.get_evaluation_distribution(self.id)

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        code_matiere: str = "",
        titre_matiere: str = "",
        client: Optional[Any] = None,
    ) -> Evaluation:
        note_dict = data.get("note") or {}
        val = note_dict.get("value") if isinstance(note_dict, dict) else data.get("note")
        p_min = note_dict.get("min") if isinstance(note_dict, dict) else None
        p_moy = note_dict.get("moy") if isinstance(note_dict, dict) else None
        p_max = note_dict.get("max") if isinstance(note_dict, dict) else None

        date_val = data.get("date_debut") or data.get("date") or ""
        if "T" in str(date_val):
            date_val = date_val.split("T")[0]

        return cls(
            id=_parse_int(data.get("id")) or 0,
            description=data.get("description") or titre_matiere or "Évaluation",
            code_matiere=code_matiere,
            titre_matiere=titre_matiere,
            note=_parse_float(val),
            coefficient=_parse_float(data.get("coef")) or 1.0,
            date=date_val or None,
            min_promo=_parse_float(p_min),
            moy_promo=_parse_float(p_moy),
            max_promo=_parse_float(p_max),
            poids_par_ue=data.get("poids") or {},
            raw=data,
            _client=client,
        )


@dataclass
class Matiere:
    """Représente une ressource ou une SAÉ (Situation d'Apprentissage et d'Évaluation)."""
    code: str
    titre: str
    type: str  # "ressource" ou "sae"
    id: int = 0
    moyenne: Optional[float] = None
    evaluations: List[Evaluation] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def est_evaluee(self) -> bool:
        return any(e.note is not None for e in self.evaluations)


@dataclass
class UE:
    """Unité d'Enseignement ou Compétence (ex: UE1.1)."""
    code: str
    titre: str
    moyenne: Optional[float] = None
    min_promo: Optional[float] = None
    moy_promo: Optional[float] = None
    max_promo: Optional[float] = None
    rang: Optional[int] = None
    total_promo: Optional[int] = None
    ects_acquis: int = 0
    ects_total: int = 0
    coefficients_ressources: Dict[str, float] = field(default_factory=dict)
    coefficients_saes: Dict[str, float] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, code: str, data: Dict[str, Any]) -> UE:
        moy_dict = data.get("moyenne")
        val = None
        p_min = None
        p_max = None
        p_moy = None
        rang = None
        total = None

        if isinstance(moy_dict, dict):
            val = _parse_float(moy_dict.get("value"))
            p_min = _parse_float(moy_dict.get("min"))
            p_max = _parse_float(moy_dict.get("max"))
            p_moy = _parse_float(moy_dict.get("moy"))
            rang = _parse_int(moy_dict.get("rang"))
            total = _parse_int(moy_dict.get("total"))

        ects_data = data.get("ECTS") or {}

        coef_res = {}
        for r_code, r_info in (data.get("ressources") or {}).items():
            if isinstance(r_info, dict):
                coef_res[r_code] = _parse_float(r_info.get("coef")) or 0.0

        coef_sae = {}
        for s_code, s_info in (data.get("saes") or {}).items():
            if isinstance(s_info, dict):
                coef_sae[s_code] = _parse_float(s_info.get("coef")) or 0.0

        return cls(
            code=code,
            titre=data.get("titre", ""),
            moyenne=val,
            min_promo=p_min,
            moy_promo=p_moy,
            max_promo=p_max,
            rang=rang,
            total_promo=total,
            ects_acquis=_parse_int(ects_data.get("acquis")) or 0,
            ects_total=_parse_int(ects_data.get("total")) or 0,
            coefficients_ressources=coef_res,
            coefficients_saes=coef_sae,
            raw=data,
        )


@dataclass
class StatistiquesSemestre:
    """Statistiques globales du semestre (moyenne générale, rang, promo, ECTS)."""
    moyenne_generale: Optional[float] = None
    min_promo: Optional[float] = None
    moy_promo: Optional[float] = None
    max_promo: Optional[float] = None
    rang: Optional[int] = None
    total_promo: Optional[int] = None
    ects_acquis: int = 0
    ects_total: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StatistiquesSemestre:
        notes = data.get("notes") or {}
        rangs = data.get("rang") or {}
        ects = data.get("ECTS") or {}
        return cls(
            moyenne_generale=_parse_float(notes.get("value")),
            min_promo=_parse_float(notes.get("min")),
            moy_promo=_parse_float(notes.get("moy")),
            max_promo=_parse_float(notes.get("max")),
            rang=_parse_int(rangs.get("value")),
            total_promo=_parse_int(rangs.get("total")),
            ects_acquis=_parse_int(ects.get("acquis")) or 0,
            ects_total=_parse_int(ects.get("total")) or 0,
        )


@dataclass
class CreneauAbsence:
    """Représente un créneau horaire d'absence, de retard ou de présence enregistrée."""
    id: int
    date: str
    debut: float
    fin: float
    heure_debut: str
    heure_fin: str
    duree_heures: float
    statut: str  # "absent", "retard", "present"
    justifie: bool
    matiere: str
    enseignant: str
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class Absences:
    """
    Bilan complet d'assiduité et liste détaillée des créneaux d'absences / retards.
    """
    justifiees_nb: int = 0
    justifiees_heures: float = 0.0
    justifiees_demi_journees: int = 0
    justifiees_journees: int = 0
    injustifiees_nb: int = 0
    injustifiees_heures: float = 0.0
    injustifiees_demi_journees: int = 0
    injustifiees_journees: int = 0
    total_nb: int = 0
    total_heures: float = 0.0
    total_demi_journees: int = 0
    retards_nb: int = 0
    retards_heures: float = 0.0
    creneaux: List[CreneauAbsence] = field(default_factory=list)

    @property
    def creneaux_absents(self) -> List[CreneauAbsence]:
        """Retourne la liste des créneaux où l'étudiant était absent (triée par date)."""
        return [c for c in self.creneaux if c.statut == "absent"]

    @property
    def creneaux_retards(self) -> List[CreneauAbsence]:
        """Retourne la liste des créneaux de retard."""
        return [c for c in self.creneaux if c.statut == "retard"]

    @classmethod
    def from_api_data(
        cls,
        totaux_data: Optional[Dict[str, Any]],
        absences_detail: Optional[Dict[str, Any]],
        semestre_absences: Optional[Dict[str, Any]] = None,
        matieres_map: Optional[Dict[Any, str]] = None,
    ) -> Absences:
        totaux = totaux_data or {}
        mat_map = matieres_map or {}
        sem_abs = semestre_absences or {}

        # 1. Totaux depuis totauxAbsences['absent']
        abs_tot = totaux.get("absent") or {}
        just = abs_tot.get("justifie") or {}
        non_just = abs_tot.get("non_justifie") or {}

        j_nb = _parse_int(just.get("compte")) or 0
        j_h = _parse_float(just.get("heure")) or 0.0
        j_demi = _parse_int(just.get("demi")) or 0
        j_jour = _parse_int(just.get("journee")) or 0

        nj_nb = _parse_int(non_just.get("compte")) or 0
        nj_h = _parse_float(non_just.get("heure")) or 0.0
        nj_demi = _parse_int(non_just.get("demi")) or 0
        nj_jour = _parse_int(non_just.get("journee")) or 0

        tot_nb = _parse_int(abs_tot.get("compte")) or (j_nb + nj_nb)
        tot_h = _parse_float(abs_tot.get("heure")) or (j_h + nj_h)
        tot_demi = _parse_int(sem_abs.get("total")) or (j_demi + nj_demi)

        # Retards
        ret_tot = totaux.get("retard") or {}
        ret_nb = _parse_int(ret_tot.get("compte")) or 0
        ret_h = _parse_float(ret_tot.get("heure")) or 0.0

        # Si totauxAbsences est manquant, fallback sur semestre['absences']
        if tot_nb == 0 and sem_abs:
            tot_demi = _parse_int(sem_abs.get("total")) or 0
            nj_demi = _parse_int(sem_abs.get("injustifie")) or 0
            j_demi = max(0, tot_demi - nj_demi)

        # 2. Créneaux détaillés
        creneaux: List[CreneauAbsence] = []
        if absences_detail and isinstance(absences_detail, dict):
            for date_str, items in absences_detail.items():
                if not isinstance(items, list):
                    continue
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    deb = _parse_float(it.get("debut")) or 0.0
                    fin = _parse_float(it.get("fin")) or deb
                    duree = round(fin - deb, 2)
                    mat_id = it.get("matiereComplet")
                    nom_mat = mat_map.get(mat_id) or mat_map.get(str(mat_id)) or (str(mat_id) if mat_id else "Matière non définie")

                    creneaux.append(CreneauAbsence(
                        id=_parse_int(it.get("idAbs")) or 0,
                        date=date_str,
                        debut=deb,
                        fin=fin,
                        heure_debut=_format_heure(deb),
                        heure_fin=_format_heure(fin),
                        duree_heures=duree,
                        statut=it.get("statut", "absent"),
                        justifie=bool(it.get("justifie", False)),
                        matiere=nom_mat,
                        enseignant=it.get("enseignant", ""),
                        raw=it,
                    ))

        # Tri chronologique des créneaux
        creneaux.sort(key=lambda c: (c.date, c.debut), reverse=True)

        return cls(
            justifiees_nb=j_nb,
            justifiees_heures=j_h,
            justifiees_demi_journees=j_demi,
            justifiees_journees=j_jour,
            injustifiees_nb=nj_nb,
            injustifiees_heures=nj_h,
            injustifiees_demi_journees=nj_demi,
            injustifiees_journees=nj_jour,
            total_nb=tot_nb,
            total_heures=tot_h,
            total_demi_journees=tot_demi,
            retards_nb=ret_nb,
            retards_heures=ret_h,
            creneaux=creneaux,
        )


@dataclass
class Releve:
    """
    Objet principal regroupant toutes les données du relevé de notes ScoDoc.
    Offre des méthodes rapides pour accéder aux moyennes, rangs, notes et assiduité.
    """
    etudiant: Etudiant
    formation: str
    semestre_id: int
    semestre_numero: int
    annee_universitaire: str
    stats: StatistiquesSemestre
    ues: Dict[str, UE] = field(default_factory=dict)
    ressources: Dict[str, Matiere] = field(default_factory=dict)
    saes: Dict[str, Matiere] = field(default_factory=dict)
    absences: Absences = field(default_factory=Absences)
    groupes: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)
    _client: Optional[Any] = field(default=None, repr=False, compare=False)

    @property
    def moyenne_generale(self) -> Optional[float]:
        """Retourne la moyenne générale indicative de l'étudiant."""
        return self.stats.moyenne_generale

    @property
    def rang(self) -> Optional[int]:
        """Retourne le rang de l'étudiant dans sa promotion."""
        return self.stats.rang

    @property
    def total_promo(self) -> Optional[int]:
        """Retourne l'effectif total de la promotion."""
        return self.stats.total_promo

    @property
    def toutes_les_notes(self) -> List[Evaluation]:
        """
        Retourne la liste à plat de toutes les évaluations saisies,
        triées par date décroissante.
        """
        all_evals = []
        for mat in list(self.ressources.values()) + list(self.saes.values()):
            all_evals.extend(mat.evaluations)
        return sorted(all_evals, key=lambda e: e.date or "", reverse=True)

    @property
    def notes_avec_valeur(self) -> List[Evaluation]:
        """Retourne uniquement les évaluations ayant déjà reçu une note numérique."""
        return [e for e in self.toutes_les_notes if e.note is not None]

    def get_ue(self, code_ue: str) -> Optional[UE]:
        """Retourne l'objet UE correspondant au code (ex: 'UE1.1')."""
        return self.ues.get(code_ue)

    def get_matiere(self, code: str) -> Optional[Matiere]:
        """Retourne la ressource ou la SAÉ par son code (ex: 'R101' ou 'SAÉ1.1')."""
        return self.ressources.get(code) or self.saes.get(code)

    def get_student_pic(self) -> bytes:
        """Télécharge les octets (JPEG) de la photo officielle de l'étudiant."""
        if not self._client:
            raise RuntimeError("Ce relevé n'est rattaché à aucun client ScoDoc connecté.")
        return self._client.get_student_pic(nip=self.etudiant.code_nip)

    def get_student_pic_base64(self) -> str:
        """Retourne la photo de l'étudiant sous forme d'URI data base64."""
        if not self._client:
            raise RuntimeError("Ce relevé n'est rattaché à aucun client ScoDoc connecté.")
        return self._client.get_student_pic_base64(nip=self.etudiant.code_nip)

    def save_student_pic(self, destination_path: str) -> str:
        """Enregistre la photo de l'étudiant dans un fichier local."""
        if not self._client:
            raise RuntimeError("Ce relevé n'est rattaché à aucun client ScoDoc connecté.")
        return self._client.save_student_pic(destination_path, nip=self.etudiant.code_nip)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet Releve complet en dictionnaire Python."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Sérialise l'objet Releve complet en chaîne JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_api_response(
        cls,
        data: Dict[str, Any],
        base_url: str = "",
        client: Optional[Any] = None,
    ) -> Releve:
        """Instancie un Releve à partir de la réponse brute JSON de dataPremièreConnexion."""
        releve_data = data.get("relevé") or {}
        etud_data = releve_data.get("etudiant") or {}
        sem_data = releve_data.get("semestre") or {}
        formation_data = releve_data.get("formation") or {}

        etudiant = Etudiant.from_dict(etud_data, base_url=base_url)
        stats = StatistiquesSemestre.from_dict(sem_data)

        # Parsing des UEs
        ues = {}
        for code, ue_dict in (releve_data.get("ues") or {}).items():
            if isinstance(ue_dict, dict):
                ues[code] = UE.from_dict(code, ue_dict)

        # Mapping des identifiants vers les noms de matières
        matieres_map: Dict[Any, str] = {}

        # Parsing des ressources
        ressources = {}
        for code, res_dict in (releve_data.get("ressources") or {}).items():
            if isinstance(res_dict, dict):
                titre = res_dict.get("titre", "")
                mat_id = res_dict.get("id")
                if mat_id:
                    matieres_map[mat_id] = f"{code} - {titre}"
                    matieres_map[str(mat_id)] = f"{code} - {titre}"

                evals = [
                    Evaluation.from_dict(ev, code_matiere=code, titre_matiere=titre, client=client)
                    for ev in (res_dict.get("evaluations") or [])
                ]
                moy = _parse_float(res_dict.get("moyenne", {}).get("value") if isinstance(res_dict.get("moyenne"), dict) else None)
                ressources[code] = Matiere(
                    code=code,
                    titre=titre,
                    type="ressource",
                    id=_parse_int(mat_id) or 0,
                    moyenne=moy,
                    evaluations=evals,
                    raw=res_dict,
                )

        # Parsing des SAÉs
        saes = {}
        for code, sae_dict in (releve_data.get("saes") or {}).items():
            if isinstance(sae_dict, dict):
                titre = sae_dict.get("titre", "")
                mat_id = sae_dict.get("id")
                if mat_id:
                    matieres_map[mat_id] = f"{code} - {titre}"
                    matieres_map[str(mat_id)] = f"{code} - {titre}"

                evals = [
                    Evaluation.from_dict(ev, code_matiere=code, titre_matiere=titre, client=client)
                    for ev in (sae_dict.get("evaluations") or [])
                ]
                moy = _parse_float(sae_dict.get("moyenne", {}).get("value") if isinstance(sae_dict.get("moyenne"), dict) else None)
                saes[code] = Matiere(
                    code=code,
                    titre=titre,
                    type="sae",
                    id=_parse_int(mat_id) or 0,
                    moyenne=moy,
                    evaluations=evals,
                    raw=sae_dict,
                )

        # Parsing complet des absences
        absences = Absences.from_api_data(
            totaux_data=data.get("totauxAbsences"),
            absences_detail=data.get("absences"),
            semestre_absences=sem_data.get("absences"),
            matieres_map=matieres_map,
        )

        # Groupes (TD, TP)
        groupes = []
        for g in (sem_data.get("groupes") or []):
            if isinstance(g, dict):
                p_name = g.get("partition", {}).get("partition_name") if isinstance(g.get("partition"), dict) else None
                g_name = g.get("group_name")
                if p_name and p_name not in groupes:
                    groupes.append(p_name)
                if g_name and g_name not in groupes:
                    groupes.append(g_name)

        return cls(
            etudiant=etudiant,
            formation=formation_data.get("titre") or formation_data.get("titre_officiel") or "Formation",
            semestre_id=_parse_int(releve_data.get("formsemestre_id")) or 0,
            semestre_numero=_parse_int(sem_data.get("numero")) or 1,
            annee_universitaire=sem_data.get("annee_universitaire") or "",
            stats=stats,
            ues=ues,
            ressources=ressources,
            saes=saes,
            absences=absences,
            groupes=groupes,
            raw=data,
            _client=client,
        )
