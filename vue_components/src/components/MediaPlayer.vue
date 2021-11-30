<template>
  <div v-if="currentMedia">
    <video
      v-show="!audioOnly"
      ref="video_player"
      id="video-player"
      muted
      style="width: 100%"
      height="675"
      v-on:playing="syncAudioAndVideo"
      :src="currentMedia.video"
    >
      <track
        label="English"
        kind="subtitles"
        srclang="en"
        default
        :src="currentMedia.subtitles_url"
      />
    </video>

    <audio
      ref="audio_player"
      id="audio-player"
      autoplay
      controls
      style="width: 100%"
      :src="currentMedia.audio"
      v-on:play="this.$refs.video_player.play()"
      v-on:pause="this.$refs.video_player.pause()"
      v-on:seeked="syncAudioAndVideo"
      v-on:ended="onMediaEnded"
    ></audio>

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
      v-on:click="this.$refs.video_player.requestFullscreen()"
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

    <p>{{ currentMedia.title }}</p>
  </div>
  <p v-if="nextMedia">Up next: {{ nextMedia.title }}</p>
</template>

<script>
export default {
  emits: ["media-started", "media-playing", "media-played"],
  props: ["nextMediaProp", "mediaPlayingEventTiming"],
  watch: {
    nextMediaProp: function(newVal) {
      this.nextMedia = newVal;
      this.playNextSong(false);
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
      mediaInProgress: false
    };
  },
  methods: {
    syncAudioAndVideo() {
      let audioVideoDesync = Math.abs(
        this.$refs.video_player.currentTime -
          this.$refs.audio_player.currentTime
      );

      // Tolerate up to 200 ms of delay between audio and video, and try to synchronize when it's beyond that
      if (audioVideoDesync > 0.2) {
        this.$refs.video_player.currentTime = this.$refs.audio_player.currentTime;
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