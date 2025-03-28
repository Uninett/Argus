const projectPaths = [
    '../templates/**/*.html',
    './**/templates/**/*.html',
    'src/argus_htmx/templates/**/*.html',
    '!**/templates/**/admin/**'
];

const contentPaths = [...projectPaths];
console.log(`tailwindcss will scan ${contentPaths}`);

module.exports = {
    content: contentPaths,
    theme: {
        borderWidth: {
            DEFAULT: '2px',
            '0': '0',
            '1': '1px',
            '2': '2px',
            '3': '3px',
            '4': '4px',
            '6': '6px',
            '8': '8px',
        },
        ...{},
        extend:{
            colors: {
                "severity-primary-1": "red",
                "severity-primary-2": "orange",
                "severity-primary-3": "yellow",
                "severity-primary-4": "green",
                "severity-primary-5": "blue",
                "severity-secondary-1": "white",
                "severity-secondary-2": "black",
                "severity-secondary-3": "black",
                "severity-secondary-4": "white",
                "severity-secondary-5": "white",

            },
        },
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
                "color-scheme": "light",
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
