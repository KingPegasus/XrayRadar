import { Link } from '../components/Link'

export function NotFoundPage() {
  return (
    <main className="page" style={{ paddingTop: 48, paddingBottom: 48 }}>
      <div className="container" style={{ maxWidth: 800 }}>
        <div className="pageCard">
          <header className="pageHeader">
            <h1 className="pageTitle">Page not found</h1>
            <p className="pageSubtitle">The page you are looking for doesn&apos;t exist or has moved.</p>
            <div style={{ marginTop: 12 }}>
              <Link to="/" className="small">Back to home</Link>
            </div>
          </header>
        </div>
      </div>
    </main>
  )
}
