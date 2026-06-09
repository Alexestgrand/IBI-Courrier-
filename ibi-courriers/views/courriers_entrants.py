"""Vue de gestion des courriers entrants."""



import os

import tkinter.filedialog as filedialog

from datetime import datetime

from typing import Any



import customtkinter as ctk



from services.courriers import (

    creer_courrier_entrant,

    generer_numero_entrant,

    lister_courriers_entrants,

    lister_services,

)

from utils.constants import (

    COULEURS_STATUT,

    COULEURS_URGENCE,

    FILTRES_STATUT,

    LIBELLES_STATUT,

    LIBELLES_URGENCE,

    URGENCES_UI,

)

from utils.theme import (

    ACCENT,

    ACCENT_HOVER,

    ERREUR,

    FOND_CONTENU,

    HAUTEUR_BOUTON_LIGNE,

    HAUTEUR_CHAMP,

    POLICE_ENTETE,

    POLICE_TEXTE,

    SECONDAIRE,

    TEXTE_PRIMAIRE,

    TEXTE_SECONDAIRE,

)

from views.fiche_courrier import ouvrir_fiche_entrant

from views.ui_helpers import (

    afficher_message_statut,

    alterner_couleur_ligne,

    configurer_modale,

    configurer_survol_ligne,

    creer_barre_titre,

    creer_entete_tableau,

    creer_etat_vide,

    lier_infobulle,

    packer_barre_actions,

    tronquer_texte,

)



COULEUR_CONTENU_DEFAUT = FOND_CONTENU



LARGEURS_COLONNES = (100, 90, 120, 180, 110, 80, 90, 70)





