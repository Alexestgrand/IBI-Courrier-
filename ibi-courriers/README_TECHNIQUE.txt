================================================================
IBI COURRIERS - Documentation technique
================================================================

Stack : Python 3.11, CustomTkinter, SQLite, ReportLab, bcrypt
Packaging : PyInstaller --onedir --windowed

Emplacement des donnees (a cote de IBI_COURRIERS.exe) :
  courriers.db      - base SQLite
  uploads\          - pieces jointes scannees
  exports\          - PDF courriers sortants
  backups\          - sauvegardes (dont _pre_restore\)
  assets\           - optionnel cote utilisateur ; logo bundle
                      dans _internal\assets\

Assets en lecture (logo UI/PDF) : extraits dans _internal\ via PyInstaller.

Journal / tracabilite :
  Table audit_log dans courriers.db (PAS de dossier logs\ fichier)

Sauvegarde automatique :
  Quotidienne a minuit : create_backup()
  Tache hebdomadaire : purge backups > 30 jours (min. 5 conservees)
  Ce n'est PAS une 2e copie hebdomadaire.

En cas de probleme :
  - Verifier droits d'ecriture sur le dossier de l'exe
  - Restaurer depuis backups\ via menu Sauvegardes
  - Consulter journal d'audit (admin > Utilisateurs)
  - Voir readme.md pour depannage detaille

Statut "Traite" (cahier des charges) = "Valide" (valide) en base.

Version : IBI COURRIERS v1.0
================================================================
