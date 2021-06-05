<template>
    <VueMultiselect
        v-model="selected"
        :hide-selected="true"
        :close-on-select="false"
        :multiple="true"
    >
        <template v-slot:tag="props">
            <span class="multiselect__tag">
                <img
                    class="option__image"
                    :src="getDiscordAvatar(props.option, 16)"
                    height="16"
                    width="16"
                    :data-default-image="props.option.default_image"
                    onerror="this.src = this.dataset.defaultImage"
                />
                <span>{{ props.option.name }}</span>
                <i
                    aria-hidden="true"
                    tabindex="1"
                    class="multiselect__tag-icon"
                    @click="props.remove(props.option)"
                ></i>
            </span>
        </template>
        <template v-slot:option="props">
            <img
                class="option__image"
                :src="getDiscordAvatar(props.option, 32)"
                height="32"
                width="32"
                :data-default-image="props.option.default_image"
                onerror="this.src = this.dataset.defaultImage"
            />
            <div class="option__desc">
                <div class="option__desc">
                    <span class="option__title">{{ props.option.name }}</span>
                </div>
            </div>
        </template>
    </VueMultiselect>
</template>

<script>
import VueMultiselect from "vue-multiselect";
export default {
    components: { VueMultiselect },
    data() {
        return {
            selected: null,
        };
    },
    methods: {
        getDiscordAvatar: function (user, size) {
            return `${user.image}?size=${size}`;
        },
    },
};
</script>

<style>
.option__image {
    max-height: 80px;
    margin-right: 10px;
}

.option__desc,
.option__image {
    display: inline-block;
    vertical-align: middle;
}

.option__title {
    font-size: 24px;
}

.multiselect__tag,
.multiselect__option--highlight {
    background: var(--discord-blue);
}

.multiselect__tags,
.multiselect__content-wrapper {
    background: var(--discord-dark);
    border: 2px solid var(--discord-black);
}

.multiselect__content-wrapper {
    border-top-width: 0;
}

.multiselect--active > .multiselect__tags {
    border-color: var(--discord-blue);
}

.multiselect,
.multiselect__tag-icon:focus,
.multiselect__tag-icon:hover,
.multiselect__option--highlight:after,
.multiselect__option--disabled,
.multiselect__input,
.multiselect__single {
    color: white;
    background: none;
}

.multiselect__option--disabled {
    opacity: 25%;
}

.multiselect__tag-icon:after {
    color: var(--discord-black);
}
</style>