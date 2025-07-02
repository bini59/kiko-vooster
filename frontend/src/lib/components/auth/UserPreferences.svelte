<!-- User Preferences Component -->
<script lang="ts">
  import { userPreferences, preferencesActions } from '$lib/stores/authStore';
  import { showNotification } from '$lib/stores/notificationStore';
  import { onMount } from 'svelte';
  import type { UserPreferences } from '$lib/types/auth';

  // Local state for UI feedback
  let isSaving = false;
  let hasUnsavedChanges = false;

  // Additional accessibility settings (local state)
  let accessibilitySettings = {
    fontSize: 16,
    lineHeight: 1.5,
    reduceMotion: false,
    highContrast: false
  };

  // Watch for changes to mark as unsaved
  let lastSavedPreferences: UserPreferences | null = null;
  
  $: if (lastSavedPreferences && $userPreferences) {
    const current = JSON.stringify($userPreferences);
    const last = JSON.stringify(lastSavedPreferences);
    hasUnsavedChanges = current !== last;
  }

  onMount(() => {
    if ($userPreferences) {
      lastSavedPreferences = JSON.parse(JSON.stringify($userPreferences));
    }
    
    // Load accessibility settings from localStorage
    const savedAccessibility = localStorage.getItem('accessibility_settings');
    if (savedAccessibility) {
      try {
        accessibilitySettings = { ...accessibilitySettings, ...JSON.parse(savedAccessibility) };
      } catch (error) {
        console.error('Failed to load accessibility settings:', error);
      }
    }
    
    // Apply accessibility settings to document
    applyAccessibilitySettings();
  });

  // Apply accessibility settings to document
  const applyAccessibilitySettings = () => {
    const root = document.documentElement;
    root.style.setProperty('--font-size-user', `${accessibilitySettings.fontSize}px`);
    root.style.setProperty('--line-height-user', accessibilitySettings.lineHeight.toString());
    
    if (accessibilitySettings.reduceMotion) {
      root.style.setProperty('--animation-duration', '0s');
      root.style.setProperty('--transition-duration', '0s');
    } else {
      root.style.removeProperty('--animation-duration');
      root.style.removeProperty('--transition-duration');
    }
    
    if (accessibilitySettings.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }
  };

  // Handle preference updates
  const updatePreference = async (key: keyof UserPreferences, value: any) => {
    try {
      await preferencesActions.updateSetting(key, value);
      // Update last saved state
      if ($userPreferences) {
        lastSavedPreferences = JSON.parse(JSON.stringify($userPreferences));
        hasUnsavedChanges = false;
      }
    } catch (error) {
      console.error('Failed to update preference:', error);
      showNotification('설정 저장에 실패했습니다.', 'error');
    }
  };

  // Handle accessibility setting updates
  const updateAccessibilitySetting = (key: keyof typeof accessibilitySettings, value: any) => {
    accessibilitySettings = { ...accessibilitySettings, [key]: value };
    applyAccessibilitySettings();
    
    // Save to localStorage
    localStorage.setItem('accessibility_settings', JSON.stringify(accessibilitySettings));
    showNotification('접근성 설정이 적용되었습니다.', 'success', { duration: 3000 });
  };

  // Save all changes
  const saveAllChanges = async () => {
    if (!hasUnsavedChanges || !$userPreferences) return;
    
    isSaving = true;
    try {
      await preferencesActions.savePreferences($userPreferences);
      lastSavedPreferences = JSON.parse(JSON.stringify($userPreferences));
      hasUnsavedChanges = false;
      showNotification('설정이 저장되었습니다.', 'success');
    } catch (error) {
      console.error('Failed to save preferences:', error);
      showNotification('설정 저장에 실패했습니다.', 'error');
    } finally {
      isSaving = false;
    }
  };

  // Reset to defaults
  const resetToDefaults = async () => {
    try {
      await preferencesActions.resetToDefaults();
      lastSavedPreferences = JSON.parse(JSON.stringify($userPreferences));
      hasUnsavedChanges = false;
      
      // Reset accessibility settings
      accessibilitySettings = {
        fontSize: 16,
        lineHeight: 1.5,
        reduceMotion: false,
        highContrast: false
      };
      applyAccessibilitySettings();
      localStorage.removeItem('accessibility_settings');
      
      showNotification('설정이 기본값으로 초기화되었습니다.', 'info');
    } catch (error) {
      console.error('Failed to reset preferences:', error);
      showNotification('설정 초기화에 실패했습니다.', 'error');
    }
  };

  // Keyboard shortcuts
  const handleKeydown = (event: KeyboardEvent) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
      event.preventDefault();
      if (hasUnsavedChanges) {
        saveAllChanges();
      }
    }
  };

  // Map theme values
  const getThemeDisplayValue = (theme: string) => {
    switch (theme) {
      case 'auto': return 'system';
      case 'light': return 'light';
      case 'dark': return 'dark';
      default: return 'system';
    }
  };

  const setThemeValue = (displayValue: string) => {
    switch (displayValue) {
      case 'system': return 'auto';
      case 'light': return 'light';
      case 'dark': return 'dark';
      default: return 'auto';
    }
  };
