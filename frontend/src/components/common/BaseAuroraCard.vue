<template>
  <section class="base-aurora-card aurora-glass-surface">
    <header v-if="$slots.header || title" class="card-header">
      <template v-if="$slots.header">
        <slot name="header" />
      </template>
      <template v-else>
        <div class="card-heading">
          <div v-if="icon" class="card-icon" aria-hidden="true">
            <component :is="icon" />
          </div>
          <div class="card-text">
            <h3 class="card-title">{{ title }}</h3>
            <p v-if="subtitle" class="card-subtitle">{{ subtitle }}</p>
          </div>
        </div>
        <div v-if="$slots.actions" class="card-actions">
          <slot name="actions" />
        </div>
      </template>
    </header>
    <div class="card-body">
      <slot />
    </div>
    <footer v-if="$slots.footer" class="card-footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  icon: {
    type: [Object, Function, String],
    default: null,
  },
});
</script>

<style scoped>
.base-aurora-card {
  position: relative;
  padding: 1.5rem;
  color: var(--aurora-text-primary);
  overflow: hidden;
}

.base-aurora-card::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at top right, rgba(14, 165, 233, 0.18), transparent 55%);
  opacity: 0;
  transition: opacity var(--aurora-transition-base);
}

.base-aurora-card:hover::after {
  opacity: 1;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.card-heading {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.card-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.28), rgba(168, 85, 247, 0.3));
  color: white;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.card-title {
  margin: 0;
  font-size: 1.125rem;
  letter-spacing: 0.01em;
}

.card-subtitle {
  margin: 0.15rem 0 0;
  font-size: 0.95rem;
  color: var(--aurora-text-muted);
}

.card-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.card-body {
  position: relative;
  z-index: 1;
}

.card-footer {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--aurora-border);
}

:deep(.el-button) {
  transition: transform var(--aurora-transition-base);
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .base-aurora-card {
    padding: 1.25rem;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
