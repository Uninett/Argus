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
