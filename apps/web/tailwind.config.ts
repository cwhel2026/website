import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        asphalt: {
          DEFAULT: "#1a1f1e",
          950: "#0d1010",
          900: "#151a19",
          800: "#1f2624",
        },
        restore: {
          green: "#3d8f6c",
          dark: "#2a6b4f",
          muted: "#e8f3ed",
        },
        stone: {
          wash: "#f4f2ee",
          line: "#e2ded6",
        },
        brand: {
          ink: "#151515",
          charcoal: "#242424",
          gold: "#DDB747",
          paper: "#F8F8F5",
          line: "#E4E1D8",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        lift: "0 24px 48px -12px rgba(13, 16, 16, 0.18)",
      },
      animation: {
        "fade-up": "fade-up 0.6s ease-out forwards",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(12px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;