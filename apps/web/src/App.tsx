import { useEffect, useState } from 'react'
import { api } from './lib/api'
import { DashboardPage } from './pages/DashboardPage'
import { SetupPage } from './pages/SetupPage'
import type { Project } from './types'

export default function App() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    api.listProjects().then((items) => {
      setProjects(items)
      if (items[0]) setSelected(items[0].id)
    }).catch(() => undefined)
  }, [])

  if (!selected) {
    return <SetupPage onCreated={(project) => { setProjects([project, ...projects]); setSelected(project.id) }} />
  }

  return (
    <>
      <nav className="topbar">
        <strong>Content Diagnosis</strong>
        <select value={selected} onChange={(event) => setSelected(event.target.value)}>
          {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
        </select>
        <button onClick={() => setSelected(null)}>New project</button>
      </nav>
      <DashboardPage projectId={selected} />
    </>
  )
}
