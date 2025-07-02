<!-- Notification Container Component -->
<script lang="ts">
  import { notifications, notificationActions } from '$lib/stores/notificationStore';
  import { fade, fly } from 'svelte/transition';
  import type { Notification } from '$lib/stores/notificationStore';

  // Icon mapping for different notification types
  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />`;
      case 'error':
        return `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />`;
      case 'warning':
        return `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-1.996-.833-2.767 0L3.047 16.5c-.77.833.192 2.5 1.732 2.5z" />`;
      case 'info':
      default:
        return `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />`;
    }
  };

  // Get alert class for notification type
  const getAlertClass = (type: string) => {
    switch (type) {
      case 'success': return 'alert-success';
      case 'error': return 'alert-error';
      case 'warning': return 'alert-warning';
      case 'info':
      default: return 'alert-info';
    }
  };

  // Dismiss notification
  const dismiss = (id: string) => {
    notificationActions.remove(id);
  };

  // Handle action click
  const handleAction = (notification: Notification) => {
    if (notification.action?.callback) {
      notification.action.callback();
    }
    dismiss(notification.id);
  };

  // Keyboard handling for notifications
  const handleKeydown = (event: KeyboardEvent, notification: Notification) => {
    if (event.key === 'Escape' && notification.dismissible) {
      event.preventDefault();
      dismiss(notification.id);
    } else if (event.key === 'Enter' && notification.action) {
      event.preventDefault();
      handleAction(notification);
    }
  };
</script>

<!-- Notification Container -->
<div 
  class="toast toast-top toast-end z-50 p-4 space-y-2"
  role="region"
  aria-label="알림"
  aria-live="polite"
>
  {#each $notifications as notification (notification.id)}
    <div
      class="alert {getAlertClass(notification.type)} shadow-lg max-w-sm"
      role="alert"
      aria-labelledby="notification-{notification.id}"
      tabindex="0"
      on:keydown={(e) => handleKeydown(e, notification)}
      transition:fly={{ x: 300, duration: 300 }}
    >
      <!-- Icon -->
      <svg 
        class="w-6 h-6 stroke-current shrink-0" 
        fill="none" 
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        {@html getIcon(notification.type)}
      </svg>
      
      <!-- Content -->
      <div class="flex-1">
        <span id="notification-{notification.id}" class="text-sm font-medium">
          {notification.message}
        </span>
      </div>
      
      <!-- Action Button -->
      {#if notification.action}
        <button
          class="btn btn-sm btn-ghost"
          on:click={() => handleAction(notification)}
          aria-label={notification.action.label}
        >
          {notification.action.label}
        </button>
      {/if}
      
      <!-- Dismiss Button -->
      {#if notification.dismissible}
        <button
          class="btn btn-sm btn-ghost btn-square"
          on:click={() => dismiss(notification.id)}
          aria-label="알림 닫기"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      {/if}
    </div>
  {/each}
</div>

<style>
  .toast {
    position: fixed;
    top: 4rem;
    right: 1rem;
    z-index: 1000;
  }
  
  .alert {
    min-width: 20rem;
    max-width: 24rem;
  }
  
  @media (max-width: 640px) {
    .toast {
      top: 1rem;
      right: 1rem;
      left: 1rem;
    }
    
    .alert {
      min-width: auto;
      max-width: none;
    }
  }
  
  /* Focus styles for accessibility */
  .alert:focus {
    outline: 2px solid currentColor;
    outline-offset: 2px;
  }
  
  /* High contrast mode support */
  :global(.high-contrast) .alert {
    border: 2px solid currentColor;
  }
  
  /* Reduced motion support */
  @media (prefers-reduced-motion: reduce) {
    .alert {
      transition: none;
    }
  }
</style> 