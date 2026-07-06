function buildPages(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const delta = 2;
  const left = Math.max(2, current - delta);
  const right = Math.min(total - 1, current + delta);
  const pages = [1];
  if (left > 2) pages.push("…");
  for (let i = left; i <= right; i++) pages.push(i);
  if (right < total - 1) pages.push("…");
  pages.push(total);
  return pages;
}

export default function Pagination({ page, pages, total, onPageChange }) {
  if (pages <= 1) return null;

  const pageList = buildPages(page, pages);

  return (
    <div className="pagination">
      <span className="pagination__info">
        {total} résultat{total > 1 ? "s" : ""}
      </span>
      <div className="pagination__pages">
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Page précédente"
        >
          ‹
        </button>
        {pageList.map((p, i) =>
          p === "…" ? (
            <span key={`ell-${i}`} className="pagination__page-btn is-ellipsis">
              …
            </span>
          ) : (
            <button
              key={p}
              type="button"
              className={`pagination__page-btn${p === page ? " is-current" : ""}`}
              onClick={() => p !== page && onPageChange(p)}
              aria-label={`Page ${p}`}
              aria-current={p === page ? "page" : undefined}
            >
              {p}
            </button>
          )
        )}
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
          aria-label="Page suivante"
        >
          ›
        </button>
      </div>
    </div>
  );
}
