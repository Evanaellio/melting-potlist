<template>
  <MediaPlayer
      :next-media-prop="nextMedia"
      :media-playing-event-timing="0"
      :remote-status="remoteStatus"
      @play="queryStatus"
  ></MediaPlayer>
</template>

<script>
import MediaPlayer from "../components/MediaPlayer.vue";

export default {
  components: {
    MediaPlayer
  },
  data() {
    return {
      users: {
        selected: [],
        all: []
      },
      playlistId: null,
      csrfToken: null,
      nextMedia: null,
      websocket: null,
      remoteStatus: null,
      initialRemoteSync: false,
      currentMediaPersisted: false
    };
  },
  methods: {
    queryStatus() {
      this.sendWebsocketData({action: "query_status"});
    },
    sendWebsocketData(data) {
      this.websocket.send(JSON.stringify(data));
    },
    onWebsocketMessage(event) {
      const data = JSON.parse(event.data);

      if (data.action === 'update_status') {
        this.remoteStatus = data.status;
      }
    }
  },
  created() {
    this.playlistId = this.$window.context.playlistId;
  },
  mounted() {
    this.csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    this.websocket = new WebSocket(`wss://${window.location.host}/ws/dynamicplaylists/${this.playlistId}/`);
    this.websocket.onmessage = this.onWebsocketMessage;
    this.websocket.onopen = () => this.sendWebsocketData({action: "query_status"});
    this.websocket.onclose = () => console.error('Websocket closed unexpectedly');
  }
};
</script>