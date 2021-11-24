<template>
  <form>
    <div class="mb-3">
      <label class="form-label">Music curators</label>
      <Multiselect
        v-model="users.selected"
        :options="users.all"
        label="name"
        track-by="id"
        :option-height="60"
        placeholder=""
      ></Multiselect>
      <div v-if="!selectedUsers.length" class="text-danger">
        You can't listen to music if nobody's providing some !
      </div>
      <div class="form-text">
        Who will provide the good vibes ?
      </div>
    </div>
    <div class="mb-3">
      <label class="form-label">Listeners</label>
      <div class="form-check">
        <input
          class="form-check-input"
          type="radio"
          value="solo"
          id="listenersSolo"
          v-model="groupMode"
        />
        <label class="form-check-label" for="listenersSolo">
          <i class="bi bi-person-fill"></i> I'm just discovering songs by myself
        </label>
      </div>
      <div class="form-check">
        <input
          class="form-check-input"
          type="radio"
          value="group"
          id="listenersGroup"
          v-model="groupMode"
        />
        <label class="form-check-label" for="listenersGroup">
          <i class="bi bi-people-fill"></i> The whole gang will be grooving with
          me
        </label>
      </div>
      <div class="form-text">Who will listen along ?</div>
    </div>

    <div v-if="groupMode === 'solo'">
      Playlist and listening stats won't be saved for a solo music discovery
      session
    </div>

    <div class="mb-3" v-if="groupMode === 'group'">
      <label for="titleInput" class="form-label"> Title </label>
      <input
        v-model="title"
        type="text"
        class="form-control"
        id="titleInput"
        aria-describedby="titleHelp"
        placeholder="Unnamed dynamic playlist"
      />
      <div id="titleHelp" class="form-text">
        Make this playlist memorable !
      </div>
    </div>

    <div v-if="groupMode && selectedUsers.length">
      <br />
      <br />
      <button
        type="button"
        class="btn btn-primary"
        v-on:click="createDynamicPlaylist()"
      >
        Let's groove <i class="bi bi-music-note-beamed"></i>
      </button>
    </div>
  </form>
</template>

<script>
import Multiselect from "../components/Multiselect.vue";

export default {
  components: {
    Multiselect
  },
  data() {
    return {
      users: {
        selected: [],
        all: []
      },
      title: "",
      groupMode: null,
      csrfToken: null
    };
  },
  computed: {
    selectedUsers() {
      return this.users.selected.map(item => item.id);
    }
  },
  methods: {
    async createDynamicPlaylist() {
      const dynamicPlaylist = {
        groups: [],
        users: this.selectedUsers
      };

      if (this.groupMode === "group") {
        dynamicPlaylist.groups = [this.$window.context.guild_id];

        if (this.title !== null && this.title !== "") {
          dynamicPlaylist.title = this.title;
        }
      }

      await fetch("/api/dynamicplaylists/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.csrfToken
        },
        body: JSON.stringify(dynamicPlaylist)
      })
        .then(response => {
          if (!response.ok) {
            throw new Error("HTTP status : " + response.status);
          }
          return response.json();
        })
        .then(data => (window.location.href = "/playlists/" + data.id))
        .catch(error => {
          console.error("Error:", error);
        });
    }
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
  }
};
</script>