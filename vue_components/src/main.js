import {createApp} from "vue";

import PlaylistHost from "./pages/play_dynamic_playlist_host.vue";
import PlaylistListener from "./pages/play_dynamic_playlist_listener.vue";
import CreatePlaylist from "./pages/create_dynamic_playlist.vue";
import Groups from "./pages/groups.vue";

const app = createApp({});

app.config.globalProperties.$window = window;
window.vue_app = app; // Used to debug vue app in production

// Register pages as components
app.component("play-dynamic-playlist-host", PlaylistHost)
    .component("play-dynamic-playlist-listener", PlaylistListener)
    .component("create-dynamic-playlist", CreatePlaylist)
    .component("groups", Groups)
    .mount("#vue_app");