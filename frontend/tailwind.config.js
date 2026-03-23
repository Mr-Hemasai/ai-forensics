/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#08111f",
        panel: "#0f172a",
        accent: "#f59e0b",
        alert: "#ef4444",
        mint: "#14b8a6"
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'DM Sans'", "sans-serif"]
      },
      boxShadow: {
        glow: "0 24px 80px rgba(15, 23, 42, 0.35)"
      }
    }
  },
  plugins: []
}
