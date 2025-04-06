<template>
  <v-app>
    <v-app-bar
      color="primary"
      app
    >
      <v-app-bar-title>Метрики анализаторов Python-кода</v-app-bar-title>
      <v-spacer />
      <v-btn
        icon
        href="https://github.com"
        target="_blank"
      >
        <v-icon>mdi-github</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>

    <v-footer
      app
      class="text-center"
    >
      <span>&copy; {{ new Date().getFullYear() }} - Метрики анализаторов Python-кода</span>
    </v-footer>
  </v-app>
</template>

<script lang="ts" setup>
//
</script>

<style lang="scss">
html,
body {
    overflow-y: auto;
}
</style>
