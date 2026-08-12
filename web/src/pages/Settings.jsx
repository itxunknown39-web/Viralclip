import { useEffect, useState } from 'react'
import { getDevices, getSettings, updateSettings } from '../api/client.js'

export default function Settings() {
  const [devices, setDevices] = useState(null)
  const [settings, setSettings] = useState(null)
  const [apiKey, setApiKey] = useState('')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getDevices().then(setDevices).catch(() => setDevices(null))
    getSettings().then(setSettings).catch(() => setSettings(null))
  }, [])

  function patch(field, value) {
    setSettings((s) => (s ? { ...s, [field]: value } : s))
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      const payload = {
        openrouter_api_key: apiKey.trim() || undefined,
        openrouter_model: settings?.openrouter_model,
        whisper_model: settings?.whisper_model,
        whisper_device: settings?.whisper_device,
        whisper_compute_type: settings?.whisper_compute_type,
        default_clip_count: settings?.default_clip_count,
        min_clip_duration: settings?.min_clip_duration,
        max_clip_duration: settings?.max_clip_duration,
        default_caption_style: settings?.default_caption_style,
      }
      await updateSettings(payload)
      setApiKey('')
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (!settings && !devices) {
    return <div className="page"><p className="empty">Loading settings…</p></div>
  }

  return (
    <div className="page narrow">
      <div className="page-head">
        <h1>Settings</h1>
      </div>

      <div className="card">
        <h2 className="card-title">AI</h2>
        <label className="field">
          <span>OpenRouter API Key</span>
          <input
            type="password"
            className="input"
            placeholder={settings?.api_key_configured ? '•••••••••• (configured)' : 'sk-or-v1-…'}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          {!settings?.api_key_configured && (
            <span className="hint">Required for AI viral analysis. Stored server-side only.</span>
          )}
        </label>
        <label className="field">
          <span>Model</span>
          <input
            type="text"
            className="input"
            value={settings?.openrouter_model || ''}
            onChange={(e) => patch('openrouter_model', e.target.value)}
          />
        </label>
      </div>

      <div className="card">
        <h2 className="card-title">Transcription</h2>
        <div className="options-grid">
          <label className="field">
            <span>Whisper Model</span>
            <select
              className="input"
              value={settings?.whisper_model || 'medium'}
              onChange={(e) => patch('whisper_model', e.target.value)}
            >
              <option value="tiny">tiny</option>
              <option value="base">base</option>
              <option value="small">small</option>
              <option value="medium">medium</option>
              <option value="large-v3">large-v3</option>
            </select>
          </label>
          <label className="field">
            <span>Device</span>
            <select
              className="input"
              value={settings?.whisper_device || 'auto'}
              onChange={(e) => patch('whisper_device', e.target.value)}
            >
              <option value="auto">auto</option>
              <option value="cuda">cuda</option>
              <option value="cpu">cpu</option>
            </select>
          </label>
          <label className="field">
            <span>Compute Type</span>
            <select
              className="input"
              value={settings?.whisper_compute_type || 'auto'}
              onChange={(e) => patch('whisper_compute_type', e.target.value)}
            >
              <option value="auto">auto</option>
              <option value="float16">float16</option>
              <option value="int8">int8</option>
              <option value="int8_float16">int8_float16</option>
            </select>
          </label>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Defaults</h2>
        <div className="options-grid">
          <label className="field">
            <span>Clip Count</span>
            <select
              className="input"
              value={settings?.default_clip_count ?? 5}
              onChange={(e) => patch('default_clip_count', Number(e.target.value))}
            >
              {[3, 5, 10, 20].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Min Duration (s)</span>
            <input
              type="number"
              className="input"
              value={settings?.min_clip_duration ?? 20}
              onChange={(e) => patch('min_clip_duration', Number(e.target.value))}
            />
          </label>
          <label className="field">
            <span>Max Duration (s)</span>
            <input
              type="number"
              className="input"
              value={settings?.max_clip_duration ?? 60}
              onChange={(e) => patch('max_clip_duration', Number(e.target.value))}
            />
          </label>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">System</h2>
        <ul className="status-list">
          <li>
            GPU <span className={devices?.cuda_available ? 'ok' : 'warn'}>
              {devices?.cuda_available ? `${devices.gpu} · CUDA ready` : 'CPU Mode'}
            </span>
          </li>
          <li>
            NVENC <span className={devices?.nvenc_available ? 'ok' : 'warn'}>
              {devices?.nvenc_available ? 'Ready' : 'Not available (CPU fallback)'}
            </span>
          </li>
          <li>
            Whisper device <span className="ok">{settings?.whisper_device || 'auto'}</span>
          </li>
        </ul>
      </div>

      {error && <p className="text-error">{error}</p>}
      {saved && <p className="text-ok">Settings saved.</p>}
      <button className="btn primary" onClick={handleSave} disabled={saving}>
        {saving ? 'Saving…' : 'Save Settings'}
      </button>
    </div>
  )
}