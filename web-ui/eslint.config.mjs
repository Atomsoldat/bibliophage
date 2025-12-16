// eslint.config.mjs
import antfu from '@antfu/eslint-config'

// https://github.com/antfu/eslint-config?tab=readme-ov-file#rules-overrides
// https://eslint.vuejs.org/user-guide/
// https://eslint.vuejs.org/rules/

export default antfu({
  rules: {
    // override default which would abbreviate v-bind:xyz to :xyz
    'vue/v-bind-style': ['error', 'longform'],
  },
})
