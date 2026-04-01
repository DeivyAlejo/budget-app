import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import ExpenseChart from '../components/ExpenseChart'
import { formatDisplayDate } from '../utils/dateFormat'
import { getCategoryColor, withHexAlpha } from '../utils/categoryColors'
import type {
  Budget,
  BudgetCategoryAllocation,
  Category,
  CategoryDetail,
  CategoryTotal,
  Expense,
  PaymentMethod,
  User,
} from '../types/api'

const now = new Date()
const currencyFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

export default function DashboardPage() {
  const queryClient = useQueryClient()
  const { logout } = useAuth()

  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null)

  const [budgetAmount, setBudgetAmount] = useState('')
  const [copyPrevious, setCopyPrevious] = useState(false)

  const [newCategoryName, setNewCategoryName] = useState('')
  const [newPaymentMethodName, setNewPaymentMethodName] = useState('')

  const [allocationInputs, setAllocationInputs] = useState<Record<number, string>>({})
  const [isBudgetSectionExpanded, setIsBudgetSectionExpanded] = useState(false)
  const [isCategorySectionExpanded, setIsCategorySectionExpanded] = useState(false)
  const [isPaymentMethodSectionExpanded, setIsPaymentMethodSectionExpanded] = useState(false)

  const [editingExpenseId, setEditingExpenseId] = useState<number | null>(null)
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [spentAt, setSpentAt] = useState(new Date().toISOString().slice(0, 10))
  const [categoryId, setCategoryId] = useState<number | null>(null)
  const [paymentMethodId, setPaymentMethodId] = useState<number | null>(null)
  const [expenseFormError, setExpenseFormError] = useState('')

  const addExpenseCardRef = useRef<HTMLElement | null>(null)

  const meQuery = useQuery({
    queryKey: ['me'],
    queryFn: async () => (await apiClient.get<User>('/auth/me')).data,
  })

  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: async () => (await apiClient.get<Category[]>('/categories')).data,
  })

  const methodsQuery = useQuery({
    queryKey: ['payment-methods'],
    queryFn: async () => (await apiClient.get<PaymentMethod[]>('/payment-methods')).data,
  })

  const budgetsQuery = useQuery({
    queryKey: ['budgets', year],
    queryFn: async () => (await apiClient.get<Budget[]>(`/budgets?year=${year}`)).data,
  })

  const expensesQuery = useQuery({
    queryKey: ['expenses', year, month],
    queryFn: async () => (await apiClient.get<Expense[]>(`/expenses?year=${year}&month=${month}`)).data,
  })

  const totalsQuery = useQuery({
    queryKey: ['totals', year, month],
    queryFn: async () => (await apiClient.get<CategoryTotal[]>(`/reports/categories/totals?year=${year}&month=${month}`)).data,
  })

  const detailQuery = useQuery({
    queryKey: ['detail', selectedCategoryId, year, month],
    queryFn: async () =>
      selectedCategoryId
        ? (await apiClient.get<CategoryDetail>(`/reports/categories/${selectedCategoryId}?year=${year}&month=${month}`)).data
        : null,
    enabled: selectedCategoryId !== null,
  })

  const selectedBudget = useMemo(
    () => budgetsQuery.data?.find((b) => b.year === year && b.month === month) ?? null,
    [budgetsQuery.data, year, month],
  )

  const allocationsQuery = useQuery({
    queryKey: ['budget-allocations', selectedBudget?.id],
    queryFn: async () =>
      selectedBudget
        ? (await apiClient.get<BudgetCategoryAllocation[]>(`/budgets/${selectedBudget.id}/allocations`)).data
        : [],
    enabled: selectedBudget !== null,
  })

  useEffect(() => {
    const next: Record<number, string> = {}
    for (const item of allocationsQuery.data ?? []) {
      next[item.category_id] = item.allocated_amount
    }
    setAllocationInputs(next)
  }, [allocationsQuery.data, selectedBudget?.id])

  const refreshAll = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['categories'] }),
      queryClient.invalidateQueries({ queryKey: ['payment-methods'] }),
      queryClient.invalidateQueries({ queryKey: ['budgets'] }),
      queryClient.invalidateQueries({ queryKey: ['budget-allocations'] }),
      queryClient.invalidateQueries({ queryKey: ['expenses'] }),
      queryClient.invalidateQueries({ queryKey: ['totals'] }),
      queryClient.invalidateQueries({ queryKey: ['detail'] }),
    ])
  }

  const resetExpenseForm = () => {
    setEditingExpenseId(null)
    setDescription('')
    setAmount('')
    setSpentAt(new Date().toISOString().slice(0, 10))
    setCategoryId(null)
    setPaymentMethodId(null)
    setExpenseFormError('')
  }

  const createBudget = useMutation({
    mutationFn: async () =>
      apiClient.post('/budgets', {
        year,
        month,
        planned_amount: budgetAmount ? Number(budgetAmount) : null,
        copy_previous_month: copyPrevious,
      }),
    onSuccess: refreshAll,
  })

  const saveAllocations = useMutation({
    mutationFn: async () => {
      if (!selectedBudget) {
        throw new Error('Create monthly budget first')
      }
      const allocations = Object.entries(allocationInputs)
        .filter(([, value]) => value.trim() !== '')
        .map(([key, value]) => ({
          category_id: Number(key),
          allocated_amount: Number(value),
        }))
      return apiClient.put(`/budgets/${selectedBudget.id}/allocations`, { allocations })
    },
    onSuccess: refreshAll,
  })

  const createCategory = useMutation({
    mutationFn: async () => apiClient.post('/categories', { name: newCategoryName.trim() }),
    onSuccess: async () => {
      setNewCategoryName('')
      await queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
  })

  const deleteCategory = useMutation({
    mutationFn: async (id: number) => apiClient.delete(`/categories/${id}`),
    onSuccess: refreshAll,
  })

  const createPaymentMethod = useMutation({
    mutationFn: async () => apiClient.post('/payment-methods', { name: newPaymentMethodName.trim() }),
    onSuccess: async () => {
      setNewPaymentMethodName('')
      await queryClient.invalidateQueries({ queryKey: ['payment-methods'] })
    },
  })

  const deleteExpense = useMutation({
    mutationFn: async (id: number) => apiClient.delete(`/expenses/${id}`),
    onSuccess: refreshAll,
  })

  const deletePaymentMethod = useMutation({
    mutationFn: async (id: number) => apiClient.delete(`/payment-methods/${id}`),
    onSuccess: refreshAll,
  })

  const saveExpense = useMutation({
    mutationFn: async () => {
      if (!categoryId || !paymentMethodId) {
        throw new Error('Please select category and payment method')
      }
      if (!description.trim()) {
        throw new Error('Description is required')
      }
      if (!amount || Number(amount) <= 0) {
        throw new Error('Amount must be greater than 0')
      }

      const payload = {
        category_id: categoryId,
        payment_method_id: paymentMethodId,
        description: description.trim(),
        amount: Number(amount),
        spent_at: spentAt,
      }

      if (editingExpenseId) {
        return apiClient.put(`/expenses/${editingExpenseId}`, payload)
      }

      return apiClient.post('/expenses', payload)
    },
    onSuccess: async () => {
      resetExpenseForm()
      await refreshAll()
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : 'Could not save expense'
      setExpenseFormError(message)
    },
  })

  const categories = categoriesQuery.data ?? []

  const categoryNameById = useMemo(() => {
    const map = new Map<number, string>()
    for (const category of categories) {
      map.set(category.id, category.name)
    }
    return map
  }, [categories])

  const selectedBudgetValue = Number(selectedBudget?.planned_amount ?? 0)
  const monthlySpentValue = useMemo(
    () => (expensesQuery.data ?? []).reduce((sum, item) => sum + Number(item.amount), 0),
    [expensesQuery.data],
  )

  const startEditingExpense = (expense: Expense) => {
    setEditingExpenseId(expense.id)
    setDescription(expense.description)
    setAmount(expense.amount)
    setSpentAt(expense.spent_at)
    setCategoryId(expense.category_id)
    setPaymentMethodId(expense.payment_method_id)
    setExpenseFormError('')

    addExpenseCardRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    })
  }

  return (
    <main className="page dashboard-page">
      <header className="toolbar card">
        <h1>Budget Dashboard</h1>
        <div className="toolbar-actions">
          <label>
            Year
            <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} />
          </label>
          <label>
            Month
            <input type="number" min={1} max={12} value={month} onChange={(e) => setMonth(Number(e.target.value))} />
          </label>
          {meQuery.data?.is_admin && <Link className="button-link" to="/admin">Admin Panel</Link>}
          <button onClick={() => logout()}>Log out</button>
        </div>
      </header>


      <section className="card monthly-summary-card">
        <h2>Month Snapshot</h2>
        <div className="monthly-summary-grid">
          <div className="monthly-summary-item">
            <span className="monthly-summary-label">Total Budget</span>
            <strong>{currencyFormatter.format(selectedBudgetValue)}</strong>
          </div>
          <div className="monthly-summary-item">
            <span className="monthly-summary-label">Spent So Far</span>
            <strong>{currencyFormatter.format(monthlySpentValue)}</strong>
          </div>
        </div>
      </section>

      <section className="grid two">
        <article className="card" ref={addExpenseCardRef}>
          <h2>{editingExpenseId ? 'Edit Expense' : 'Add Expense'}</h2>
          <div className="form-grid">
            <select value={categoryId ?? ''} onChange={(e) => setCategoryId(Number(e.target.value))}>
              <option value="">Category</option>
              {categoriesQuery.data?.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <select value={paymentMethodId ?? ''} onChange={(e) => setPaymentMethodId(Number(e.target.value))}>
              <option value="">Payment method</option>
              {methodsQuery.data?.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <input placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
            <input placeholder="Amount" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
            <input type="date" value={spentAt} onChange={(e) => setSpentAt(e.target.value)} />
            {expenseFormError && <p className="error">{expenseFormError}</p>}
            <div className="actions-row">
              <button onClick={() => saveExpense.mutate()} disabled={saveExpense.isPending}>
                {editingExpenseId ? 'Update expense' : 'Add expense'}
              </button>
              {editingExpenseId && (
                <button className="secondary" onClick={resetExpenseForm} type="button">
                  Cancel edit
                </button>
              )}
            </div>
          </div>
        </article>

        <article className="card">
          <h2>Expenses Chart</h2>
          <ExpenseChart expenses={expensesQuery.data ?? []} categories={categories} size="compact" />
        </article>
      </section>

      <section className="grid two">
        <article className="card">
          <h2>Category Totals</h2>
          <ul className="list category-totals-list">
            {totalsQuery.data?.map((item) => {
              const categoryColor = getCategoryColor(item.category_id, categories)
              return (
                <li
                  key={item.category_id}
                  style={{
                    backgroundColor: withHexAlpha(categoryColor, '24'),
                    borderRadius: '10px',
                    padding: '0.55rem 0.7rem',
                  }}
                  onClick={() => setSelectedCategoryId(item.category_id)}
                >
                  <button className="link-button category-total-name" type="button">
                    {item.category_name}
                  </button>
                  <span className="category-total-value">{currencyFormatter.format(Number(item.total_amount))}</span>
                </li>
              )
            })}
          </ul>
          <p className="muted spaced-top">Click category rows to open detail panel.</p>
        </article>

        <article className="card">
          <h2>Expenses Table</h2>
          <ul className="list expense-list">
            {expensesQuery.data?.map((item) => {
              const categoryName = categoryNameById.get(item.category_id) ?? 'Unknown'
              const categoryColor = getCategoryColor(item.category_id, categories)

              return (
                <li
                  key={item.id}
                  style={{
                    backgroundColor: withHexAlpha(categoryColor, '17'),
                    borderRadius: '10px',
                    padding: '0.55rem 0.7rem',
                  }}
                >
                  <span className="expense-date">{formatDisplayDate(item.spent_at)}</span>
                  <strong className="expense-category" style={{ color: categoryColor }}>
                    {categoryName}
                  </strong>
                  <span className="expense-description">{item.description}</span>
                  <span className="expense-amount">{currencyFormatter.format(Number(item.amount))}</span>
                  <button type="button" onClick={() => startEditingExpense(item)}>
                    Edit
                  </button>
                  <button type="button" className="delete" onClick={() => deleteExpense.mutate(item.id)}>
                    Delete
                  </button>
                </li>
              )
            })}
          </ul>
        </article>
      </section>

      {selectedCategoryId && detailQuery.data && (
        <section className="card">
          <h2>{detailQuery.data.category_name} Details</h2>
          <p>
            Total: <strong>{currencyFormatter.format(Number(detailQuery.data.total_amount))}</strong>
          </p>
          <ul className="list">
            {detailQuery.data.expenses.map((item) => (
              <li key={item.expense_id}>
                <span>{formatDisplayDate(item.spent_at)}</span>
                <span>{item.description}</span>
                <span>{currencyFormatter.format(Number(item.amount))}</span>
              </li>
            ))}
          </ul>
          <button className="secondary" onClick={() => setSelectedCategoryId(null)}>
            Close
          </button>
        </section>
      )}

      <section className="grid two">
        <article className="card">
          <div className="section-header">
            <h2>Monthly Budget</h2>
            <button
              className="collapse-toggle"
              onClick={() => setIsBudgetSectionExpanded(!isBudgetSectionExpanded)}
              type="button"
              title={isBudgetSectionExpanded ? 'Collapse' : 'Expand'}
            >
              {isBudgetSectionExpanded ? '-' : '+'}
            </button>
          </div>
          {isBudgetSectionExpanded && (
            <>
              <p className="muted">Selected: {year}-{String(month).padStart(2, '0')}</p>
              <div className="form-grid">
                <input
                  type="number"
                  placeholder="Planned amount"
                  value={budgetAmount}
                  onChange={(e) => setBudgetAmount(e.target.value)}
                />
                <label className="inline">
                  <input
                    type="checkbox"
                    checked={copyPrevious}
                    onChange={(e) => setCopyPrevious(e.target.checked)}
                  />
                  Copy allocations from previous month
                </label>
                <button onClick={() => createBudget.mutate()} disabled={createBudget.isPending}>
                  Create / Update monthly budget
                </button>
              </div>

              <hr className="separator" />

              <h3>Category Allocations</h3>
              <div className="form-grid">
                {categoriesQuery.data?.map((item) => (
                  <label key={item.id}>
                    {item.name}
                    <input
                      type="number"
                      placeholder="0"
                      value={allocationInputs[item.id] ?? ''}
                      onChange={(e) =>
                        setAllocationInputs((prev) => ({
                          ...prev,
                          [item.id]: e.target.value,
                        }))
                      }
                    />
                  </label>
                ))}
                <button onClick={() => saveAllocations.mutate()} disabled={saveAllocations.isPending}>
                  Save allocations
                </button>
              </div>
            </>
          )}
        </article>

        <article className="card">
          <div className="section-header">
            <h2>Categories</h2>
            <button
              className="collapse-toggle"
              onClick={() => setIsCategorySectionExpanded(!isCategorySectionExpanded)}
              type="button"
              title={isCategorySectionExpanded ? 'Collapse' : 'Expand'}
            >
              {isCategorySectionExpanded ? '-' : '+'}
            </button>
          </div>
          {isCategorySectionExpanded && (
            <>
              <div className="actions-row">
                <input
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  placeholder="New category"
                />
                <button onClick={() => createCategory.mutate()} disabled={createCategory.isPending || !newCategoryName.trim()}>
                  Add
                </button>
              </div>
              <ul className="list spaced-top">
                {categoriesQuery.data?.map((item) => (
                  <li key={item.id}>
                    <span>{item.name}</span>
                    <button
                      type="button"
                      className="delete"
                      onClick={() => deleteCategory.mutate(item.id)}
                      disabled={deleteCategory.isPending}
                    >
                      Delete
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </article>
      </section>

      <section className="card">
        <div className="section-header">
          <h2>Payment Methods</h2>
          <button
            className="collapse-toggle"
            onClick={() => setIsPaymentMethodSectionExpanded(!isPaymentMethodSectionExpanded)}
            type="button"
            title={isPaymentMethodSectionExpanded ? 'Collapse' : 'Expand'}
          >
            {isPaymentMethodSectionExpanded ? '-' : '+'}
          </button>
        </div>
        {isPaymentMethodSectionExpanded && (
          <>
            <div className="actions-row">
              <input
                value={newPaymentMethodName}
                onChange={(e) => setNewPaymentMethodName(e.target.value)}
                placeholder="New payment method"
              />
              <button
                onClick={() => createPaymentMethod.mutate()}
                disabled={createPaymentMethod.isPending || !newPaymentMethodName.trim()}
              >
                Add
              </button>
            </div>
            <ul className="list spaced-top">
              {methodsQuery.data?.map((item) => (
                <li key={item.id}>
                  <span>{item.name}</span>
                  <button
                    type="button"
                    className="delete"
                    onClick={() => deletePaymentMethod.mutate(item.id)}
                    disabled={deletePaymentMethod.isPending}
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </main>
  )
}
