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
        }
    },
    daisyui: {
        themes: {{ daisyuithemes }},
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require("daisyui"),
    ]
}