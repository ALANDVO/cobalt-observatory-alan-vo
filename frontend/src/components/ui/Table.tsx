import { TableHTMLAttributes } from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

export interface TableProps<T> extends TableHTMLAttributes<HTMLTableElement> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string | number;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
  striped?: boolean;
  hoverable?: boolean;
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  emptyMessage = 'No data available',
  onRowClick,
  striped = true,
  hoverable = true,
  className = '',
  ...props
}: TableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className={`w-full border-collapse ${className}`} {...props}>
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200">
            {columns.map((column) => (
              <th
                key={column.key}
                className={`px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider ${column.className || ''}`}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-slate-500">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item, index) => (
              <tr
                key={keyExtractor(item)}
                className={`
                  ${striped && index % 2 === 1 ? 'bg-slate-50' : ''}
                  ${hoverable && onRowClick ? 'hover:bg-slate-50 cursor-pointer' : ''}
                  transition-colors
                `}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((column) => (
                  <td key={column.key} className={`px-4 py-3 text-sm text-slate-700 ${column.className || ''}`}>
                    {column.render ? column.render(item) : (item as Record<string, unknown>)[column.key] as React.ReactNode}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}