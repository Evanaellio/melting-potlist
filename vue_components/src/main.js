import {createApp, defineAsyncComponent} from "vue";

const app = createApp({});

app.config.globalProperties.$window = window;
window.vue_app = app; // Used to debug vue app in production

// Register pages as components
app.component("play-dynamic-playlist-host", defineAsyncComponent(() => import("./pages/play_dynamic_playlist_host.vue")))
    .component("play-dynamic-playlist-listener", defineAsyncComponent(() => import("./pages/play_dynamic_playlist_listener.vue")))
    .component("create-dynamic-playlist", defineAsyncComponent(() => import("./pages/create_dynamic_playlist.vue")))
    .component("groups", defineAsyncComponent(() => import("./pages/groups.vue")))
    .mount("#vue_app");
