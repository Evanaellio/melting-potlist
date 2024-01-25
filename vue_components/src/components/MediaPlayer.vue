<template>
  <vue-title v-if="currentMedia" :title="currentMedia.title"></vue-title>
  <div v-if="currentMedia">
    <canvas v-if="!audioOnly && enableBacklight" ref="backlight" id="backlight"></canvas>
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
        v-on:volumechange="onVolumeChange"
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
          v-if="!audioOnly"
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
import VueTitle from "/src/components/VueTitle.vue";

export default {
  components: {
    VueTitle
  },

  emits: [
    "media-started",
    "media-playing",
    "media-played",
    "media-seeked",
    "initial-playback-started",
    "play",
    "pause"
  ],
  props: ["nextMediaProp", "mediaPlayingEventTiming", "isMobile", "remoteStatus"],

  watch: {
    nextMediaProp: function (newVal) {
      this.nextMedia = newVal;
      this.playNextSong(false);
    },
    remoteStatus: function (newStatus) {
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
      initialPlaybackStarted: false,
      enableBacklight: false
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
    onVolumeChange(event) {
      // Only store new volume if change is triggered by user
      if (event.isTrusted) {
        localStorage.setItem("volume", this.$refs.audio_player.volume.toString());
      }
    },
    onAudioPlay() {
      this.$emit("play", {
        currentTime: this.$refs.audio_player.currentTime
      });
      if (this.$refs.video_player) {
        this.$refs.video_player.play();
      }
      navigator.mediaSession.metadata = new window.MediaMetadata({
        title: this.currentMedia.title,
        artist: this.currentMedia.artist,
        artwork: [{src: this.currentMedia.thumbnail}]
      });
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
      let localVolume = localStorage.getItem("volume");
      if (localVolume !== null) {
        this.$refs.audio_player.volume = parseFloat(localVolume);
      }
      console.log("Start initial playback", this.$refs.audio_player.paused);
      this.$refs.audio_player.play();
      console.log("Start initial playback", this.$refs.audio_player.paused);
      this.initialPlaybackStarted = true;
      this.$emit("initial-playback-started");
    },
    updateMediaSession() {
      navigator.mediaSession.setPositionState({
        duration: this.$refs.audio_player.duration,
        playbackRate: this.$refs.audio_player.playbackRate,
        position: this.$refs.audio_player.currentTime,
      });
    },
    updateBacklight() {
      if (this.enableBacklight && this.$refs.video_player) {
        const video = this.$refs.video_player;
        const backlight = this.$refs.backlight;
        const ctx = backlight.getContext('2d');
        ctx.filter='opacity(5%)';
        ctx.globalCompositeOperation = 'source-over';
        ctx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight, 0, 0, backlight.width, backlight.height);
        ctx.restore();
      }
    }
  },
  mounted() {
    if (this.mediaPlayingEventTiming > 0) {
      this.mediaPlayingInterval = setInterval(
          this.mediaPlaying,
          this.mediaPlayingEventTiming * 1000
      );
    }
    if (this.isMobile) {
      this.audioOnly = true;
    } else {
      setInterval(this.updateBacklight, 100);
      window.addEventListener("keypress", e => {
        if (e.code === "KeyB") {
          this.enableBacklight = !this.enableBacklight;
          console.log("Backlight enabled = ", this.enableBacklight);
        }
      });
    }
    if (!this.remoteStatus) {
      navigator.mediaSession.setActionHandler('previoustrack', () => {
        this.$refs.audio_player.currentTime = 0;
      });
      navigator.mediaSession.setActionHandler('nexttrack', () => {
        this.$refs.audio_player.currentTime = this.$refs.audio_player.duration;
      });
      navigator.mediaSession.setActionHandler('seekbackward', () => {
        this.$refs.audio_player.currentTime = this.$refs.audio_player.currentTime - 10;
      });
      navigator.mediaSession.setActionHandler('seekforward', () => {
        this.$refs.audio_player.currentTime = this.$refs.audio_player.currentTime + 10;
      });
    }
    setInterval(this.updateMediaSession, 1000);
  },
};
</script>

<style>
/* Disable video controls when in fullscreen on Chromium browsers */
video::-webkit-media-controls {
  display: none !important;
}
</style>