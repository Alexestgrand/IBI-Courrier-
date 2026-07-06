"""Modèles SQLAlchemy."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    mot_de_passe: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    derniere_connexion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    chemin_signature: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Entite(Base):
    __tablename__ = "entites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    courriers: Mapped[list["Courrier"]] = relationship(back_populates="entite")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Courrier(Base):
    __tablename__ = "courriers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    entite_id: Mapped[int] = mapped_column(ForeignKey("entites.id"), nullable=False)
    date_reception: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expediteur: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    objet: Mapped[str] = mapped_column(Text, nullable=False)
    service_destinataire: Mapped[str | None] = mapped_column(String(100), nullable=True)
    destinataire: Mapped[str | None] = mapped_column(String(255), nullable=True)
    adresse_destinataire: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_emetteur: Mapped[str | None] = mapped_column(String(100), nullable=True)
    corps_courrier: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgence: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    statut: Mapped[str] = mapped_column(String(20), default="en_attente", nullable=False)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    chemin_pdf: Mapped[str | None] = mapped_column(String(500), nullable=True)
    signe_par_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    signe_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    entite: Mapped["Entite"] = relationship(back_populates="courriers")
    signataire: Mapped["User | None"] = relationship(foreign_keys=[signe_par_id])
    pieces_jointes: Mapped[list["PieceJointe"]] = relationship(
        back_populates="courrier", cascade="all, delete-orphan"
    )
    historique_statuts: Mapped[list["StatutLog"]] = relationship(
        back_populates="courrier", cascade="all, delete-orphan"
    )


class PieceJointe(Base):
    __tablename__ = "pieces_jointes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    courrier_id: Mapped[int] = mapped_column(ForeignKey("courriers.id"), nullable=False)
    nom_original: Mapped[str] = mapped_column(String(255), nullable=False)
    chemin_stockage: Mapped[str] = mapped_column(String(500), nullable=False)
    taille_octets: Mapped[int] = mapped_column(Integer, nullable=False)
    type_mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    courrier: Mapped["Courrier"] = relationship(back_populates="pieces_jointes")


class StatutLog(Base):
    __tablename__ = "statuts_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    courrier_id: Mapped[int] = mapped_column(ForeignKey("courriers.id"), nullable=False)
    ancien_statut: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nouveau_statut: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    courrier: Mapped["Courrier"] = relationship(back_populates="historique_statuts")
    utilisateur: Mapped["User | None"] = relationship()


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    titre: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    courrier_id: Mapped[int | None] = mapped_column(
        ForeignKey("courriers.id"), nullable=True
    )
    lu: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    utilisateur: Mapped["User"] = relationship()
    courrier: Mapped["Courrier | None"] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    utilisateur: Mapped["User | None"] = relationship(foreign_keys=[user_id])
