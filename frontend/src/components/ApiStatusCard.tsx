import type { ApiStatus } from '../app/api-status'

const statusContent: Record<
  ApiStatus,
  { title: string; description: string }
> = {
  checking: {
    title: 'Comprobando API',
    description: 'Consultando el endpoint de salud del backend.',
  },
  available: {
    title: 'API disponible',
    description: 'El backend responde correctamente al contrato de salud.',
  },
  unavailable: {
    title: 'API no disponible',
    description:
      'No se pudo completar la comprobación. Revisa que el backend esté iniciado.',
  },
}

interface ApiStatusCardProps {
  status: ApiStatus
}

export function ApiStatusCard({ status }: ApiStatusCardProps) {
  const content = statusContent[status]

  return (
    <section
      className={`status-card status-card--${status}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <span className="status-card__indicator" aria-hidden="true" />
      <div>
        <p className="status-card__eyebrow">Estado de conexión</p>
        <h2 className="status-card__title">{content.title}</h2>
        <p className="status-card__description">{content.description}</p>
      </div>
    </section>
  )
}
