<script lang="ts">
  import { onMount } from 'svelte';
  import { notifications, removeNotification } from '$lib/stores/notificationStore';
  
  export let notification: {
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message?: string;
    duration?: number;
  };
  
  let timeoutId: number | null = null;
  
  onMount(() => {
    if (notification.duration && notification.duration > 0) {
      timeoutId = window.setTimeout(() => {
        removeNotification(notification.id);
      }, notification.duration);
    }
    
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  });
  
  function handleClose() {
    removeNotification(notification.id);
  }
  
  function getAlertClass(type: string): string {
    switch (type) {
      case 'success': return 'alert-success';
      case 'error': return 'alert-error';
      case 'warning': return 'alert-warning';
      case 'info': return 'alert-info';
      default: return 'alert-info';
    }
  }
  
  function getIcon(type: string): string {
    switch (type) {
      case 'success': return '✓';
      case 'error': return '✕';
      case 'warning': return '⚠';
      case 'info': return 'ℹ';
      default: return 'ℹ';
    }
  }
</script>

<div 
  class="alert {getAlertClass(notification.type)} mb-4 shadow-lg"
  role="alert"
  aria-live="polite"
  data-notification-id={notification.id}
>
  <div class="flex items-start gap-3">
    <span class="text-lg font-bold" aria-hidden="true">
      {getIcon(notification.type)}
    </span>
    
    <div class="flex-grow min-w-0">
      <h4 class="font-semibold text-sm mb-1">
        {notification.title}
      </h4>
      {#if notification.message}
        <p class="text-sm opacity-90">
          {notification.message}
        </p>
      {/if}
    </div>
    
    <button
      type="button"
      class="btn btn-ghost btn-sm btn-square"
      on:click={handleClose}
      aria-label="알림 닫기"
    >
      <span class="text-lg" aria-hidden="true">×</span>
    </button>
  </div>
</div>

<style>
  .alert {
    animation: slideIn 0.3s ease-out;
  }
  
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  /* 접근성: 애니메이션 감소 설정 */
  @media (prefers-reduced-motion: reduce) {
    .alert {
      animation: none;
    }
  }
</style> 