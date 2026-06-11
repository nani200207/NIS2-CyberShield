import React, { useState, useEffect } from 'react'
import { Plus, User, Calendar, CheckSquare, Trash2, ArrowRight, ShieldAlert } from 'lucide-react'

export default function RemediationBoard({ currentOrgId, gaps, API_BASE }) {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  
  // New task form fields
  const [newTask, setNewTask] = useState({
    gap_id: '',
    title: '',
    description: '',
    assignee: '',
    due_date: '',
    status: 'Open'
  })

  // Fetch tasks for the current organization
  const fetchTasks = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/tasks?org_id=${currentOrgId}`)
      if (res.ok) {
        const data = await res.json()
        setTasks(data)
      }
    } catch (err) {
      console.error("Failed to load tasks:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
    if (gaps && gaps.length > 0 && !newTask.gap_id) {
      setNewTask(prev => ({ ...prev, gap_id: gaps[0].article_id }))
    }
  }, [currentOrgId, gaps])

  // Handle task creation
  const handleCreateTask = async (e) => {
    e.preventDefault()
    if (!newTask.title.trim()) return

    try {
      const res = await fetch(`${API_BASE}/tasks?org_id=${currentOrgId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newTask,
          due_date: newTask.due_date ? new Date(newTask.due_date).toISOString() : null
        })
      })
      if (res.ok) {
        setShowAddForm(false)
        setNewTask({
          gap_id: gaps[0]?.article_id || '',
          title: '',
          description: '',
          assignee: '',
          due_date: '',
          status: 'Open'
        })
        fetchTasks()
      }
    } catch (err) {
      console.error("Error creating task:", err)
    }
  }

  // Handle task status transition
  const handleUpdateStatus = async (taskId, nextStatus) => {
    try {
      const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus })
      })
      if (res.ok) {
        fetchTasks()
      }
    } catch (err) {
      console.error("Error updating status:", err)
    }
  }

  // Handle task deletion
  const handleDeleteTask = async (taskId) => {
    if (!confirm("Are you sure you want to delete this remediation task?")) return
    try {
      const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        fetchTasks()
      }
    } catch (err) {
      console.error("Error deleting task:", err)
    }
  }

  // Helper to filter tasks by columns
  const getTasksByStatus = (status) => {
    return tasks.filter(t => t.status === status)
  }

  return (
    <div className="space-y-6">
      {/* Header Panel */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-gray-900 bg-opacity-40 border border-gray-800 rounded-2xl p-6 backdrop-blur-md">
        <div>
          <h2 className="text-2xl font-bold font-outfit text-white tracking-tight flex items-center space-x-2">
            <CheckSquare className="w-6 h-6 text-cyber-primary" />
            <span>NIS2 Remediation Tracker</span>
          </h2>
          <p className="text-gray-400 text-sm mt-1">Assign, track, and manage cybersecurity tasks across critical compliance gaps.</p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="mt-4 sm:mt-0 px-4 py-2 bg-gradient-to-r from-cyber-primary to-cyber-secondary hover:opacity-90 text-white rounded-xl text-sm font-medium shadow-lg transition-all flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Remediation Task</span>
        </button>
      </div>

      {/* Task Creation Modal Form Overlay */}
      {showAddForm && (
        <div className="bg-gray-900 border border-cyber-primary border-opacity-30 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-2 h-full bg-cyber-primary"></div>
          <h3 className="text-lg font-bold font-outfit text-white mb-4">Create Remediation Task</h3>
          
          <form onSubmit={handleCreateTask} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-gray-400 font-medium">Link to NIS2 Gap Requirement</label>
              <select
                value={newTask.gap_id}
                onChange={e => setNewTask(prev => ({ ...prev, gap_id: e.target.value }))}
                className="w-full bg-gray-950 border border-gray-800 rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-cyber-primary"
              >
                {gaps.map(g => (
                  <option key={g.article_id} value={g.article_id}>
                    {g.article_id} - {g.control_name} ({g.status})
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs text-gray-400 font-medium">Task Action Title</label>
              <input
                type="text"
                placeholder="e.g. Roll out FIDO2 security keys to IT Admins"
                value={newTask.title}
                onChange={e => setNewTask(prev => ({ ...prev, title: e.target.value }))}
                className="w-full bg-gray-950 border border-gray-800 rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-cyber-primary"
                required
              />
            </div>

            <div className="space-y-1 md:col-span-2">
              <label className="text-xs text-gray-400 font-medium">Detailed Instructions / Description</label>
              <textarea
                placeholder="Specific operational milestones required to close this NIS2 security gap..."
                value={newTask.description}
                onChange={e => setNewTask(prev => ({ ...prev, description: e.target.value }))}
                className="w-full bg-gray-950 border border-gray-800 rounded-xl px-3 py-2 text-sm text-gray-200 h-20 focus:outline-none focus:border-cyber-primary resize-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-gray-400 font-medium">Assignee Name</label>
              <input
                type="text"
                placeholder="e.g. Johan Andersson (SecOps)"
                value={newTask.assignee}
                onChange={e => setNewTask(prev => ({ ...prev, assignee: e.target.value }))}
                className="w-full bg-gray-950 border border-gray-800 rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-cyber-primary"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs text-gray-400 font-medium">Due Date Deadline</label>
              <input
                type="date"
                value={newTask.due_date}
                onChange={e => setNewTask(prev => ({ ...prev, due_date: e.target.value }))}
                className="w-full bg-gray-950 border border-gray-800 rounded-xl px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-cyber-primary"
              />
            </div>

            <div className="md:col-span-2 flex justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 border border-gray-800 rounded-xl hover:bg-gray-800 text-sm text-gray-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 bg-cyber-primary hover:bg-opacity-90 text-white font-medium rounded-xl text-sm shadow-md"
              >
                Save Task
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Kanban Board Layout */}
      {loading && tasks.length === 0 ? (
        <div className="flex justify-center py-20 text-cyber-primary">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-current"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Columns definition */}
          {[
            { id: 'Open', title: 'Open Backlog', color: 'border-cyber-rose text-cyber-rose' },
            { id: 'In Progress', title: 'In Progress', color: 'border-cyber-primary text-cyber-primary' },
            { id: 'Done', title: 'Resolved / Done', color: 'border-cyber-emerald text-cyber-emerald' }
          ].map(col => {
            const colTasks = getTasksByStatus(col.id)
            return (
              <div key={col.id} className="bg-gray-900 bg-opacity-40 border border-gray-850 rounded-2xl p-4 flex flex-col min-h-[500px]">
                {/* Column Title Header */}
                <div className={`border-b-2 ${col.color.split(' ')[0]} pb-3 mb-4 flex justify-between items-center`}>
                  <h3 className="font-bold font-outfit text-white tracking-tight flex items-center space-x-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${col.id === 'Open' ? 'bg-cyber-rose' : col.id === 'In Progress' ? 'bg-cyber-primary' : 'bg-cyber-emerald'}`}></span>
                    <span>{col.title}</span>
                  </h3>
                  <span className="bg-gray-950 border border-gray-850 text-gray-400 text-xs px-2 py-0.5 rounded-md font-semibold font-outfit">
                    {colTasks.length}
                  </span>
                </div>

                {/* Column Cards Lists */}
                <div className="space-y-4 flex-grow overflow-y-auto">
                  {colTasks.length === 0 ? (
                    <div className="h-40 border border-dashed border-gray-850 rounded-xl flex flex-col items-center justify-center text-center p-4">
                      <ShieldAlert className="w-6 h-6 text-gray-600 mb-2" />
                      <p className="text-xs text-gray-500">No tasks in this stage.</p>
                    </div>
                  ) : (
                    colTasks.map(task => {
                      const linkedGap = gaps.find(g => g.article_id === task.gap_id)
                      return (
                        <div key={task.id} className="bg-gray-950 border border-gray-850 hover:border-gray-700 rounded-xl p-4 transition-all relative overflow-hidden group">
                          {/* Task visual anchor bar */}
                          <div className={`absolute top-0 left-0 w-1 h-full ${col.id === 'Open' ? 'bg-cyber-rose' : col.id === 'In Progress' ? 'bg-cyber-primary' : 'bg-cyber-emerald'}`}></div>
                          
                          <div className="flex justify-between items-start">
                            <span className="text-[10px] font-semibold text-cyber-secondary bg-cyber-secondary bg-opacity-10 px-2 py-0.5 rounded-md uppercase font-outfit tracking-wide">
                              {task.gap_id}
                            </span>
                            <button
                              onClick={() => handleDeleteTask(task.id)}
                              className="text-gray-500 hover:text-cyber-rose p-1 rounded-md hover:bg-gray-900 transition-all opacity-0 group-hover:opacity-100"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          <h4 className="font-bold text-sm text-gray-100 font-outfit mt-2 leading-snug">{task.title}</h4>
                          {task.description && (
                            <p className="text-xs text-gray-400 mt-1 leading-relaxed line-clamp-3">{task.description}</p>
                          )}

                          {linkedGap && (
                            <div className="mt-2.5 flex items-center space-x-1.5 text-[10px] text-gray-500 border-t border-gray-900 pt-2">
                              <span>Scope sector:</span>
                              <span className="text-gray-400 font-semibold">{linkedGap.control_name}</span>
                            </div>
                          )}

                          {/* Task metadata footer */}
                          <div className="mt-3 flex items-center justify-between text-[10px] text-gray-400 pt-2 border-t border-gray-900">
                            <div className="flex items-center space-x-1">
                              <User className="w-3 h-3 text-gray-500" />
                              <span>{task.assignee || 'Unassigned'}</span>
                            </div>
                            {task.due_date && (
                              <div className="flex items-center space-x-1 text-gray-500">
                                <Calendar className="w-3 h-3" />
                                <span>{new Date(task.due_date).toLocaleDateString()}</span>
                              </div>
                            )}
                          </div>

                          {/* Interactive Move Controls */}
                          <div className="mt-3 flex justify-end space-x-1.5 pt-2 border-t border-gray-900">
                            {col.id === 'Open' && (
                              <button
                                onClick={() => handleUpdateStatus(task.id, 'In Progress')}
                                className="text-[10px] bg-cyber-primary bg-opacity-20 hover:bg-opacity-40 text-cyber-primary font-medium px-2.5 py-1 rounded-md transition-all flex items-center space-x-1"
                              >
                                <span>Claim</span>
                                <ArrowRight className="w-3 h-3" />
                              </button>
                            )}
                            {col.id === 'In Progress' && (
                              <button
                                onClick={() => handleUpdateStatus(task.id, 'Done')}
                                className="text-[10px] bg-cyber-emerald bg-opacity-20 hover:bg-opacity-40 text-cyber-emerald font-medium px-2.5 py-1 rounded-md transition-all flex items-center space-x-1"
                              >
                                <span>Resolve</span>
                                <ArrowRight className="w-3 h-3" />
                              </button>
                            )}
                            {col.id === 'Done' && (
                              <button
                                onClick={() => handleUpdateStatus(task.id, 'In Progress')}
                                className="text-[9px] border border-gray-800 text-gray-500 hover:text-white px-2 py-0.5 rounded-md transition-all"
                              >
                                Reopen
                              </button>
                            )}
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
