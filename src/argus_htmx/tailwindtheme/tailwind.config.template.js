const projectPaths = [
    '../templates/**/*.html',
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
    daisyui: {
        themes: {{ daisyuithemes }},
    },
    plugins: [
        require("daisyui"),
    ]
}
