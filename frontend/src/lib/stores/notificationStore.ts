// Notification Store
import { writable } from 'svelte/store';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  message: string;
  type: NotificationType;
  duration?: number; // ms, 0 = no auto-dismiss
  action?: {
    label: string;
    callback: () => void;
  };
  dismissible?: boolean;
  timestamp: number;
}

// Notification state
const notifications = writable<Notification[]>([]);

// Actions
export const notificationActions = {
  add: (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: Notification = {
      id,
      timestamp: Date.now(),
      duration: 5000, // Default 5 seconds
      dismissible: true,
      ...notification,
    };
    
    notifications.update(items => [...items, newNotification]);
    
    // Auto-dismiss if duration is set
    if (newNotification.duration && newNotification.duration > 0) {
      setTimeout(() => {
        notificationActions.remove(id);
      }, newNotification.duration);
    }
    
    return id;
  },
  
  remove: (id: string) => {
    notifications.update(items => items.filter(item => item.id !== id));
  },
  
  clear: () => {
    notifications.set([]);
  },
  
  removeByType: (type: NotificationType) => {
    notifications.update(items => items.filter(item => item.type !== type));
  }
};

// Convenience functions
export const showNotification = (
  message: string, 
  type: NotificationType = 'info', 
  options?: Partial<Omit<Notification, 'id' | 'message' | 'type' | 'timestamp'>>
): string => {
  return notificationActions.add({
    message,
    type,
    ...options,
  });
};

export const showSuccess = (message: string, options?: Partial<Omit<Notification, 'id' | 'message' | 'type' | 'timestamp'>>) => 
  showNotification(message, 'success', options);

export const showError = (message: string, options?: Partial<Omit<Notification, 'id' | 'message' | 'type' | 'timestamp'>>) => 
  showNotification(message, 'error', { duration: 8000, ...options });

export const showWarning = (message: string, options?: Partial<Omit<Notification, 'id' | 'message' | 'type' | 'timestamp'>>) => 
  showNotification(message, 'warning', options);

export const showInfo = (message: string, options?: Partial<Omit<Notification, 'id' | 'message' | 'type' | 'timestamp'>>) => 
  showNotification(message, 'info', options);

// Export store and convenience aliases
export { notifications };

// Convenience aliases for common actions
export const removeNotification = notificationActions.remove;
export const addNotification = notificationActions.add;
export const clearNotifications = notificationActions.clear; 