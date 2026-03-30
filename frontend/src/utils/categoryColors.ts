import type { Category } from '../types/api'

const CATEGORY_COLORS = [
  '#3b82f6',
  '#ef4444',
  '#10b981',
  '#f59e0b',
  '#8b5cf6',
  '#ec4899',
  '#06b6d4',
  '#6366f1',
  '#f97316',
  '#14b8a6',
] as const

export function getCategoryColor(categoryId: number, categories: Category[]): string {
  const index = categories.findIndex((category) => category.id === categoryId)
  if (index >= 0) {
    return CATEGORY_COLORS[index % CATEGORY_COLORS.length]
  }

  return CATEGORY_COLORS[Math.abs(categoryId) % CATEGORY_COLORS.length]
}

export function withHexAlpha(color: string, alphaHex: string): string {
  return `${color}${alphaHex}`
}
