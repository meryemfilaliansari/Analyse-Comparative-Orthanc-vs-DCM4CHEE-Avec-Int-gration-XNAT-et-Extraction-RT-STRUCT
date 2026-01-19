import React, { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Activity, AlertCircle, CheckCircle, Clock, Database } from 'lucide-react'
import './index.css'

function App() {
  const [health, setHealth] = useState(null)
  const [comparisons, setComparisons] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [healthRes, statsRes, compRes] = await Promise.all([
        fetch(`${API_URL}/api/health`),
        fetch(`${API_URL}/api/statistics`),
        fetch(`${API_URL}/api/comparisons`)
      ])

      if (healthRes.ok) setHealth(await healthRes.json())
      if (statsRes.ok) setStatistics(await statsRes.json())
      if (compRes.ok) setComparisons(await compRes.json())
      
      setLoading(false)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const handleSync = async () => {
    try {
      const response = await fetch(`${API_URL}/api/patients/sync`, { method: 'POST' })
      if (response.ok) {
        alert('Synchronisation initiée!')
        fetchData()
      }
    } catch (err) {
      alert(`Erreur: ${err.message}`)
    }
  }

  const getServiceStatus = (service) => {
    if (!health) return 'unknown'
    const status = health.services[service]
    if (status === 'healthy') return 'success'
    if (status && status.includes('unhealthy')) return 'error'
    return 'warning'
  }

  if (loading) {
    return <div className="app-loading">Chargement...</div>
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <h1>🏥 PACS Multi-Systèmes</h1>
          <p>Plateforme Intégrée de Comparaison et d'Analyse Médicale DICOM</p>
        </div>
        <button className="sync-button" onClick={handleSync}>🔄 Synchroniser</button>
      </header>

      <nav className="app-nav">
        {['dashboard', 'comparisons', 'services', 'documentation'].map(tab => (
          <button
            key={tab}
            className={`nav-button ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {error && (
          <div className="error-alert">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {activeTab === 'dashboard' && (
          <div className="dashboard">
            <div className="stats-grid">
              {statistics && (
                <>
                  <div className="stat-card">
                    <Database size={32} />
                    <h3>Patients</h3>
                    <p className="stat-value">{statistics.total_patients}</p>
                  </div>
                  <div className="stat-card">
                    <Activity size={32} />
                    <h3>Études</h3>
                    <p className="stat-value">{statistics.total_studies}</p>
                  </div>
                  <div className="stat-card">
                    <CheckCircle size={32} />
                    <h3>Comparaisons</h3>
                    <p className="stat-value">{statistics.total_comparisons}</p>
                  </div>
                  <div className="stat-card">
                    <Clock size={32} />
                    <h3>Timestamp</h3>
                    <p className="stat-value">{new Date(statistics.timestamp).toLocaleString()}</p>
                  </div>
                </>
              )}
            </div>

            <div className="charts-grid">
              <div className="chart-container">
                <h3>État des Services</h3>
                <div className="services-status">
                  {health && health.services && Object.entries(health.services).map(([service, status]) => (
                    <div key={service} className={`service-status ${getServiceStatus(service)}`}>
                      <span className={`status-indicator ${getServiceStatus(service)}`}></span>
                      <span className="service-name">{service}</span>
                      <span className="service-status-text">
                        {status === 'healthy' ? '✓ En ligne' : `✗ ${status}`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'comparisons' && (
          <div className="comparisons-view">
            <h2>Comparaisons DCM4CHEE vs Orthanc</h2>
            <div className="comparisons-list">
              {comparisons.map(comp => (
                <div key={comp.id} className="comparison-card">
                  <div className="comparison-header">
                    <span className="study-id">Étude: {comp.study_id.substring(0, 8)}...</span>
                    <span className={`sync-status ${comp.sync_status}`}>{comp.sync_status}</span>
                  </div>
                  <div className="comparison-content">
                    <div className="pacs-comparison">
                      <div className="pacs-column">
                        <h4>DCM4CHEE</h4>
                        <div className="metric">
                          <span>Images:</span>
                          <strong>{comp.dcm4chee_images}</strong>
                        </div>
                        <div className="metric">
                          <span>Temps réponse:</span>
                          <strong>{comp.dcm4chee_response_time?.toFixed(2)}s</strong>
                        </div>
                        <div className="metric">
                          <span>Statut:</span>
                          <strong>{comp.dcm4chee_success ? '✓ Succès' : '✗ Erreur'}</strong>
                        </div>
                      </div>
                      <div className="vs-separator">VS</div>
                      <div className="pacs-column">
                        <h4>Orthanc</h4>
                        <div className="metric">
                          <span>Images:</span>
                          <strong>{comp.orthanc_images}</strong>
                        </div>
                        <div className="metric">
                          <span>Temps réponse:</span>
                          <strong>{comp.orthanc_response_time?.toFixed(2)}s</strong>
                        </div>
                        <div className="metric">
                          <span>Statut:</span>
                          <strong>{comp.orthanc_success ? '✓ Succès' : '✗ Erreur'}</strong>
                        </div>
                      </div>
                    </div>
                    {comp.differences && Object.keys(comp.differences).length > 0 && (
                      <div className="differences">
                        <h5>Différences détectées :</h5>
                        {Object.entries(comp.differences).map(([key, value]) => (
                          <div key={key} className="difference-item">
                            <span>{key} :</span>
                            {typeof value === 'object' && value !== null && ('dcm4chee' in value && 'orthanc' in value) ? (
                              <span>
                                <strong>DCM4CHEE:</strong> {Array.isArray(value.dcm4chee) ? value.dcm4chee.join(', ') : String(value.dcm4chee)}<br />
                                <strong>Orthanc:</strong> {Array.isArray(value.orthanc) ? value.orthanc.join(', ') : String(value.orthanc)}
                              </span>
                            ) : (
                              <strong>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</strong>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {comparisons.length === 0 && (
                <div className="empty-state">
                  <p>Aucune comparaison disponible. Lancez d'abord une synchronisation.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'services' && (
          <div className="services-view">
            <h2>État Détaillé des Services</h2>
            <div className="services-grid">
              <ServiceCard
                name="DCM4CHEE"
                port="8080"
                url={import.meta.env.VITE_DCM4CHEE_URL}
                status={getServiceStatus('dcm4chee')}
                description="Archive DICOM professionnelle complète"
              />
              <ServiceCard
                name="Orthanc"
                port="8042"
                url={import.meta.env.VITE_ORTHANC_URL}
                status={getServiceStatus('orthanc')}
                description="Serveur PACS léger et performant"
              />
              <ServiceCard
                name="XNAT"
                port="8090"
                url={import.meta.env.VITE_XNAT_URL}
                status={getServiceStatus('xnat')}
                description="Plateforme d'anonymisation"
              />
              <ServiceCard
                name="PostgreSQL"
                port="5432"
                status={getServiceStatus('postgres')}
                description="Base de données centralisée"
              />
              <ServiceCard
                name="Backend API"
                port="8000"
                url={import.meta.env.VITE_API_URL}
                status={health?.status === 'healthy' ? 'success' : 'error'}
                description="Orchestrateur FastAPI"
              />
              <ServiceCard
                name="OHIF Viewer"
                port="5173"
                description="Visualiseur DICOM professionnel"
                status="success"
              />
            </div>
          </div>
        )}

        {activeTab === 'documentation' && (
          <div className="documentation">
            <h2>Documentation du Système</h2>
            <div className="doc-sections">
              <section>
                <h3>Accès aux Services</h3>
                <ul>
                  <li><strong>DCM4CHEE:</strong> <code>http://localhost:8080</code></li>
                  <li><strong>Orthanc:</strong> <code>http://localhost:8042</code></li>
                  <li><strong>XNAT:</strong> <code>http://localhost:8090</code></li>
                  <li><strong>Backend API:</strong> <code>http://localhost:8000</code> (Documentation: <code>/docs</code>)</li>
                  <li><strong>OHIF Viewer:</strong> <code>http://localhost:5173</code></li>
                  <li><strong>Prometheus:</strong> <code>http://localhost:9090</code></li>
                  <li><strong>Grafana:</strong> <code>http://localhost:3001</code></li>
                </ul>
              </section>
              <section>
                <h3>Fonctionnalités Principales</h3>
                <ul>
                  <li>✓ Synchronisation automatique des patients et études</li>
                  <li>✓ Comparaison détaillée côte-à-côte entre DCM4CHEE et Orthanc</li>
                  <li>✓ Visualisation DICOM avec OHIF (segmentation, annotation, mesurements)</li>
                  <li>✓ Anonymisation automatique via XNAT</li>
                  <li>✓ Métriques de performance en temps réel</li>
                  <li>✓ Monitoring avec Prometheus/Grafana</li>
                </ul>
              </section>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function ServiceCard({ name, port, url, status, description }) {
  return (
    <div className={`service-card service-${status}`}>
      <h4>{name}</h4>
      <p className="service-description">{description}</p>
      <div className="service-details">
        <span className="port">Port: {port}</span>
        <a href={url || '#'} target="_blank" rel="noopener noreferrer" className="service-link">
          Accéder →
        </a>
      </div>
      <div className={`status-badge ${status}`}>
        {status === 'success' ? '✓ En ligne' : status === 'error' ? '✗ Hors ligne' : '⚠ Indéfini'}
      </div>
    </div>
  )
}

export default App
