import { api } from "@/lib/api";

export default async function SettingsPage() {
  const settings = await api.getSettings();

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <h1 className="text-xl font-semibold">Settings</h1>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h2 className="font-semibold mb-3">Notifications</h2>
        <dl className="text-sm grid grid-cols-2 gap-y-2">
          <dt className="text-gray-500">Mode</dt>
          <dd>{String(settings.notification_mode)}</dd>
          <dt className="text-gray-500">Email enabled</dt>
          <dd>{settings.email_notifications_enabled ? "Yes" : "No"}</dd>
          <dt className="text-gray-500">Email configured</dt>
          <dd>{settings.email_configured ? "Yes (SMTP_HOST + NOTIFICATION_EMAIL set)" : "No — set SMTP env vars"}</dd>
          <dt className="text-gray-500">Telegram enabled</dt>
          <dd>{settings.telegram_notifications_enabled ? "Yes" : "No"}</dd>
          <dt className="text-gray-500">Telegram configured</dt>
          <dd>{settings.telegram_configured ? "Yes (bot token + chat id set)" : "No — set TELEGRAM env vars"}</dd>
          <dt className="text-gray-500">Search interval</dt>
          <dd>{String(settings.search_interval_minutes)} minutes</dd>
        </dl>
        <p className="text-xs text-gray-400 mt-3">
          Channel credentials and toggles are configured via environment variables (.env) for security and are not
          editable from this dashboard. See the README for setup instructions.
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h2 className="font-semibold mb-3">Default scoring weights</h2>
        <p className="text-xs text-gray-400 mb-3">
          Per-search-profile weight overrides can be set via the Search Profiles API (scoring_weights field).
        </p>
        <div className="grid grid-cols-2 gap-y-1 text-sm">
          {Object.entries(settings.default_scoring_weights as Record<string, number>).map(([key, value]) => (
            <div key={key} className="contents">
              <span className="text-gray-500">{key.replace(/_/g, " ")}</span>
              <span className={value < 0 ? "text-red-600" : "text-gray-900"}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
