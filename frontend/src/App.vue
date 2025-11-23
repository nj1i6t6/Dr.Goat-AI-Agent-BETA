<template>
  <div id="app-container">
    <router-view />
  </div>
</template>

<script setup>
// This root component remains simple. Its only job is to provide a mounting point for the router.
</script>

<style scoped>
/* Remove the background-color from here to avoid conflicts with AppLayout's main content area. */
#app-container {
  min-height: 100vh;
}
</style>