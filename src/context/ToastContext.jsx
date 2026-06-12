import React, { createContext, useContext, useCallback, useState } from 'react';

const ToastContext = createContext();

// eslint-disable-next-line react-refresh/only-export-components
export const useToast = () => useContext(ToastContext);

const STYLES = {
  success: 'bg-green-600',
  error: 'bg-red-600',
  info: 'bg-gray-800',
};

let nextId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const remove = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id));
  }, []);

  const notify = useCallback((message, type = 'info') => {
    const id = (nextId += 1);
    setToasts((list) => [...list, { id, message, type }]);
    setTimeout(() => remove(id), 3500);
  }, [remove]);

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] space-y-2 max-w-xs">
        {toasts.map((t) => (
          <div
            key={t.id}
            onClick={() => remove(t.id)}
            role="status"
            className={`px-4 py-2 rounded shadow-lg text-sm text-white cursor-pointer ${STYLES[t.type] || STYLES.info}`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
