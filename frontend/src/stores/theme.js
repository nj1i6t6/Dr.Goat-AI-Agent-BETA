import { defineStore } from 'pinia';
import { computed, ref, watch } from 'vue';

const COLOR_SCHEME_STORAGE_KEY = 'aurora-color-scheme';
const MOTION_STORAGE_KEY = 'aurora-motion-enabled';

function getSystemColorScheme() {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function getSystemMotionPreference() {
  if (typeof window === 'undefined') return true;
  return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function applyColorScheme(value) {
  if (typeof document === 'undefined') return;
  document.documentElement.setAttribute('data-theme', value);
}

function applyMotionPreference(isEnabled) {
  if (typeof document === 'undefined') return;
  document.documentElement.setAttribute('data-aurora-motion', isEnabled ? 'enabled' : 'reduced');
}

export const useThemeStore = defineStore('theme', () => {
  const storedScheme =
    typeof localStorage !== 'undefined' ? localStorage.getItem(COLOR_SCHEME_STORAGE_KEY) : null;
  const storedMotion =
    typeof localStorage !== 'undefined' ? localStorage.getItem(MOTION_STORAGE_KEY) : null;

  const colorScheme = ref(storedScheme || getSystemColorScheme());
  const motionEnabled = ref(
    storedMotion ? storedMotion === 'true' : getSystemMotionPreference()
  );

  const isDark = computed(() => colorScheme.value === 'dark');
  const motionPreference = computed(() => (motionEnabled.value ? 'enabled' : 'reduced'));

  const setColorScheme = (value) => {
    colorScheme.value = value;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(COLOR_SCHEME_STORAGE_KEY, value);
    }
  };

  const toggleColorScheme = () => {
    setColorScheme(isDark.value ? 'light' : 'dark');
  };

  const setMotionEnabled = (value) => {
    motionEnabled.value = value;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(MOTION_STORAGE_KEY, value ? 'true' : 'false');
    }
  };

  const toggleMotion = () => {
    setMotionEnabled(!motionEnabled.value);
  };

  watch(
    colorScheme,
    (value) => {
      applyColorScheme(value);
    },
    { immediate: true }
  );

  watch(
    motionEnabled,
    (value) => {
      applyMotionPreference(value);
    },
    { immediate: true }
  );

  return {
    colorScheme,
    motionEnabled,
    isDark,
    motionPreference,
    setColorScheme,
    toggleColorScheme,
    setMotionEnabled,
    toggleMotion,
  };
});
