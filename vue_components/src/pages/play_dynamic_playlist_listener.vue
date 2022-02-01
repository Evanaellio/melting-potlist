<template>
  <button class="btn btn-primary btn-lg" v-on:click="queryStatus">
    Resync with host
  </button>
  <MediaPlayer
    :next-media-prop="nextMedia"
    :media-playing-event-timing="0"
    :remote-status="remoteStatus"
    @initialPlaybackStarted="queryStatus"
  ></MediaPlayer>
</template>

<script>
import MediaPlayer from "../components/MediaPlayer.vue";
// import ReconnectingWebSocket from "reconnecting-websocket";

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
      this.sendWebsocketData({ action: "query_status" });
    },
    sendWebsocketData(data) {
      this.websocket.send(JSON.stringify(data));
    },
    onWebsocketMessage(event) {
      console.log("Message from " + this.websocket, event);

      const data = JSON.parse(event.data);

      if (data.action === "update_status") {
        this.remoteStatus = data.status;
      }
    }
  },
  created() {
    this.playlistId = this.$window.context.playlistId;
    this.websocketProtocol = this.$window.context.websocketProtocol;
  },
  mounted() {
    this.csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    this.websocket = new WebSocket(
        `${this.$window.context.websocketProtocol}://${window.location.host}/ws/dynamicplaylists/${this.playlistId}/`
    );

    this.websocket.addEventListener("message", this.onWebsocketMessage);

    this.websocket.addEventListener("open", () => {
      console.log(this.websocket);
      this.sendWebsocketData({action: "query_status"});
    });

    this.websocket.addEventListener("close", () => {
      console.log(this.websocket);
      console.error("Websocket closed unexpectedly");
    });
  }
};
</script>