interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'default';
  className?: string;
  title?: string;
}

export function Badge({ children, variant = 'default', className = '', title }: BadgeProps) {
  const variantClasses = {
    primary: 'bg-blue-100 text-blue-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-amber-100 text-amber-800',
    danger: 'bg-red-100 text-red-800',
    default: 'bg-slate-100 text-slate-800',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]} ${className}`}
      title={title}
    >
      {children}
    </span>
  );
}
