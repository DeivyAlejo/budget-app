export type TokenResponse = {
  access_token: string
  token_type: string
}

export type User = {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
}

export type Category = {
  id: number
  name: string
  is_default: boolean
  created_at: string
}

export type PaymentMethod = {
  id: number
  name: string
  is_default: boolean
  created_at: string
}

export type Budget = {
  id: number
  year: number
  month: number
  planned_amount: string
  copied_from_budget_id: number | null
  created_at: string
  updated_at: string
}

export type BudgetCategoryAllocation = {
  category_id: number
  category_name: string
  allocated_amount: string
}

export type Expense = {
  id: number
  category_id: number
  payment_method_id: number
  description: string
  amount: string
  spent_at: string
  created_at: string
}

export type CategoryTotal = {
  category_id: number
  category_name: string
  total_amount: string
}

export type CategoryDetail = {
  category_id: number
  category_name: string
  total_amount: string
  expenses: Array<{
    expense_id: number
    description: string
    amount: string
    spent_at: string
  }>
}
