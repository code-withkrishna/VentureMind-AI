"use client"

import * as React from "react"
import type { ToastProps, ToastActionElement } from "@/components/ui/toast"
import {
  ToastProvider, ToastViewport, Toast,
  ToastTitle, ToastDescription, ToastClose,
} from "@/components/ui/toast"

const TOAST_LIMIT = 4
const TOAST_REMOVE_DELAY = 1_000_000

type ToasterToast = ToastProps & {
  id: string
  title?: React.ReactNode
  description?: React.ReactNode
  action?: ToastActionElement
}

let count = 0
function genId() { return `toast_${++count}` }

type Action =
  | { type: "ADD_TOAST";    toast: ToasterToast }
  | { type: "UPDATE_TOAST"; toast: Partial<ToasterToast> }
  | { type: "DISMISS_TOAST"; toastId?: string }
  | { type: "REMOVE_TOAST";  toastId?: string }

interface State { toasts: ToasterToast[] }

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

function addToRemoveQueue(toastId?: string) {
  const toastIds = toastId ? [toastId] : memoryState.toasts.map(toast => toast.id)

  for (const id of toastIds) {
    if (toastTimeouts.has(id)) continue
    const timeout = setTimeout(() => {
      toastTimeouts.delete(id)
      dispatch({ type: "REMOVE_TOAST", toastId: id })
    }, TOAST_REMOVE_DELAY)
    toastTimeouts.set(id, timeout)
  }
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "ADD_TOAST":
      return { ...state, toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT) }
    case "UPDATE_TOAST":
      return { ...state, toasts: state.toasts.map(t => t.id === action.toast.id ? { ...t, ...action.toast } : t) }
    case "DISMISS_TOAST": {
      const { toastId } = action
      return {
        ...state,
        toasts: state.toasts.map(t =>
          t.id === toastId || toastId === undefined ? { ...t, open: false } : t
        ),
      }
    }
    case "REMOVE_TOAST":
      return { ...state, toasts: action.toastId === undefined ? [] : state.toasts.filter(t => t.id !== action.toastId) }
  }
}

const listeners: Array<(state: State) => void> = []
let memoryState: State = { toasts: [] }

function dispatch(action: Action) {
  if (action.type === "DISMISS_TOAST") {
    addToRemoveQueue(action.toastId)
  }
  memoryState = reducer(memoryState, action)
  listeners.forEach(l => l(memoryState))
}

type Toast = Omit<ToasterToast, "id">

function toast(props: Toast) {
  const id = genId()
  const update  = (p: ToasterToast) => dispatch({ type: "UPDATE_TOAST", toast: { ...p, id } })
  const dismiss = () => dispatch({ type: "DISMISS_TOAST", toastId: id })
  dispatch({ type: "ADD_TOAST", toast: { ...props, id, open: true, onOpenChange: o => { if (!o) dismiss() } } })
  return { id, dismiss, update }
}

function useToast() {
  const [state, setState] = React.useState<State>(memoryState)
  React.useEffect(() => {
    listeners.push(setState)
    return () => { const i = listeners.indexOf(setState); if (i > -1) listeners.splice(i, 1) }
  }, [])
  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => dispatch({ type: "DISMISS_TOAST", toastId }),
  }
}

function Toaster() {
  const { toasts } = useToast()
  return (
    <ToastProvider>
      {toasts.map(({ id, title, description, action, ...props }) => (
        <Toast key={id} {...props}>
          <div className="flex-1 grid gap-1">
            {title       && <ToastTitle>{title}</ToastTitle>}
            {description && <ToastDescription>{description}</ToastDescription>}
          </div>
          {action}
          <ToastClose />
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  )
}

export { useToast, toast, Toaster }
