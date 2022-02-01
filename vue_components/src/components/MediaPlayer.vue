<template>
  <div v-if="currentMedia">
    <video
      v-if="!audioOnly"
      v-show="initialPlaybackStarted"
      ref="video_player"
      id="video-player"
      muted
      style="width: 100%"
      height="675"
      v-on:loadedmetadata="syncAudioAndVideo"
      v-on:playing="syncAudioAndVideo"
      :src="currentMedia.video"
      v-on:dblclick="toggleFullscreen"
    >
      <track
        label="English"
        kind="subtitles"
        srclang="en"
        default
        :src="currentMedia.subtitles_url"
      />
    </video>

    <button
      type="button"
      class="btn btn-primary btn-lg btn-block"
      v-on:click="startInitialPlayback"
      v-if="!initialPlaybackStarted"
    >
      Click here to start music playback
    </button>

    <audio
      ref="audio_player"
      id="audio-player"
      controls
      v-bind:autoplay="initialPlaybackStarted ? 'autoplay' : undefined"
      style="width: 100%"
      :src="currentMedia.audio"
      v-show="initialPlaybackStarted"
      v-on:play="onAudioPlay"
      v-on:pause="onAudioPause"
      v-on:seeked="onMediaSeeked"
      v-on:ended="onMediaEnded"
    ></audio>

    <div id="buttons" v-show="initialPlaybackStarted">
      <button
        type="button"
        class="btn btn-outline-primary"
        style="font-size: 1.5rem"
        v-on:click="audioOnly = !audioOnly"
      >
        <i
          :class="audioOnly ? 'bi bi-camera-video' : 'bi bi-camera-video-off'"
        ></i>
      </button>
      <button
        type="button"
        class="btn btn-outline-primary"
        style="font-size: 1.5rem"
        v-on:click="toggleFullscreen"
      >
        <i class="bi bi-arrows-fullscreen"></i>
      </button>
      <a :href="currentMedia.url" target="_blank">
        <button
          type="button"
          class="btn btn-outline-primary"
          style="font-size: 1.5rem"
        >
          <i class="bi bi-box-arrow-up-right"></i>
        </button>
      </a>
    </div>

    <div id="metadata" v-show="initialPlaybackStarted">
      <p>{{ currentMedia.title }}</p>
      <p v-if="nextMedia">Up next: {{ nextMedia.title }}</p>
    </div>
  </div>
</template>

<script>
export default {
  emits: [
    "media-started",
    "media-playing",
    "media-played",
    "media-seeked",
    "initial-playback-started",
    "play",
    "pause"
  ],
  props: ["nextMediaProp", "mediaPlayingEventTiming", "remoteStatus"],

  watch: {
    nextMediaProp: function(newVal) {
      this.nextMedia = newVal;
      this.playNextSong(false);
    },
    // audioOnly: function(newVal) {
    //   if(newVal === false) {
    //     console.log("AudioOnly change", this.$refs.video_player.paused);
    //     this.$refs.video_player.play();
    //     this.syncAudioAndVideo();
    //     console.log("AudioOnly change", this.$refs.video_player.paused);
    //   }
    // },
    remoteStatus: function(newStatus) {
      this.currentMedia = newStatus.currentMedia;
      this.nextMedia = newStatus.nextMedia;

      if (this.$refs.audio_player) {
        let remoteAudioDesync = Math.abs(
          newStatus.elapsedTime - this.$refs.audio_player.currentTime
        );

        // Only synchronize if delay between host audio and listener audio is higher than 500 ms
        if (remoteAudioDesync > 0.5) {
          this.$refs.audio_player.currentTime = newStatus.elapsedTime;
        }

        if (newStatus.paused) {
          this.$refs.audio_player.pause();
        } else {
          this.$refs.audio_player.play();
        }
      }
    }
  },
  data() {
    return {
      /* Media format :
          {
              video: "",
              audio: "",
              subtitles_url: "",
              title: "",
          }
      */
      currentMedia: null,
      nextMedia: null,
      audioOnly: false,
      mediaPlayingInterval: null,
      mediaInProgress: false,
      initialPlaybackStarted: false
    };
  },
  methods: {
    onMediaSeeked() {
      this.$emit("media-seeked", {
        elapsedTime: this.$refs.audio_player.currentTime
      });
      this.syncAudioAndVideo();
    },
    syncAudioAndVideo() {
      if (this.$refs.video_player) {
        let audioVideoDesync = Math.abs(
          this.$refs.video_player.currentTime -
            this.$refs.audio_player.currentTime
        );

        // Only synchronize if delay between audio and video is higher than 200 ms
        if (audioVideoDesync > 0.2) {
          this.$refs.video_player.currentTime = this.$refs.audio_player.currentTime;
        }

        if (this.$refs.audio_player.paused) {
          this.$refs.video_player.pause();
        } else {
          this.$refs.video_player.play();
        }
      }
    },
    toggleFullscreen() {
      if (!document.fullscreenElement) {
        this.$refs.video_player.requestFullscreen();
      } else {
        document.exitFullscreen();
      }
    },
    onMediaEnded() {
      this.$emit("media-played", {
        currentMedia: this.currentMedia,
        nextMedia: this.nextMedia,
        elapsedTime: this.$refs.audio_player.currentTime
      });

      this.mediaInProgress = false;

      this.playNextSong(false);
    },
    onAudioPlay() {
      this.$emit("play", {
        currentTime: this.$refs.audio_player.currentTime
      });
      if (this.$refs.video_player) {
        this.$refs.video_player.play();
      }
    },
    onAudioPause() {
      this.$emit("pause", {
        currentTime: this.$refs.audio_player.currentTime
      });

      if (this.$refs.video_player) {
        this.$refs.video_player.pause();
      }
    },
    playNextSong(force = false) {
      if (
        this.nextMedia != null &&
        (force === true || this.mediaInProgress === false)
      ) {
        this.currentMedia = this.nextMedia;
        this.nextMedia = null;
        this.$emit("media-started", {
          currentMedia: this.currentMedia
        });
        this.mediaInProgress = true;
      }
    },

    mediaPlaying() {
      this.$emit("media-playing", {
        currentMedia: this.currentMedia,
        nextMedia: this.nextMedia,
        elapsedTime: this.$refs.audio_player.currentTime
      });
    },
    status() {
      return {
        currentMedia: this.currentMedia,
        nextMedia: this.nextMedia,
        elapsedTime: this.$refs.audio_player.currentTime,
        paused: this.$refs.audio_player.paused
      };
    },
    startInitialPlayback() {
      console.log("Start initial playback", this.$refs.audio_player.paused);
      this.$refs.audio_player.play();
      console.log("Start initial playback", this.$refs.audio_player.paused);
      this.initialPlaybackStarted = true;
      this.$emit("initial-playback-started");
    }
  },
  mounted() {
    if (this.mediaPlayingEventTiming > 0) {
      this.mediaPlayingInterval = setInterval(
        this.mediaPlaying,
        this.mediaPlayingEventTiming * 1000
      );
    }
  }
};
</script>

<style>
/* Disable video controls when in fullscreen on Chromium browsers */
video::-webkit-media-controls {
  display: none !important;
}
</style>