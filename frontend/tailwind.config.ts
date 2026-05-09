import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0F0F0F",
        paper: "#F8FAFC",
        alert: "#FF4444",
      },
      fontFamily: {
        mono: ["Geist Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui"],
      },
      boxShadow: {
        urgent: "0 0 0 1px rgba(255, 68, 68, 0.35), 0 18px 60px rgba(0, 0, 0, 0.35)",
      },
    },
  },
  plugins: [],
};

export default config;
