import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import type { RemindersResponse } from '../types/api'

interface ReminderCardsPanelProps {
  year: number
  month: number
}

export default function ReminderCardsPanel({ year, month }: ReminderCardsPanelProps) {
  const remindersQuery = useQuery({
    queryKey: ['reminders', year, month],
    queryFn: async () =>
      (
        await apiClient.get<RemindersResponse>(
          `/reminders?year=${year}&month=${month}`
        )
      ).data,
  })

  if (!remindersQuery.data?.cards.length) {
    return null
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'alert':
        return 'bg-red-100 border-red-300 text-red-800'
      case 'warning':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800'
      case 'info':
      default:
        return 'bg-blue-100 border-blue-300 text-blue-800'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'alert':
        return '⚠️'
      case 'warning':
        return '⚡'
      case 'info':
      default:
        return 'ℹ️'
    }
  }

  return (
    <div className="mt-4 space-y-2">
      {remindersQuery.data.cards.map((card, idx) => (
        <div
          key={idx}
          className={`p-3 border rounded ${getSeverityColor(
            card.severity
          )}`}
        >
          <div className="flex items-start gap-2">
            <span className="text-lg">{getSeverityIcon(card.severity)}</span>
            <div className="flex-1">
              <div className="font-semibold">{card.title}</div>
              <div className="text-sm mt-1">{card.message}</div>
              {card.action_url && (
                <a
                  href={card.action_url}
                  className="text-sm underline mt-2 inline-block"
                >
                  View →
                </a>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
