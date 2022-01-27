<template>
  <Multiselect
      v-model="users.selected"
      :options="users.all"
      label="name"
      track-by="id"
      :option-height="60"
      placeholder=""
      @select="onSelectUser"
      @remove="onRemoveUser"
  ></Multiselect>
  <MediaPlayer
      ref="mediaPlayer"
      :next-media-prop="nextMedia"
      :media-playing-event-timing="8"
      @media-playing="onMediaPlaying"
      @media-started="onMediaStarted"
      @media-played="onMediaPlayed"
      @media-seeked="updateStatus"
      @play="updateStatus"
      @pause="updateStatus"
  ></MediaPlayer>
</template>

<script>
import MediaPlayer from "../components/MediaPlayer.vue";
import Multiselect from "../components/Multiselect.vue";

export default {
  components: {
    MediaPlayer,
    Multiselect
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
      currentMediaPersisted: false
    };
  },
  watch: {
    nextMedia: function (newVal) {
      this.sendWebsocketData({action: "update_status", status: {nextMedia: newVal}});
    },
  },
  computed: {
    selectedUsers() {
      return this.users.selected.map(item => item.id);
    }
  },
  methods: {
    onSelectUser(user) {
      this.updateUser(user, true);
    },
    onRemoveUser(user) {
      this.updateUser(user, false);
    },
    async updateUser(user, isActive) {
      await fetch(`/api/dynamicplaylists/${this.playlistId}/users/${user.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.csrfToken
        },
        body: JSON.stringify({is_active: isActive})
      }).then(() => {
        if (this.currentMediaPersisted) {
          this.persistPlayedSongAndFetchNext();
        }
      });
    },
    persistPlayedSongAndFetchNext(playedSongId = null) {
      if (playedSongId !== null) {
        this.currentMediaPersisted = true;
      }
      return fetch(
          `/api/dynamicplaylists/${this.playlistId}/persist_and_next/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": this.csrfToken
            },
            body: JSON.stringify({trackToPersist: playedSongId})
          }
      )
          .then(response => response.json())
          .then(jsonData => (this.nextMedia = jsonData))
          .catch(reason => console.error(reason));
    },
    onMediaPlaying(event) {
      if (event.elapsedTime > 30 && event.nextMedia === null) {
        this.persistPlayedSongAndFetchNext(event.currentMedia.id);
      }
    },
    onMediaStarted() {
      this.currentMediaPersisted = false;
    },
    onMediaPlayed(event) {
      // Should only happen when skipping or for medias less than or around 30 seconds in length
      if (event.nextMedia === null) {
        this.persistPlayedSongAndFetchNext(event.currentMedia.id);
      }
    },
    sendWebsocketData(data) {
      this.websocket.send(JSON.stringify(data));
    },
    onWebsocketMessage(event) {
      const data = JSON.parse(event.data);

      if (data.action === 'query_status') {
        this.updateStatus();
      }
    },
    updateStatus() {
      this.sendWebsocketData({action: "update_status", status: this.$refs.mediaPlayer.status()});
    }
  },
  created() {
    this.playlistId = this.$window.context.playlistId;
  },
  mounted() {
    this.users.all = this.$window.context.users.sort(
        (a, b) =>
            a.$isDisabled - b.$isDisabled || ("" + a.name).localeCompare(b.name)
    );

    this.users.selected = this.users.all.filter(
        user => user.inInitialSelection
    );

    this.csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    this.persistPlayedSongAndFetchNext();

    this.websocket = new WebSocket(`wss://${window.location.host}/ws/dynamicplaylists/${this.playlistId}/`);
    this.websocket.onmessage = this.onWebsocketMessage;
    this.websocket.onclose = () => {
      console.error('Websocket closed unexpectedly');
    };
  }
};
</script>