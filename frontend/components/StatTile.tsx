const ACCENTS: Record<string, string> = {
  rose: "text-rose-600 bg-rose-50",
  emerald: "text-emerald-600 bg-emerald-50",
  amber: "text-amber-600 bg-amber-50",
  brand: "text-brand-600 bg-brand-50",
  gray: "text-gray-600 bg-gray-100",
};

export default function StatTile({
  label,
  value,
  icon,
  accent = "gray",
}: {
  label: string;
  value: number | string;
  icon?: string;
  accent?: keyof typeof ACCENTS;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-col gap-2 hover:shadow-sm transition-shadow">
      <div className="flex items-center justify-between">
        <span className="text-2xl font-bold text-gray-900 tabular-nums">{value}</span>
        {icon && (
          <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-sm ${ACCENTS[accent]}`}>
            {icon}
          </span>
        )}
      </div>
      <span className="text-xs uppercase tracking-wide text-gray-500 font-medium">{label}</span>
    </div>
  );
}
