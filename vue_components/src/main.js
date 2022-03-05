import { createApp, defineAsyncComponent } from "vue";

const app = createApp({});

// Register pages as components
app.component(
    "play-dynamic-playlist-host",
    defineAsyncComponent(() => import("./pages/play_dynamic_playlist_host.vue"))
);
app.component(
    "play-dynamic-playlist-listener",
    defineAsyncComponent(() => import("./pages/play_dynamic_playlist_listener.vue"))
);
app.component(
    "create-dynamic-playlist",
    defineAsyncComponent(() => import("./pages/create_dynamic_playlist.vue"))
);

app.config.globalProperties.$window = window;
window.vue_app = app; // Used to debug vue app in production

app.mount("#vue_app");
