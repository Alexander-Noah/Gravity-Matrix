<script setup>
defineProps({
  iconPaths: { type: Object, required: true },
  route: { type: Object, required: true },
})
</script>

<template>
  <section class="route-placeholder" aria-labelledby="route-placeholder-title">
    <div class="route-placeholder-icon">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path v-for="path in iconPaths.folder" :key="path" :d="path" />
      </svg>
    </div>
    <div>
      <span>产品级路由</span>
      <h2 id="route-placeholder-title">{{ route.title }}</h2>
      <p>{{ route.description }}</p>
    </div>
  </section>
</template>
