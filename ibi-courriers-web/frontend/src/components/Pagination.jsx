export default function Pagination({ page, pages, total, onPageChange }) {
  if (pages <= 1) return null;

  return (
    <div className="pagination">
      <span className="pagination__info">
        {total} résultat{total > 1 ? "s" : ""} — page {page} / {pages}
      </span>
      <div className="pagination__actions">
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Précédent
        </button>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          Suivant
        </button>
      </div>
    </div>
  );
}
