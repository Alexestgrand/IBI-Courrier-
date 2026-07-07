"""Schémas Pydantic (requêtes / réponses API)."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginResponse(BaseModel):
    must_change_password: bool = False
    message: str = "Connecté."


class TokenResponse(BaseModel):
    """Conservé pour compatibilité tests / clients legacy."""
    access_token: str = ""
    token_type: str = "bearer"
    must_change_password: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    mot_de_passe: str


class UserResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    role: str
    actif: bool
    must_change_password: bool = False
    a_signature: bool = False
    derniere_connexion: datetime | None = None

    model_config = {"from_attributes": True}


class EntiteResponse(BaseModel):
    id: int
    nom: str
    code: str
    actif: bool

    model_config = {"from_attributes": True}


class ServiceResponse(BaseModel):
    id: int
    nom: str
    actif: bool

    model_config = {"from_attributes": True}


class PieceJointeResponse(BaseModel):
    id: int
    nom_original: str
    taille_octets: int
    type_mime: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StatutLogResponse(BaseModel):
    id: int
    ancien_statut: str | None
    nouveau_statut: str
    observation: str | None
    date: datetime
    utilisateur_nom: str | None = None

    model_config = {"from_attributes": True}


class CourrierListItem(BaseModel):
    id: int
    numero: str
    type: str
    entite_nom: str
    entite_code: str
    objet: str
    expediteur: str | None
    destinataire: str | None
    service_destinataire: str | None
    service_emetteur: str | None
    urgence: str
    statut: str
    date_reception: str | None
    nb_pieces_jointes: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedCourriersResponse(BaseModel):
    items: list[CourrierListItem]
    total: int
    page: int
    page_size: int
    pages: int


class CourrierDetail(BaseModel):
    id: int
    numero: str
    type: str
    entite_id: int
    entite_nom: str
    entite_code: str
    date_reception: str | None
    expediteur: str | None
    reference_document: str | None
    objet: str
    service_destinataire: str | None
    destinataire: str | None
    adresse_destinataire: str | None
    service_emetteur: str | None
    corps_courrier: str | None
    urgence: str
    statut: str
    observations: str | None
    chemin_pdf: str | None = None
    signe_par_nom: str | None = None
    signe_le: datetime | None = None
    createur_nom: str | None = None
    peut_signer: bool = False
    peut_supprimer: bool = False
    pieces_jointes: list[PieceJointeResponse] = Field(default_factory=list)
    statuts_possibles: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ChangementStatutRequest(BaseModel):
    nouveau_statut: str
    observation: str | None = None


class JournalDuJour(BaseModel):
    date: str = ""
    recus: list[CourrierListItem] = Field(default_factory=list)
    traites: list[CourrierListItem] = Field(default_factory=list)


class DashboardStats(BaseModel):
    total_courriers: int
    en_attente: int
    transmis: int
    valides: int
    urgents: int = 0
    par_entite: dict[str, int]
    par_service: dict[str, int] = Field(default_factory=dict)
    recents: list[CourrierListItem] = Field(default_factory=list)
    courriers_urgents: list[CourrierListItem] = Field(default_factory=list)
    journal_du_jour: JournalDuJour = Field(default_factory=JournalDuJour)


class BackupItem(BaseModel):
    nom: str
    type: str
    taille_octets: int
    date: datetime


class RestoreBackupRequest(BaseModel):
    nom_fichier: str
    confirmation: str


class SmtpStatusResponse(BaseModel):
    enabled: bool
    host: str | None = None
    from_address: str | None = None


class TestEmailRequest(BaseModel):
    email: EmailStr


class NotificationResponse(BaseModel):
    id: int
    type: str
    titre: str
    message: str
    courrier_id: int | None
    lu: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int


class MigrationStatusResponse(BaseModel):
    pret: bool
    fichier: str | None = None
    taille_octets: int = 0


class MigrationRunRequest(BaseModel):
    entite_defaut: str = "IBI"
    dry_run: bool = False


class OcrSuggestions(BaseModel):
    expediteur: str | None = None
    reference_document: str | None = None
    objet: str | None = None


class OcrExtractionResponse(BaseModel):
    texte_brut: str = ""
    methode: str
    ocr_disponible: bool
    avertissement: str | None = None
    suggestions: OcrSuggestions = Field(default_factory=OcrSuggestions)
    confiance: str = "basse"


class UserCreateRequest(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    role: str
    mot_de_passe: str
    actif: bool = True


class UserUpdateRequest(BaseModel):
    nom: str | None = None
    prenom: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    actif: bool | None = None


class ResetPasswordRequest(BaseModel):
    mot_de_passe: str = Field(min_length=6)


class ChangePasswordRequest(BaseModel):
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str


class CourrierUpdateRequest(BaseModel):
    expediteur: str | None = None
    objet: str | None = None
    service_destinataire: str | None = None
    date_reception: str | None = None
    reference_document: str | None = None
    urgence: str | None = None
    observations: str | None = None
    destinataire: str | None = None
    adresse_destinataire: str | None = None
    service_emetteur: str | None = None
    corps_courrier: str | None = None


class RechercheRequest(BaseModel):
    mot_cle: str | None = None
    type_courrier: str | None = None
    statut: str | None = None
    service: str | None = None
    urgence: str | None = None
    entite_id: int | None = None
    date_debut: str | None = None
    date_fin: str | None = None


class AuditLogResponse(BaseModel):
    id: int
    action: str
    detail: str | None
    module: str | None
    date: datetime
    utilisateur_nom: str | None = None

    model_config = {"from_attributes": True}
