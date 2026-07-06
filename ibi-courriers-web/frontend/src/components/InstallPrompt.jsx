import { useEffect, useState } from "react";

export default function InstallPrompt() {
  const [deferred, setDeferred] = useState(null);
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem("pwa_install_dismissed") === "1"
  );

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferred(e);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  if (!deferred || dismissed) return null;

  const installer = async () => {
    deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
    localStorage.setItem("pwa_install_dismissed", "1");
  };

  return (
    <div className="install-banner">
      <span>Installez IBI Courriers sur votre appareil pour un accès rapide.</span>
      <div className="install-banner__actions">
        <button type="button" className="btn btn-primary btn-sm" onClick={installer}>
          Installer
        </button>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => {
            setDismissed(true);
            localStorage.setItem("pwa_install_dismissed", "1");
          }}
        >
          Plus tard
        </button>
      </div>
    </div>
  );
}
