<template>
  <p><span v-for="(user, index) in remoteSelectedUsers" v-bind:key="index" class="multiselect__tag">
    <img class="option__image"
         :src="user.image_16"
         height="16" width="16"
         :data-default-image="user.default_image"
         onerror="this.src = this.dataset.defaultImage">
    <span>{{ user.name }}</span>
  </span></p>

  <MediaPlayer
      :next-media-prop="nextMedia"
      :media-playing-event-timing="0"
      :is-mobile="this.$window.context.isMobile"
      :remote-status="remoteStatus"
      @initialPlaybackStarted="queryStatus"
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
      playlistId: null,
      csrfToken: null,
      nextMedia: null,
      websocket: null,
      remoteStatus: null,
      remoteSelectedUsers: null
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

      if (data.action === "update_status") {
        this.remoteStatus = data.status;
        this.remoteSelectedUsers = data.selectedUsers;
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