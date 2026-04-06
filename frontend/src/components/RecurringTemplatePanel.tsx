import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import type {
  RecurringTemplate,
  RecurringTemplateCreate,
  Category,
  PaymentMethod,
  GenerationSummary,
} from '../types/api'

interface RecurringTemplatePanelProps {
  year: number
  month: number
  categories: Category[]
  paymentMethods: PaymentMethod[]
  onGenerationSuccess?: () => void
}

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

export default function RecurringTemplatePanel({
  year,
  month,
  categories,
  paymentMethods,
  onGenerationSuccess,
}: RecurringTemplatePanelProps) {
  const [showForm, setShowForm] = useState(false)
  const [generationLoading, setGenerationLoading] = useState(false)
  const [generationMessage, setGenerationMessage] = useState('')

  const [formData, setFormData] = useState<RecurringTemplateCreate>({
    category_id: categories[0]?.id || 0,
    payment_method_id: paymentMethods[0]?.id || 0,
    description: '',
    amount: '',
    day_of_month: 1,
    frequency: 'monthly',
    is_active: true,
  })

  // Fetch recurring templates
  const templatesQuery = useQuery({
    queryKey: ['recurring-templates'],
    queryFn: async () =>
      (await apiClient.get<RecurringTemplate[]>('/recurring-expenses')).data,
  })

  // Create template mutation
  const createMutation = useMutation({
    mutationFn: async (data: RecurringTemplateCreate) =>
      (await apiClient.post<RecurringTemplate>('/recurring-expenses', data)).data,
    onSuccess: () => {
      templatesQuery.refetch()
      setShowForm(false)
      setFormData({
        category_id: categories[0]?.id || 0,
        payment_method_id: paymentMethods[0]?.id || 0,
        description: '',
        amount: '',
        day_of_month: 1,
        frequency: 'monthly',
        is_active: true,
      })
    },
  })

  // Generate recurring expenses
  const handleGenerateAll = async () => {
    setGenerationLoading(true)
    setGenerationMessage('')
    try {
      const response = await apiClient.post<GenerationSummary[]>(
        `/recurring-expenses/batch/generate?year=${year}&month=${month}`
      )
      const summaries = response.data
      const totalCreated = summaries.reduce((sum, s) => sum + s.created_count, 0)
      const totalAmount = summaries
        .reduce((sum, s) => sum + parseFloat(s.total_amount), 0)
        .toFixed(2)

      setGenerationMessage(
        `Generated ${totalCreated} expense(s) totaling ${currencyFormatter.format(parseFloat(totalAmount))}`
      )
      templatesQuery.refetch()
      onGenerationSuccess?.()

      // Clear message after 3 seconds
      setTimeout(() => setGenerationMessage(''), 3000)
    } catch (err) {
      setGenerationMessage('Failed to generate recurring expenses')
    } finally {
      setGenerationLoading(false)
    }
  }

  // Toggle template active status
  const toggleMutation = useMutation({
    mutationFn: async (template: RecurringTemplate) =>
      (
        await apiClient.put(`/recurring-expenses/${template.id}`, {
          is_active: !template.is_active,
        })
      ).data,
    onSuccess: () => {
      templatesQuery.refetch()
    },
  })

  // Delete template
  const deleteMutation = useMutation({
    mutationFn: async (templateId: number) =>
      await apiClient.delete(`/recurring-expenses/${templateId}`),
    onSuccess: () => {
      templatesQuery.refetch()
    },
  })

  const isGenerated = (template: RecurringTemplate) =>
    template.last_generated_year === year &&
    template.last_generated_month === month

  const getCategoryName = (id: number) =>
    categories.find((c) => c.id === id)?.name || `Category ${id}`

  const getMethodName = (id: number) =>
    paymentMethods.find((m) => m.id === id)?.name || `Method ${id}`

  return (
    <div className="mt-6 p-4 border border-gray-300 rounded">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Recurring Expenses</h3>
        <button
          onClick={handleGenerateAll}
          disabled={generationLoading || !templatesQuery.data?.length}
          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
        >
          {generationLoading ? 'Generating...' : 'Generate for This Month'}
        </button>
      </div>

      {generationMessage && (
        <div className="mb-4 p-2 bg-blue-100 text-blue-700 rounded">
          {generationMessage}
        </div>
      )}

      {/* List of templates */}
      {templatesQuery.data && templatesQuery.data.length > 0 && (
        <div className="mb-4 space-y-2">
          {templatesQuery.data.map((template) => (
            <div
              key={template.id}
              className="p-3 border border-gray-200 rounded flex justify-between items-start"
            >
              <div className="flex-1">
                <div className="font-semibold">{template.description}</div>
                <div className="text-sm text-gray-600">
                  {getCategoryName(template.category_id)} • {getMethodName(template.payment_method_id)} •
                  Day {template.day_of_month}
                </div>
                <div className="text-sm font-mono">
                  {currencyFormatter.format(parseFloat(template.amount))}
                </div>
                <div
                  className={`text-xs mt-1 ${
                    isGenerated(template) ? 'text-green-600' : 'text-orange-600'
                  }`}
                >
                  {isGenerated(template)
                    ? '✓ Generated this month'
                    : '○ Pending'}
                </div>
              </div>
              <div className="ml-3 space-y-1">
                <button
                  onClick={() => toggleMutation.mutate(template)}
                  className={`block px-2 py-1 text-sm rounded ${
                    template.is_active
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {template.is_active ? 'Active' : 'Off'}
                </button>
                <button
                  onClick={() => deleteMutation.mutate(template.id)}
                  className="block px-2 py-1 text-sm bg-red-100 text-red-700 rounded"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create new template form */}
      {showForm && (
        <div className="p-3 border border-blue-300 bg-blue-50 rounded">
          <h4 className="font-semibold mb-3">New Recurring Template</h4>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <input
              type="text"
              placeholder="Description"
              value={formData.description}
              onChange={(e) =>
                setFormData({...formData, description: e.target.value})
              }
              className="col-span-2 border rounded px-2 py-1"
            />
            <select
              value={formData.category_id}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  category_id: parseInt(e.target.value),
                })
              }
              className="border rounded px-2 py-1"
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <select
              value={formData.payment_method_id}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  payment_method_id: parseInt(e.target.value),
                })
              }
              className="border rounded px-2 py-1"
            >
              {paymentMethods.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
            <input
              type="number"
              placeholder="Amount"
              value={formData.amount}
              onChange={(e) =>
                setFormData({...formData, amount: e.target.value})
              }
              className="border rounded px-2 py-1"
            />
            <input
              type="number"
              min="1"
              max="31"
              placeholder="Day of month"
              value={formData.day_of_month}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  day_of_month: parseInt(e.target.value),
                })
              }
              className="border rounded px-2 py-1"
            />
            <textarea
              placeholder="Notes (optional)"
              value={formData.notes || ''}
              onChange={(e) =>
                setFormData({...formData, notes: e.target.value})
              }
              className="col-span-2 border rounded px-2 py-1"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => createMutation.mutate(formData)}
              disabled={
                createMutation.isPending ||
                !formData.description ||
                !formData.amount
              }
              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {createMutation.isPending ? 'Creating...' : 'Create'}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {!showForm && (
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          + New Template
        </button>
      )}
    </div>
  )
}
