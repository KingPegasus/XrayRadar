export function SectionHeader({ title, desc }) {
  return (
    <div>
      <h2 className="sectionTitle">{title}</h2>
      {desc ? <p className="sectionDesc">{desc}</p> : null}
    </div>
  )
}
