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
  <div class="app-layout">
    <AppSidebar :icon-paths="iconPaths" :nav-items="navItems" :quick-actions="quickActions" />

    <main class="main-wrapper" aria-label="工作区">
      <div class="page-content">
        <WorkspaceHeader :icon-paths="iconPaths" />
        <div class="workflow-sticky">
          <WorkflowStepper :icon-paths="iconPaths" :steps="workflowSteps" />
        </div>

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
      </div>
    </main>
  </div>
</template>
