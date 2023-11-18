<template>
  <template v-for="guild in guilds" v-bind:key="guild.id">
    <div class="mb-3">
      <label class="form-label">{{ guild.name }}</label>
      <Multiselect
          v-model="guild.users.selected"
          :options="guild.users.all"
          label="name"
          track-by="id"
          :option-height="60"
          placeholder=""
          @select="onSelectUser"
          @remove="onRemoveUser"
      ></Multiselect>
    </div>
  </template>

  <br/>
  <MediaPlayer
      ref="mediaPlayer"
      :next-media-prop="nextMedia"
      :media-playing-event-timing="1"
      :is-mobile="this.$window.context.isMobile"
      @media-playing="onMediaPlaying"
      @media-started="onMediaStarted"
      @media-played="onMediaPlayed"
      @media-seeked="updateStatus()"
      @play="updateStatus()"
      @pause="updateStatus()"
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
      guilds: [],
      playlistId: null,
      csrfToken: null,
      nextMedia: null,
      websocket: null,
      currentMediaPersisted: false
    };
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
          this.persistPlayedMediaAndFetchNext();
        }
        this.updateStatus();
      });
    },
    persistPlayedMediaAndFetchNext(playedMedia = null) {
      if (playedMedia !== null) {
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
            body: JSON.stringify({trackId: playedMedia?.track_id, userId: playedMedia?.user_id})
          }
      )
          .then(response => response.json())
          .then(jsonData => (this.nextMedia = jsonData))
          .then(() => this.updateStatus())
          .catch(reason => console.error(reason));
    },
    onMediaPlaying(event) {
      if (event.elapsedTime > 30 && event.nextMedia === null) {
        this.persistPlayedMediaAndFetchNext(event.currentMedia);
      }
    },
    onMediaStarted() {
      this.currentMediaPersisted = false;
    },
    onMediaPlayed(event) {
      // Should only happen when skipping or for medias less than or around 30 seconds in length
      if (event.nextMedia === null) {
        this.persistPlayedMediaAndFetchNext(event.currentMedia);
      }
    },
    sendWebsocketData(data) {
      this.websocket.send(JSON.stringify(data));
    },
    selectUser(username) {
      for (const guild of this.guilds) {
        for (const user of guild.users.all) {
          if (user.name === username) {
            if (!guild.users.selected.includes(user)) {
              guild.users.selected.push(user);
              this.onSelectUser(user);
            }
          }
        }
      }
    },
    onWebsocketMessage(event) {
      console.log("Message from " + this.websocket, event);

      const data = JSON.parse(event.data);

      if (data.action === "query_status" && data.from) {
        this.updateStatus(data.from);
      } else if (data.action == "connect") {
        this.selectUser(data.username);
      }
    },
    updateStatus(toUser = undefined) {
      let selectedUsers = []
      for (const guild of this.guilds) {
        for (const user of guild.users.selected) {
          selectedUsers.push(user);
        }
      }

      this.sendWebsocketData({
        action: "update_status",
        to: toUser,
        status: this.$refs.mediaPlayer.status(),
        selectedUsers: selectedUsers,
      });
    }
  },
  created() {
    this.playlistId = this.$window.context.playlistId;
  },
  mounted() {
    this.guilds = this.$window.context.guilds;
    for (const guild of this.guilds) {
      guild.users.all = guild.users.sort(
          (a, b) =>
              a.$isDisabled - b.$isDisabled || ("" + a.name).localeCompare(b.name)
      );
      guild.users.selected = guild.users.all.filter(
          user => user.inInitialSelection
      );
    }

    this.csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    this.persistPlayedMediaAndFetchNext();

    this.websocket = new WebSocket(
        `${this.$window.context.websocketProtocol}://${window.location.host}/ws/dynamicplaylists/${this.playlistId}/`
    );
    this.websocket.addEventListener("message", this.onWebsocketMessage);
    this.websocket.addEventListener("close", () => {
      console.log(this.websocket);
      console.error("Websocket closed unexpectedly");
    });
  }
};
</script>