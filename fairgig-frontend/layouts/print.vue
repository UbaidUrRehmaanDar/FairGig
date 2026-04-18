<template>
  <div class="print-layout">
    <slot />
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.print-layout {
  min-height: 100vh;
  background: var(--fg-bg);
  color: var(--fg-text);
  font-family: 'Raleway', sans-serif;
}

@media print {
  .print-layout {
    background: #fff;
  }
}
</style>