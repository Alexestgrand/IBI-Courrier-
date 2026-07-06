export default function AlerteErreur({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="alerte-erreur" role="alert">
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn btn-secondary btn-sm" onClick={onRetry}>
          Réessayer
        </button>
      )}
    </div>
  );
}
