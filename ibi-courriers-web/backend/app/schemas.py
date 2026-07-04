"""Schémas Pydantic (requêtes / réponses API)."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
    pieces_jointes: list[PieceJointeResponse] = Field(default_factory=list)
    statuts_possibles: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ChangementStatutRequest(BaseModel):
    nouveau_statut: str
    observation: str | None = None


class DashboardStats(BaseModel):
    total_courriers: int
    en_attente: int
    transmis: int
    valides: int
    par_entite: dict[str, int]
