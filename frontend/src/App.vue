<template>
    <v-app>
        <v-app-bar color="primary" app>
            <span class="app-title">Анализ производительности статических анализаторов кода</span>
            <v-spacer />
            <v-btn
                icon
                href="https://github.com/caVenikk/ITMO_nir_4"
                target="_blank"
                aria-label="Посетить репозиторий GitHub проекта"
            >
                <v-icon>mdi-github</v-icon>
            </v-btn>
        </v-app-bar>

        <v-main>
            <router-view />
        </v-main>
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

.app-title {
    margin-left: 20px;
    font-size: 1.25rem;
    font-weight: 400;
    letter-spacing: 0;
    line-height: 1.75rem;
    text-transform: none;
}
</style>
