import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

import type { Income } from '../types/api'

type IncomeChartProps = {
  income: Income[]
  size?: 'default' | 'compact'
}

type PieLabelProps = {
  name?: string
  percent?: number
}

const incomeTypeColors: Record<string, string> = {
  salary: '#3b82f6',
  freelance: '#8b5cf6',
  bonus: '#ec4899',
  other: '#6b7280',
}

function getIncomeTypeColor(type: string): string {
  return incomeTypeColors[type.toLowerCase()] || '#9ca3af'
}

function renderPieLabel({ name, percent }: PieLabelProps) {
  if (!name) return ''
  const ratio = typeof percent === 'number' ? Math.round(percent * 100) : 0
  return `${name} (${ratio}%)`
}

export default function IncomeChart({ income, size = 'default' }: IncomeChartProps) {
  const data = income.reduce(
    (acc, item) => {
      const amount = Number(item.amount)
      const existing = acc.find((i) => i.type === item.income_type)
      if (existing) {
        existing.value += amount
      } else {
        acc.push({
          type: item.income_type,
          name: item.income_type.charAt(0).toUpperCase() + item.income_type.slice(1),
          value: amount,
        })
      }
      return acc
    },
    [] as Array<{ type: string; name: string; value: number }>,
  )

  if (data.length === 0) {
    return <p className="muted">No income to display yet.</p>
  }

  const sortedData = [...data].sort((a, b) => b.value - a.value)
  const isCompact = size === 'compact'
  const chartHeight = isCompact ? 300 : 360
  const innerRadius = isCompact ? 58 : 72
  const outerRadius = isCompact ? 84 : 108

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={chartHeight}>
        <PieChart margin={{ top: 16, right: 36, bottom: 16, left: 36 }}>
          <Pie
            data={sortedData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={2}
            minAngle={3}
            labelLine
            label={renderPieLabel}
          >
            {sortedData.map((item, index) => (
              <Cell key={`${item.type}-${index}`} fill={getIncomeTypeColor(item.type)} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `$${Number(value).toFixed(2)}`} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
