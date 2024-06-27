import { formatDate } from '../utils/format'

interface Day {
  date: string
  count: number
}

const CHART_HEIGHT = 140

function shortDate(date: string) {
  return formatDate(`${date}T12:00:00`).replace(/,? \d{4}$/, '')
}

export default function DailyColumns({ days }: { days: Day[] }) {
  const max = Math.max(...days.map((day) => day.count), 1)
  const peak = days.reduce((best, day) => (day.count > best.count ? day : best), days[0])
  const labelled = new Set([days[0]?.date, days[days.length - 1]?.date])

  return (
    <figure>
      <div className="relative flex items-end gap-0.5 border-b border-slate-200" style={{ height: CHART_HEIGHT }}>
        {days.map((day) => {
          const height = day.count ? Math.max((day.count / max) * (CHART_HEIGHT - 20), 3) : 0
          return (
            <div key={day.date} className="group relative flex h-full flex-1 flex-col items-center justify-end">
              {day === peak && day.count > 0 && (
                <span className="mb-1 text-xs tabular-nums text-slate-600">{day.count}</span>
              )}
              <div className="w-full max-w-[24px] rounded-t bg-indigo-500" style={{ height }} />
              <div className="pointer-events-none absolute bottom-full z-10 mb-1 hidden whitespace-nowrap rounded bg-slate-900 px-2 py-1 text-xs text-white group-hover:block">
                {shortDate(day.date)}: {day.count} {day.count === 1 ? 'ticket' : 'tickets'}
              </div>
            </div>
          )
        })}
      </div>
      <div className="mt-1 flex gap-0.5 text-xs text-slate-500">
        {days.map((day) => (
          <span key={day.date} className="flex-1 text-center">
            {labelled.has(day.date) ? shortDate(day.date) : ''}
          </span>
        ))}
      </div>
      <table className="sr-only">
        <caption>Tickets created per day</caption>
        <tbody>
          {days.map((day) => (
            <tr key={day.date}>
              <th scope="row">{day.date}</th>
              <td>{day.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  )
}