class CourriersEntrantsView(ctk.CTkFrame):

    """Liste et gestion des courriers entrants."""



    def __init__(

        self,

        parent: ctk.CTkFrame,

        *,

        utilisateur: dict[str, Any],

        couleur_contenu: str = COULEUR_CONTENU_DEFAUT,

    ) -> None:

        super().__init__(parent, fg_color=couleur_contenu, corner_radius=0)

        self.utilisateur = utilisateur

        self.couleur_contenu = couleur_contenu

        self.filtre_statut_actuel: str | None = None

        self.recherche_actuelle = ""

        self.chemin_piece_jointe_source: str | None = None

        self.pack(fill="both", expand=True)

        self._construire_interface()

        self.charger_liste()



    def _construire_interface(self) -> None:

        _, zone_actions = creer_barre_titre(self, "Courriers entrants")

        self.champ_recherche = ctk.CTkEntry(
            zone_actions,
            placeholder_text="N\u00b0, objet ou exp\u00e9diteur\u2026",
            font=POLICE_TEXTE,
            width=200,
        )
        self.champ_recherche.bind("<KeyRelease>", self._on_recherche_key)

        btn_rechercher = ctk.CTkButton(
            zone_actions,
            text="Rechercher",
            font=POLICE_TEXTE,
            width=90,
            fg_color=SECONDAIRE,
            command=self._lancer_recherche,
        )

        self.menu_filtre = ctk.CTkOptionMenu(
            zone_actions,
            values=list(FILTRES_STATUT.keys()),
            font=POLICE_TEXTE,
            command=self._appliquer_filtre,
        )
        self.menu_filtre.set("Tous")

        packer_barre_actions(
            zone_actions,
            [self.champ_recherche, btn_rechercher, self.menu_filtre],
            bouton_primaire=("Nouveau courrier", self.ouvrir_formulaire_nouveau),
        )



        creer_entete_tableau(

            self,

            [

                "N°",

                "Date",

                "Expéditeur",

                "Objet",

                "Service",

                "Urgence",

                "Statut",

                "Actions",

            ],

            LARGEURS_COLONNES,

        )



        self.zone_liste = ctk.CTkScrollableFrame(

            self, fg_color="transparent", corner_radius=0

        )

        self.zone_liste.pack(fill="both", expand=True, padx=24, pady=(0, 16))



    def _configurer_grille(self, conteneur: ctk.CTkFrame) -> None:

        for index, largeur in enumerate(LARGEURS_COLONNES):

            conteneur.grid_columnconfigure(index, minsize=largeur, weight=1 if index == 3 else 0)



    def _appliquer_filtre(self, choix: str) -> None:

        self.filtre_statut_actuel = FILTRES_STATUT.get(choix)

        self.charger_liste()



    def _on_recherche_key(self, _event: object) -> None:

        self.recherche_actuelle = self.champ_recherche.get().strip()

        self.charger_liste()



    def _lancer_recherche(self) -> None:

        self.recherche_actuelle = self.champ_recherche.get().strip()

        self.charger_liste()



    def charger_liste(self) -> None:

        """Recharge la liste des courriers."""

        for widget in self.zone_liste.winfo_children():

            widget.destroy()



        try:

            courriers = lister_courriers_entrants(

                filtre_statut=self.filtre_statut_actuel,

                recherche=self.recherche_actuelle or None,

            )

        except RuntimeError:

            courriers = []



        if not courriers:

            creer_etat_vide(

                self.zone_liste,

                "Aucun courrier entrant",

                sous_message="Créez un courrier ou modifiez les filtres",

            )

            return



        for index, courrier in enumerate(courriers):

            self._ajouter_ligne(courrier, index)



    def _ajouter_ligne(self, courrier: dict[str, Any], index: int) -> None:

        couleur_base = alterner_couleur_ligne(index)

        ligne = ctk.CTkFrame(

            self.zone_liste,

            fg_color=couleur_base,

            corner_radius=4,

        )

        ligne.pack(fill="x", pady=1)

        configurer_survol_ligne(ligne, couleur_base)

        self._configurer_grille(ligne)



        date_aff = courrier.get("date_reception") or (

            (courrier.get("created_at") or "")[:10]

        )

        statut = str(courrier.get("statut", ""))

        urgence = str(courrier.get("urgence", "normal"))



        valeurs = (

            courrier.get("numero", ""),

            date_aff,

            courrier.get("expediteur", ""),

            courrier.get("objet", ""),

            courrier.get("service_destinataire", ""),

        )

        for col, texte in enumerate(valeurs):

            if col == 3:

                texte_complet = str(texte)

                texte_affiche = tronquer_texte(texte_complet, 40)

                label = ctk.CTkLabel(

                    ligne,

                    text=texte_affiche,

                    font=POLICE_TEXTE,

                    text_color=TEXTE_PRIMAIRE,

                    anchor="w",

                )

                lier_infobulle(label, texte_complet)

            else:

                label = ctk.CTkLabel(

                    ligne,

                    text=str(texte),

                    font=POLICE_TEXTE,

                    text_color=TEXTE_PRIMAIRE,

                    anchor="w",

                )

            label.grid(row=0, column=col, padx=6, pady=6, sticky="ew")



        ctk.CTkLabel(

            ligne,

            text=LIBELLES_URGENCE.get(urgence, urgence),

            font=POLICE_TEXTE,

            text_color=COULEURS_URGENCE.get(urgence, TEXTE_PRIMAIRE),

            anchor="w",

        ).grid(row=0, column=5, padx=6, pady=6, sticky="ew")



        ctk.CTkLabel(

            ligne,

            text=LIBELLES_STATUT.get(statut, statut),

            font=POLICE_TEXTE,

            text_color=COULEURS_STATUT.get(statut, TEXTE_PRIMAIRE),

            anchor="w",

        ).grid(row=0, column=6, padx=6, pady=6, sticky="ew")



        ctk.CTkButton(

            ligne,

            text="Voir",

            width=60,

            height=HAUTEUR_BOUTON_LIGNE,

            font=POLICE_TEXTE,

            fg_color=ACCENT,

            hover_color=ACCENT_HOVER,

            command=lambda cid=courrier["id"]: self.ouvrir_fiche(cid),

        ).grid(row=0, column=7, padx=6, pady=4)



    def ouvrir_formulaire_nouveau(self) -> None:

        """Ouvre le formulaire modal de création."""

        fenetre = ctk.CTkToplevel(self)

        fenetre.title("Nouveau courrier entrant")

        configurer_modale(fenetre, self, 520, 680, couleur=self.couleur_contenu)



        label_erreur = ctk.CTkLabel(

            fenetre, text="", font=POLICE_TEXTE, text_color=ERREUR

        )

        label_erreur.pack(fill="x", padx=24, pady=(8, 0))



        boutons = ctk.CTkFrame(fenetre, fg_color="transparent")

        boutons.pack(side="bottom", fill="x", padx=24, pady=16)



        scroll = ctk.CTkScrollableFrame(fenetre, fg_color="transparent")

        scroll.pack(fill="both", expand=True, padx=8, pady=(4, 0))



        try:

            numero_prevu = generer_numero_entrant()

        except RuntimeError:

            numero_prevu = "ENT-????-????"



        services = lister_services()

        if not services:

            services = ["—"]



        champs: dict[str, Any] = {}



        def ajouter_ligne(label: str, widget: ctk.CTkBaseClass) -> None:

            ctk.CTkLabel(

                scroll,

                text=label,

                font=POLICE_TEXTE,

                text_color=TEXTE_PRIMAIRE,

                anchor="w",

            ).pack(fill="x", padx=16, pady=(8, 2))

            widget.pack(fill="x", padx=16)



        ctk.CTkLabel(

            scroll,

            text=f"Numéro (indicatif) : {numero_prevu}",

            font=POLICE_ENTETE,

            text_color=TEXTE_SECONDAIRE,

        ).pack(anchor="w", padx=16, pady=(8, 0))



        champs["date"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE, height=HAUTEUR_CHAMP)

        champs["date"].insert(0, datetime.now().strftime("%d/%m/%Y"))

        ajouter_ligne("Date réception", champs["date"])



        champs["expediteur"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE, height=HAUTEUR_CHAMP)

        ajouter_ligne("Expéditeur *", champs["expediteur"])



        champs["reference"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE, height=HAUTEUR_CHAMP)

        ajouter_ligne("Référence document", champs["reference"])



        champs["objet"] = ctk.CTkEntry(scroll, font=POLICE_TEXTE, height=HAUTEUR_CHAMP)

        ajouter_ligne("Objet *", champs["objet"])



        champs["service"] = ctk.CTkOptionMenu(

            scroll, values=services, font=POLICE_TEXTE

        )

        champs["service"].set(services[0])

        ajouter_ligne("Service destinataire *", champs["service"])



        champs["urgence"] = ctk.CTkOptionMenu(

            scroll, values=list(URGENCES_UI.keys()), font=POLICE_TEXTE

        )

        champs["urgence"].set("Normal")

        ajouter_ligne("Urgence", champs["urgence"])



        champs["observations"] = ctk.CTkTextbox(scroll, height=80, font=POLICE_TEXTE)

        ajouter_ligne("Observations", champs["observations"])



        ctk.CTkLabel(

            scroll,

            text="Pièce jointe",

            font=POLICE_TEXTE,

            text_color=TEXTE_PRIMAIRE,

            anchor="w",

        ).pack(fill="x", padx=16, pady=(8, 2))



        frame_pj = ctk.CTkFrame(scroll, fg_color="transparent")

        frame_pj.pack(fill="x", padx=16, pady=(0, 8))

        label_pj = ctk.CTkLabel(

            frame_pj,

            text="Aucun fichier",

            font=POLICE_TEXTE,

            text_color=TEXTE_SECONDAIRE,

            anchor="w",

        )

        label_pj.pack(side="left", fill="x", expand=True)

        chemin_pj: dict[str, str | None] = {"valeur": None}



        def parcourir() -> None:

            chemin = filedialog.askopenfilename(

                parent=fenetre,

                title="Sélectionner une pièce jointe",

                filetypes=[

                    ("Documents", "*.pdf *.jpg *.jpeg *.png *.docx"),

                    ("Tous les fichiers", "*.*"),

                ],

            )

            if chemin:

                chemin_pj["valeur"] = chemin

                label_pj.configure(text=os.path.basename(chemin))



        ctk.CTkButton(

            frame_pj,

            text="Parcourir",

            width=100,

            font=POLICE_TEXTE,

            fg_color=SECONDAIRE,

            command=parcourir,

        ).pack(side="right")



        def enregistrer() -> None:

            label_erreur.configure(text="")

            data = {

                "numero": numero_prevu,

                "date_reception": champs["date"].get().strip(),

                "expediteur": champs["expediteur"].get(),

                "reference_document": champs["reference"].get().strip() or None,

                "objet": champs["objet"].get(),

                "service_destinataire": champs["service"].get(),

                "urgence": URGENCES_UI.get(champs["urgence"].get(), "normal"),

                "observations": champs["observations"].get("1.0", "end").strip() or None,

                "chemin_piece_jointe_source": chemin_pj["valeur"],

            }

            try:

                creer_courrier_entrant(data, self.utilisateur["id"])

                fenetre.destroy()

                self.charger_liste()

                afficher_message_statut("Courrier entrant créé avec succès.")

            except ValueError as erreur:

                label_erreur.configure(text=str(erreur))

            except RuntimeError:

                label_erreur.configure(

                    text="Erreur lors de l'enregistrement. Veuillez réessayer."

                )



        ctk.CTkButton(

            boutons,

            text="Enregistrer",

            font=POLICE_TEXTE,

            fg_color=ACCENT,

            hover_color=ACCENT_HOVER,

            command=enregistrer,

        ).pack(side="right", padx=(8, 0))



        ctk.CTkButton(

            boutons,

            text="Annuler",

            font=POLICE_TEXTE,

            fg_color=SECONDAIRE,

            command=fenetre.destroy,

        ).pack(side="right")



    def ouvrir_fiche(self, courrier_id: int) -> None:

        """Ouvre la fiche détail d'un courrier."""

        ouvrir_fiche_entrant(

            self,

            self.utilisateur,

            courrier_id,

            self.couleur_contenu,

            self.charger_liste,

        )

