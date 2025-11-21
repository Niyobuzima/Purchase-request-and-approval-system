/**
 * FullPageLoader component.
 * Displays a centered loading spinner for full-page loading states.
 */

interface FullPageLoaderProps {
  message?: string;
}

export function FullPageLoader({ message = 'Loading...' }: FullPageLoaderProps) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center" role="status" aria-live="polite">
        <div
          className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"
          aria-hidden="true"
        ></div>
        <p className="mt-4 text-gray-600">{message}</p>
      </div>
    </div>
  );
}