</script>

<svelte:window on:keydown={handleKeydown} />

{#if $userPreferences}
  <div class="space-y-6" aria-label="사용자 설정">
    <!-- Theme Settings -->
    <div class="form-control">
      <label class="label" for="theme-select">
        <span class="label-text font-semibold">테마</span>
      </label>
      <select 
        id="theme-select"
        class="select select-bordered w-full max-w-xs"
        value={getThemeDisplayValue($userPreferences.theme)}
        on:change={(e) => updatePreference('theme', setThemeValue(e.currentTarget.value))}
        aria-describedby="theme-help"
      >
        <option value="system">시스템 설정 따르기</option>
        <option value="light">라이트 모드</option>
        <option value="dark">다크 모드</option>
      </select>
      <div id="theme-help" class="label">
        <span class="label-text-alt text-base-content/60">
          시스템 설정을 따르거나 수동으로 선택할 수 있습니다.
        </span>
      </div>
    </div>

    <div class="divider"></div>

    <!-- Language Settings -->
    <div class="form-control">
      <label class="label" for="language-select">
        <span class="label-text font-semibold">언어</span>
      </label>
      <select 
        id="language-select"
        class="select select-bordered w-full max-w-xs"
        bind:value={$userPreferences.language}
        on:change={(e) => updatePreference('language', e.currentTarget.value)}
        aria-describedby="language-help"
      >
        <option value="ko">한국어</option>
        <option value="ja">日本語</option>
        <option value="en">English</option>
      </select>
      <div id="language-help" class="label">
        <span class="label-text-alt text-base-content/60">
          인터페이스 언어를 선택하세요.
        </span>
      </div>
    </div>

    <div class="divider"></div>

    <!-- Accessibility Settings -->
    <div class="space-y-4">
      <h3 class="text-lg font-semibold text-base-content">접근성</h3>
      
      <!-- Font Size -->
      <div class="form-control">
        <label class="label" for="system-font-size">
          <span class="label-text font-medium">시스템 폰트 크기</span>
        </label>
        <select 
          id="system-font-size"
          class="select select-bordered w-full max-w-xs"
          bind:value={$userPreferences.font_size}
          on:change={(e) => updatePreference('font_size', e.currentTarget.value)}
          aria-describedby="system-font-size-help"
        >
          <option value="small">작게</option>
          <option value="medium">보통</option>
          <option value="large">크게</option>
        </select>
        <div id="system-font-size-help" class="label">
          <span class="label-text-alt text-base-content/60">
            시스템 전체 폰트 크기를 설정하세요.
          </span>
        </div>
      </div>

      <!-- Accessibility Font Size -->
      <div class="form-control">
        <label class="label" for="font-size-range">
          <span class="label-text font-medium">접근성 폰트 크기</span>
          <span class="label-text-alt">{accessibilitySettings.fontSize}px</span>
        </label>
        <input 
          id="font-size-range"
          type="range" 
          min="12" 
          max="24" 
          step="1"
          class="range range-primary"
          bind:value={accessibilitySettings.fontSize}
          on:change={(e) => updateAccessibilitySetting('fontSize', parseInt(e.currentTarget.value))}
          aria-describedby="font-size-help"
        />
        <div class="w-full flex justify-between text-xs px-2 text-base-content/60">
          <span>12px</span>
          <span>18px</span>
          <span>24px</span>
        </div>
        <div id="font-size-help" class="label">
          <span class="label-text-alt text-base-content/60">
            텍스트 크기를 세밀하게 조절하세요. (12px - 24px)
          </span>
        </div>
      </div>

      <!-- Line Height -->
      <div class="form-control">
        <label class="label" for="line-height-range">
          <span class="label-text font-medium">행간</span>
          <span class="label-text-alt">{accessibilitySettings.lineHeight}</span>
        </label>
        <input 
          id="line-height-range"
          type="range" 
          min="1.2" 
          max="2.0" 
          step="0.1"
          class="range range-primary"
          bind:value={accessibilitySettings.lineHeight}
          on:change={(e) => updateAccessibilitySetting('lineHeight', parseFloat(e.currentTarget.value))}
          aria-describedby="line-height-help"
        />
        <div class="w-full flex justify-between text-xs px-2 text-base-content/60">
          <span>좁게</span>
          <span>보통</span>
          <span>넓게</span>
        </div>
        <div id="line-height-help" class="label">
          <span class="label-text-alt text-base-content/60">
            줄 사이의 간격을 조절하세요. (1.2 - 2.0)
          </span>
        </div>
      </div>

      <!-- Reduce Motion -->
      <div class="form-control">
        <label class="label cursor-pointer" for="reduce-motion">
          <span class="label-text font-medium">애니메이션 감소</span>
          <input 
            id="reduce-motion"
            type="checkbox" 
            class="toggle toggle-primary"
            bind:checked={accessibilitySettings.reduceMotion}
            on:change={(e) => updateAccessibilitySetting('reduceMotion', e.currentTarget.checked)}
            aria-describedby="reduce-motion-help"
          />
        </label>
        <div id="reduce-motion-help" class="label">
          <span class="label-text-alt text-base-content/60">
            움직임에 민감한 경우 애니메이션을 줄입니다.
          </span>
        </div>
      </div>

      <!-- High Contrast -->
      <div class="form-control">
        <label class="label cursor-pointer" for="high-contrast">
          <span class="label-text font-medium">고대비 모드</span>
          <input 
            id="high-contrast"
            type="checkbox" 
            class="toggle toggle-primary"
            bind:checked={accessibilitySettings.highContrast}
            on:change={(e) => updateAccessibilitySetting('highContrast', e.currentTarget.checked)}
            aria-describedby="high-contrast-help"
          />
        </label>
        <div id="high-contrast-help" class="label">
          <span class="label-text-alt text-base-content/60">
            시각적 대비를 높여 가독성을 개선합니다.
          </span>
        </div>
      </div>
    </div>

    <div class="divider"></div>

    <!-- Audio Settings -->
    <div class="space-y-4">
      <h3 class="text-lg font-semibold text-base-content">오디오</h3>
      
      <!-- Playback Speed -->
      <div class="form-control">
        <label class="label" for="playback-speed-range">
          <span class="label-text font-medium">재생 속도</span>
          <span class="label-text-alt">{$userPreferences.playback_speed}x</span>
        </label>
        <input 
          id="playback-speed-range"
          type="range" 
          min="0.5" 
          max="2.0" 
          step="0.1"
          class="range range-primary"
          bind:value={$userPreferences.playback_speed}
          on:change={(e) => updatePreference('playback_speed', parseFloat(e.currentTarget.value))}
          aria-describedby="playback-speed-help"
        />
        <div class="w-full flex justify-between text-xs px-2 text-base-content/60">
          <span>0.5x</span>
          <span>1.0x</span>
          <span>2.0x</span>
        </div>
        <div id="playback-speed-help" class="label">
          <span class="label-text-alt text-base-content/60">
            기본 재생 속도를 설정하세요.
          </span>
        </div>
      </div>

      <!-- Auto Pause on Unknown Word -->
      <div class="form-control">
        <label class="label cursor-pointer" for="auto-pause">
          <span class="label-text font-medium">모르는 단어에서 자동 정지</span>
          <input 
            id="auto-pause"
            type="checkbox" 
            class="toggle toggle-primary"
            bind:checked={$userPreferences.auto_pause_on_unknown_word}
            on:change={(e) => updatePreference('auto_pause_on_unknown_word', e.currentTarget.checked)}
            aria-describedby="auto-pause-help"
          />
        </label>
        <div id="auto-pause-help" class="label">
          <span class="label-text-alt text-base-content/60">
            모르는 단어가 나올 때 자동으로 재생을 멈춥니다.
          </span>
        </div>
      </div>

      <!-- Show Furigana -->
      <div class="form-control">
        <label class="label cursor-pointer" for="show-furigana">
          <span class="label-text font-medium">후리가나 표시</span>
          <input 
            id="show-furigana"
            type="checkbox" 
            class="toggle toggle-primary"
            bind:checked={$userPreferences.show_furigana}
            on:change={(e) => updatePreference('show_furigana', e.currentTarget.checked)}
            aria-describedby="show-furigana-help"
          />
        </label>
        <div id="show-furigana-help" class="label">
          <span class="label-text-alt text-base-content/60">
            일본어 텍스트에 후리가나를 표시합니다.
          </span>
        </div>
      </div>
    </div>

    <div class="divider"></div>

    <!-- Action Buttons -->
    <div class="flex flex-wrap gap-3 pt-4">
      {#if hasUnsavedChanges}
        <button 
          class="btn btn-primary"
          class:loading={isSaving}
          disabled={isSaving}
          on:click={saveAllChanges}
          aria-describedby="save-help"
        >
          {#if isSaving}
            저장 중...
          {:else}
            변경사항 저장
          {/if}
        </button>
        <div id="save-help" class="text-xs text-base-content/60 self-center">
          Ctrl/Cmd + S
        </div>
      {/if}
      
      <button 
        class="btn btn-ghost"
        on:click={resetToDefaults}
        disabled={isSaving}
      >
        기본값으로 초기화
      </button>
    </div>

    {#if hasUnsavedChanges}
      <div class="alert alert-warning" role="alert">
        <svg class="w-6 h-6 stroke-current shrink-0" fill="none" viewBox="0 0 24 24" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-1.996-.833-2.767 0L3.047 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <span>저장하지 않은 변경사항이 있습니다.</span>
      </div>
    {/if}
  </div>
{:else}
  <div class="flex justify-center items-center py-8">
    <div class="loading loading-spinner loading-lg text-primary"></div>
  </div>
{/if}

<style>
  :global([data-theme="dark"]) .range::-webkit-slider-thumb {
    background-color: hsl(var(--p));
  }
  
  :global([data-theme="light"]) .range::-webkit-slider-thumb {
    background-color: hsl(var(--p));
  }
</style> 