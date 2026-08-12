export default function Header({ devices }) {
  let cls = 'dot gray'
  let label = 'Checking…'
  if (devices) {
    if (devices.cuda_available) {
      cls = 'dot green'
      label = `${devices.gpu || 'GPU'} Ready`
    } else {
      cls = 'dot amber'
      label = 'CPU Mode'
    }
  }
  return (
    <header className="header">
      <div className="header-title">AI Viral Clip Finder</div>
      <div className="device-badge" title={`NVENC: ${devices?.nvenc_available ? 'ready' : 'n/a'}`}>
        <span className={cls} />
        {label}
      </div>
    </header>
  )
}