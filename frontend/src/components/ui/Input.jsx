import { forwardRef } from "react";

export const Label = ({ children, className = "" }) => (
  <label className={`block text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1.5 ${className}`}>
    {children}
  </label>
);

export const Input = forwardRef(({ error, className = "", ...props }, ref) => (
  <input
    ref={ref}
    className={`w-full h-10 px-3 rounded-lg border bg-white text-sm text-ink placeholder:text-ink-faint
      transition-colors duration-150
      ${error ? "border-danger focus:border-danger" : "border-border focus:border-brand-500"}
      focus:outline-none focus:ring-2 ${error ? "focus:ring-red-100" : "focus:ring-brand-100"}
      disabled:bg-canvas disabled:text-ink-faint
      ${className}`}
    {...props}
  />
));
Input.displayName = "Input";

export const Textarea = forwardRef(({ error, className = "", ...props }, ref) => (
  <textarea
    ref={ref}
    className={`w-full px-3 py-2 rounded-lg border bg-white text-sm text-ink placeholder:text-ink-faint
      transition-colors duration-150
      ${error ? "border-danger focus:border-danger" : "border-border focus:border-brand-500"}
      focus:outline-none focus:ring-2 ${error ? "focus:ring-red-100" : "focus:ring-brand-100"}
      ${className}`}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export const Select = forwardRef(({ error, className = "", children, ...props }, ref) => (
  <select
    ref={ref}
    className={`w-full h-10 px-3 rounded-lg border bg-white text-sm text-ink
      transition-colors duration-150 appearance-none
      ${error ? "border-danger" : "border-border focus:border-brand-500"}
      focus:outline-none focus:ring-2 focus:ring-brand-100
      ${className}`}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = "Select";

export const FieldError = ({ children }) =>
  children ? <p className="mt-1 text-xs text-danger">{children}</p> : null;
