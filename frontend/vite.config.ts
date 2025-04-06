// Plugins
import Components from "unplugin-vue-components/vite";
import Vue from "@vitejs/plugin-vue";
import Vuetify, { transformAssetUrls } from "vite-plugin-vuetify";
import ViteFonts from "unplugin-fonts/vite";
import VueRouter from "unplugin-vue-router/vite";

// Utilities
import { defineConfig, loadEnv } from "vite";
import { fileURLToPath, URL } from "node:url";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
    // Загружаем переменные окружения из соответствующего файла
    // в зависимости от режима сборки (development или production)
    const env = loadEnv(mode, process.cwd(), '');
    
    return {
        plugins: [
            VueRouter(),
            Vue({
                template: { transformAssetUrls },
            }),
            // https://github.com/vuetifyjs/vuetify-loader/tree/master/packages/vite-plugin#readme
            Vuetify({
                autoImport: true,
                styles: {
                    configFile: "src/styles/settings.scss",
                },
            }),
            Components(),
            ViteFonts({
                google: {
                    families: [
                        {
                            name: "Roboto",
                            styles: "wght@100;300;400;500;700;900",
                        },
                    ],
                },
            }),
        ],
        define: { 
            "process.env": env 
        },
        resolve: {
            alias: {
                "@": fileURLToPath(new URL("./src", import.meta.url)),
            },
            extensions: [".js", ".json", ".jsx", ".mjs", ".ts", ".tsx", ".vue"],
        },
        server: {
            port: 3000,
        },
        css: {
            preprocessorOptions: {
                sass: {
                    api: "modern-compiler",
                    silenceDeprecations: ["legacy-js-api"],
                },
                scss: {
                    api: "modern-compiler",
                    silenceDeprecations: ["legacy-js-api"],
                },
            },
        },
    };
});
