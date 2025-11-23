import { storeToRefs } from 'pinia';
import { computed, watch, nextTick } from 'vue';
import { useThemeStore } from '@/stores/theme';
import { readCssVar } from '@/utils/themeColors';

const THEME_COLOR_META = 'theme-color';

function updateThemeColorMeta() {
  if (typeof document === 'undefined') return;
  let meta = document.querySelector(`meta[name="${THEME_COLOR_META}"]`);
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', THEME_COLOR_META);
    document.head.appendChild(meta);
  }
  const color = readCssVar('--aurora-meta-theme-color');
  if (color) {
    meta.setAttribute('content', color);
  }
}

export function useTheme() {
  const themeStore = useThemeStore();
  const { colorScheme, motionEnabled, isDark, motionPreference } = storeToRefs(themeStore);

  watch(
    isDark,
    async () => {
      await nextTick();
      updateThemeColorMeta();
    },
    { immediate: true }
  );

  const auroraAccentClass = computed(() => (isDark.value ? 'aurora-dark' : 'aurora-light'));

  return {
    colorScheme,
    motionEnabled,
    isDark,
    motionPreference,
    auroraAccentClass,
    setColorScheme: themeStore.setColorScheme,
    toggleColorScheme: themeStore.toggleColorScheme,
    setMotionEnabled: themeStore.setMotionEnabled,
    toggleMotion: themeStore.toggleMotion,
  };
}
