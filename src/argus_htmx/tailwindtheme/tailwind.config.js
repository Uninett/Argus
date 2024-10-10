const projectPaths = [
    '../templates/**/*.html',
    './**/templates/**/*.html',
    'src/argus_htmx/templates/**/*.html'
];

const contentPaths = [...projectPaths];
console.log(`tailwindcss will scan ${contentPaths}`);

module.exports = {
    content: contentPaths,
    theme: {
        borderWidth: {
            DEFAULT: '2px',
        },
        ...{},
    },
    safelist: [
        "htmx-request"
    ],
    daisyui: {
        themes: [
            "dark",
            "light",
            {
              "argus": {
                "primary": "#006d91",
                "primary-content": "#d1e1e9",
                "secondary": "#f3b61f",
                "secondary-content": "#140c00",
                "accent": "#c84700",
                "accent-content": "#f8dbd1",
                "neutral": "#006d91",
                "neutral-content": "#d1e1e9",
                "base-100": "#edfaff",
                "base-200": "#ced9de",
                "base-300": "#b0babd",
                "base-content": "#141516",
                "info": "#0073e5",
                "info-content": "#000512",
                "success": "#008700",
                "success-content": "#d3e7d1",
                "warning": "#ee4900",
                "warning-content": "#140200",
                "error": "#e5545a",
                "error-content": "#120203"
              }
            }
          ],
    },
    plugins: [
        require("daisyui"),
    ]
}
