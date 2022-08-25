<template>
  <form :action="create_playlist_url" method="post">
    <div class="mb-3">
      <label class="form-label">My groups</label>
      <Multiselect
          v-model="user_guilds.selected"
          :options="user_guilds.all"
          label="name"
          track-by="id"
          :option-height="60"
          placeholder=""
      ></Multiselect>
      <!--        <div class="form-text">-->
      <!--          Who will provide the good vibes ?-->
      <!--        </div>-->
    </div>
    <div class="mb-3">
      <label class="form-label">Other groups</label>
      <Multiselect
          v-model="other_guilds.selected"
          :options="other_guilds.all"
          label="name"
          track-by="id"
          :option-height="60"
          placeholder=""
      ></Multiselect>
      <!--        <div class="form-text">-->
      <!--          Who will provide the good vibes ?-->
      <!--        </div>-->
    </div>
    <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken">
    <input id="selectedGuilds" name="selectedGuilds" type="hidden" :value="selectedGuilds">
    <div v-if="user_guilds.selected.length + other_guilds.selected.length > 0">
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
      const selectedUserGuildsIds = this.user_guilds.selected.map(guild => guild.id);
      const otherUserGuildsIds = this.other_guilds.selected.map(guild => guild.id);
      return [...selectedUserGuildsIds, ...otherUserGuildsIds];
    }
  },
  data() {
    return {
      user_guilds: {
        all: [],
        selected: []
      },
      other_guilds: {
        all: [],
        selected: []
      },
      create_playlist_url: null,
      csrfToken: null
    };
  },
  mounted() {
    this.user_guilds.all = this.$window.context.user_guilds;
    this.other_guilds.all = this.$window.context.other_guilds;
    this.create_playlist_url = this.$window.context.create_playlist_url;
    this.csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
  }
};
</script>