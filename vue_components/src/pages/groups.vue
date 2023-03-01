<template>
  <form :action="create_playlist_url" method="post">
    <div class="mb-3">
      <p v-if="ready_guilds_count === 0" class="text-warning">
        You're all alone in here, go and invite some friends to use Melting Potlist!
      </p>
      <label class="form-label">My groups</label>
      <Multiselect
          v-model="user_guilds.selected"
          :options="user_guilds.all"
          label="name"
          track-by="id"
          :option-height="60"
          placeholder=""
      ></Multiselect>
    </div>
    <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken">
    <input id="selectedGuilds" name="selectedGuilds" type="hidden" :value="selectedGuilds">
    <div v-if="user_guilds.selected.length">
      <button type="submit" class="btn btn-primary">Continue with selected groups</button>
    </div>
  </form>
</template>

<script>
import Multiselect from "../components/Multiselect.vue";

export default {
  components: {
    Multiselect
  },
  computed: {
    selectedGuilds() {
      return this.user_guilds.selected.map(guild => guild.id);
    }
  },
  data() {
    return {
      user_guilds: {
        all: [],
        selected: []
      },
      ready_guilds_count: 0,
      create_playlist_url: null,
      csrfToken: null
    };
  },
  mounted() {
    this.user_guilds.all = this.$window.context.user_guilds;
    this.ready_guilds_count = this.$window.context.ready_guilds_count;
    this.create_playlist_url = this.$window.context.create_playlist_url;
    this.csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
  }
};
</script>