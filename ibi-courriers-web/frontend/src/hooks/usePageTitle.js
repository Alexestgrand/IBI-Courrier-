import { useEffect } from "react";

export function usePageTitle(title) {
  useEffect(() => {
    const previous = document.title;
    document.title = title ? `${title} — IBI Courriers` : "IBI Courriers";
    return () => {
      document.title = previous;
    };
  }, [title]);
}
