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
            '0': '0',
            '1': '1px',
            '2': '2px',
            '3': '3px',
            '4': '4px',
            '6': '6px',
            '8': '8px',
        },
        ...{{ themeoverride }},
    },
    safelist: [
        "htmx-request"
    ],
    daisyui: {
        themes: {{ daisyuithemes }},
    },
    plugins: [
        require("daisyui"),
    ]
}
