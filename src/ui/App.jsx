import { useCallback, useEffect, useState } from 'react'
import { api } from './api'

const navigation = [
  ['Inbox', '⌂'], ['Starred', '☆'], ['Important', '!'], ['Attachments', '⌇'],
  ['Jobs', '▣'], ['Education', '▤'], ['Shopping', '◫'], ['GitHub', '⌘'], ['LinkedIn', 'in'],
]
const suggestions = ['What emails do I have about Python?', 'Who sent the Python statistics email?', 'Show my latest emails', 'Show unread job emails', 'Summarize the Python statistics email']

function formatDate(value) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? value : new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date)
}

function Sidebar({ active, onSelect, onSync, syncing }) {
  return <aside className="sidebar"><div className="brand"><span className="brand-mark">✦</span><span>Smart Mail<br />Manager</span></div>
    <button className="sync-button" onClick={onSync} disabled={syncing}>{syncing ? 'Syncing…' : '↻  Sync mail'}</button>
    <nav>{navigation.map(([name, icon]) => <button key={name} className={active === name ? 'nav-item selected' : 'nav-item'} onClick={() => onSelect(name)}><span className="nav-icon">{icon}</span>{name}</button>)}</nav>
    <button className="settings">⚙ Settings <span>⌄</span></button></aside>
}

function EmailList({ emails, loading, error, active, onOpen }) {
  return <section className="list-panel"><div className="panel-header"><div><p className="eyebrow">Mailbox</p><h1>{active}</h1></div><span className="count">{emails.length}</span></div>
    {loading && <div className="state">Loading emails…</div>}
    {error && <div className="state error">{error}</div>}
    {!loading && !error && !emails.length && <div className="state">No emails match this filter yet.</div>}
    <div className="email-scroll">{emails.map(email => <button className={`email-row ${email.unread ? 'unread' : ''}`} key={email.id} onClick={() => onOpen(email.id)}>
      <div className="sender-line"><span className="sender">{email.sender}</span><time>{formatDate(email.date)}</time></div><div className="subject-line">{email.unread && <i />}{email.subject}</div>
      <p>{email.snippet || 'No preview available.'}</p><div className="chips">{email.category !== 'Uncategorized' && <span>{email.category}</span>}{email.hasAttachment && <span>⌇ Attachment</span>}</div>
    </button>)}</div></section>
}

function EmailBody({ body, snippet }) {
  const content = body || snippet || 'This email does not contain readable text.'
  const isHtml = /<\/?[a-z][\s\S]*>/i.test(content)

  if (isHtml) {
    return <iframe className="email-html" title="Email content" sandbox="allow-popups allow-popups-to-escape-sandbox" srcDoc={content} />
  }
  return <article className="email-plain">{content}</article>
}

function EmailViewer({ email, loading, error, onBack }) {
  return <section className="viewer"><div className="viewer-header"><button className="back" onClick={onBack}>← Back to list</button>{loading && <div className="state">Opening email…</div>}{error && <div className="state error">{error}</div>}
    {email && <><div className="message-heading"><div className="avatar">{email.sender[0]?.toUpperCase()}</div><div><h2>{email.subject}</h2><p>From <strong>{email.sender}</strong> · {formatDate(email.date)}</p><p>To {email.recipient || 'you'}{email.cc && ` · Cc ${email.cc}`}</p></div></div>
      <div className="message-tags"><span>{email.category}</span>{email.hasAttachment && <span>⌇ Has attachment</span>}{email.important && <span>Important</span>}</div></>}</div>
    {email && <div className="message-body"><EmailBody body={email.body} snippet={email.snippet} /></div>}
  </section>
}

function Assistant({ result, query, setQuery, submitting, onAsk, onOpen }) {
  const submit = (event) => { event.preventDefault(); onAsk(query) }
  return <aside className="assistant"><div className="assistant-title"><div><p className="eyebrow">LOCAL AI ASSISTANT</p><h2>Ask your inbox</h2></div><span className="status-dot">● Local</span></div>
    <form onSubmit={submit}><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Ask about your emails…" /><button disabled={submitting || !query.trim()}>{submitting ? '…' : '→'}</button></form>
    {!result && <div className="suggestions"><p>Try asking</p>{suggestions.map(s => <button key={s} onClick={() => setQuery(s)}>{s}</button>)}</div>}
    {result?.error && <div className="assistant-error">{result.error}</div>}
    {result?.answer && <div className="answer"><p className="eyebrow">AI ANSWER</p><div>{result.answer}</div><p className="eyebrow sources-title">SOURCES · {result.sources?.length || 0}</p>{result.sources?.length ? result.sources.map(source => <button className="source" key={source.id} onClick={() => onOpen(source.id)}><b>{source.subject}</b><span>{source.sender}</span><small>{source.similarity == null ? 'Metadata match' : `${(source.similarity * 100).toFixed(1)}% similarity`}</small></button>) : <p className="muted">No source emails were returned.</p>}</div>}
  </aside>
}

export default function App() {
  const [active, setActive] = useState('Inbox'), [emails, setEmails] = useState([]), [loading, setLoading] = useState(true), [error, setError] = useState(''), [selected, setSelected] = useState(null), [viewerError, setViewerError] = useState(''), [viewerLoading, setViewerLoading] = useState(false), [query, setQuery] = useState(''), [result, setResult] = useState(null), [submitting, setSubmitting] = useState(false), [syncing, setSyncing] = useState(false)
  const loadEmails = useCallback(async (filter) => { setLoading(true); setError(''); try { const data = await api.getEmails(filter); if (!Array.isArray(data)) throw new Error('Malformed email list received from the backend.'); setEmails(data) } catch (e) { setEmails([]); setError(e.message) } finally { setLoading(false) } }, [])
  useEffect(() => { loadEmails(active) }, [active, loadEmails])
  async function openEmail(id) { setViewerLoading(true); setViewerError(''); setSelected({}); try { setSelected(await api.getEmail(id)) } catch (e) { setSelected(null); setViewerError(e.message) } finally { setViewerLoading(false) } }
  async function ask(question) { if (!question.trim()) return; setSubmitting(true); setResult(null); try { setResult(await api.ask(question)) } catch (e) { setResult({ error: e.message }) } finally { setSubmitting(false) } }
  async function sync() { setSyncing(true); setError(''); try { const data = await api.sync(); await loadEmails(active); setResult({ answer: `Sync complete: ${data.added || 0} new emails, ${data.existing || 0} already stored.`, sources: [] }) } catch (e) { setError(e.message) } finally { setSyncing(false) } }
  return <main className="app"><Sidebar active={active} onSelect={name => { setActive(name); setSelected(null) }} onSync={sync} syncing={syncing} /><div className="content">{selected !== null || viewerLoading || viewerError ? <EmailViewer email={selected?.id ? selected : null} loading={viewerLoading} error={viewerError} onBack={() => { setSelected(null); setViewerError('') }} /> : <EmailList emails={emails} loading={loading} error={error} active={active} onOpen={openEmail} />}</div><Assistant result={result} query={query} setQuery={setQuery} submitting={submitting} onAsk={ask} onOpen={openEmail} /></main>
}
