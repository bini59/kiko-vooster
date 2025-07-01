/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        jp: ["Noto Sans JP", "Hiragino Sans", "Yu Gothic", "sans-serif"],
      },
      colors: {
        primary: {
          50: "#fff0f0",
          100: "#ffdddd",
          200: "#ffc0c0",
          300: "#ff9494",
          400: "#ff5757",
          500: "#ff2323",
          600: "#ed0707",
          700: "#c80606",
          800: "#a50a0a",
          900: "#881010",
        },
      },
    },
  },
  plugins: [
    // require('@tailwindcss/typography'),
    require("daisyui"),
  ],
  daisyui: {
    themes: [
      {
        light: {
          primary: "#ff2323",
          secondary: "#f6d860",
          accent: "#37cdbe",
          neutral: "#3d4451",
          "base-100": "#ffffff",
          info: "#3abff8",
          success: "#36d399",
          warning: "#fbbd23",
          error: "#f87272",
        },
        dark: {
          primary: "#ff2323",
          secondary: "#f6d860",
          accent: "#37cdbe",
          neutral: "#191d24",
          "base-100": "#1f2937",
          info: "#3abff8",
          success: "#36d399",
          warning: "#fbbd23",
          error: "#f87272",
        },
      },
    ],
    darkTheme: "dark",
    base: true,
    styled: true,
    utils: true,
    rtl: false,
    prefix: "",
    logs: true,
  },
};
