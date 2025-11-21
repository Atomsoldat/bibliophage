// note, that the configuration mechanism will change in v4
// https://v3.tailwindcss.com/docs/configuration
// https://tailwindcss.com/blog/tailwindcss-v4#css-first-configuration

import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: ["light", "dark"],
    darkTheme: "dark",
  },
} satisfies Config
