<script setup>
import AppSidebar from './components/AppSidebar.vue'
import ScriptWorkspace from './components/ScriptWorkspace.vue'
import SupportColumn from './components/SupportColumn.vue'
import WorkflowStepper from './components/WorkflowStepper.vue'
import WorkspaceHeader from './components/WorkspaceHeader.vue'
import {
  analysisMetrics,
  iconPaths,
  insightItems,
  navItems,
  previewDialogues,
  projectStages,
  quickActions,
  scriptChapters,
  workflowSteps,
  yamlLines,
} from './data/workbench'
</script>

<template>
  <div class="app-shell">
    <AppSidebar :icon-paths="iconPaths" :nav-items="navItems" :quick-actions="quickActions" />

    <main class="workspace" aria-label="工作区">
      <WorkspaceHeader :icon-paths="iconPaths" />
      <WorkflowStepper :icon-paths="iconPaths" :steps="workflowSteps" />

      <div class="content-grid">
        <SupportColumn
          :analysis-metrics="analysisMetrics"
          :icon-paths="iconPaths"
          :insight-items="insightItems"
          :project-stages="projectStages"
        />
        <ScriptWorkspace
          :icon-paths="iconPaths"
          :preview-dialogues="previewDialogues"
          :script-chapters="scriptChapters"
          :yaml-lines="yamlLines"
        />
      </div>
    </main>
  </div>
</template>
