import { createApp, defineAsyncComponent } from "vue";

const app = createApp({});

// Register pages as components
app.component(
  "play-dynamic-playlist",
  defineAsyncComponent(() => import("./pages/play_dynamic_playlist.vue"))
);
app.component(
  "create-dynamic-playlist",
  defineAsyncComponent(() => import("./pages/create_dynamic_playlist.vue"))
);

app.config.globalProperties.$window = window;

app.mount("#vue_app");
