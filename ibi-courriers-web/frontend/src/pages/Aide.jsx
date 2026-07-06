import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../hooks/usePageTitle";

const SECTIONS = {
  all: [
    {
      title: "Connexion",
      items: [
        "Ouvrez https://courriersibi.com dans votre navigateur.",
        "Connectez-vous avec votre e-mail et mot de passe fournis par l'administrateur.",
        "Changez votre mot de passe à la première connexion si demandé.",
      ],
    },
    {
      title: "Recherche",
      items: [
        "Menu Recherche : filtrez par mot-clé, statut, service, période.",
        "Exportez les résultats en PDF ou CSV.",
      ],
    },
  ],
  reception: [
    {
      title: "Courriers entrants",
      items: [
        "Menu Entrants → Nouveau entrant.",
        "Renseignez expéditeur, objet, service destinataire et urgence.",
        "Joignez les scans (PDF, JPG, PNG, DOCX).",
        "Le numéro est généré automatiquement.",
        "Transmettez le courrier au service concerné (statut → Transmis).",
      ],
    },
  ],
  dg: [
    {
      title: "Validation",
      items: [
        "Consultez les courriers au statut Transmis.",
        "Ouvrez la fiche courrier pour valider ou rejeter.",
        "Ajoutez une observation si nécessaire.",
        "Le tableau de bord affiche les urgents et le journal du jour.",
      ],
    },
  ],
  comptabilite: [
    {
      title: "Votre service",
      items: [
        "Menu Entrants → cochez Mon service pour voir vos courriers.",
        "Traitez les courriers reçus pour la Comptabilité.",
      ],
    },
  ],
  marche: [
    {
      title: "Votre service",
      items: [
        "Menu Entrants → cochez Mon service.",
        "Consultez les DAO et appels d'offres reçus.",
      ],
    },
  ],
  achat: [
    {
      title: "Votre service",
      items: [
        "Menu Entrants → cochez Mon service.",
        "Consultez les courriers fournisseurs.",
      ],
    },
  ],
  admin: [
    {
      title: "Administration",
      items: [
        "Utilisateurs : créer, modifier, réinitialiser les mots de passe.",
        "Administration : sauvegardes manuelles, test e-mail SMTP.",
        "Journal d'audit visible dans Utilisateurs.",
      ],
    },
  ],
};

const LIBELLES_ROLE = {
  admin: "Administrateur",
  dg: "Direction Générale",
  reception: "Réception / Archiviste",
  comptabilite: "Comptabilité",
  marche: "Service Marché",
  achat: "Service Achat",
};

export default function Aide() {
  usePageTitle("Aide");
  const { user } = useAuth();
  const role = user?.role || "reception";

  const sections = [
    ...SECTIONS.all,
    ...(SECTIONS[role] || []),
    ...(role === "admin" ? SECTIONS.admin : []),
  ];

  return (
    <div>
      <h2 className="page-title" style={{ marginBottom: "0.5rem" }}>
        Manuel utilisateur
      </h2>
      <p className="text-secondary" style={{ marginBottom: "1.5rem" }}>
        Guide pour le profil : <strong>{LIBELLES_ROLE[role] || role}</strong>
      </p>

      {sections.map((section) => (
        <div key={section.title} className="panel">
          <h3 className="panel__title">{section.title}</h3>
          <ul className="aide-list">
            {section.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ))}

      <div className="panel">
        <h3 className="panel__title">Workflow des statuts</h3>
        <p className="text-secondary">
          En attente → Transmis → Validé ou Rejeté → Archivé
        </p>
        <p className="text-muted" style={{ marginTop: "0.5rem", fontSize: "0.875rem" }}>
          « Validé » correspond au statut « Traité » du cahier des charges.
        </p>
      </div>

      <div className="panel">
        <h3 className="panel__title">Support</h3>
        <p className="text-secondary">
          En cas de problème, contactez l&apos;administrateur système du Groupe IBI.
        </p>
      </div>
    </div>
  );
}
