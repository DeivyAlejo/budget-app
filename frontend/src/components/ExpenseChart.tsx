import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

import type { Category, Expense } from '../types/api'
import { getCategoryColor } from '../utils/categoryColors'

type ExpenseChartProps = {
  expenses: Expense[]
  categories: Category[]
  size?: 'default' | 'compact'
}

type PieLabelProps = {
  name?: string
  percent?: number
}

function renderPieLabel({ name, percent }: PieLabelProps) {
  if (!name) {
    return ''
  }

  const ratio = typeof percent === 'number' ? Math.round(percent * 100) : 0
  return `${name} (${ratio}%)`
}

export default function ExpenseChart({ expenses, categories, size = 'default' }: ExpenseChartProps) {
  const categoryMap = new Map<number, string>()
  for (const category of categories) {
    categoryMap.set(category.id, category.name)
  }

  const data = expenses.reduce(
    (acc, expense) => {
      const amount = Number(expense.amount)
      const existing = acc.find((item) => item.categoryId === expense.category_id)
      if (existing) {
        existing.value += amount
      } else {
        acc.push({
          categoryId: expense.category_id,
          name: categoryMap.get(expense.category_id) ?? `Category ${expense.category_id}`,
          value: amount,
        })
      }
      return acc
    },
    [] as Array<{ categoryId: number; name: string; value: number }>,
  )

  if (data.length === 0) {
    return <p className="muted">No expenses to display yet.</p>
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
              <Cell
                key={`${item.categoryId}-${index}`}
                fill={getCategoryColor(item.categoryId, categories)}
              />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `$${Number(value).toFixed(2)}`} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
