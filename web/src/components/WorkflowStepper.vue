<script setup>
defineProps({
  iconPaths: { type: Object, required: true },
  steps: { type: Array, required: true },
})
</script>

<template>
  <section class="workflow-stepper" aria-label="小说转剧本流程">
    <ol>
      <li
        v-for="(step, index) in steps"
        :key="step.title"
        class="workflow-step"
        :class="`is-${step.status}`"
        :aria-current="step.status === 'current' ? 'step' : undefined"
      >
        <span class="step-marker">
          <svg v-if="step.status === 'done'" viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="path in iconPaths.check" :key="path" :d="path" />
          </svg>
          <span v-else>{{ step.number }}</span>
        </span>
        <span class="step-copy">
          <strong>{{ step.title }}</strong>
          <span>{{ step.description }}</span>
        </span>
        <svg v-if="index < steps.length - 1" class="step-arrow" viewBox="0 0 24 24" aria-hidden="true">
          <path v-for="path in iconPaths.chevron" :key="path" :d="path" />
        </svg>
      </li>
    </ol>
  </section>
</template>
