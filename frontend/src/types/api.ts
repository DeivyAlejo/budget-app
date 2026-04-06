export type TokenResponse = {
  access_token: string
  token_type: string
}

export type User = {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export type PendingUser = {
  id: number
  email: string
  full_name: string | null
  created_at: string
}

export type InviteCode = {
  id: number
  code: string
  created_at: string
  used_at: string | null
  used_by_user_id: number | null
}

export type InviteCodeCreateResponse = {
  codes: string[]
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
  is_recurring: boolean
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

export type RecurringTemplate = {
  id: number
  category_id: number
  payment_method_id: number
  description: string
  amount: string
  day_of_month: number
  frequency: string
  is_active: boolean
  last_generated_year: number | null
  last_generated_month: number | null
  notes: string | null
  created_at: string
  updated_at: string
}

export type RecurringTemplateCreate = {
  category_id: number
  payment_method_id: number
  description: string
  amount: string
  day_of_month: number
  frequency?: string
  is_active?: boolean
  notes?: string | null
}

export type GenerationSummary = {
  template_id: number
  created_count: number
  total_amount: string
  month: number
  year: number
}

export type ReminderCard = {
  reminder_type: string
  title: string
  message: string
  severity: string
  action_url: string | null
}

export type RemindersResponse = {
  year: number
  month: number
  cards: ReminderCard[]
}
